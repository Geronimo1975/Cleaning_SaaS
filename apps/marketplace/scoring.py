"""
Evaluarea ofertelor pe criterii multiple.

Premisa: clientul nu alege cel mai mic preț, ci cea mai bună potrivire. Dar un
scor opac e mai rău decât niciun scor — dacă nu se vede DE CE o ofertă e prima,
clientul nu are motive să aibă încredere în ordine, iar prestatorul respins nu
are ce corecta. De aceea fiecare scor vine cu descompunerea pe criterii.

Normalizarea se face în interiorul setului de oferte al cererii: un scor nu are
sens absolut, ci doar relativ la ce a primit clientul.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from apps.accounts.enums import EntityType

# Prețul contează, dar nu cât toate celelalte criterii la un loc. Cu price la
# 0,35 un prestator neverificat și fără experiență se clasa la egalitate cu unul
# verificat, cu documente și 10 ani de experiență — exact rezultatul pe care
# „bursa nu e licitație pe preț" ar trebui să-l excludă.
# Ponderile implicite, valabile cât timp membrii nu au votat altele. Într-o
# cooperativă regulile de repartizare se votează, deci trăiesc în
# `cooperative.DispatchPolicy` — rânduri datate, legate de hotărârea care le-a
# adoptat. Dicționarul de aici e doar fallback-ul de pornire.
DEFAULT_WEIGHTS = {
    "price": Decimal("0.30"),
    "verification": Decimal("0.25"),
    "experience": Decimal("0.20"),
    "availability": Decimal("0.15"),
    "proximity": Decimal("0.10"),
}
WEIGHTS = DEFAULT_WEIGHTS


def resolve_weights(request=None) -> dict[str, Decimal]:
    """
    Ponderile aplicabile: cele fixate pe cerere la publicare, altfel politica
    în vigoare azi, altfel valorile implicite.
    """
    from apps.cooperative.models import DispatchPolicy

    policy = getattr(request, "dispatch_policy", None)
    if policy is None:
        policy = DispatchPolicy.current()
    if policy is None:
        return DEFAULT_WEIGHTS
    return policy.as_weights()

CRITERION_LABELS = {
    "price": "Preț pe oră",
    "verification": "Nivel de verificare",
    "proximity": "Acoperire zonă",
    "experience": "Experiență",
    "availability": "Disponibilitate",
}


@dataclass
class ScoredOffer:
    offer: object
    total: Decimal
    breakdown: dict[str, Decimal] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def percent(self) -> int:
        return int(self.total * 100)

    weights: dict = field(default_factory=dict)

    def explain(self) -> list[tuple[str, int, str]]:
        weights = self.weights or DEFAULT_WEIGHTS
        return [
            (CRITERION_LABELS[k], int(v * 100), f"pondere {int(weights[k] * 100)} %")
            for k, v in self.breakdown.items()
        ]


def score_offers(request, offers=None) -> list[ScoredOffer]:
    from .models import OfferStatus

    offers = list(
        offers
        if offers is not None
        else request.offers.filter(status=OfferStatus.SUBMITTED).select_related(
            "provider__worker_profile", "provider__company_profile", "provider__locality"
        )
    )
    if not offers:
        return []

    hourly = [o.implied_hourly for o in offers]
    lo, hi = min(hourly), max(hourly)

    weights = resolve_weights(request)
    scored = []
    for offer in offers:
        breakdown = {
            "price": _price_score(offer.implied_hourly, lo, hi),
            "verification": _verification_score(offer.provider),
            "proximity": _proximity_score(offer.provider, request),
            "experience": _experience_score(offer.provider),
            "availability": _availability_score(offer, request),
        }
        total = sum(weights[k] * v for k, v in breakdown.items())
        scored.append(ScoredOffer(
            offer=offer,
            total=Decimal(total).quantize(Decimal("0.001")),
            breakdown=breakdown,
            weights=weights,
            notes=_notes(offer, request),
        ))
    # Departajare determinist la scor egal: prețul mai mic, apoi oferta mai veche.
    return sorted(scored, key=lambda s: (-s.total, s.offer.implied_hourly, s.offer.pk))


def _price_score(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    """Cel mai ieftin ia 1, cel mai scump 0. Dacă toate sunt egale, toate iau 1."""
    if hi == lo:
        return Decimal("1")
    return ((hi - value) / (hi - lo)).quantize(Decimal("0.001"))


def _verification_score(provider) -> Decimal:
    return (Decimal(provider.verification_level) / 3).quantize(Decimal("0.001"))


def _proximity_score(provider, request) -> Decimal:
    """
    Fără coordonate geocodate, proximitatea e o aproximare pe localități:
    aceeași localitate > localitate deservită declarat > nimic.
    Se înlocuiește cu distanță reală când `Locality` are lat/lon.
    """
    if provider.locality_id == request.locality_id:
        return Decimal("1")
    if provider.areas.filter(locality_id=request.locality_id).exists():
        return Decimal("0.7")
    return Decimal("0.2")


def _experience_score(provider) -> Decimal:
    if provider.entity_type == EntityType.INDIVIDUAL:
        profile = getattr(provider, "worker_profile", None)
        if not profile:
            return Decimal("0")
        return min(Decimal(profile.years_experience) / 10, Decimal("1")).quantize(Decimal("0.001"))

    profile = getattr(provider, "company_profile", None)
    if not profile:
        return Decimal("0")
    score = Decimal("0.4")
    if profile.has_liability_insurance:
        score += Decimal("0.4")
    if profile.hwk_registered:
        score += Decimal("0.2")
    return min(score, Decimal("1"))


def _availability_score(offer, request) -> Decimal:
    delay = (offer.earliest_start - request.earliest_start).days
    if delay <= 0:
        return Decimal("1")
    if delay >= 28:
        return Decimal("0")
    return (Decimal(28 - delay) / 28).quantize(Decimal("0.001"))


def _notes(offer, request) -> list[str]:
    """Semnalele care nu intră în scor, dar pe care clientul trebuie să le vadă."""
    notes = []
    if request.supplies_provided and offer.includes_supplies:
        notes.append("Oferta include materiale, deși clientul le pune la dispoziție.")
    if not request.supplies_provided and not offer.includes_supplies:
        notes.append("Materialele NU sunt incluse — costul real e mai mare.")
    if request.is_35a_eligible:
        notes.append(
            f"Deducere §35a estimată: {offer.deduction_35a} €/an "
            "(necesită factură și plată prin bancă)."
        )
    return notes


def suggest_providers(request, limit: int = 10):
    """
    Prestatori cărora le-ar putea interesa cererea.

    E o SUGESTIE, nu o repartizare: fiecare decide singur dacă ofertează și la
    ce preț. Un sistem care ar aloca automat munca unei persoane fizice ar
    îndeplini criteriile §7 SGB IV.
    """
    from apps.accounts.models import Account

    candidates = (
        Account.objects.published()
        .providers()
        .filter(services__category=request.category)
        .filter(areas__locality=request.locality)
        .exclude(pk=request.client_id)
        .distinct()
        .select_related("locality", "worker_profile", "company_profile")
    )

    ranked = []
    for provider in candidates:
        breakdown = {
            "verification": _verification_score(provider),
            "proximity": _proximity_score(provider, request),
            "experience": _experience_score(provider),
        }
        total = sum(breakdown.values()) / 3
        ranked.append((provider, Decimal(total).quantize(Decimal("0.01")), breakdown))
    ranked.sort(key=lambda row: -row[1])
    return ranked[:limit]
