"""Publicarea planului, vederea lucrătorului și pontajul."""

from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.enums import Capability

from ..attendance import (
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
from ..models import PlanStatus, Shift, ShiftPlan, ShiftStatus
from .sites import _monday


def publish_plan_view(request, pk):
    plan = get_object_or_404(ShiftPlan, pk=pk, account=request.account)
    if request.method != "POST":
        return redirect("dashboard:planning")
    try:
        publish_plan(plan, actor=request.account)
        messages.success(
            request,
            f"Plan publicat. {plan.shifts.count()} ture trimise lucrătorilor.",
        )
    except ShiftError as exc:
        messages.error(request, str(exc))
    return redirect(f"/dashboard/planificare/?week={plan.week_start.isoformat()}")


def my_shifts_view(request):
    """Turele lucrătorului. Doar din planuri publicate — ciornele nu se văd."""
    if request.account is None:
        return redirect("accounts:onboarding")

    week_start = _monday(request.GET.get("week"))
    shifts = (
        Shift.objects.filter(
            worker=request.account,
            plan__status=PlanStatus.PUBLISHED,
            date__gte=week_start,
            date__lte=week_start + timedelta(days=6),
        )
        .select_related("zone__site__locality", "plan")
        .order_by("date", "start_time")
    )

    if request.method == "POST":
        shift = get_object_or_404(Shift, pk=request.POST.get("shift"), worker=request.account)
        action = request.POST.get("action")
        try:
            if action == "confirm":
                confirm_shift(shift, request.account)
                messages.success(request, "Tură confirmată.")
            elif action == "decline":
                decline_shift(shift, request.account, request.POST.get("reason", ""))
                messages.info(request, "Tură refuzată. Angajatorul a fost informat.")
            elif action == "check_in":
                check_in(shift, request.account)
                messages.success(request, "Pontaj început.")
            elif action == "check_out":
                check_out(shift, request.account, note=request.POST.get("note", ""))
                messages.success(request, f"Pontaj încheiat: {shift.actual_minutes} min.")
        except ShiftError as exc:
            messages.error(request, str(exc))
        return redirect(f"/dashboard/turele-mele/?week={week_start.isoformat()}")

    total = sum(s.billable_minutes for s in shifts if s.status == ShiftStatus.DONE)
    return render(request, "dashboard/my_shifts.html", {
        "week_start": week_start,
        "prev_week": week_start - timedelta(days=7),
        "next_week": week_start + timedelta(days=7),
        "shifts": shifts,
        "done_minutes": total,
        "today": timezone.localdate(),
    })


def time_records_view(request):
    """Evidența timpului de lucru — ce trebuie arătat la un control FKS."""
    if request.account is None:
        return redirect("accounts:onboarding")
    if not ({Capability.EMPLOYER, Capability.PROVIDER} & request.account.capability_set()):
        raise PermissionDenied

    week_start = _monday(request.GET.get("week"))
    week_end = week_start + timedelta(days=6)

    if request.method == "POST":
        shift = get_object_or_404(Shift, pk=request.POST.get("shift"), plan__account=request.account)
        try:
            if request.POST.get("action") == "correct":
                correct_minutes(
                    shift, request.account,
                    int(request.POST.get("minutes", 0)),
                    request.POST.get("reason", ""),
                )
                messages.success(request, "Pontaj corectat. Valoarea veche rămâne în jurnal.")
            elif request.POST.get("action") == "missed":
                mark_missed(shift, request.account)
                messages.info(request, "Tură marcată ca neefectuată.")
        except (ShiftError, ValueError) as exc:
            messages.error(request, str(exc))
        return redirect(f"/dashboard/pontaj/?week={week_start.isoformat()}")

    records = time_records(request.account, week_start, week_end)
    open_shifts = Shift.objects.filter(
        plan__account=request.account, date__gte=week_start, date__lte=week_end,
    ).exclude(status__in=[ShiftStatus.DONE, ShiftStatus.MISSED]).select_related(
        "worker", "zone__site"
    )
    return render(request, "dashboard/time_records.html", {
        "week_start": week_start,
        "prev_week": week_start - timedelta(days=7),
        "next_week": week_start + timedelta(days=7),
        "records": records,
        "open_shifts": open_shifts,
    })
