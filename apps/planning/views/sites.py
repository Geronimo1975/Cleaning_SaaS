"""Obiective și zone: CRUD-ul pe care se sprijină planificarea."""

from datetime import date, timedelta

from django.views.generic import CreateView, ListView

from apps.accounts.enums import Capability
from apps.accounts.permissions import CapabilityRequiredMixin, OwnedByAccountMixin

from ..forms import SiteForm, ZoneForm
from ..models import Site


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
