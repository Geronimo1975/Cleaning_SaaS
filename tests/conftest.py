from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.enums import (
    Capability,
    EntityType,
    LegalStatus,
    VerificationLevel,
)
from apps.accounts.models import User
from apps.accounts.profiles import AccountService, ServiceArea
from apps.accounts.services import create_account, publish_profile
from apps.contracts.models import ContractDraft, DraftStatus
from apps.contracts.services import active_template, render_contract
from apps.geo.models import Locality
from apps.jobs.models import EmploymentType, JobPosting, JobStatus
from apps.marketplace.models import Frequency, ServiceRequest
from apps.taxonomy.models import ServiceCategory


@pytest.fixture(autouse=True)
def operator_declarat(settings):
    """
    Lumea implicită a testelor are un operator declarat.

    Fără el, poarta din `apps.legal.publication` pune `noindex` peste tot și
    oprește notificările către Google — corect în producție, dar ar cere ca
    fiecare test de SEO să repete aceeași configurare. Testele care verifică
    tocmai starea neconfigurată o cer explicit, punând `settings.OPERATOR = {}`.
    """
    settings.OPERATOR = {
        "name": "Nordclean", "legal_form": "GmbH", "street": "Ulzburger Str. 40",
        "postal_code": "22846", "city": "Norderstedt", "email": "info@example.de",
        "phone": "+49 40 1234567", "represented_by": "Klaus Meyer",
    }


@pytest.fixture
def norderstedt(db):
    return Locality.objects.get(slug="norderstedt")


@pytest.fixture
def pinneberg(db):
    return Locality.objects.get(slug="pinneberg")


@pytest.fixture
def category(db):
    return ServiceCategory.objects.get(slug="treppenhausreinigung")


@pytest.fixture
def employer(db, norderstedt):
    user = User.objects.create_user("hr@residenz.de", "parola-lunga-123")
    account = create_account(
        user=user, entity_type=EntityType.COMPANY, display_name="Seniorenresidenz Nord",
        capabilities=[Capability.EMPLOYER, Capability.CLIENT], locality=norderstedt,
        legal_status=LegalStatus.COMPANY, legal_name="Seniorenresidenz Nord GmbH",
        street="Ulzburger Str. 40", postal_code="22846",
    )
    publish_profile(account)
    account.user = user
    return account


@pytest.fixture
def worker(db, norderstedt):
    user = User.objects.create_user("maria@example.de", "parola-lunga-123")
    account = create_account(
        user=user, entity_type=EntityType.INDIVIDUAL, display_name="Maria Ionescu",
        capabilities=[Capability.WORKER, Capability.CLIENT], locality=norderstedt,
        legal_status=LegalStatus.MINIJOB, phone="+49 170 9998877",
        street="Segeberger Chaussee 9",
    )
    publish_profile(account)
    account.user = user
    return account


@pytest.fixture
def job(db, employer, norderstedt, category):
    return JobPosting.objects.create(
        account=employer, title="Reinigungskraft Norderstedt (bis 40 Std./Monat)",
        description="Reinigung der Gemeinschaftsflächen.", category=category,
        locality=norderstedt, employment_type=EmploymentType.MINIJOB,
        salary_min=15, salary_max=16, status=JobStatus.PUBLISHED,
        published_at=timezone.now(), valid_through=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def next_monday():
    today = date(2026, 10, 1)
    return today + timedelta(days=(7 - today.isoweekday() + 1) % 7 or 7)


@pytest.fixture
def signed_contract(db, employer, worker, norderstedt, next_monday):
    def _make(hours="40", wage="15.00", worker_account=None, start=None):
        draft = ContractDraft.objects.create(
            employer=employer, worker=worker_account or worker,
            template=active_template("MINIJOB"), contract_type="MINIJOB",
            start_date=start or (next_monday - timedelta(days=30)),
            hours_per_month=Decimal(hours), hourly_wage=Decimal(wage),
            workplace=norderstedt,
        )
        render_contract(draft)
        draft.status = DraftStatus.SIGNED
        draft.save(update_fields=["status"])
        return draft

    return _make


# --- Fixture-uri partajate de bursă și cooperativă -------------------------

@pytest.fixture
def haushaltshilfe(db):
    return ServiceCategory.objects.get(slug="haushaltshilfe")


@pytest.fixture
def client_account(db, norderstedt):
    user = User.objects.create_user("kunde@example.de", "parola-lunga-123")
    account = create_account(
        user=user, entity_type=EntityType.INDIVIDUAL, display_name="Familie Weber",
        capabilities=[Capability.CLIENT], locality=norderstedt,
        street="Rathausallee 12", phone="+49 40 5556677",
    )
    account.user = user
    return account


@pytest.fixture
def service_request(db, client_account, norderstedt, haushaltshilfe):
    return ServiceRequest.objects.create(
        client=client_account, category=haushaltshilfe, locality=norderstedt,
        postal_code="22846", area_sqm=95, rooms=4, frequency=Frequency.WEEKLY,
        earliest_start=timezone.localdate() + timedelta(days=7),
        title="Haushaltshilfe für 95 m² Wohnung",
        offers_close_at=timezone.now() + timedelta(days=5),
    )


@pytest.fixture
def make_provider(db, norderstedt, haushaltshilfe):
    def _make(name, *, years=3, verification=VerificationLevel.EMAIL,
              legal_status=LegalStatus.SELBSTSTAENDIG, locality=None, serves=True):
        user = User.objects.create_user(f"{name.lower().replace(' ', '')}@example.de",
                                        "parola-lunga-123")
        account = create_account(
            user=user, entity_type=EntityType.INDIVIDUAL, display_name=name,
            capabilities=[Capability.WORKER], locality=locality or norderstedt,
            legal_status=legal_status,
        )
        account.verification_level = verification
        account.save()
        account.worker_profile.years_experience = years
        account.worker_profile.save()
        AccountService.objects.create(account=account, category=haushaltshilfe)
        if serves:
            ServiceArea.objects.create(account=account, locality=norderstedt)
        publish_profile(account)
        account.user = user
        return account

    return _make



@pytest.fixture
def make_offer(db):
    """O ofertă la o cerere deschisă, cu valorile implicite folosite în teste."""
    from decimal import Decimal

    from apps.marketplace.services import submit_offer

    def _make(request, provider, price="80", minutes=180, delay=0):
        return submit_offer(
            request, provider,
            price_per_visit=Decimal(price), estimated_minutes=minutes,
            includes_supplies=True,
            earliest_start=request.earliest_start + timedelta(days=delay),
            message="",
        )

    return _make
