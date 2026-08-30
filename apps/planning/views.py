from datetime import date, timedelta

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import CreateView, ListView

from apps.accounts.enums import Capability
from apps.accounts.permissions import CapabilityRequiredMixin, OwnedByAccountMixin

from .forms import SiteForm, ZoneForm
from .models import PlanStatus, ShiftPlan, Site, Zone
from .services import capacity_report, generate_week_plan


def _monday(value: str | None) -> date:
    if value:
        parsed = date.fromisoformat(value)
    else:
        parsed = date.today()
    return parsed - timedelta(days=parsed.isoweekday() - 1)


class SiteListView(CapabilityRequiredMixin, OwnedByAccountMixin, ListView):
    required_capability = (Capability.EMPLOYER, Capability.PROVIDER)
    template_name = "dashboard/sites.html"
    context_object_name = "sites"
    model = Site

    def get_queryset(self):
        return super().get_queryset().prefetch_related("zones__category")


class SiteCreateView(CapabilityRequiredMixin, CreateView):
    required_capability = (Capability.EMPLOYER, Capability.PROVIDER)
    template_name = "dashboard/site_form.html"
    form_class = SiteForm

    def form_valid(self, form):
        form.instance.account = self.request.account
        return super().form_valid(form)

    def get_success_url(self):
        return "/dashboard/obiective/"


class ZoneCreateView(CapabilityRequiredMixin, CreateView):
    required_capability = (Capability.EMPLOYER, Capability.PROVIDER)
    template_name = "dashboard/site_form.html"
    form_class = ZoneForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["account"] = self.request.account
        return kwargs

    def get_success_url(self):
        return "/dashboard/obiective/"


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


# --- Publicare, vederea lucrătorului, pontaj -------------------------------

from datetime import datetime  # noqa: E402

from django.core.exceptions import PermissionDenied  # noqa: E402
from django.shortcuts import get_object_or_404  # noqa: E402
from django.utils import timezone  # noqa: E402

from .attendance import (  # noqa: E402
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
from .models import Shift, ShiftStatus  # noqa: E402


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


# --- Calibrare din pontaj --------------------------------------------------

from .calibration import (  # noqa: E402
    analyze_zone,
    apply_calibration,
    pending_impact,
    propose_calibrations,
    reject_calibration,
)
from .models import CalibrationStatus, ZoneCalibration  # noqa: E402


def calibration_view(request):
    """Propuneri de corectare a estimărilor. Se decid manual, una câte una."""
    if request.account is None:
        return redirect("accounts:onboarding")
    if not ({Capability.EMPLOYER, Capability.PROVIDER} & request.account.capability_set()):
        raise PermissionDenied

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "scan":
            created = propose_calibrations(request.account)
            if created:
                messages.success(request, f"{len(created)} propuneri noi.")
            else:
                messages.info(request, "Nicio abatere sistematică peste prag.")
        else:
            calibration = get_object_or_404(
                ZoneCalibration, pk=request.POST.get("calibration"),
                zone__site__account=request.account,
            )
            note = request.POST.get("note", "")
            try:
                if action == "apply":
                    apply_calibration(calibration, request.account, note)
                    messages.success(
                        request,
                        f"{calibration.zone.name}: estimare actualizată la "
                        f"{calibration.suggested_minutes} min. "
                        "Regenerează planul ca să se aplice.",
                    )
                elif action == "reject":
                    reject_calibration(calibration, request.account, note)
                    messages.info(request, "Propunere respinsă.")
            except ValueError as exc:
                messages.error(request, str(exc))
        return redirect("dashboard:calibration")

    zones = Zone.objects.filter(
        site__account=request.account, is_active=True
    ).select_related("site")
    return render(request, "dashboard/calibration.html", {
        "proposals": ZoneCalibration.objects.filter(
            zone__site__account=request.account, status=CalibrationStatus.PROPOSED
        ).select_related("zone__site"),
        "history": ZoneCalibration.objects.filter(
            zone__site__account=request.account
        ).exclude(status=CalibrationStatus.PROPOSED).select_related("zone")[:20],
        "analyses": [analyze_zone(z) for z in zones],
        "impact": pending_impact(request.account),
    })


# --- export Reinigungsplan ------------------------------------------------
from django.http import FileResponse  # noqa: E402

from .reinigungsplan import build_workbook, filename  # noqa: E402


def reinigungsplan_view(request, pk):
    """
    Reinigungsplan-ul obiectivului, ca XLSX. Doar pentru contul care deține
    obiectivul — e un document operațional, nu o pagină publică.
    """
    account = request.account
    if account is None:
        raise PermissionDenied
    site = get_object_or_404(Site, pk=pk, account=account)
    return FileResponse(
        build_workbook(site),
        as_attachment=True,
        filename=filename(site),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
