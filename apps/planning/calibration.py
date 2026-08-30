"""
Calibrarea estimărilor din pontaj.

Fiecare tură încheiată produce o abatere față de estimare. Adunate, abaterile
spun dacă `minutes_per_visit` e greșit — dar numai dacă se citesc cu grijă:

  * Mediana, nu media. O singură tură de 300 de minute (o inundație, o
    predare de locuință) ar trage media în sus și ar strica estimarea pentru
    toate săptămânile următoare.

  * Prag dublu: abaterea trebuie să fie și relativă (≥ 15 %), și absolută
    (≥ 10 min). 8 minute peste o estimare de 45 nu merită un plan schimbat.

  * Eșantion minim și fereastră care începe la ULTIMA calibrare aplicată.
    Altfel se măsoară eroarea unei estimări care nu mai există, iar sistemul
    oscilează la infinit între două valori.

  * Perioadă de liniște după o aplicare, din același motiv.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    CalibrationStatus,
    Confidence,
    Shift,
    ShiftStatus,
    Zone,
    ZoneCalibration,
)

MIN_SAMPLE = 5
MIN_RELATIVE_DEVIATION = 0.15
MIN_ABSOLUTE_DEVIATION = 10
COOLDOWN_DAYS = 28
MAX_LOOKBACK_DAYS = 180


@dataclass
class Analysis:
    zone: Zone
    sample_size: int
    window_start: date
    window_end: date
    current_minutes: int
    median_minutes: int | None = None
    dispersion_minutes: int = 0
    suggested_minutes: int | None = None
    confidence: str | None = None
    verdict: str = ""

    @property
    def actionable(self) -> bool:
        return self.suggested_minutes is not None


def _median(values: list[int]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


def _mad(values: list[int], center: float) -> float:
    """Abaterea mediană absolută — dispersie rezistentă la valori extreme."""
    return _median([int(abs(v - center)) for v in values]) if values else 0.0


def _window_start(zone: Zone, today: date) -> date:
    """Fereastra începe după ultima calibrare aplicată, ca să nu măsurăm trecutul."""
    last_applied = zone.calibrations.filter(status=CalibrationStatus.APPLIED).first()
    floor = today - timedelta(days=MAX_LOOKBACK_DAYS)
    if last_applied and last_applied.decided_at:
        return max(floor, last_applied.decided_at.date())
    return floor


def analyze_zone(zone: Zone, today: date | None = None) -> Analysis:
    today = today or timezone.localdate()
    start = _window_start(zone, today)
    analysis = Analysis(
        zone=zone, sample_size=0, window_start=start, window_end=today,
        current_minutes=zone.minutes_per_visit,
    )

    last_applied = zone.calibrations.filter(status=CalibrationStatus.APPLIED).first()
    if last_applied and last_applied.decided_at:
        if (today - last_applied.decided_at.date()).days < COOLDOWN_DAYS:
            analysis.verdict = (
                f"Calibrat recent; se așteaptă {COOLDOWN_DAYS} de zile de date noi."
            )
            return analysis

    durations = list(
        Shift.objects.filter(
            zone=zone, status=ShiftStatus.DONE, actual_minutes__isnull=False,
            date__gte=start, date__lte=today,
        ).values_list("actual_minutes", flat=True)
    )
    analysis.sample_size = len(durations)

    if len(durations) < MIN_SAMPLE:
        analysis.verdict = f"Prea puține ture pontate ({len(durations)}/{MIN_SAMPLE})."
        return analysis

    median = _median(durations)
    analysis.median_minutes = round(median)
    analysis.dispersion_minutes = round(_mad(durations, median))

    deviation = median - zone.minutes_per_visit
    relative = abs(deviation) / zone.minutes_per_visit if zone.minutes_per_visit else 0

    if abs(deviation) < MIN_ABSOLUTE_DEVIATION or relative < MIN_RELATIVE_DEVIATION:
        analysis.verdict = (
            f"Estimarea e corectă: mediana {round(median)} min față de "
            f"{zone.minutes_per_visit} min planificate."
        )
        return analysis

    analysis.suggested_minutes = round(median)
    analysis.confidence = _confidence(len(durations), analysis.dispersion_minutes, median)
    direction = "mai mult" if deviation > 0 else "mai puțin"
    analysis.verdict = (
        f"Durează sistematic {direction}: mediana {round(median)} min "
        f"pe {len(durations)} ture, față de {zone.minutes_per_visit} min planificate."
    )
    return analysis


def _confidence(sample: int, dispersion: float, median: float) -> str:
    """Un eșantion mare cu ture consistente e o dovadă; unul mic și împrăștiat, nu."""
    spread = dispersion / median if median else 1
    if sample >= 12 and spread <= 0.15:
        return Confidence.HIGH
    if sample >= 8 and spread <= 0.30:
        return Confidence.MEDIUM
    return Confidence.LOW


@transaction.atomic
def propose_calibrations(account, today: date | None = None) -> list[ZoneCalibration]:
    """Rulează analiza pe toate zonele contului și creează propunerile lipsă."""
    today = today or timezone.localdate()
    created = []
    zones = Zone.objects.filter(
        site__account=account, is_active=True, site__is_active=True
    ).select_related("site")

    for zone in zones:
        analysis = analyze_zone(zone, today)
        existing = zone.calibrations.filter(status=CalibrationStatus.PROPOSED).first()

        if not analysis.actionable:
            # O propunere care nu mai e susținută de date se retrage singură.
            if existing:
                existing.status = CalibrationStatus.REJECTED
                existing.decision_note = "Retrasă automat: datele noi nu o mai susțin."
                existing.decided_at = timezone.now()
                existing.save(update_fields=["status", "decision_note", "decided_at"])
            continue

        if existing:
            if existing.suggested_minutes == analysis.suggested_minutes:
                continue
            existing.status = CalibrationStatus.REJECTED
            existing.decision_note = "Înlocuită de o propunere mai recentă."
            existing.decided_at = timezone.now()
            existing.save(update_fields=["status", "decision_note", "decided_at"])

        created.append(ZoneCalibration.objects.create(
            zone=zone,
            sample_size=analysis.sample_size,
            window_start=analysis.window_start,
            window_end=analysis.window_end,
            current_minutes=analysis.current_minutes,
            suggested_minutes=analysis.suggested_minutes,
            median_minutes=analysis.median_minutes,
            dispersion_minutes=analysis.dispersion_minutes,
            confidence=analysis.confidence,
        ))
    return created


@transaction.atomic
def apply_calibration(calibration: ZoneCalibration, actor, note: str = "") -> ZoneCalibration:
    if calibration.status != CalibrationStatus.PROPOSED:
        raise ValueError("Propunerea a fost deja decisă.")
    if calibration.zone.site.account_id != actor.pk:
        raise ValueError("Zona nu aparține contului.")

    zone = calibration.zone
    zone.minutes_per_visit = calibration.suggested_minutes
    zone.save(update_fields=["minutes_per_visit"])

    calibration.status = CalibrationStatus.APPLIED
    calibration.decided_by = actor
    calibration.decided_at = timezone.now()
    calibration.decision_note = note[:300]
    calibration.save(update_fields=["status", "decided_by", "decided_at", "decision_note"])
    return calibration


@transaction.atomic
def reject_calibration(calibration: ZoneCalibration, actor, note: str = "") -> ZoneCalibration:
    if calibration.status != CalibrationStatus.PROPOSED:
        raise ValueError("Propunerea a fost deja decisă.")
    if calibration.zone.site.account_id != actor.pk:
        raise ValueError("Zona nu aparține contului.")
    calibration.status = CalibrationStatus.REJECTED
    calibration.decided_by = actor
    calibration.decided_at = timezone.now()
    calibration.decision_note = note[:300]
    calibration.save(update_fields=["status", "decided_by", "decided_at", "decision_note"])
    return calibration


def pending_impact(account) -> dict:
    """
    Ce s-ar schimba dacă TOATE propunerile deschise ar fi aplicate.
    Contează, pentru că o creștere de estimare poate transforma un plan care
    încape într-unul care nu mai încape în orele contractate.
    """
    proposals = ZoneCalibration.objects.filter(
        zone__site__account=account, status=CalibrationStatus.PROPOSED
    ).select_related("zone")
    delta = sum(p.weekly_impact_minutes for p in proposals)
    return {
        "count": len(proposals),
        "weekly_delta_minutes": delta,
        "increases": sum(1 for p in proposals if p.delta_minutes > 0),
        "decreases": sum(1 for p in proposals if p.delta_minutes < 0),
    }
