"""Generarea planului săptămânal și raportul de capacitate."""

from datetime import timedelta

from django.contrib import messages
from django.shortcuts import redirect, render

from apps.accounts.enums import Capability

from ..models import ShiftPlan, Zone
from ..services import capacity_report, generate_week_plan
from .sites import _monday


def planning_view(request):
    """Capacitate vs. cerere, apoi generarea planului săptămânal."""
    if request.account is None:
        return redirect("accounts:onboarding")
    caps = request.account.capability_set()
    if not ({Capability.EMPLOYER, Capability.PROVIDER} & caps):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied

    week_start = _monday(request.GET.get("week"))
    plan = ShiftPlan.objects.filter(account=request.account, week_start=week_start).first()

    if request.method == "POST":
        plan = generate_week_plan(request.account, week_start)
        messages.success(
            request,
            f"Plan generat: {plan.shifts.count()} ture, "
            f"{len(plan.unmet_demand)} vizite nealocate.",
        )
        return redirect(f"/dashboard/planificare/?week={week_start.isoformat()}")

    days = [week_start + timedelta(days=i) for i in range(7)]
    grid = {d: [] for d in days}
    if plan:
        for shift in plan.shifts.select_related("zone__site", "worker"):
            grid[shift.date].append(shift)

    return render(request, "dashboard/planning.html", {
        "week_start": week_start,
        "prev_week": week_start - timedelta(days=7),
        "next_week": week_start + timedelta(days=7),
        "report": capacity_report(request.account, week_start),
        "plan": plan,
        "grid": [(d, grid[d]) for d in days],
        "zones": Zone.objects.filter(site__account=request.account, is_active=True).count(),
    })
