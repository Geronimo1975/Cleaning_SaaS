"""
Numărul de interogări, ca test de regresie.

Aceste funcții rulează peste liste care cresc cu utilizarea: ture pontate
într-o săptămână, echipamente ale unui cont, prestatori dintr-un oraș. Un
`select_related` scos din greșeală la o refactorizare nu strică niciun test
funcțional — se vede doar aici, ca număr de interogări care crește cu N.

Regula verificată: numărul de interogări e CONSTANT în raport cu N.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.enums import Capability, EntityType, LegalStatus
from apps.accounts.models import User
from apps.accounts.profiles import ServiceArea
from apps.accounts.services import create_account, publish_profile
from apps.devices.models import Device, TelemetrySession
from apps.devices.services import find_discrepancies, utilisation
from apps.planning.models import PlanStatus, Shift, ShiftPlan, ShiftStatus, Site, Zone


def _monday():
    today = timezone.localdate()
    return today - timedelta(days=today.isoweekday() - 1)


@pytest.fixture
def site(db, employer, norderstedt):
    return Site.objects.create(account=employer, name="Haus Nord", locality=norderstedt)


@pytest.fixture
def make_shifts(db, employer, worker, site, category):
    def _make(count):
        zone = Zone.objects.create(
            site=site, name=f"Zonă {count}", category=category,
            minutes_per_visit=120, visits_per_week=2,
        )
        plan = ShiftPlan.objects.create(
            account=employer, week_start=_monday() - timedelta(weeks=count),
            status=PlanStatus.PUBLISHED,
        )
        start = timezone.localtime(timezone.now()) - timedelta(hours=2)
        for i in range(count):
            Shift.objects.create(
                plan=plan, zone=zone, worker=worker, date=start.date(),
                start_time=start.time().replace(microsecond=0), duration_minutes=120,
                status=ShiftStatus.DONE, actual_minutes=110,
            )
        return plan

    return _make


@pytest.mark.django_db
class TestFindDiscrepancies:
    """`_site_has_devices` era un EXISTS per tură."""

    def _count(self, employer, make_shifts, site, count, tag):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        plan = make_shifts(count)
        Device.objects.create(
            account=employer, label=f"Aspirator {tag}", site=site,
            token_hash=f"hash-{tag}", token_prefix="",
        )
        start = plan.week_start
        end = timezone.localdate() + timedelta(days=1)
        with CaptureQueriesContext(connection) as ctx:
            findings = [f for f in find_discrepancies(employer, start, end)
                        if f.shift.plan_id == plan.pk]
        return len(ctx), findings

    def test_numarul_de_interogari_nu_creste_cu_turele(self, employer, make_shifts, site):
        few, findings_few = self._count(employer, make_shifts, site, 2, "a")
        many, findings_many = self._count(employer, make_shifts, site, 20, "b")
        assert len(findings_few) == 2 and len(findings_many) == 20, "constatările rămân corecte"
        assert few == many, f"N+1: {few} interogări la 2 ture, {many} la 20"


@pytest.mark.django_db
class TestUtilisation:
    """`device.sessions.filter(...)` era o interogare per echipament."""

    def _count(self, employer, site, count, offset):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        for i in range(count):
            device = Device.objects.create(
                account=employer, label=f"Aparat {offset}-{i}", site=site,
                token_hash=f"hash-{offset}-{i}", token_prefix="",
            )
            TelemetrySession.objects.create(
                device=device, external_id=f"s-{offset}-{i}",
                started_at=timezone.now() - timedelta(hours=2),
                ended_at=timezone.now() - timedelta(hours=1),
                runtime_minutes=60, area_sqm=100,
            )
        start = timezone.localdate() - timedelta(days=1)
        end = timezone.localdate() + timedelta(days=1)
        with CaptureQueriesContext(connection) as ctx:
            rows = utilisation(employer, start, end)
        return len(ctx), rows

    def test_numarul_de_interogari_nu_creste_cu_echipamentele(self, employer, site):
        few, rows_few = self._count(employer, site, 2, "a")
        many, rows_many = self._count(employer, site, 20, "b")
        assert len(rows_few) == 2 and len(rows_many) == 22
        assert sum(r["runtime_minutes"] for r in rows_many) == 22 * 60
        assert few == many, f"N+1: {few} interogări la 2 aparate, {many} la 22"


@pytest.mark.django_db
class TestRankProviders:
    """`_proximity_score` interoga `provider.areas` per prestator."""

    def _providers(self, count, locality, service_locality, category, offset):
        for i in range(count):
            user = User.objects.create_user(f"p{offset}{i}@example.de", "parola-lunga-123")
            account = create_account(
                user=user, entity_type=EntityType.INDIVIDUAL,
                display_name=f"Prestator {offset}{i}",
                capabilities=[Capability.WORKER], locality=locality,
                legal_status=LegalStatus.SELBSTSTAENDIG,
            )
            publish_profile(account)
            from apps.accounts.profiles import AccountService

            AccountService.objects.create(account=account, category=category)
            ServiceArea.objects.create(account=account, locality=service_locality)

    def test_numarul_de_interogari_nu_creste_cu_prestatorii(
        self, db, employer, norderstedt, pinneberg, category
    ):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from apps.marketplace.models import Frequency, ServiceRequest
        from apps.marketplace.scoring import suggest_providers

        service_request = ServiceRequest.objects.create(
            client=employer, category=category, locality=norderstedt,
            area_sqm=100, frequency=Frequency.WEEKLY,
            earliest_start=timezone.localdate() + timedelta(days=7),
            title="Treppenhaus", offers_close_at=timezone.now() + timedelta(days=3),
        )

        # Prestatorii stau în ALTĂ localitate decât cererea: exact ramura care
        # ajungea la `provider.areas.filter(...).exists()`.
        self._providers(2, pinneberg, norderstedt, category, "a")
        with CaptureQueriesContext(connection) as ctx:
            few_rows = suggest_providers(service_request, limit=100)
        few = len(ctx)

        self._providers(18, pinneberg, norderstedt, category, "b")
        with CaptureQueriesContext(connection) as ctx:
            many_rows = suggest_providers(service_request, limit=100)
        many = len(ctx)

        assert len(few_rows) == 2 and len(many_rows) == 20
        assert few == many, f"N+1: {few} interogări la 2 prestatori, {many} la 20"
