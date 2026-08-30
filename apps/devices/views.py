from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.enums import Capability

from .forms import DeviceForm
from .models import Device
from .services import find_discrepancies, utilisation


def _guard(request):
    if request.account is None:
        return redirect("accounts:onboarding")
    if not ({Capability.EMPLOYER, Capability.PROVIDER} & request.account.capability_set()):
        raise PermissionDenied
    return None


def device_list_view(request):
    if (redirect_response := _guard(request)) is not None:
        return redirect_response

    end = timezone.localdate()
    start = end - timedelta(days=30)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            form = DeviceForm(request.POST, account=request.account)
            if form.is_valid():
                device = form.save(commit=False)
                device.account = request.account
                device.token_hash = "pending"
                device.token_prefix = ""
                device.save()
                raw = device.issue_token()
                messages.success(
                    request,
                    f"Echipament adăugat. Cheia se afișează O SINGURĂ DATĂ: {raw}",
                )
                return redirect("dashboard:devices")
        elif action == "reissue":
            device = get_object_or_404(
                Device, pk=request.POST.get("device"), account=request.account
            )
            raw = device.issue_token()
            messages.warning(
                request,
                f"Cheie nouă pentru {device.label} (cea veche nu mai e validă): {raw}",
            )
            return redirect("dashboard:devices")
    else:
        form = DeviceForm(account=request.account)

    return render(request, "dashboard/devices.html", {
        "form": form,
        "rows": utilisation(request.account, start, end),
        "start": start,
        "end": end,
    })


def discrepancies_view(request):
    if (redirect_response := _guard(request)) is not None:
        return redirect_response

    end = timezone.localdate()
    start = end - timedelta(days=int(request.GET.get("days", 30)))
    findings = find_discrepancies(request.account, start, end)
    return render(request, "dashboard/discrepancies.html", {
        "findings": findings,
        "start": start,
        "end": end,
        "by_kind": {
            kind: [f for f in findings if f.kind == kind]
            for kind in {f.kind for f in findings}
        },
    })
