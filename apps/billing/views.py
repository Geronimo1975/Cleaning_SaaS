"""Comenzi și clienți, văzute de prestator. Scoping strict pe `provider`."""

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from apps.accounts.enums import Capability
from apps.accounts.permissions import (
    AccountRequiredMixin,
    CapabilityRequiredMixin,
    OwnedByAccountMixin,
    require_manage,
)

from .models import Customer, Order
from .services import ALLOWED_TRANSITIONS, BillingError, transition_order

PROVIDER_SIDE = (Capability.PROVIDER, Capability.WORKER)


class CustomerListView(CapabilityRequiredMixin, OwnedByAccountMixin, ListView):
    required_capability = PROVIDER_SIDE
    account_field = "provider"
    model = Customer
    template_name = "dashboard/customer_list.html"
    context_object_name = "customers"

    def get_queryset(self):
        return (
            super().get_queryset()
            .select_related("account__locality")
            .annotate(orders_count=Count("orders"))
        )


class OrderListView(CapabilityRequiredMixin, OwnedByAccountMixin, ListView):
    required_capability = PROVIDER_SIDE
    account_field = "provider"
    model = Order
    template_name = "dashboard/order_list.html"
    context_object_name = "orders"
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related("customer__account", "site", "category")


class OrderDetailView(AccountRequiredMixin, OwnedByAccountMixin, DetailView):
    # Fără CapabilityRequiredMixin: obiectul e deja scopat pe `provider`, deci
    # un cont străin (indiferent de capabilități) primește 404, nu 403 — un
    # cont fără nicio comandă nu trebuie să afle dacă pk-ul ghicit există.
    account_field = "provider"
    model = Order
    template_name = "dashboard/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "customer__account", "site__locality", "category", "source_offer"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        labels = dict(Order._meta.get_field("status").choices)
        ctx["next_statuses"] = [
            (value, labels[value]) for value in sorted(ALLOWED_TRANSITIONS[self.object.status])
        ]
        return ctx


@require_POST
def order_transition_view(request, pk):
    if request.account is None:
        return redirect("accounts:onboarding")
    # Ownership întâi: 404 pentru un cont străin, indiferent de capabilități.
    order = get_object_or_404(Order, pk=pk, provider=request.account)
    require_manage(request.membership)
    try:
        transition_order(order, request.POST.get("status", ""), actor=request.account)
        messages.success(request, f"Comanda {order.order_number}: {order.get_status_display()}.")
    except BillingError as exc:
        messages.error(request, str(exc))
    return redirect("dashboard:order_detail", pk=order.pk)
