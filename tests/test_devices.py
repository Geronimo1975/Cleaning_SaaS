"""
Telemetrie.

Premisa care ține toată proiectarea: timpul de funcționare al unui aspirator
NU este timpul de curățenie. Telemetria verifică, nu calibrează — de aceea
nu există niciun test care să o lase să modifice `minutes_per_visit`.
"""

import json
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.devices.models import Device, DeviceStatus, TelemetrySession
from apps.devices.services import (
    TelemetryError,
    authenticate_device,
    find_discrepancies,
    ingest_session,
    utilisation,
)
from apps.planning.models import PlanStatus, Shift, ShiftPlan, ShiftStatus, Site, Zone


@pytest.fixture
def site(db, employer, norderstedt):
    return Site.objects.create(account=employer, name="Haus Nord", locality=norderstedt)


@pytest.fixture
def zone(db, site, category):
    return Zone.objects.create(
        site=site, name="Etaj 1", category=category, minutes_per_visit=120, visits_per_week=2
    )


@pytest.fixture
def device(db, employer, site):
    dev = Device.objects.create(
        account=employer, label="Aspirator 1", site=site,
        token_hash="pending", token_prefix="",
    )
    dev.raw_token = dev.issue_token()
    return dev


@pytest.fixture
def shift(db, employer, worker, zone):
    """
    Tura se ancorează în ceas, nu într-o oră fixă. O oră de start scrisă în
    clar („08:00") face testele să pice când suita rulează dimineața devreme:
    telemetria refuză, corect, sesiunile datate în viitor.
    """
    plan = ShiftPlan.objects.create(
        account=employer, week_start=_monday(), status=PlanStatus.PUBLISHED
    )
    start = timezone.localtime(timezone.now()) - timedelta(hours=1)
    return Shift.objects.create(
        plan=plan, zone=zone, worker=worker, date=start.date(),
        start_time=start.time().replace(microsecond=0), duration_minutes=120,
    )


def _monday():
    today = timezone.localdate()
    return today - timedelta(days=today.isoweekday() - 1)


def _payload(shift, runtime=30, external_id="s-1"):
    """Sesiune care tocmai s-a încheiat — mereu în trecut, oricând rulează suita."""
    start = timezone.now() - timedelta(minutes=runtime)
    return {
        "external_id": external_id,
        "started_at": start.isoformat(),
        "ended_at": (start + timedelta(minutes=runtime)).isoformat(),
        "runtime_minutes": runtime,
        "area_sqm": 210,
        "battery_start": 100,
        "battery_end": 62,
    }


@pytest.mark.django_db
class TestAuthentication:
    def test_cheia_nu_se_stocheaza_in_clar(self, device):
        assert device.raw_token not in device.token_hash
        assert len(device.token_hash) == 64

    def test_cheia_valida_identifica_aparatul(self, device):
        assert authenticate_device(device.raw_token) == device

    def test_cheia_gresita_e_refuzata(self, device):
        with pytest.raises(TelemetryError):
            authenticate_device("altceva")

    def test_reemiterea_invalideaza_cheia_veche(self, device):
        old = device.raw_token
        device.issue_token()
        with pytest.raises(TelemetryError):
            authenticate_device(old)

    def test_aparatul_scos_din_uz_nu_mai_raporteaza(self, device):
        device.status = DeviceStatus.RETIRED
        device.save()
        with pytest.raises(TelemetryError):
            authenticate_device(device.raw_token)


@pytest.mark.django_db
class TestIngestion:
    def test_sesiunea_se_leaga_de_tura(self, device, shift):
        session, created = ingest_session(device, _payload(shift))
        assert created
        assert session.shift == shift
        assert session.runtime_minutes == 30

    def test_ingestia_e_idempotenta(self, device, shift):
        ingest_session(device, _payload(shift))
        _, created = ingest_session(device, _payload(shift))
        assert not created
        assert TelemetrySession.objects.count() == 1

    def test_sesiunea_in_viitor_e_refuzata(self, device, shift):
        payload = _payload(shift)
        future = timezone.now() + timedelta(days=2)
        payload["started_at"] = future.isoformat()
        payload["ended_at"] = (future + timedelta(minutes=30)).isoformat()
        with pytest.raises(TelemetryError):
            ingest_session(device, payload)

    def test_functionarea_nu_poate_depasi_intervalul(self, device, shift):
        payload = _payload(shift, runtime=30)
        payload["runtime_minutes"] = 400
        with pytest.raises(TelemetryError):
            ingest_session(device, payload)

    def test_campurile_lipsa_sunt_semnalate(self, device):
        with pytest.raises(TelemetryError, match="Câmpuri lipsă"):
            ingest_session(device, {"external_id": "x"})

    def test_potrivirea_ambigua_nu_alege_nimic(self, device, shift, zone, employer, worker):
        Shift.objects.create(
            plan=shift.plan, zone=zone, worker=worker, date=shift.date,
            start_time=(
                timezone.localtime(timezone.now()) - timedelta(minutes=30)
            ).time().replace(microsecond=0),
            duration_minutes=120,
        )
        session, _ = ingest_session(device, _payload(shift))
        assert session.shift is None, "două ture candidate = nicio atribuire"

    def test_aparatul_isi_actualizeaza_prezenta(self, device, shift):
        assert device.last_seen_at is None
        ingest_session(device, _payload(shift))
        device.refresh_from_db()
        assert device.is_online


@pytest.mark.django_db
class TestApi:
    def test_ingestie_prin_http(self, client, device, shift):
        response = client.post(
            "/api/telemetry/", data=json.dumps(_payload(shift)),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {device.raw_token}",
        )
        assert response.status_code == 201
        assert response.json()["matched_shift"] == shift.pk

    def test_fara_cheie_401(self, client, shift):
        response = client.post(
            "/api/telemetry/", data=json.dumps(_payload(shift)),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_json_invalid_400(self, client, device):
        response = client.post(
            "/api/telemetry/", data="{nu e json",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {device.raw_token}",
        )
        assert response.status_code == 400

    def test_payload_invalid_422(self, client, device):
        response = client.post(
            "/api/telemetry/", data=json.dumps({"external_id": "x"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {device.raw_token}",
        )
        assert response.status_code == 422

    def test_retrimiterea_da_200_nu_duplicat(self, client, device, shift):
        body = json.dumps(_payload(shift))
        headers = {"content_type": "application/json",
                   "HTTP_AUTHORIZATION": f"Bearer {device.raw_token}"}
        assert client.post("/api/telemetry/", data=body, **headers).status_code == 201
        assert client.post("/api/telemetry/", data=body, **headers).status_code == 200


@pytest.mark.django_db
class TestDiscrepancies:
    def _complete(self, shift, minutes):
        shift.status = ShiftStatus.DONE
        shift.actual_minutes = minutes
        shift.save()

    def test_pontaj_lung_cu_aspirator_scurt_e_semnalat(self, device, shift):
        self._complete(shift, 90)
        ingest_session(device, _payload(shift, runtime=5))
        findings = find_discrepancies(
            shift.plan.account, shift.date - timedelta(days=1), shift.date
        )
        assert len(findings) == 1
        assert findings[0].kind == "LOW_ACTIVITY"

    def test_raport_plauzibil_nu_e_semnalat(self, device, shift):
        self._complete(shift, 120)
        ingest_session(device, _payload(shift, runtime=35))
        findings = find_discrepancies(
            shift.plan.account, shift.date - timedelta(days=1), shift.date
        )
        assert findings == [], "35 min de aspirat la 120 min de curățenie e normal"

    def test_tura_fara_telemetrie_pe_obiectiv_cu_aparate(self, device, shift):
        self._complete(shift, 120)
        findings = find_discrepancies(
            shift.plan.account, shift.date - timedelta(days=1), shift.date
        )
        assert findings[0].kind == "NO_TELEMETRY"

    def test_obiectiv_fara_aparate_nu_produce_alerte(self, employer, shift):
        self._complete(shift, 120)
        findings = find_discrepancies(
            employer, shift.date - timedelta(days=1), shift.date
        )
        assert findings == []

    def test_aparat_pornit_mai_mult_decat_pontajul(self, device, shift):
        self._complete(shift, 20)
        ingest_session(device, _payload(shift, runtime=45))
        findings = find_discrepancies(
            shift.plan.account, shift.date - timedelta(days=1), shift.date
        )
        assert findings[0].kind == "OVER_RUNTIME"


@pytest.mark.django_db
class TestDeviceDashboard:
    def test_utilizarea_insumeaza_sesiunile(self, device, shift, employer):
        ingest_session(device, _payload(shift, runtime=30, external_id="a"))
        ingest_session(device, _payload(shift, runtime=25, external_id="b"))
        rows = utilisation(employer, shift.date - timedelta(days=1), shift.date)
        assert rows[0]["runtime_minutes"] == 55
        assert rows[0]["sessions"] == 2

    def test_pagina_afiseaza_cheia_o_singura_data(self, client, employer, site):
        client.force_login(employer.user)
        response = client.post("/dashboard/echipamente/", {
            "action": "create", "label": "Aspirator 2", "kind": "VACUUM",
            "site": site.pk, "status": "ACTIVE",
        }, follow=True)
        assert b"O SINGUR" in response.content
        created = Device.objects.get(label="Aspirator 2")
        assert client.get("/dashboard/echipamente/").content.count(
            created.token_hash.encode()
        ) == 0

    def test_lucratorul_nu_are_acces(self, client, worker):
        client.force_login(worker.user)
        assert client.get("/dashboard/echipamente/").status_code == 403
        assert client.get("/dashboard/echipamente/discrepante/").status_code == 403
