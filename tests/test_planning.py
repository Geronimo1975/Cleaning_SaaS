"""
Planificatorul.

Regula pe care o apără fiecare test: orele din contract sunt un PLAFON LEGAL.
Un plan care le depășește nu e un plan suboptim — e o depășire a
Geringfügigkeitsgrenze care schimbă natura raportului de muncă.
"""

from datetime import date, timedelta

import pytest

from apps.accounts.enums import Capability, EntityType
from apps.accounts.models import User
from apps.accounts.profiles import ServiceArea
from apps.accounts.services import create_account
from apps.planning.models import Site, Zone
from apps.planning.services import (
    MAX_DAILY_MINUTES,
    capacity_report,
    generate_week_plan,
)

MONDAY = date(2026, 10, 5)  # luni


@pytest.fixture
def site(db, employer, norderstedt):
    return Site.objects.create(
        account=employer, name="Haus Nord", locality=norderstedt,
        street="Ulzburger Str. 40", postal_code="22846",
    )


@pytest.fixture
def zone(db, site, category):
    def _make(name="Etaj 1", minutes=120, visits=2, weekdays="1,2,3,4,5"):
        return Zone.objects.create(
            site=site, name=name, category=category, minutes_per_visit=minutes,
            visits_per_week=visits, allowed_weekdays=weekdays,
        )

    return _make


@pytest.fixture
def second_worker(db, norderstedt):
    user = User.objects.create_user("petra@example.de", "parola-lunga-123")
    account = create_account(
        user=user, entity_type=EntityType.INDIVIDUAL, display_name="Petra Schulz",
        capabilities=[Capability.WORKER], locality=norderstedt,
    )
    return account


@pytest.mark.django_db
class TestCapacity:
    def test_capacitatea_vine_din_contract_semnat(self, employer, signed_contract):
        signed_contract(hours="40")
        report = capacity_report(employer, MONDAY)
        # 40 h/lună = 2400 min/lună; săptămânal = 2400 / (52/12) ≈ 553 min
        assert report["workers"] == 1
        assert 550 <= report["supply_minutes"] <= 555

    def test_fara_contract_semnat_nu_exista_capacitate(self, employer, worker):
        assert capacity_report(employer, MONDAY)["workers"] == 0

    def test_raportul_arata_deficitul(self, employer, signed_contract, zone):
        signed_contract(hours="40")
        zone(minutes=300, visits=5)  # 1500 min cerere vs ~553 capacitate
        report = capacity_report(employer, MONDAY)
        assert report["demand_minutes"] == 1500
        assert report["deficit_minutes"] > 900


@pytest.mark.django_db
class TestPlanGeneration:
    def test_planul_respecta_bugetul_contractual(self, employer, signed_contract, zone):
        signed_contract(hours="40")
        zone(minutes=120, visits=5)  # 600 min cerute, ~553 disponibile
        plan = generate_week_plan(employer, MONDAY)
        assert plan.planned_minutes <= 553
        assert plan.unmet_demand, "surplusul apare în raport, nu în plan"
        assert "buget săptămânal epuizat" in str(plan.unmet_demand)

    def test_nu_depaseste_8_ore_pe_zi(self, employer, signed_contract, zone):
        signed_contract(hours="200")  # buget generos
        for i in range(6):
            zone(name=f"Zonă {i}", minutes=180, visits=1, weekdays="1")
        plan = generate_week_plan(employer, MONDAY)
        per_day = {}
        for shift in plan.shifts.all():
            per_day[(shift.worker_id, shift.date)] = (
                per_day.get((shift.worker_id, shift.date), 0) + shift.duration_minutes
            )
        assert max(per_day.values()) <= MAX_DAILY_MINUTES
        assert any("8 h într-o zi" in str(u["reasons"]) for u in plan.unmet_demand)

    def test_duminica_ramane_libera(self, employer, signed_contract, zone):
        signed_contract(hours="100")
        zone(minutes=60, visits=7, weekdays="1,2,3,4,5,6,7")
        plan = generate_week_plan(employer, MONDAY)
        assert all(s.date.isoweekday() != 7 for s in plan.shifts.all())

    def test_respecta_zilele_permise_ale_zonei(self, employer, signed_contract, zone):
        signed_contract(hours="100")
        zone(minutes=60, visits=2, weekdays="2,4")  # marți și joi
        plan = generate_week_plan(employer, MONDAY)
        assert {s.date.isoweekday() for s in plan.shifts.all()} <= {2, 4}

    def test_lucratorul_care_nu_deserveste_localitatea_nu_e_alocat(
        self, employer, worker, signed_contract, zone, pinneberg
    ):
        ServiceArea.objects.create(account=worker, locality=pinneberg)
        signed_contract(hours="100")
        zone(minutes=60, visits=1)  # obiectivul e în Norderstedt
        plan = generate_week_plan(employer, MONDAY)
        assert plan.shifts.count() == 0
        assert "nu deservește localitatea" in str(plan.unmet_demand)

    def test_doi_lucratori_impart_sarcina(
        self, employer, signed_contract, second_worker, zone
    ):
        signed_contract(hours="40")
        signed_contract(hours="40", worker_account=second_worker)
        zone(minutes=120, visits=5)
        plan = generate_week_plan(employer, MONDAY)
        assert plan.shifts.count() == 5
        assert plan.unmet_demand == []
        assert len({s.worker_id for s in plan.shifts.all()}) == 2

    def test_regenerarea_nu_dubleaza_turele(self, employer, signed_contract, zone):
        signed_contract(hours="40")
        zone(minutes=60, visits=2)
        first = generate_week_plan(employer, MONDAY).shifts.count()
        second = generate_week_plan(employer, MONDAY).shifts.count()
        assert first == second

    def test_turele_incep_secvential_in_aceeasi_zi(self, employer, signed_contract, zone):
        signed_contract(hours="100")
        zone(name="A", minutes=60, visits=1, weekdays="1")
        zone(name="B", minutes=90, visits=1, weekdays="1")
        plan = generate_week_plan(employer, MONDAY)
        times = sorted(s.start_time.strftime("%H:%M") for s in plan.shifts.all())
        assert times[0] == "07:00"
        assert times[1] != "07:00", "a doua tură nu se suprapune peste prima"

    def test_planul_incepe_luni(self, employer):
        with pytest.raises(ValueError):
            generate_week_plan(employer, MONDAY + timedelta(days=1))

    def test_raportul_de_nealocat_spune_motivul_per_lucrator(
        self, employer, signed_contract, zone
    ):
        signed_contract(hours="40")
        zone(minutes=200, visits=5)
        plan = generate_week_plan(employer, MONDAY)
        unmet = plan.unmet_demand[0]
        assert unmet["zone"] and unmet["date"] and unmet["reasons"]
        assert "Maria Ionescu" in unmet["reasons"]


@pytest.mark.django_db
class TestPlanningDashboard:
    def test_pagina_arata_capacitatea(self, client, employer, signed_contract, zone):
        signed_contract(hours="40")
        zone(minutes=120, visits=2)
        client.force_login(employer.user)
        response = client.get("/dashboard/planificare/?week=2026-10-05")
        assert response.status_code == 200
        assert b"Capacitate" in response.content

    def test_generarea_din_dashboard(self, client, employer, signed_contract, zone):
        signed_contract(hours="40")
        zone(minutes=120, visits=2)
        client.force_login(employer.user)
        client.post("/dashboard/planificare/?week=2026-10-05", follow=True)
        from apps.planning.models import ShiftPlan

        plan = ShiftPlan.objects.get(account=employer)
        assert plan.shifts.count() == 2

    def test_prestatorul_fara_capabilitate_primeste_403(self, client, worker):
        client.force_login(worker.user)
        assert client.get("/dashboard/planificare/").status_code == 403

    def test_obiectivele_altui_cont_nu_apar(self, client, employer, site, norderstedt):
        from apps.accounts.enums import Capability, EntityType
        from apps.accounts.models import User
        from apps.accounts.services import create_account

        other = create_account(
            user=User.objects.create_user("x@example.de", "parola-lunga-123"),
            entity_type=EntityType.COMPANY, display_name="Alt SRL",
            capabilities=[Capability.EMPLOYER], locality=norderstedt,
        )
        client.force_login(other.memberships.first().user)
        response = client.get("/dashboard/obiective/")
        assert b"Haus Nord" not in response.content
