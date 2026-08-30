"""Ingestia telemetriei, potrivirea cu turele și verificarea încrucișată."""

from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.planning.models import Shift, ShiftStatus

from .models import Device, DeviceStatus, TelemetrySession

# Cât de departe de tură poate cădea o sesiune și tot să-i aparțină.
MATCH_TOLERANCE = timedelta(hours=2)
# Sub acest raport, timpul pontat nu e susținut de funcționarea echipamentului.
SUSPICIOUS_RATIO = 0.10


class TelemetryError(ValueError):
    pass


def authenticate_device(raw_token: str) -> Device:
    if not raw_token:
        raise TelemetryError("Lipsește cheia echipamentului.")
    device = Device.objects.filter(token_hash=Device.hash_token(raw_token)).first()
    if device is None:
        raise TelemetryError("Cheie necunoscută.")
    if device.status == DeviceStatus.RETIRED:
        raise TelemetryError("Echipament scos din uz.")
    return device


@transaction.atomic
def ingest_session(device: Device, payload: dict) -> tuple[TelemetrySession, bool]:
    """Idempotent pe (device, external_id). Returnează (sesiune, e_nouă)."""
    required = ("external_id", "started_at", "ended_at")
    missing = [f for f in required if not payload.get(f)]
    if missing:
        raise TelemetryError(f"Câmpuri lipsă: {', '.join(missing)}")

    started = _parse(payload["started_at"])
    ended = _parse(payload["ended_at"])
    if ended <= started:
        raise TelemetryError("Încheierea nu poate fi înaintea începerii.")
    if started > timezone.now() + timedelta(minutes=5):
        raise TelemetryError("Sesiune datată în viitor.")

    runtime = payload.get("runtime_minutes")
    elapsed = int((ended - started).total_seconds() // 60)
    if runtime is None:
        runtime = elapsed
    if int(runtime) > elapsed + 1:
        raise TelemetryError("Timpul de funcționare depășește intervalul raportat.")

    session, created = TelemetrySession.objects.get_or_create(
        device=device,
        external_id=str(payload["external_id"])[:64],
        defaults={
            "started_at": started,
            "ended_at": ended,
            "runtime_minutes": int(runtime),
            "area_sqm": payload.get("area_sqm"),
            "battery_start": payload.get("battery_start"),
            "battery_end": payload.get("battery_end"),
            "error_code": str(payload.get("error_code", ""))[:32],
            "raw_payload": payload,
        },
    )
    if created:
        session.shift = match_shift(session)
        if session.shift:
            session.save(update_fields=["shift"])
    device.touch()
    return session, created


def _parse(value):
    from django.utils.dateparse import parse_datetime

    parsed = parse_datetime(value) if isinstance(value, str) else value
    if parsed is None:
        raise TelemetryError(f"Dată invalidă: {value}")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


def match_shift(session: TelemetrySession) -> Shift | None:
    """
    Potrivirea e conservatoare: dacă rămân mai multe ture candidate, nu alege
    niciuna. O sesiune atribuită greșit strică și verificarea, și pontajul.
    """
    device = session.device
    local_date = session.date
    candidates = Shift.objects.filter(
        plan__account=device.account,
        date__gte=local_date - timedelta(days=1),
        date__lte=local_date + timedelta(days=1),
    ).select_related("zone__site")

    if device.site_id:
        candidates = candidates.filter(zone__site_id=device.site_id)

    matches = [s for s in candidates if _overlaps(session, s)]
    return matches[0] if len(matches) == 1 else None


def _overlaps(session: TelemetrySession, shift: Shift) -> bool:
    from datetime import datetime

    start = timezone.make_aware(datetime.combine(shift.date, shift.start_time))
    end = start + timedelta(minutes=shift.duration_minutes)
    return (
        session.started_at >= start - MATCH_TOLERANCE
        and session.ended_at <= end + MATCH_TOLERANCE
    )


@dataclass
class Discrepancy:
    shift: Shift
    reported_minutes: int
    device_minutes: int
    ratio: float | None
    kind: str
    message: str


def find_discrepancies(account, start, end) -> list[Discrepancy]:
    """
    Compară ce s-a pontat cu ce a funcționat. Nu produce sancțiuni — produce
    întrebări. Un raport mic poate însemna și o zonă cu mochetă puțină.
    """
    shifts = (
        Shift.objects.filter(
            plan__account=account, date__gte=start, date__lte=end,
            status=ShiftStatus.DONE, actual_minutes__isnull=False,
        )
        .prefetch_related("telemetry_sessions")
        .select_related("zone__site", "worker")
    )

    # Obiectivele care AU echipamente active, o singură dată. Interogat în buclă
    # (cum era), asta însemna un EXISTS per tură — 200 de ture pontate într-o
    # săptămână, 200 de interogări în plus.
    sites_with_devices = set(
        Device.objects.filter(
            account=account, status=DeviceStatus.ACTIVE, site__isnull=False
        ).values_list("site_id", flat=True)
    )

    results = []
    for shift in shifts:
        sessions = list(shift.telemetry_sessions.all())
        device_minutes = sum(s.runtime_minutes for s in sessions)

        if not sessions:
            if shift.zone.site_id in sites_with_devices:
                results.append(Discrepancy(
                    shift=shift, reported_minutes=shift.actual_minutes,
                    device_minutes=0, ratio=None, kind="NO_TELEMETRY",
                    message="Tură pontată, dar niciun echipament nu a raportat activitate.",
                ))
            continue

        ratio = device_minutes / shift.actual_minutes if shift.actual_minutes else 0
        if ratio < SUSPICIOUS_RATIO:
            results.append(Discrepancy(
                shift=shift, reported_minutes=shift.actual_minutes,
                device_minutes=device_minutes, ratio=round(ratio, 2), kind="LOW_ACTIVITY",
                message=(
                    f"Pontaj {shift.actual_minutes} min, echipament {device_minutes} min "
                    f"({round(ratio * 100)} %)."
                ),
            ))
        elif device_minutes > shift.actual_minutes:
            results.append(Discrepancy(
                shift=shift, reported_minutes=shift.actual_minutes,
                device_minutes=device_minutes, ratio=round(ratio, 2), kind="OVER_RUNTIME",
                message=(
                    f"Echipamentul a funcționat {device_minutes} min, mai mult decât "
                    f"cele {shift.actual_minutes} min pontate."
                ),
            ))
    return results


def utilisation(account, start, end) -> list[dict]:
    """Cât e folosit fiecare echipament — baza deciziei de a mai cumpăra sau nu."""
    # Un singur SELECT pentru toate sesiunile din interval, grupate în Python.
    # Varianta cu `device.sessions.filter(...)` în buclă costa o interogare per
    # echipament.
    devices = list(
        Device.objects.filter(account=account).exclude(status=DeviceStatus.RETIRED)
    )
    by_device: dict[int, list[TelemetrySession]] = {d.pk: [] for d in devices}
    sessions = TelemetrySession.objects.filter(
        device__in=devices, started_at__date__gte=start, started_at__date__lte=end
    )
    for session in sessions:
        by_device[session.device_id].append(session)

    rows = []
    for device in devices:
        found = by_device[device.pk]
        rows.append({
            "device": device,
            "sessions": len(found),
            "runtime_minutes": sum(s.runtime_minutes for s in found),
            "area_sqm": sum(s.area_sqm or 0 for s in found),
            "errors": sum(1 for s in found if s.error_code),
            "online": device.is_online,
        })
    return sorted(rows, key=lambda r: -r["runtime_minutes"])
