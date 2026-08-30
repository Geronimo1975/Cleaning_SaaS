"""Calibrarea estimărilor de zonă, din pontajul real."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.enums import Capability

from ..calibration import (
    analyze_zone,
    apply_calibration,
    pending_impact,
    propose_calibrations,
    reject_calibration,
)
from ..models import CalibrationStatus, Zone, ZoneCalibration


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
