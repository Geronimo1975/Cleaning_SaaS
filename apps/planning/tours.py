"""Interfața pentru runde. Fără ea, `Tour` ar fi accesibil doar din shell."""

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.enums import Capability

from .models import Tour, TourStop, Zone


class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ["name", "allowed_weekdays", "visits_per_week"]
        labels = {"allowed_weekdays": "Zile permise (1=Lu … 6=Sâ)"}


class TourStopForm(forms.ModelForm):
    class Meta:
        model = TourStop
        fields = ["zone", "position", "travel_minutes"]
        labels = {
            "position": "Poziția în rundă",
            "travel_minutes": "Deplasare până aici (min)",
        }

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zone"].queryset = Zone.objects.filter(
            site__account=account, is_active=True
        ).select_related("site")


def tours_view(request):
    if request.account is None:
        return redirect("accounts:onboarding")
    if not ({Capability.EMPLOYER, Capability.PROVIDER} & request.account.capability_set()):
        raise PermissionDenied

    form = TourForm(request.POST or None)
    if request.method == "POST" and request.POST.get("action") == "create" and form.is_valid():
        tour = form.save(commit=False)
        tour.account = request.account
        tour.save()
        messages.success(request, "Rundă creată. Adaugă opririle în ordine.")
        return redirect("dashboard:tour_detail", pk=tour.pk)

    return render(request, "dashboard/tours.html", {
        "form": form,
        "tours": Tour.objects.filter(account=request.account).prefetch_related(
            "stops__zone__site"
        ),
    })


def tour_detail_view(request, pk):
    if request.account is None:
        return redirect("accounts:onboarding")
    tour = get_object_or_404(Tour, pk=pk, account=request.account)
    form = TourStopForm(request.POST or None, account=request.account)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_stop" and form.is_valid():
            stop = form.save(commit=False)
            stop.tour = tour
            try:
                stop.full_clean()
            except Exception as exc:  # ValidationError sau IntegrityError de unicitate
                messages.error(request, str(exc))
            else:
                stop.save()
                messages.success(request, "Oprire adăugată.")
            return redirect("dashboard:tour_detail", pk=pk)
        if action == "remove_stop":
            tour.stops.filter(pk=request.POST.get("stop")).delete()
            messages.info(request, "Oprire eliminată.")
            return redirect("dashboard:tour_detail", pk=pk)
        if action == "toggle":
            tour.is_active = not tour.is_active
            tour.save(update_fields=["is_active"])
            messages.info(
                request,
                "Rundă reactivată." if tour.is_active else
                "Rundă dezactivată. Zonele rămân active și se vor planifica individual.",
            )
            return redirect("dashboard:tour_detail", pk=pk)

    return render(request, "dashboard/tour_detail.html", {
        "tour": tour,
        "stops": tour.stops.select_related("zone__site").order_by("position"),
        "form": form,
    })
