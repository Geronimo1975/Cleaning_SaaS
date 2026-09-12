"""
Modulul de comenzi: Customer e o relație între două conturi, Order e containerul
comercial al unui Auftrag. Fără facturi aici.
"""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection

from apps.accounts.enums import Capability
from apps.accounts.models import AccountCapability
from apps.billing.enums import ContractKind, DocumentType, OrderStatus
from apps.billing.models import Customer, Order
from apps.billing.numbering import allocate
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
