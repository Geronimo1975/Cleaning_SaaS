"""
Publicare, pontaj, evidența timpului de lucru.

Pontajul nu e confort: BAG 13.09.2022 (1 ABR 22/21) pe baza §3 Abs. 2 Nr. 1
ArbSchG obligă la înregistrarea întregului timp lucrat. De aceea jurnalul e
append-only și corecțiile păstrează valoarea veche.
"""

from datetime import date, timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.planning.attendance import (
    ShiftError,
    check_in,
    check_out,
    confirm_shift,
    correct_minutes,
    decline_shift,
    mark_missed,
    publish_plan,
    time_records,
)
from apps.planning.models import PlanStatus, Shift, ShiftEvent, ShiftStatus, Site, Zone
from apps.planning.services import generate_week_plan

MONDAY = date(2026, 10, 5)


@pytest.fixture
def plan(db, employer, worker, norderstedt, category, signed_contract):
    signed_contract(hours="40")
    site = Site.objects.create(account=employer, name="Haus Nord", locality=norderstedt)
    Zone.objects.create(
        site=site, name="Etaj 1", category=category, minutes_per_visit=120,
        visits_per_week=2, allowed_weekdays="1,3",
    )
    return generate_week_plan(employer, MONDAY)


@pytest.fixture
def shift(plan, employer):
    publish_plan(plan, actor=employer)
    return plan.shifts.first()


@pytest.mark.django_db
class TestPublishing:
    def test_publicarea_anunta_lucratorii(self, plan, employer):
        mail.outbox.clear()
        publish_plan(plan, actor=employer)
        plan.refresh_from_db()
        assert plan.status == PlanStatus.PUBLISHED
        assert plan.published_at is not None
        assert len(mail.outbox) == 1, "un email per lucrător, nu unul per tură"
        assert "Haus Nord" in mail.outbox[0].body

    def test_un_plan_gol_nu_se_publica(self, db, employer):
        from apps.planning.models import ShiftPlan

        empty = ShiftPlan.objects.create(account=employer, week_start=MONDAY)
        with pytest.raises(ShiftError):
            publish_plan(empty)

    def test_planul_publicat_nu_se_regenereaza_accidental(self, plan, employer):
        publish_plan(plan, actor=employer)
        with pytest.raises(ValueError):
            generate_week_plan(employer, MONDAY)

    def test_regenerarea_explicita_e_permisa(self, plan, employer):
        publish_plan(plan, actor=employer)
        regenerated = generate_week_plan(employer, MONDAY, replace=True)
        assert regenerated.shifts.count() == 2

    def test_ciornele_nu_apar_la_lucrator(self, client, plan, worker):
        client.force_login(worker.user)
        response = client.get(f"/dashboard/turele-mele/?week={MONDAY}")
        assert b"Nicio tur" in response.content


@pytest.mark.django_db
class TestAttendance:
    def test_confirmare(self, shift, worker):
        confirm_shift(shift, worker)
        shift.refresh_from_db()
        assert shift.status == ShiftStatus.CONFIRMED

    def test_refuz_cu_motiv(self, shift, worker):
        decline_shift(shift, worker, "Sunt bolnavă")
        shift.refresh_from_db()
        assert shift.status == ShiftStatus.DECLINED
        assert shift.worker_note == "Sunt bolnavă"

    def test_pontajul_calculeaza_timpul_real(self, shift, worker):
        start = timezone.now()
        check_in(shift, worker, now=start)
        check_out(shift, worker, now=start + timedelta(minutes=95))
        shift.refresh_from_db()
        assert shift.status == ShiftStatus.DONE
        assert shift.actual_minutes == 95
        assert shift.variance_minutes == -25, "a durat mai puțin decât estimarea de 120 min"

    def test_check_out_fara_check_in_e_refuzat(self, shift, worker):
        with pytest.raises(ShiftError):
            check_out(shift, worker)

    def test_check_out_inainte_de_check_in_e_refuzat(self, shift, worker):
        now = timezone.now()
        check_in(shift, worker, now=now)
        with pytest.raises(ShiftError):
            check_out(shift, worker, now=now - timedelta(minutes=5))

    def test_tura_altuia_nu_se_ponteaza(self, shift, employer):
        with pytest.raises(ShiftError):
            check_in(shift, employer)

    def test_jurnalul_inregistreaza_fiecare_pas(self, shift, worker):
        start = timezone.now()
        confirm_shift(shift, worker)
        check_in(shift, worker, now=start)
        check_out(shift, worker, now=start + timedelta(minutes=60))
        kinds = list(shift.events.values_list("kind", flat=True))
        assert kinds == ["PUBLISHED", "CONFIRMED", "CHECK_IN", "CHECK_OUT"]

    def test_evenimentele_sunt_imutabile(self, shift, worker):
        confirm_shift(shift, worker)
        event = shift.events.last()
        event.kind = ShiftEvent.Kind.CHECK_IN
        with pytest.raises(RuntimeError):
            event.save()


@pytest.mark.django_db
class TestCorrections:
    def test_corectia_pastreaza_valoarea_veche(self, shift, worker, employer):
        start = timezone.now()
        check_in(shift, worker, now=start)
        check_out(shift, worker, now=start + timedelta(minutes=200))
        correct_minutes(shift, employer, 120, "Pauză neînregistrată")
        shift.refresh_from_db()
        assert shift.actual_minutes == 120
        event = shift.events.filter(kind=ShiftEvent.Kind.CORRECTED).get()
        assert event.payload["from"] == 200 and event.payload["to"] == 120
        assert event.payload["reason"] == "Pauză neînregistrată"

    def test_corectia_are_nevoie_de_motiv(self, shift, employer):
        with pytest.raises(ShiftError):
            correct_minutes(shift, employer, 120, "")

    def test_doar_angajatorul_corecteaza(self, shift, worker):
        with pytest.raises(ShiftError):
            correct_minutes(shift, worker, 120, "vreau mai mult")


@pytest.mark.django_db
class TestTimeRecords:
    def test_evidenta_insumeaza_timpul_efectiv(self, plan, employer, worker):
        publish_plan(plan, actor=employer)
        start = timezone.now()
        for index, shift in enumerate(plan.shifts.all()):
            check_in(shift, worker, now=start + timedelta(days=index))
            check_out(shift, worker, now=start + timedelta(days=index, minutes=100))
        records = time_records(employer, MONDAY, MONDAY + timedelta(days=6))
        assert len(records["rows"]) == 2
        assert records["totals_minutes"][worker.pk] == 200

    def test_tura_neefectuata_nu_se_ponteaza(self, shift, employer):
        mark_missed(shift, employer)
        records = time_records(employer, MONDAY, MONDAY + timedelta(days=6))
        assert records["rows"][0]["actual"] == 0
        assert records["totals_minutes"][shift.worker_id] == 0

    def test_retentia_e_de_doi_ani(self, employer):
        end = MONDAY + timedelta(days=6)
        records = time_records(employer, MONDAY, end)
        assert (records["retention_until"] - end).days >= 730


@pytest.mark.django_db
class TestShiftViews:
    def test_lucratorul_ponteaza_din_dashboard(self, client, shift, worker):
        client.force_login(worker.user)
        Shift.objects.filter(pk=shift.pk).update(date=timezone.localdate())
        client.post("/dashboard/turele-mele/",
                    {"shift": shift.pk, "action": "check_in"}, follow=True)
        shift.refresh_from_db()
        assert shift.status == ShiftStatus.IN_PROGRESS

    def test_pontajul_e_inaccesibil_lucratorului(self, client, worker):
        client.force_login(worker.user)
        assert client.get("/dashboard/pontaj/").status_code == 403

    def test_angajatorul_publica_din_dashboard(self, client, plan, employer):
        client.force_login(employer.user)
        client.post(f"/dashboard/planificare/{plan.pk}/publicare/", follow=True)
        plan.refresh_from_db()
        assert plan.status == PlanStatus.PUBLISHED
