"""
Modulul de comenzi: Customer e o relație între două conturi, Order e containerul
comercial al unui Auftrag. Fără facturi aici.
"""

from datetime import date

import pytest
from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from apps.accounts.enums import Capability, EntityType
from apps.accounts.models import AccountCapability, User
from apps.accounts.services import create_account
from apps.billing.backfill import backfill_orders
from apps.billing.enums import ContractKind, DocumentType, OrderStatus
from apps.billing.models import Customer, Order
from apps.billing.numbering import allocate
from apps.billing.services import BillingError, create_order_from_request, transition_order
from apps.contracts.models import DraftStatus
from apps.contracts.services import render_contract
from apps.marketplace.services import (
    MarketplaceError,
    activate_recurring_request,
    award_offer,
    create_contract_from_offer,
    publish_request,
)
from apps.planning.models import Site


@pytest.fixture
def customer(db, employer, client_account):
    """`employer` e prestatorul, `client_account` beneficiarul."""
    return Customer.objects.create(provider=employer, account=client_account)


@pytest.fixture
def site(db, employer, norderstedt):
    return Site.objects.create(
        account=employer, name="Sediu Nord", locality=norderstedt,
        street="Hauptstr. 1", postal_code="22844",
    )


@pytest.fixture
def order(db, employer, customer, site, haushaltshilfe):
    # `employer` are EMPLOYER + CLIENT; comenzile sunt gate-uite pe PROVIDER/WORKER.
    AccountCapability.objects.get_or_create(account=employer, kind=Capability.PROVIDER)
    return Order.objects.create(
        provider=employer, customer=customer, site=site, category=haushaltshilfe,
        order_number="A-2026-0001", title="Curățenie sediu",
        start_date=date(2026, 10, 1),
    )


@pytest.mark.django_db
class TestModele:
    def test_clientul_nu_poate_fi_propriul_prestator(self, employer):
        with pytest.raises(IntegrityError):
            Customer.objects.create(provider=employer, account=employer)

    def test_comanda_refuza_obiectiv_strain(self, order, client_account, norderstedt):
        order.site = Site.objects.create(
            account=client_account, name="Altundeva", locality=norderstedt,
        )
        with pytest.raises(ValidationError) as exc:
            order.full_clean()
        assert "site" in exc.value.error_dict

    def test_comanda_refuza_client_al_altui_prestator(self, order, client_account, worker):
        order.customer = Customer.objects.create(provider=worker, account=client_account)
        with pytest.raises(ValidationError) as exc:
            order.full_clean()
        assert "customer" in exc.value.error_dict

    def test_comanda_refuza_categorie_parinte(self, order, haushaltshilfe):
        order.category = haushaltshilfe.parent
        with pytest.raises(ValidationError) as exc:
            order.full_clean()
        assert "category" in exc.value.error_dict

    def test_comanda_refuza_sfarsit_inainte_de_inceput(self, order):
        order.end_date = date(2026, 9, 1)
        with pytest.raises(ValidationError) as exc:
            order.full_clean()
        assert "end_date" in exc.value.error_dict

    def test_comanda_valida_trece(self, order):
        order.full_clean()
        assert order.status == OrderStatus.ACTIVE
        assert order.contract_kind == ContractKind.DIENSTVERTRAG


@pytest.mark.django_db
class TestNumerotare:
    def test_numerele_sunt_consecutive(self, employer):
        assert allocate(employer, DocumentType.ORDER, 2026) == "A-2026-0001"
        assert allocate(employer, DocumentType.ORDER, 2026) == "A-2026-0002"

    def test_alt_an_incepe_o_serie_noua(self, employer):
        allocate(employer, DocumentType.ORDER, 2026)
        assert allocate(employer, DocumentType.ORDER, 2027) == "A-2027-0001"

    def test_seriile_sunt_per_prestator(self, employer, worker):
        allocate(employer, DocumentType.ORDER, 2026)
        assert allocate(worker, DocumentType.ORDER, 2026) == "A-2026-0001"

    def test_prefixul_e_configurabil(self, employer):
        from apps.billing.models import DocumentSequence

        DocumentSequence.objects.create(
            provider=employer, document_type=DocumentType.ORDER, year=2026, prefix="AUF",
        )
        assert allocate(employer, DocumentType.ORDER, 2026) == "AUF-2026-0001"


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="select_for_update doar pe Postgres")
def test_concurenta_nu_lasa_goluri(employer):
    """20 de fire aloca în paralel: 20 de numere distincte, consecutive."""
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections

    def worker():
        try:
            return allocate(employer, DocumentType.ORDER, 2026)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=8) as pool:
        numbers = sorted(pool.map(lambda _: worker(), range(20)))
    assert numbers == [f"A-2026-{n:04d}" for n in range(1, 21)]


@pytest.fixture
def ready_to_activate(db, service_request, make_provider, make_offer):
    """Cerere publicată, ofertă câștigătoare, contract semnat — gata de activare."""
    provider = make_provider("Nordclean")
    publish_request(service_request, invite=False)
    offer = make_offer(service_request, provider, price="90", minutes=180)
    award_offer(service_request, offer, service_request.client)
    service_request.refresh_from_db()
    contract = create_contract_from_offer(service_request, service_request.client)
    render_contract(contract)
    contract.status = DraftStatus.SIGNED
    contract.save(update_fields=["status"])
    return service_request, provider


@pytest.fixture
def activated(db, ready_to_activate):
    """Cerere publicată, ofertă câștigătoare, contract semnat, cerere activată."""
    service_request, provider = ready_to_activate
    site = activate_recurring_request(service_request, service_request.client)
    service_request.refresh_from_db()
    return service_request, site, provider


@pytest.mark.django_db
class TestCreareDinCerere:
    def test_activarea_creeaza_clientul_si_comanda(self, activated):
        request, site, provider = activated
        order = Order.objects.get(source_offer=request.awarded_offer)
        assert order.provider == provider
        assert order.customer.account == request.client
        assert order.site == site
        assert order.category == request.category
        assert order.start_date == request.awarded_offer.earliest_start
        assert order.order_number.startswith(f"A-{order.start_date.year}-")

    def test_a_doua_chemare_e_idempotenta(self, activated):
        request, site, provider = activated
        first = Order.objects.get(source_offer=request.awarded_offer)
        again = create_order_from_request(request, site, actor=request.client)
        assert again.pk == first.pk
        assert Order.objects.count() == 1
        assert Customer.objects.count() == 1

    def test_cererea_neactiva_e_refuzata(self, service_request, site):
        with pytest.raises(BillingError):
            create_order_from_request(service_request, site, actor=service_request.client)

    def test_eroarea_stratului_comercial_devine_marketplace_error(
        self, ready_to_activate, monkeypatch
    ):
        """Seam-ul traduce excepția: view-ul din marketplace prinde doar MarketplaceError."""
        import apps.billing.services as billing_services

        service_request, provider = ready_to_activate

        def _explodeaza(request, site, *, actor):
            raise billing_services.BillingError("x")

        monkeypatch.setattr(billing_services, "create_order_from_request", _explodeaza)
        with pytest.raises(MarketplaceError):
            activate_recurring_request(service_request, service_request.client)

    def test_doua_comenzi_pe_aceeasi_oferta_sunt_refuzate_de_baza(self, activated):
        request, site, provider = activated
        first = Order.objects.get(source_offer=request.awarded_offer)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Order.objects.create(
                    provider=first.provider,
                    customer=first.customer,
                    site=first.site,
                    category=first.category,
                    order_number="A-2026-9999",
                    title=first.title,
                    start_date=first.start_date,
                    source_offer=first.source_offer,
                )


@pytest.mark.django_db
class TestTranzitii:
    def test_suspendare_si_reluare(self, order, employer):
        transition_order(order, OrderStatus.SUSPENDED, actor=employer)
        assert order.status == OrderStatus.SUSPENDED
        transition_order(order, OrderStatus.ACTIVE, actor=employer)
        assert order.status == OrderStatus.ACTIVE

    def test_incheiata_e_terminala(self, order, employer):
        transition_order(order, OrderStatus.COMPLETED, actor=employer)
        with pytest.raises(BillingError):
            transition_order(order, OrderStatus.ACTIVE, actor=employer)

    def test_incheierea_unui_werkvertrag_marcheaza_receptia(self, order, employer):
        order.contract_kind = ContractKind.WERKVERTRAG
        order.save()
        before = timezone.now()
        transition_order(order, OrderStatus.COMPLETED, actor=employer)
        order.refresh_from_db()
        assert order.accepted_at is not None and order.accepted_at >= before

    def test_dienstvertrag_nu_are_receptie(self, order, employer):
        transition_order(order, OrderStatus.COMPLETED, actor=employer)
        order.refresh_from_db()
        assert order.accepted_at is None

    def test_strainul_nu_schimba_starea(self, order, worker):
        with pytest.raises(BillingError):
            transition_order(order, OrderStatus.CANCELLED, actor=worker)

    def test_tranzitia_concurenta_e_detectata(self, order, employer):
        """Rândul a fost schimbat de altcineva între citire și scriere: BillingError."""
        Order.objects.filter(pk=order.pk).update(status=OrderStatus.CANCELLED)
        with pytest.raises(BillingError):
            transition_order(order, OrderStatus.SUSPENDED, actor=employer)


@pytest.mark.django_db
class TestBackfill:
    def test_cererea_activa_fara_comanda_primeste_una(self, activated):
        request, site, provider = activated
        Order.objects.all().delete()          # simulează starea de dinaintea modulului
        Customer.objects.all().delete()
        assert backfill_orders(django_apps) == 1
        order = Order.objects.get(source_offer=request.awarded_offer)
        assert order.site == site
        assert order.provider == provider
        assert order.start_date == request.awarded_offer.earliest_start

    def test_backfill_e_idempotent(self, activated):
        assert backfill_orders(django_apps) == 0
        assert Order.objects.count() == 1

    def test_cererea_fara_obiectiv_e_sarita(self, activated):
        request, site, provider = activated
        Order.objects.all().delete()
        site.delete()
        assert backfill_orders(django_apps) == 0


@pytest.mark.django_db
class TestDashboard:
    def test_tranzitia_din_dashboard(self, client, employer, order):
        client.force_login(employer.user)
        response = client.post(f"/dashboard/comenzi/{order.pk}/stare/", {"status": "SUSPENDED"})
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.status == OrderStatus.SUSPENDED

    def test_tranzitia_ilegala_afiseaza_eroare(self, client, employer, order):
        client.force_login(employer.user)
        transition_order(order, OrderStatus.COMPLETED, actor=employer)
        response = client.post(f"/dashboard/comenzi/{order.pk}/stare/",
                               {"status": "ACTIVE"}, follow=True)
        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.COMPLETED
        assert "nu se poate trece" in response.content.decode()

    def test_panourile_apar_la_prestator(self, client, employer, order):
        client.force_login(employer.user)
        html = client.get("/dashboard/").content.decode()
        assert "/dashboard/comenzi/" in html
        assert "/dashboard/clienti/" in html

    def test_membrul_simplu_nu_vede_butoane_de_tranzitie(self, client, employer, order):
        from apps.accounts.enums import MembershipRole
        from apps.accounts.models import Membership, User

        member = User.objects.create_user("membru2@example.de", "parola-lunga-123")
        Membership.objects.create(user=member, account=employer, role=MembershipRole.MEMBER)
        client.force_login(member)
        response = client.get(f"/dashboard/comenzi/{order.pk}/")
        assert response.status_code == 200
        assert 'name="status"' not in response.content.decode()

    def test_lista_clientilor_nu_face_o_interogare_per_client(
        self, client, employer, order, worker, client_account, norderstedt
    ):
        from django.test.utils import CaptureQueriesContext

        client.force_login(employer.user)
        client.get("/dashboard/clienti/")  # încălzire: sesiune, content-type etc.

        # `order` a creat deja primul `Customer` (pe `client_account`).
        with CaptureQueriesContext(connection) as ctx:
            client.get("/dashboard/clienti/")
        few = len(ctx)

        Customer.objects.create(provider=employer, account=worker)
        for i in range(2):
            other = create_account(
                user=User.objects.create_user(f"client{i}@example.de", "parola-lunga-123"),
                entity_type=EntityType.INDIVIDUAL, display_name=f"Client {i}",
                capabilities=[Capability.CLIENT], locality=norderstedt,
            )
            Customer.objects.create(provider=employer, account=other)

        with CaptureQueriesContext(connection) as ctx:
            client.get("/dashboard/clienti/")
        many = len(ctx)

        assert few == many, f"N+1: {few} interogări la 1 client, {many} la 4"
