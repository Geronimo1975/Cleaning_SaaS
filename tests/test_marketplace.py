"""
Bursa de servicii.

Două invariante pe care se sprijină tot modulul:

  1. Nu există alocare automată. Sistemul sugerează; prestatorul decide.
     Un sistem care repartizează munca unei persoane fizice bifează
     criteriile §7 SGB IV (Scheinselbstständigkeit).

  2. O ofertă nu dă acces la datele clientului. Altfel oricine ar putea
     oferta doar ca să afle o adresă.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.enums import Capability, EntityType, LegalStatus, VerificationLevel
from apps.accounts.models import User
from apps.accounts.profiles import AccountService, ServiceArea
from apps.accounts.services import create_account, publish_profile
from apps.accounts.visibility import AccountView, Relation
from apps.marketplace.models import Frequency, Offer, OfferStatus, RequestStatus, ServiceRequest
from apps.marketplace.scoring import score_offers, suggest_providers
from apps.marketplace.services import (
    MarketplaceError,
    activate_recurring_request,
    award_offer,
    create_contract_from_offer,
    award_warnings,
    cancel_request,
    expire_requests,
    publish_request,
    submit_offer,
    withdraw_offer,
)
from apps.taxonomy.models import ServiceCategory


def _offer(request, provider, price="80", minutes=180, delay=0):
    return submit_offer(
        request, provider,
        price_per_visit=Decimal(price), estimated_minutes=minutes,
        includes_supplies=True,
        earliest_start=request.earliest_start + timedelta(days=delay),
        message="",
    )


@pytest.mark.django_db
class TestRequestLifecycle:
    def test_publicarea_genereaza_sugestii(self, service_request, make_provider):
        make_provider("Anna Klein")
        make_provider("Petra Groß")
        publish_request(service_request)
        assert service_request.status == RequestStatus.OPEN
        assert service_request.invitations.count() == 2

    def test_sugestia_nu_este_repartizare(self, service_request, make_provider):
        provider = make_provider("Anna Klein")
        publish_request(service_request)
        assert service_request.offers.count() == 0, "sugestia nu creează ofertă"
        invitation = service_request.invitations.get()
        assert invitation.provider == provider
        assert invitation.seen_at is None

    def test_prestatorul_din_alta_localitate_nu_e_sugerat(
        self, service_request, make_provider, pinneberg
    ):
        make_provider("Weit Weg", locality=pinneberg, serves=False)
        publish_request(service_request)
        assert service_request.invitations.count() == 0

    def test_termen_in_trecut_blocheaza_publicarea(self, service_request):
        service_request.offers_close_at = timezone.now() - timedelta(hours=1)
        service_request.save()
        with pytest.raises(MarketplaceError):
            publish_request(service_request)

    def test_cererile_expira(self, service_request):
        publish_request(service_request, invite=False)
        ServiceRequest.objects.filter(pk=service_request.pk).update(
            offers_close_at=timezone.now() - timedelta(minutes=1)
        )
        assert expire_requests() == 1
        service_request.refresh_from_db()
        assert service_request.status == RequestStatus.EXPIRED


@pytest.mark.django_db
class TestOffers:
    def test_o_oferta_per_prestator(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Anna Klein")
        _offer(service_request, provider, price="80")
        _offer(service_request, provider, price="75")
        assert service_request.offers.count() == 1
        assert service_request.offers.get().price_per_visit == Decimal("75")

    def test_nu_ofertezi_la_propria_cerere(self, service_request, client_account):
        publish_request(service_request, invite=False)
        client_account.grant(Capability.WORKER)
        with pytest.raises(MarketplaceError):
            _offer(service_request, client_account)

    def test_cererea_inchisa_nu_primeste_oferte(self, service_request, make_provider):
        provider = make_provider("Anna Klein")
        with pytest.raises(MarketplaceError, match="nu mai primește"):
            _offer(service_request, provider)

    def test_pretul_lunar_urmeaza_frecventa(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        offer = _offer(service_request, make_provider("Anna Klein"), price="80")
        assert offer.monthly_price == Decimal("346.40")  # 80 × 4,33
        assert offer.implied_hourly == Decimal("26.67")

    def test_retragerea_ofertei(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Anna Klein")
        offer = _offer(service_request, provider)
        withdraw_offer(offer, provider)
        assert offer.status == OfferStatus.WITHDRAWN
        assert score_offers(service_request) == []


@pytest.mark.django_db
class TestScoring:
    def test_scorul_e_descompus_pe_criterii(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        _offer(service_request, make_provider("Anna Klein"))
        scored = score_offers(service_request)[0]
        assert set(scored.breakdown) == {
            "price", "verification", "proximity", "experience", "availability"
        }
        assert len(scored.explain()) == 5

    def test_cel_mai_ieftin_nu_castiga_automat(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        ieftin = make_provider("Ieftin", years=0, verification=VerificationLevel.NONE)
        bun = make_provider("Verificat", years=10, verification=VerificationLevel.DOCUMENTS)
        _offer(service_request, ieftin, price="60", minutes=180)
        _offer(service_request, bun, price="85", minutes=180)
        ranked = score_offers(service_request)
        assert ranked[0].offer.provider == bun
        assert ranked[0].breakdown["price"] < ranked[1].breakdown["price"]

    def test_la_preturi_egale_conteaza_restul(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        a = make_provider("Verificat", years=8, verification=VerificationLevel.DOCUMENTS)
        b = make_provider("Nou", years=0, verification=VerificationLevel.NONE)
        _offer(service_request, a, price="80")
        _offer(service_request, b, price="80")
        ranked = score_offers(service_request)
        assert all(s.breakdown["price"] == Decimal("1") for s in ranked)
        assert ranked[0].offer.provider == a

    def test_intarzierea_scade_scorul(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        prompt = make_provider("Prompt")
        late = make_provider("Târziu")
        _offer(service_request, prompt, delay=0)
        _offer(service_request, late, delay=21)
        by_name = {s.offer.provider.display_name: s for s in score_offers(service_request)}
        assert by_name["Prompt"].breakdown["availability"] == Decimal("1")
        assert by_name["Târziu"].breakdown["availability"] < Decimal("0.3")

    def test_deducerea_35a_apare_ca_nota(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        _offer(service_request, make_provider("Anna Klein"), price="80")
        notes = " ".join(score_offers(service_request)[0].notes)
        assert "35a" in notes and "bancă" in notes

    def test_clientul_firma_nu_primeste_nota_35a(
        self, employer, norderstedt, haushaltshilfe, make_provider
    ):
        employer.grant(Capability.CLIENT)
        request = ServiceRequest.objects.create(
            client=employer, category=haushaltshilfe, locality=norderstedt,
            area_sqm=200, frequency=Frequency.WEEKLY,
            earliest_start=timezone.localdate() + timedelta(days=7),
            title="Büroreinigung", offers_close_at=timezone.now() + timedelta(days=3),
        )
        publish_request(request, invite=False)
        _offer(request, make_provider("Anna Klein"))
        assert not request.is_35a_eligible
        assert all("35a" not in n for n in score_offers(request)[0].notes)


@pytest.mark.django_db
class TestAward:
    def test_atribuirea_inchide_celelalte_oferte(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        winner = make_provider("Anna Klein")
        loser = make_provider("Petra Groß")
        won = _offer(service_request, winner, price="80")
        lost = _offer(service_request, loser, price="70")
        award_offer(service_request, won, service_request.client)
        won.refresh_from_db(); lost.refresh_from_db(); service_request.refresh_from_db()
        assert won.status == OfferStatus.WON
        assert lost.status == OfferStatus.LOST
        assert service_request.status == RequestStatus.AWARDED

    def test_doar_clientul_atribuie(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Anna Klein")
        offer = _offer(service_request, provider)
        with pytest.raises(MarketplaceError):
            award_offer(service_request, offer, provider)

    def test_statutul_nedeclarat_produce_avertisment(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Nedeclarat", legal_status=LegalStatus.UNDECLARED)
        offer = _offer(service_request, provider)
        warnings = " ".join(award_warnings(service_request, offer))
        assert "muncă nedeclarată" in warnings

    def test_minijob_avertizeaza_ca_clientul_devine_angajator(
        self, service_request, make_provider
    ):
        publish_request(service_request, invite=False)
        provider = make_provider("Minijobberin", legal_status=LegalStatus.MINIJOB)
        offer = _offer(service_request, provider)
        warnings = " ".join(award_warnings(service_request, offer))
        assert "Haushaltsscheck" in warnings and "ANGAJATOR" in warnings

    def test_cererea_atribuita_nu_se_anuleaza(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        offer = _offer(service_request, make_provider("Anna Klein"))
        award_offer(service_request, offer, service_request.client)
        with pytest.raises(MarketplaceError):
            cancel_request(service_request, service_request.client)


@pytest.mark.django_db
class TestPrivacy:
    def test_o_oferta_nu_deschide_datele_clientului(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Anna Klein")
        _offer(service_request, provider)
        view = AccountView(service_request.client, viewer_account=provider)
        assert view.relation == Relation.AUTHENTICATED
        assert view.phone is None and view.street is None

    def test_atribuirea_deschide_datele(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Anna Klein")
        offer = _offer(service_request, provider)
        award_offer(service_request, offer, service_request.client)
        view = AccountView(service_request.client, viewer_account=provider)
        assert view.relation == Relation.ENGAGED
        assert view.phone == "+49 40 5556677"
        assert view.street == "Rathausallee 12"

    def test_pagina_de_ofertare_nu_arata_adresa(self, client, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Anna Klein")
        client.force_login(provider.user)
        response = client.get(f"/dashboard/bursa/{service_request.pk}/oferta/")
        assert response.status_code == 200
        assert b"Rathausallee" not in response.content


@pytest.mark.django_db
class TestViews:
    def test_clientul_publica_si_atribuie_din_dashboard(
        self, client, service_request, make_provider
    ):
        provider = make_provider("Anna Klein")
        client.force_login(service_request.client.user)
        client.post(f"/dashboard/cereri/{service_request.pk}/", {"action": "publish"}, follow=True)
        service_request.refresh_from_db()
        assert service_request.status == RequestStatus.OPEN

        offer = _offer(service_request, provider)
        client.post(f"/dashboard/cereri/{service_request.pk}/",
                    {"action": "award", "offer": offer.pk}, follow=True)
        service_request.refresh_from_db()
        assert service_request.awarded_offer_id == offer.pk

    def test_prestatorul_oferteaza_din_dashboard(self, client, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Anna Klein")
        client.force_login(provider.user)
        client.post(f"/dashboard/bursa/{service_request.pk}/oferta/", {
            "price_per_visit": "85", "estimated_minutes": "180",
            "includes_supplies": "on",
            "earliest_start": service_request.earliest_start.isoformat(),
            "message": "Gerne.",
        }, follow=True)
        assert Offer.objects.filter(request=service_request, provider=provider).exists()

    def test_pretul_sub_pragul_de_ramura_e_semnalat(self, client, service_request, make_provider):
        publish_request(service_request, invite=False)
        provider = make_provider("Anna Klein")
        client.force_login(provider.user)
        response = client.post(f"/dashboard/bursa/{service_request.pk}/oferta/", {
            "price_per_visit": "30", "estimated_minutes": "180",
            "earliest_start": service_request.earliest_start.isoformat(),
        })
        assert b"sub pragul de ram" in response.content
        assert not Offer.objects.filter(request=service_request).exists()

    def test_clientul_fara_capabilitate_de_prestator_nu_oferteaza(
        self, client, service_request, client_account
    ):
        publish_request(service_request, invite=False)
        client.force_login(client_account.user)
        response = client.get(f"/dashboard/bursa/{service_request.pk}/oferta/")
        assert response.status_code == 403

    def test_cererea_altui_client_nu_e_accesibila(self, client, service_request, employer):
        client.force_login(employer.user)
        assert client.get(f"/dashboard/cereri/{service_request.pk}/").status_code == 404


@pytest.mark.django_db
class TestContractSeam:
    """
    Atribuirea trebuie să producă hârtie. Tipul contractului NU e o alegere de
    produs — rezultă din statutul juridic al prestatorului, pentru că statutul
    decide cine e plătitorul legal și cine datorează contribuțiile.
    """

    def _awarded(self, service_request, provider, price="80", minutes=180):
        publish_request(service_request, invite=False)
        offer = _offer(service_request, provider, price=price, minutes=minutes)
        award_offer(service_request, offer, service_request.client)
        service_request.refresh_from_db()
        return offer

    def test_prestator_independent_primeste_werkvertrag(self, service_request, make_provider):
        provider = make_provider("Anna Klein", legal_status=LegalStatus.SELBSTSTAENDIG)
        self._awarded(service_request, provider)
        contract = create_contract_from_offer(service_request, service_request.client)
        assert contract.contract_type == "WERKVERTRAG"
        assert contract.employer == service_request.client
        assert contract.worker == provider

    def test_minijob_produce_contract_de_munca(self, service_request, make_provider):
        provider = make_provider("Minijobberin", legal_status=LegalStatus.MINIJOB)
        self._awarded(service_request, provider)
        contract = create_contract_from_offer(service_request, service_request.client)
        assert contract.contract_type == "MINIJOB"
        assert contract.employer == service_request.client, "clientul devine ANGAJATOR"

    def test_statut_nedeclarat_blocheaza_generarea(self, service_request, make_provider):
        provider = make_provider("Nedeclarat", legal_status=LegalStatus.UNDECLARED)
        self._awarded(service_request, provider)
        with pytest.raises(MarketplaceError, match="statut juridic declarat"):
            create_contract_from_offer(service_request, service_request.client)

    def test_cifrele_vin_din_oferta_nu_se_retasteaza(self, service_request, make_provider):
        provider = make_provider("Anna Klein")
        offer = self._awarded(service_request, provider, price="90", minutes=180)
        contract = create_contract_from_offer(service_request, service_request.client)
        assert contract.hourly_wage == offer.implied_hourly == Decimal("30.00")
        # 180 min × 4,33 vizite/lună ÷ 60 = 12,99 h
        assert contract.hours_per_month == Decimal("12.99")
        assert contract.start_date == offer.earliest_start

    def test_generarea_e_idempotenta(self, service_request, make_provider):
        provider = make_provider("Anna Klein")
        self._awarded(service_request, provider)
        first = create_contract_from_offer(service_request, service_request.client)
        second = create_contract_from_offer(service_request, service_request.client)
        assert first.pk == second.pk

    def test_cererea_neatribuita_nu_produce_contract(self, service_request, make_provider):
        publish_request(service_request, invite=False)
        _offer(service_request, make_provider("Anna Klein"))
        with pytest.raises(MarketplaceError, match="nu este atribuită"):
            create_contract_from_offer(service_request, service_request.client)

    def test_doar_clientul_genereaza(self, service_request, make_provider):
        provider = make_provider("Anna Klein")
        self._awarded(service_request, provider)
        with pytest.raises(MarketplaceError):
            create_contract_from_offer(service_request, provider)

    def test_onorariul_sub_tarif_avertizeaza_dar_nu_blocheaza(
        self, service_request, make_provider
    ):
        """Mindestlohn-ul de ramură leagă angajatorii, nu onorariul unui independent."""
        from apps.contracts.services import send_for_signature

        provider = make_provider("Anna Klein")
        self._awarded(service_request, provider, price="28", minutes=120)  # 14,00 €/h
        contract = create_contract_from_offer(service_request, service_request.client)
        codes = {i.code: i.blocking for i in contract.compliance_report()}
        assert codes["WAGE_FLOOR"] is False
        assert send_for_signature(contract) == []

    def test_din_dashboard_se_genereaza_si_se_deschide_contractul(
        self, client, service_request, make_provider
    ):
        provider = make_provider("Anna Klein")
        self._awarded(service_request, provider)
        client.force_login(service_request.client.memberships.first().user)
        response = client.post(
            f"/dashboard/cereri/{service_request.pk}/", {"action": "contract"}, follow=True
        )
        assert response.status_code == 200
        from apps.contracts.models import ContractDraft

        assert ContractDraft.objects.filter(worker=provider).count() == 1


@pytest.mark.django_db
class TestPlanningSeam:
    """
    Trecerea de la Vermittlung la execuție.

    Regula pe care o apără toate testele de aici: platforma NU alocă oameni
    peste granița dintre firme. Activarea creează obiectivul în contul
    prestatorului; turele le face prestatorul, pentru propriii lui angajați cu
    contract semnat. Orice altceva ar fi Arbeitnehmerüberlassung.
    """

    def _signed(self, service_request, provider, minutes=180):
        from apps.contracts.models import DraftStatus
        from apps.contracts.services import render_contract

        publish_request(service_request, invite=False)
        offer = _offer(service_request, provider, price="90", minutes=minutes)
        award_offer(service_request, offer, service_request.client)
        service_request.refresh_from_db()
        contract = create_contract_from_offer(service_request, service_request.client)
        render_contract(contract)
        contract.status = DraftStatus.SIGNED
        contract.save(update_fields=["status"])
        return contract

    def test_activarea_creeaza_obiectivul_la_prestator(self, service_request, make_provider):
        provider = make_provider("Nordclean", legal_status=LegalStatus.SELBSTSTAENDIG)
        self._signed(service_request, provider)
        site = activate_recurring_request(service_request, service_request.client)
        assert site.account == provider, "obiectivul aparține firmei care execută"
        assert site.locality == service_request.locality
        service_request.refresh_from_db()
        assert service_request.status == RequestStatus.ACTIVE

    def test_zona_preia_cifrele_din_oferta(self, service_request, make_provider):
        provider = make_provider("Nordclean")
        self._signed(service_request, provider, minutes=150)
        site = activate_recurring_request(service_request, service_request.client)
        zone = site.zones.get()
        assert zone.minutes_per_visit == 150
        assert zone.visits_per_week == 1
        assert zone.area_sqm == service_request.area_sqm
        assert zone.category == service_request.category

    def test_activarea_nu_creeaza_nicio_tura(self, service_request, make_provider):
        """Invariantul central: apps/marketplace nu are voie să creeze un Shift."""
        from apps.planning.models import Shift, ShiftPlan

        provider = make_provider("Nordclean")
        self._signed(service_request, provider)
        activate_recurring_request(service_request, service_request.client)
        assert Shift.objects.count() == 0
        assert ShiftPlan.objects.count() == 0

    def test_fara_contract_semnat_nu_se_activeaza(self, service_request, make_provider):
        provider = make_provider("Nordclean")
        publish_request(service_request, invite=False)
        offer = _offer(service_request, provider)
        award_offer(service_request, offer, service_request.client)
        service_request.refresh_from_db()
        create_contract_from_offer(service_request, service_request.client)
        with pytest.raises(MarketplaceError, match="semnat"):
            activate_recurring_request(service_request, service_request.client)

    def test_frecventa_bilunara_e_refuzata_explicit(self, service_request, make_provider):
        """
        `Zone` numără vizite pe săptămână. O cerere bilunară transformată în
        „1×/săptămână" ar produce dublul vizitelor contractate — mai bine refuz
        explicit decât o minciună tăcută către planificator.
        """
        service_request.frequency = Frequency.BIWEEKLY
        service_request.save()
        provider = make_provider("Nordclean")
        self._signed(service_request, provider)
        with pytest.raises(MarketplaceError, match="două săptămâni"):
            activate_recurring_request(service_request, service_request.client)

    def test_prestatia_unica_nu_produce_obiectiv(self, service_request, make_provider):
        service_request.frequency = Frequency.ONE_TIME
        service_request.save()
        provider = make_provider("Nordclean")
        self._signed(service_request, provider)
        with pytest.raises(MarketplaceError, match="unică"):
            activate_recurring_request(service_request, service_request.client)

    def test_activarea_e_idempotenta(self, service_request, make_provider):
        from apps.planning.models import Site

        provider = make_provider("Nordclean")
        self._signed(service_request, provider)
        first = activate_recurring_request(service_request, service_request.client)
        service_request.status = RequestStatus.AWARDED
        service_request.save()
        second = activate_recurring_request(service_request, service_request.client)
        assert first.pk == second.pk
        assert Site.objects.filter(account=provider).count() == 1
        assert first.zones.count() == 1

    def test_prestatorul_isi_planifica_singur_dupa_activare(
        self, service_request, make_provider
    ):
        """
        Capacitatea vine doar din contractele SEMNATE ale prestatorului cu
        PROPRIII angajați. Contractul client↔prestator nu dă capacitate.
        """
        from apps.planning.services import capacity_report

        provider = make_provider("Nordclean")
        self._signed(service_request, provider)
        activate_recurring_request(service_request, service_request.client)
        report = capacity_report(provider, timezone.localdate() - timedelta(
            days=timezone.localdate().isoweekday() - 1
        ))
        assert report["demand_minutes"] > 0, "obiectivul produce cerere"
        assert report["workers"] == 0, "dar niciun angajat propriu nu e încă sub contract"

    def test_doar_clientul_activeaza(self, service_request, make_provider):
        provider = make_provider("Nordclean")
        self._signed(service_request, provider)
        with pytest.raises(MarketplaceError):
            activate_recurring_request(service_request, provider)
