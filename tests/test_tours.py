"""
Runde (Tourenreinigung): un lucrător, mai multe obiective, în ordine.

Invariantul central: runda se planifică indivizibil. O rundă executată pe
jumătate lasă blocuri necurățate fără ca nimeni să vadă asta în plan — de aceea
„nu încape" produce o singură intrare în raport, nu opriri risipite.
"""

from datetime import date, timedelta

import pytest

from apps.accounts.profiles import ServiceArea
from apps.planning.models import Shift, Site, Tour, TourStop, Zone
from apps.planning.services import capacity_report, generate_week_plan

MONDAY = date(2026, 10, 5)


@pytest.fixture
def sites(db, employer, norderstedt, pinneberg):
    return {
        "a": Site.objects.create(account=employer, name="Bloc A", locality=norderstedt),
        "b": Site.objects.create(account=employer, name="Bloc B", locality=norderstedt),
        "c": Site.objects.create(account=employer, name="Bloc C", locality=pinneberg),
    }


@pytest.fixture
def make_zone(db, category):
    def _make(site, name, minutes):
        return Zone.objects.create(
            site=site, name=name, category=category,
            minutes_per_visit=minutes, visits_per_week=1,
        )

    return _make


@pytest.fixture
def tour(db, employer, sites, make_zone):
    def _make(travel=10, weekdays="1", visits=1, include_pinneberg=False):
        t = Tour.objects.create(
            account=employer, name="Rundă scări nord",
            allowed_weekdays=weekdays, visits_per_week=visits,
        )
        keys = ["a", "b", "c"] if include_pinneberg else ["a", "b"]
        for index, key in enumerate(keys, start=1):
            TourStop.objects.create(
                tour=t, zone=make_zone(sites[key], f"Scară {key.upper()}", 45),
                position=index, travel_minutes=0 if index == 1 else travel,
            )
        return t

    return _make


@pytest.mark.django_db
class TestTourModel:
    def test_totalul_include_deplasarea(self, tour):
        t = tour(travel=15)
        assert t.total_minutes == 45 + 15 + 45, "lucru + drum între opriri"

    def test_localitatile_acoperite(self, tour, norderstedt, pinneberg):
        t = tour(include_pinneberg=True)
        assert t.localities == {norderstedt.pk, pinneberg.pk}

    def test_o_zona_nu_intra_de_doua_ori_in_aceeasi_runda(self, tour, make_zone, sites):
        from django.db import IntegrityError

        t = tour()
        existing = t.stops.first()
        with pytest.raises(IntegrityError):
            TourStop.objects.create(tour=t, zone=existing.zone, position=9)


@pytest.mark.django_db
class TestTourPlanning:
    def test_runda_ajunge_la_un_singur_om_intr_o_zi(
        self, employer, tour, signed_contract, worker
    ):
        signed_contract(hours="100")
        tour()
        plan = generate_week_plan(employer, MONDAY)
        shifts = list(plan.shifts.all())
        assert len(shifts) == 2
        assert len({s.worker_id for s in shifts}) == 1
        assert len({s.date for s in shifts}) == 1

    def test_opririle_sunt_consecutive_si_includ_drumul(
        self, employer, tour, signed_contract
    ):
        signed_contract(hours="100")
        tour(travel=20)
        plan = generate_week_plan(employer, MONDAY)
        first, second = plan.shifts.order_by("position")
        assert first.position == 1 and second.position == 2
        assert first.start_time.strftime("%H:%M") == "07:00"
        # 07:00 + 45 min lucru + 20 min drum
        assert second.start_time.strftime("%H:%M") == "08:05"
        assert second.travel_minutes == 20

    def test_deplasarea_consuma_din_bugetul_contractat(
        self, employer, tour, signed_contract
    ):
        signed_contract(hours="100")
        t = tour(travel=30)
        plan = generate_week_plan(employer, MONDAY)
        lucrat = sum(s.duration_minutes for s in plan.shifts.all())
        assert lucrat == 90
        assert t.total_minutes == 120, "bugetul consumat include cele 30 min de drum"

    def test_cererea_raportata_include_deplasarea(self, employer, tour, signed_contract):
        signed_contract(hours="100")
        tour(travel=30)
        report = capacity_report(employer, MONDAY)
        assert report["demand_minutes"] == 90 + 30

    def test_runda_care_nu_incape_ramane_intreaga_nealocata(
        self, employer, tour, signed_contract
    ):
        signed_contract(hours="5")  # ~69 min/săptămână, runda cere 100
        tour(travel=10)
        plan = generate_week_plan(employer, MONDAY)
        assert plan.shifts.count() == 0, "nicio oprire nu se execută separat"
        assert len(plan.unmet_demand) == 1
        entry = plan.unmet_demand[0]
        assert entry["tour"] is True
        assert entry["minutes"] == 100
        assert "buget săptămânal epuizat" in str(entry["reasons"])

    def test_lucratorul_trebuie_sa_acopere_toate_localitatile(
        self, employer, worker, tour, signed_contract, norderstedt
    ):
        ServiceArea.objects.create(account=worker, locality=norderstedt)
        signed_contract(hours="100")
        tour(include_pinneberg=True)  # o oprire e în Pinneberg
        plan = generate_week_plan(employer, MONDAY)
        assert plan.shifts.count() == 0
        assert "nu deservește localitatea" in str(plan.unmet_demand[0]["reasons"])

    def test_zonele_din_runda_nu_se_mai_planifica_separat(
        self, employer, tour, signed_contract
    ):
        signed_contract(hours="100")
        t = tour()
        plan = generate_week_plan(employer, MONDAY)
        zone_ids = [s.zone_id for s in plan.shifts.all()]
        assert sorted(zone_ids) == sorted(s.zone_id for s in t.stops.all())
        assert len(zone_ids) == len(set(zone_ids)), "nicio zonă planificată de două ori"

    def test_zonele_libere_se_planifica_pe_langa_runda(
        self, employer, tour, signed_contract, make_zone, sites
    ):
        signed_contract(hours="100")
        tour()
        make_zone(sites["a"], "Subsol", 30)
        plan = generate_week_plan(employer, MONDAY)
        assert plan.shifts.count() == 3
        assert plan.shifts.filter(tour__isnull=True).count() == 1

    def test_runda_respecta_ziua_permisa(self, employer, tour, signed_contract):
        signed_contract(hours="100")
        tour(weekdays="3")
        plan = generate_week_plan(employer, MONDAY)
        assert all(s.date.isoweekday() == 3 for s in plan.shifts.all())

    def test_runda_de_doua_ori_pe_saptamana(self, employer, tour, signed_contract):
        signed_contract(hours="100")
        tour(weekdays="1,4", visits=2)
        plan = generate_week_plan(employer, MONDAY)
        assert plan.shifts.count() == 4
        assert {s.date.isoweekday() for s in plan.shifts.all()} == {1, 4}

    def test_runda_inactiva_lasa_zonele_sa_se_planifice_individual(
        self, employer, tour, signed_contract
    ):
        """
        Dezactivarea rundei desface gruparea, nu anulează munca: zonele rămân
        active și trebuie curățate în continuare, doar că nu mai ca o rundă.
        """
        signed_contract(hours="100")
        t = tour()
        Tour.objects.filter(pk=t.pk).update(is_active=False)
        plan = generate_week_plan(employer, MONDAY)
        assert plan.shifts.count() == 2
        assert plan.shifts.filter(tour__isnull=False).count() == 0
        assert plan.unmet_demand == []


@pytest.mark.django_db
class TestTourViews:
    def test_crearea_si_adaugarea_opririlor(self, client, employer, sites, make_zone):
        zone = make_zone(sites["a"], "Scară A", 45)
        client.force_login(employer.memberships.first().user)
        client.post("/dashboard/runde/", {
            "action": "create", "name": "Rundă nord",
            "allowed_weekdays": "1,3", "visits_per_week": 2,
        }, follow=True)
        t = Tour.objects.get(name="Rundă nord")
        client.post(f"/dashboard/runde/{t.pk}/", {
            "action": "add_stop", "zone": zone.pk, "position": 1, "travel_minutes": 0,
        }, follow=True)
        assert t.stops.count() == 1

    def test_o_zona_a_altui_cont_nu_e_selectabila(
        self, client, employer, sites, make_zone, norderstedt
    ):
        from apps.accounts.enums import Capability, EntityType
        from apps.accounts.models import User
        from apps.accounts.services import create_account

        other = create_account(
            user=User.objects.create_user("x@example.de", "parola-lunga-123"),
            entity_type=EntityType.COMPANY, display_name="Alt SRL",
            capabilities=[Capability.EMPLOYER], locality=norderstedt,
        )
        zone = make_zone(sites["a"], "Scară A", 45)
        client.force_login(other.memberships.first().user)
        t = Tour.objects.create(account=other, name="Rundă străină")
        client.post(f"/dashboard/runde/{t.pk}/", {
            "action": "add_stop", "zone": zone.pk, "position": 1, "travel_minutes": 0,
        }, follow=True)
        assert t.stops.count() == 0, "zona altui cont nu trece de queryset"

    def test_runda_altui_cont_da_404(self, client, employer, tour, norderstedt):
        from apps.accounts.enums import Capability, EntityType
        from apps.accounts.models import User
        from apps.accounts.services import create_account

        t = tour()
        other = create_account(
            user=User.objects.create_user("y@example.de", "parola-lunga-123"),
            entity_type=EntityType.COMPANY, display_name="Alt SRL 2",
            capabilities=[Capability.EMPLOYER], locality=norderstedt,
        )
        client.force_login(other.memberships.first().user)
        assert client.get(f"/dashboard/runde/{t.pk}/").status_code == 404

    def test_lucratorul_nu_are_acces(self, client, worker):
        client.force_login(worker.memberships.first().user)
        assert client.get("/dashboard/runde/").status_code == 403
