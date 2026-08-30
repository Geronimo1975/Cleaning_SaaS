"""Ciclul de viață al cererii și al ofertelor."""

from django.db import transaction
from django.utils import timezone

from apps.accounts.enums import EntityType, LegalStatus

from .models import (
    Frequency,
    Invitation,
    Offer,
    OfferStatus,
    RequestStatus,
    ServiceRequest,
)
from .scoring import suggest_providers


class MarketplaceError(ValueError):
    pass


@transaction.atomic
def publish_request(request: ServiceRequest, invite: bool = True) -> ServiceRequest:
    if request.status != RequestStatus.DRAFT:
        raise MarketplaceError("Doar o ciornă poate fi publicată.")
    if request.offers_close_at <= timezone.now():
        raise MarketplaceError("Termenul de ofertare trebuie să fie în viitor.")

    from apps.cooperative.models import DispatchPolicy

    request.status = RequestStatus.OPEN
    request.published_at = timezone.now()
    request.dispatch_policy = DispatchPolicy.current()
    request.save(update_fields=["status", "published_at", "dispatch_policy"])

    if invite:
        for provider, score, reasons in suggest_providers(request):
            Invitation.objects.get_or_create(
                request=request, provider=provider,
                defaults={"score": score, "reasons": {k: str(v) for k, v in reasons.items()}},
            )
    return request


@transaction.atomic
def submit_offer(request: ServiceRequest, provider, **data) -> Offer:
    if not request.is_open:
        raise MarketplaceError("Cererea nu mai primește oferte.")
    if provider.pk == request.client_id:
        raise MarketplaceError("Nu poți oferta la propria cerere.")
    if not provider.is_provider:
        raise MarketplaceError("Contul nu are capabilitate de prestator.")

    offer, created = Offer.objects.update_or_create(
        request=request, provider=provider,
        defaults={**data, "status": OfferStatus.SUBMITTED},
    )
    return offer


@transaction.atomic
def withdraw_offer(offer: Offer, provider) -> Offer:
    if offer.provider_id != provider.pk:
        raise MarketplaceError("Oferta nu îți aparține.")
    if offer.status != OfferStatus.SUBMITTED:
        raise MarketplaceError("Oferta nu mai poate fi retrasă.")
    offer.status = OfferStatus.WITHDRAWN
    offer.save(update_fields=["status"])
    return offer


def award_warnings(request: ServiceRequest, offer: Offer) -> list[str]:
    """
    Ce trebuie clarificat ÎNAINTE de atribuire. Nu blochează — informează.
    Blocarea ar fi greșită: platforma nu poate ști dacă prestatorul și-a
    înregistrat între timp activitatea.
    """
    warnings = []
    provider = offer.provider
    client_is_household = request.client.entity_type == EntityType.INDIVIDUAL

    if provider.entity_type == EntityType.INDIVIDUAL:
        if provider.legal_status == LegalStatus.UNDECLARED:
            warnings.append(
                "Prestatorul nu are un statut declarat. Într-o gospodărie privată, "
                "colaborarea trebuie să fie ori Minijob (înregistrat prin Haushaltsscheck "
                "la Minijob-Zentrale), ori activitate independentă cu Gewerbeanmeldung. "
                "Fără una dintre ele, e muncă nedeclarată."
            )
        elif provider.legal_status == LegalStatus.MINIJOB and client_is_household:
            warnings.append(
                "Colaborare de tip Minijob: clientul devine ANGAJATOR și trebuie să "
                "înregistreze raportul la Minijob-Zentrale (Haushaltsscheck), inclusiv "
                "asigurarea de accident."
            )

    if request.is_35a_eligible:
        warnings.append(
            "Pentru deducerea §35a, plata trebuie făcută prin transfer bancar, pe bază "
            "de factură. Plata în numerar nu e deductibilă."
        )

    if provider.verification_level == 0:
        warnings.append("Prestatorul nu are niciun nivel de verificare confirmat.")

    return warnings


@transaction.atomic
def award_offer(request: ServiceRequest, offer: Offer, actor) -> ServiceRequest:
    if request.client_id != actor.pk:
        raise MarketplaceError("Doar clientul poate atribui cererea.")
    if not request.is_open:
        raise MarketplaceError("Cererea nu mai este deschisă.")
    if offer.request_id != request.pk:
        raise MarketplaceError("Oferta nu aparține acestei cereri.")
    if offer.status != OfferStatus.SUBMITTED:
        raise MarketplaceError("Oferta nu mai este validă.")

    offer.status = OfferStatus.WON
    offer.save(update_fields=["status"])
    request.offers.filter(status=OfferStatus.SUBMITTED).exclude(pk=offer.pk).update(
        status=OfferStatus.LOST
    )
    request.status = RequestStatus.AWARDED
    request.awarded_offer = offer
    request.save(update_fields=["status", "awarded_offer"])
    return request


# Ce fel de contract urmează dintr-o ofertă câștigătoare, după statutul juridic
# al prestatorului. Nu e o preferință de produs: statutul decide cine e plătitorul
# legal, cine emite factura și cine datorează contribuțiile.
CONTRACT_TYPE_BY_STATUS = {
    LegalStatus.SELBSTSTAENDIG: "WERKVERTRAG",
    LegalStatus.KLEINUNTERNEHMER: "WERKVERTRAG",
    LegalStatus.COMPANY: "WERKVERTRAG",
    LegalStatus.MINIJOB: "MINIJOB",
}


def contract_type_for(offer) -> str:
    """Ridică MarketplaceError dacă statutul nu permite niciun contract valid."""
    status = offer.provider.legal_status
    if status == LegalStatus.UNDECLARED:
        raise MarketplaceError(
            "Prestatorul nu are un statut juridic declarat. Fără Minijob înregistrat "
            "sau Gewerbeanmeldung nu se poate genera un contract — orice altceva ar "
            "fi muncă nedeclarată."
        )
    try:
        return CONTRACT_TYPE_BY_STATUS[status]
    except KeyError as exc:
        raise MarketplaceError(f"Statut juridic neacoperit: {status}.") from exc


@transaction.atomic
def create_contract_from_offer(request: ServiceRequest, actor):
    """
    Atribuirea produce hârtie.

    Până acum, o cerere atribuită rămânea o înțelegere fără document. Contractul
    se naște din oferta CÂȘTIGĂTOARE, cu cifrele ei — durata estimată devine ore
    pe lună, prețul devine tarif orar. Nimeni nu retastează nimic, deci nimeni nu
    poate semna altceva decât ce s-a ofertat.

    La un prestator Minijob în gospodărie, CLIENTUL devine angajator: contractul
    e unul de muncă, iar înregistrarea la Minijob-Zentrale rămâne obligația lui.
    """
    from decimal import Decimal

    from apps.contracts.models import ContractDraft
    from apps.contracts.services import active_template

    if request.client_id != actor.pk:
        raise MarketplaceError("Doar clientul poate genera contractul.")
    offer = request.awarded_offer
    if request.status != RequestStatus.AWARDED or offer is None:
        raise MarketplaceError("Cererea nu este atribuită.")

    existing = ContractDraft.objects.filter(
        employer=request.client, worker=offer.provider, contract_type__isnull=False,
        start_date=offer.earliest_start, workplace=request.locality,
    ).first()
    if existing:
        return existing

    contract_type = contract_type_for(offer)
    template = active_template(contract_type)
    if template is None:
        raise MarketplaceError(f"Nu există șablon activ pentru {contract_type}.")

    monthly_minutes = Decimal(offer.estimated_minutes) * request.visits_per_month
    hours_per_month = (monthly_minutes / 60).quantize(Decimal("0.01"))

    return ContractDraft.objects.create(
        employer=request.client,
        worker=offer.provider,
        template=template,
        contract_type=contract_type,
        start_date=offer.earliest_start,
        hours_per_month=hours_per_month,
        hourly_wage=offer.implied_hourly,
        workplace=request.locality,
    )


# Cum se traduce frecvența cererii în ritmul unei `planning.Zone`.
# `Zone` știe doar „de n ori pe săptămână" (`apps/planning/models.py`), deci
# traducerea e posibilă DOAR pentru ritmuri săptămânale. La două săptămâni sau
# lunar nu se pot exprima fără a minți planificatorul — o cerere bilunară
# transformată în „1×/săptămână" ar produce dublul vizitelor contractate.
WEEKLY_VISITS = {
    Frequency.WEEKLY: 1,
}
UNSUPPORTED_FREQUENCY = {
    Frequency.ONE_TIME: "O prestație unică nu produce un obiectiv recurent.",
    Frequency.BIWEEKLY: (
        "Ritmul la două săptămâni nu poate fi exprimat de `Zone`, care numără "
        "vizite pe săptămână. Necesită un interval cu unitate și dată de ancorare."
    ),
    Frequency.MONTHLY: (
        "Ritmul lunar nu poate fi exprimat de `Zone`, care numără vizite pe "
        "săptămână. Necesită un interval cu unitate și dată de ancorare."
    ),
}


@transaction.atomic
def activate_recurring_request(request: ServiceRequest, actor):
    """
    Trecerea de la Vermittlung la execuție.

    Ce face: creează obiectivul și zona ÎN CONTUL PRESTATORULUI câștigător.
    Ce nu face, și nu are voie să facă: să creeze ture. Planificarea aparține
    firmei membre, nu platformei — `generate_week_plan` alocă doar oameni cu
    contract semnat la acel angajator. Alocarea peste granița dintre firme ar
    fi Arbeitnehmerüberlassung.

    Precondiție: contractul dintre client și prestator e SEMNAT. Un obiectiv
    activ fără contract semnat ar sugera o obligație care juridic nu există.
    """
    from apps.contracts.models import DraftStatus
    from apps.planning.models import Site, Zone

    if request.client_id != actor.pk:
        raise MarketplaceError("Doar clientul poate activa cererea.")
    offer = request.awarded_offer
    if request.status != RequestStatus.AWARDED or offer is None:
        raise MarketplaceError("Cererea nu este atribuită.")

    if request.frequency in UNSUPPORTED_FREQUENCY:
        raise MarketplaceError(UNSUPPORTED_FREQUENCY[request.frequency])
    visits = WEEKLY_VISITS[request.frequency]

    contract = _contract_for(request, offer)
    if contract is None or contract.status != DraftStatus.SIGNED:
        raise MarketplaceError(
            "Contractul trebuie semnat de ambele părți înainte de activare."
        )

    site, _ = Site.objects.get_or_create(
        account=offer.provider,
        name=request.title[:160],
        defaults={
            "locality": request.locality,
            "street": request.client.street,
            "postal_code": request.postal_code or request.client.postal_code,
        },
    )
    Zone.objects.get_or_create(
        site=site,
        name=request.category.name_de or request.category.name,
        defaults={
            "category": request.category,
            "area_sqm": request.area_sqm,
            "minutes_per_visit": offer.estimated_minutes,
            "visits_per_week": visits,
            "allowed_weekdays": request.preferred_weekdays or "1,2,3,4,5",
        },
    )

    request.status = RequestStatus.ACTIVE
    request.save(update_fields=["status"])
    return site


def _contract_for(request: ServiceRequest, offer):
    from apps.contracts.models import ContractDraft

    return ContractDraft.objects.filter(
        employer=request.client, worker=offer.provider,
        start_date=offer.earliest_start, workplace=request.locality,
    ).first()


@transaction.atomic
def cancel_request(request: ServiceRequest, actor) -> ServiceRequest:
    if request.client_id != actor.pk:
        raise MarketplaceError("Doar clientul poate anula cererea.")
    if request.status == RequestStatus.AWARDED:
        raise MarketplaceError("O cerere atribuită nu se anulează.")
    request.status = RequestStatus.CANCELLED
    request.save(update_fields=["status"])
    request.offers.filter(status=OfferStatus.SUBMITTED).update(status=OfferStatus.LOST)
    return request


def expire_requests(now=None) -> int:
    """Cererile la care a trecut termenul nu mai stau deschise la nesfârșit."""
    now = now or timezone.now()
    return ServiceRequest.objects.filter(
        status=RequestStatus.OPEN, offers_close_at__lte=now
    ).update(status=RequestStatus.EXPIRED)
