"""
Publicarea planului și pontajul.

Un plan pe care doar unitatea îl vede nu organizează munca. Publicarea îl face
vizibil lucrătorilor și îl îngheață: turele publicate nu mai dispar la o
regenerare, pentru că cineva și-a organizat deja săptămâna după ele.

Pontajul nu e o funcție de confort. BAG 13.09.2022 (1 ABR 22/21), pe baza
§3 Abs. 2 Nr. 1 ArbSchG, obligă angajatorul german să înregistreze întregul
timp de lucru — nu doar orele suplimentare. Înregistrările se păstrează
minimum doi ani (§16 Abs. 2 ArbZG).
"""

from datetime import datetime, timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import PlanStatus, Shift, ShiftEvent, ShiftPlan, ShiftStatus

RETENTION_YEARS = 2


class ShiftError(ValueError):
    """Tranziție de stare nepermisă."""


@transaction.atomic
def publish_plan(plan: ShiftPlan, actor=None, notify: bool = True) -> ShiftPlan:
    if plan.status == PlanStatus.PUBLISHED:
        raise ShiftError("Planul este deja publicat.")
    if not plan.shifts.exists():
        raise ShiftError("Un plan fără ture nu poate fi publicat.")

    plan.status = PlanStatus.PUBLISHED
    plan.published_at = timezone.now()
    plan.save(update_fields=["status", "published_at"])

    for shift in plan.shifts.all():
        ShiftEvent.objects.create(shift=shift, kind=ShiftEvent.Kind.PUBLISHED, actor=actor)

    if notify:
        _notify_workers(plan)
    return plan


def _notify_workers(plan: ShiftPlan) -> int:
    """Un email per lucrător, cu turele lui — nu unul per tură."""
    by_worker: dict[int, list[Shift]] = {}
    for shift in plan.shifts.select_related("worker", "zone__site"):
        if shift.worker_id:
            by_worker.setdefault(shift.worker_id, []).append(shift)

    sent = 0
    for shifts in by_worker.values():
        worker = shifts[0].worker
        email = worker.contact_email or _login_email(worker)
        if not email:
            continue
        lines = [
            f"{s.date.strftime('%d.%m.%Y')} {s.start_time.strftime('%H:%M')} — "
            f"{s.zone.site.name} / {s.zone.name} ({s.duration_minutes} min)"
            for s in shifts
        ]
        send_mail(
            subject=f"Dein Einsatzplan ab {plan.week_start.strftime('%d.%m.%Y')}",
            message="Deine Einsätze:\n\n" + "\n".join(lines),
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )
        sent += 1
    return sent


def _login_email(account):
    membership = account.memberships.select_related("user").first()
    return membership.user.email if membership else None


def _guard(shift: Shift, account, allowed: set[str]):
    if shift.worker_id != account.pk:
        raise ShiftError("Tura nu îți aparține.")
    if shift.plan.status != PlanStatus.PUBLISHED:
        raise ShiftError("Planul nu este publicat.")
    if shift.status not in allowed:
        raise ShiftError(f"Tura este în starea {shift.get_status_display()}.")


@transaction.atomic
def confirm_shift(shift: Shift, account) -> Shift:
    _guard(shift, account, {ShiftStatus.PLANNED})
    shift.status = ShiftStatus.CONFIRMED
    shift.save(update_fields=["status"])
    ShiftEvent.objects.create(shift=shift, kind=ShiftEvent.Kind.CONFIRMED, actor=account)
    return shift


@transaction.atomic
def decline_shift(shift: Shift, account, reason: str = "") -> Shift:
    _guard(shift, account, {ShiftStatus.PLANNED, ShiftStatus.CONFIRMED})
    shift.status = ShiftStatus.DECLINED
    shift.worker_note = reason[:300]
    shift.save(update_fields=["status", "worker_note"])
    ShiftEvent.objects.create(
        shift=shift, kind=ShiftEvent.Kind.DECLINED, actor=account,
        payload={"reason": reason[:300]},
    )
    return shift


@transaction.atomic
def check_in(shift: Shift, account, now=None) -> Shift:
    _guard(shift, account, {ShiftStatus.PLANNED, ShiftStatus.CONFIRMED})
    now = now or timezone.now()
    shift.checked_in_at = now
    shift.status = ShiftStatus.IN_PROGRESS
    shift.save(update_fields=["checked_in_at", "status"])
    ShiftEvent.objects.create(
        shift=shift, kind=ShiftEvent.Kind.CHECK_IN, actor=account,
        payload={"at": now.isoformat()},
    )
    return shift


@transaction.atomic
def check_out(shift: Shift, account, now=None, note: str = "") -> Shift:
    _guard(shift, account, {ShiftStatus.IN_PROGRESS})
    now = now or timezone.now()
    if now <= shift.checked_in_at:
        raise ShiftError("Încheierea nu poate fi înaintea începerii.")
    minutes = int((now - shift.checked_in_at).total_seconds() // 60)
    shift.checked_out_at = now
    shift.actual_minutes = minutes
    shift.status = ShiftStatus.DONE
    if note:
        shift.worker_note = note[:300]
    shift.save(update_fields=["checked_out_at", "actual_minutes", "status", "worker_note"])
    ShiftEvent.objects.create(
        shift=shift, kind=ShiftEvent.Kind.CHECK_OUT, actor=account,
        payload={"at": now.isoformat(), "minutes": minutes},
    )
    return shift


@transaction.atomic
def correct_minutes(shift: Shift, employer_account, minutes: int, reason: str) -> Shift:
    """
    Corecția angajatorului. Nu suprascrie discret: valoarea veche rămâne în
    jurnal, ca înregistrarea să rămână verificabilă.
    """
    if shift.plan.account_id != employer_account.pk:
        raise ShiftError("Doar angajatorul poate corecta pontajul.")
    if not reason:
        raise ShiftError("Corecția are nevoie de motiv.")
    previous = shift.actual_minutes
    shift.actual_minutes = minutes
    shift.status = ShiftStatus.DONE
    shift.save(update_fields=["actual_minutes", "status"])
    ShiftEvent.objects.create(
        shift=shift, kind=ShiftEvent.Kind.CORRECTED, actor=employer_account,
        payload={"from": previous, "to": minutes, "reason": reason[:300]},
    )
    return shift


@transaction.atomic
def mark_missed(shift: Shift, employer_account) -> Shift:
    if shift.plan.account_id != employer_account.pk:
        raise ShiftError("Doar angajatorul poate marca o tură ca neefectuată.")
    shift.status = ShiftStatus.MISSED
    shift.save(update_fields=["status"])
    ShiftEvent.objects.create(shift=shift, kind=ShiftEvent.Kind.MISSED, actor=employer_account)
    return shift


def time_records(account, start, end, worker=None):
    """
    Evidența timpului de lucru pentru o perioadă — ce trebuie să poți arăta
    la un control (Zoll / FKS).
    """
    qs = Shift.objects.filter(
        plan__account=account, date__gte=start, date__lte=end,
        status__in=[ShiftStatus.DONE, ShiftStatus.MISSED],
    ).select_related("worker", "zone__site").order_by("worker__display_name", "date")
    if worker:
        qs = qs.filter(worker=worker)

    rows, totals = [], {}
    for shift in qs:
        minutes = shift.billable_minutes if shift.status == ShiftStatus.DONE else 0
        rows.append({
            "worker": shift.worker.display_name if shift.worker else "—",
            "date": shift.date,
            "site": shift.zone.site.name,
            "zone": shift.zone.name,
            "planned": shift.duration_minutes,
            "actual": minutes,
            "variance": shift.variance_minutes,
            "status": shift.get_status_display(),
        })
        totals[shift.worker_id] = totals.get(shift.worker_id, 0) + minutes
    return {"rows": rows, "totals_minutes": totals,
            "retention_until": end + timedelta(days=365 * RETENTION_YEARS)}
