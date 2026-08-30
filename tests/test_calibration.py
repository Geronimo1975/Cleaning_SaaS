"""
Calibrarea estimărilor din pontaj.

Riscul pe care îl apără aceste teste nu e „calculul e greșit", ci
„sistemul ajustează prea ușor". O estimare care se mișcă la fiecare tură
atipică face planul imprevizibil și ascunde semnalul real.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.planning.calibration import (
    COOLDOWN_DAYS,
    MIN_SAMPLE,
    analyze_zone,
    apply_calibration,
    pending_impact,
    propose_calibrations,
    reject_calibration,
)
from apps.planning.models import (
    CalibrationStatus,
    Confidence,
    PlanStatus,
    Shift,
    ShiftPlan,
    ShiftStatus,
    Site,
    Zone,
    ZoneCalibration,
)

# Ancorat în ziua reală: `decided_at` folosește ceasul, iar perioada de liniște
# se calculează față de el — o dată fictivă ar face testele să treacă degeaba.
TODAY = timezone.localdate()


@pytest.fixture
def zone(db, employer, norderstedt, category):
    site = Site.objects.create(account=employer, name="Haus Nord", locality=norderstedt)
    return Zone.objects.create(
        site=site, name="Etaj 1", category=category,
        minutes_per_visit=120, visits_per_week=2,
    )


@pytest.fixture
def log_shifts(db, employer, worker, zone):
    """Creează ture încheiate cu durate date."""

    def _log(durations, target_zone=None, start=None):
        target_zone = target_zone or zone
        start = start or TODAY - timedelta(days=60)
        plan, _ = ShiftPlan.objects.get_or_create(
            account=employer, week_start=start - timedelta(days=start.isoweekday() - 1),
            defaults={"status": PlanStatus.PUBLISHED},
        )
        for index, minutes in enumerate(durations):
            Shift.objects.create(
                plan=plan, zone=target_zone, worker=worker,
                date=start + timedelta(days=index), start_time="07:00",
                duration_minutes=target_zone.minutes_per_visit,
                status=ShiftStatus.DONE, actual_minutes=minutes,
            )

    return _log


@pytest.mark.django_db
class TestAnalysis:
    def test_esantion_prea_mic_nu_produce_propunere(self, zone, log_shifts):
        log_shifts([180, 175, 185])
        analysis = analyze_zone(zone, TODAY)
        assert not analysis.actionable
        assert f"{MIN_SAMPLE}" in analysis.verdict

    def test_abatere_sistematica_e_detectata(self, zone, log_shifts):
        log_shifts([175, 180, 185, 178, 182, 180])
        analysis = analyze_zone(zone, TODAY)
        assert analysis.actionable
        assert analysis.suggested_minutes == 180
        assert "mai mult" in analysis.verdict

    def test_scadere_sistematica_e_detectata(self, zone, log_shifts):
        log_shifts([85, 90, 88, 92, 87, 90])
        analysis = analyze_zone(zone, TODAY)
        assert analysis.suggested_minutes == 89
        assert "mai puțin" in analysis.verdict

    def test_abatere_mica_nu_declanseaza_nimic(self, zone, log_shifts):
        log_shifts([125, 130, 128, 126, 129, 127])
        analysis = analyze_zone(zone, TODAY)
        assert not analysis.actionable, "8 min peste 120 nu justifică un plan schimbat"
        assert "corectă" in analysis.verdict

    def test_o_singura_tura_extrema_nu_muta_estimarea(self, zone, log_shifts):
        """O inundație de 400 de minute nu trebuie să rescrie estimarea."""
        log_shifts([118, 122, 120, 119, 121, 400])
        analysis = analyze_zone(zone, TODAY)
        assert not analysis.actionable, "mediana rezistă la valori extreme"

    def test_media_ar_fi_gresit_aici(self, zone, log_shifts):
        durations = [118, 122, 120, 119, 121, 400]
        log_shifts(durations)
        assert sum(durations) / len(durations) > 165, "media ar fi propus ~166 min"
        assert analyze_zone(zone, TODAY).median_minutes == 120

    def test_increderea_creste_cu_esantionul_si_consistenta(self, zone, log_shifts):
        log_shifts([180] * 14)
        assert analyze_zone(zone, TODAY).confidence == Confidence.HIGH

    def test_ture_imprastiate_dau_incredere_scazuta(self, zone, log_shifts):
        log_shifts([120, 240, 90, 260, 100, 230])
        analysis = analyze_zone(zone, TODAY)
        if analysis.actionable:
            assert analysis.confidence == Confidence.LOW

    def test_turele_neefectuate_nu_intra_in_calcul(self, zone, log_shifts, employer, worker):
        log_shifts([180, 185, 175, 182, 178, 180])
        plan = ShiftPlan.objects.first()
        Shift.objects.create(
            plan=plan, zone=zone, worker=worker, date=TODAY, start_time="07:00",
            duration_minutes=120, status=ShiftStatus.MISSED,
        )
        assert analyze_zone(zone, TODAY).sample_size == 6


@pytest.mark.django_db
class TestProposals:
    def test_propunerea_se_creeaza_o_singura_data(self, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        assert len(propose_calibrations(employer, TODAY)) == 1
        assert len(propose_calibrations(employer, TODAY)) == 0
        assert ZoneCalibration.objects.filter(status=CalibrationStatus.PROPOSED).count() == 1

    def test_propunerea_nesustinuta_se_retrage_singura(self, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        propose_calibrations(employer, TODAY)
        Shift.objects.filter(zone=zone).update(actual_minutes=120)
        propose_calibrations(employer, TODAY)
        proposal = ZoneCalibration.objects.get()
        assert proposal.status == CalibrationStatus.REJECTED
        assert "Retrasă automat" in proposal.decision_note

    def test_impactul_saptamanal_e_calculat(self, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        propose_calibrations(employer, TODAY)
        impact = pending_impact(employer)
        assert impact["count"] == 1
        assert impact["increases"] == 1
        assert impact["weekly_delta_minutes"] == 120  # +60 min × 2 vizite


@pytest.mark.django_db
class TestDecisions:
    def test_aplicarea_schimba_estimarea(self, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        proposal = propose_calibrations(employer, TODAY)[0]
        apply_calibration(proposal, employer, "Confirmat de coordonator")
        zone.refresh_from_db()
        assert zone.minutes_per_visit == 180
        assert proposal.decided_by == employer

    def test_respingerea_lasa_estimarea_neatinsa(self, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        proposal = propose_calibrations(employer, TODAY)[0]
        reject_calibration(proposal, employer, "Perioadă atipică")
        zone.refresh_from_db()
        assert zone.minutes_per_visit == 120

    def test_o_propunere_decisa_nu_se_redecide(self, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        proposal = propose_calibrations(employer, TODAY)[0]
        apply_calibration(proposal, employer)
        with pytest.raises(ValueError):
            reject_calibration(proposal, employer)

    def test_alt_cont_nu_decide(self, employer, worker, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        proposal = propose_calibrations(employer, TODAY)[0]
        with pytest.raises(ValueError):
            apply_calibration(proposal, worker)

    def test_perioada_de_liniste_previne_oscilatia(self, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        proposal = propose_calibrations(employer, TODAY)[0]
        apply_calibration(proposal, employer)
        analysis = analyze_zone(zone, TODAY + timedelta(days=COOLDOWN_DAYS - 1))
        assert not analysis.actionable
        assert "recent" in analysis.verdict

    def test_dupa_liniste_fereastra_ignora_datele_vechi(self, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        proposal = propose_calibrations(employer, TODAY)[0]
        apply_calibration(proposal, employer)
        later = TODAY + timedelta(days=COOLDOWN_DAYS + 1)
        analysis = analyze_zone(zone, later)
        assert analysis.sample_size == 0, "turele dinainte de calibrare nu se recontează"
        assert analysis.window_start >= proposal.decided_at.date()


@pytest.mark.django_db
class TestCalibrationView:
    def test_pagina_listeaza_propunerile(self, client, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180], start=TODAY - timedelta(days=20))
        client.force_login(employer.user)
        client.post("/dashboard/calibrare/", {"action": "scan"}, follow=True)
        response = client.get("/dashboard/calibrare/")
        assert b"120 &rarr; 180 min" in response.content or b"180 min" in response.content

    def test_aplicarea_din_dashboard(self, client, employer, zone, log_shifts):
        log_shifts([180, 185, 175, 182, 178, 180])
        proposal = propose_calibrations(employer, TODAY)[0]
        client.force_login(employer.user)
        client.post("/dashboard/calibrare/",
                    {"action": "apply", "calibration": proposal.pk}, follow=True)
        zone.refresh_from_db()
        assert zone.minutes_per_visit == 180

    def test_lucratorul_nu_are_acces(self, client, worker):
        client.force_login(worker.user)
        assert client.get("/dashboard/calibrare/").status_code == 403
