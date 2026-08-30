from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView

from apps.accounts.enums import Capability
from apps.accounts.permissions import AccountRequiredMixin
from apps.accounts.visibility import AccountView

from .forms import OfferForm, ServiceRequestForm
from .models import Invitation, Offer, OfferStatus, RequestStatus, ServiceRequest
from .scoring import score_offers, suggest_providers
from .services import (
    MarketplaceError,
    activate_recurring_request,
    award_offer,
    award_warnings,
    cancel_request,
    create_contract_from_offer,
    publish_request,
    submit_offer,
    withdraw_offer,
)


class MyRequestsView(AccountRequiredMixin, ListView):
    template_name = "dashboard/requests.html"
    context_object_name = "requests"

    def get_queryset(self):
        return ServiceRequest.objects.filter(client=self.request.account).select_related(
            "category", "locality"
        )


def request_create_view(request):
    if request.account is None:
        return redirect("accounts:onboarding")
    form = ServiceRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service_request = form.save(commit=False)
        service_request.client = request.account
        service_request.save()
        messages.success(request, "Cerere salvată. Publică-o ca să primești oferte.")
        return redirect("dashboard:request_detail", pk=service_request.pk)
    return render(request, "dashboard/request_form.html", {"form": form})


def request_detail_view(request, pk):
    """Vederea clientului: oferte ordonate cu descompunerea scorului."""
    if request.account is None:
        return redirect("accounts:onboarding")
    service_request = get_object_or_404(ServiceRequest, pk=pk, client=request.account)

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "publish":
                publish_request(service_request)
                messages.success(
                    request,
                    f"Cerere publicată. {service_request.invitations.count()} prestatori "
                    "potriviți au fost anunțați.",
                )
            elif action == "cancel":
                cancel_request(service_request, request.account)
                messages.info(request, "Cerere anulată.")
            elif action == "award":
                offer = get_object_or_404(
                    Offer, pk=request.POST.get("offer"), request=service_request
                )
                award_offer(service_request, offer, request.account)
                messages.success(request, f"Serviciul a fost atribuit: {offer.provider}.")
            elif action == "contract":
                contract = create_contract_from_offer(service_request, request.account)
                messages.success(
                    request,
                    f"Contract generat: {contract.get_contract_type_display()}. "
                    "Verifică datele înainte de a-l trimite spre semnare.",
                )
                return redirect("dashboard:contract_detail", pk=contract.pk)
            elif action == "activate":
                site = activate_recurring_request(service_request, request.account)
                messages.success(
                    request,
                    f"Obiectivul {site.name} a fost creat la {site.account.display_name}. "
                    "Planificarea turelor îi aparține prestatorului.",
                )
        except MarketplaceError as exc:
            messages.error(request, str(exc))
        return redirect("dashboard:request_detail", pk=pk)

    contract = None
    if service_request.awarded_offer_id:
        from apps.contracts.models import ContractDraft

        contract = ContractDraft.objects.filter(
            employer=service_request.client,
            worker=service_request.awarded_offer.provider,
            start_date=service_request.awarded_offer.earliest_start,
            workplace=service_request.locality,
        ).first()

    scored = score_offers(service_request)
    for item in scored:
        # Avertismentele juridice se atașează ofertei: clientul trebuie să le
        # vadă lângă butonul de atribuire, nu într-o listă separată.
        item.warnings = award_warnings(service_request, item.offer)
    return render(request, "dashboard/request_detail.html", {
        "request_obj": service_request,
        "scored": scored,
        "contract": contract,
        "invited": service_request.invitations.select_related("provider")[:10],
        "suggestions": (
            suggest_providers(service_request)
            if service_request.status == RequestStatus.DRAFT else []
        ),
    })


class OpenRequestsView(AccountRequiredMixin, ListView):
    """Bursa văzută de prestator."""

    template_name = "dashboard/open_requests.html"
    context_object_name = "requests"
    paginate_by = 25

    def get_queryset(self):
        account = self.request.account
        qs = ServiceRequest.objects.filter(
            status=RequestStatus.OPEN, offers_close_at__gt=timezone.now()
        ).exclude(client=account).select_related("category", "locality")
        if self.request.GET.get("mine_only"):
            qs = qs.filter(
                category__in=account.services.values("category"),
                locality__in=account.areas.values("locality"),
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["my_offers"] = set(
            Offer.objects.filter(provider=self.request.account).values_list(
                "request_id", flat=True
            )
        )
        ctx["invitations"] = Invitation.objects.filter(
            provider=self.request.account, request__status=RequestStatus.OPEN
        ).select_related("request")
        return ctx


def offer_view(request, pk):
    """Vederea prestatorului: cererea plus formularul de ofertă."""
    if request.account is None:
        return redirect("accounts:onboarding")
    if not request.account.is_provider:
        raise PermissionDenied("Contul nu are capabilitate de prestator.")

    service_request = get_object_or_404(ServiceRequest, pk=pk)
    existing = Offer.objects.filter(request=service_request, provider=request.account).first()
    form = OfferForm(request.POST or None, instance=existing)

    if request.method == "POST":
        if request.POST.get("action") == "withdraw" and existing:
            try:
                withdraw_offer(existing, request.account)
                messages.info(request, "Ofertă retrasă.")
            except MarketplaceError as exc:
                messages.error(request, str(exc))
            return redirect("dashboard:offer", pk=pk)
        if form.is_valid():
            try:
                submit_offer(service_request, request.account, **form.cleaned_data)
                messages.success(request, "Ofertă trimisă.")
                return redirect("dashboard:offer", pk=pk)
            except MarketplaceError as exc:
                messages.error(request, str(exc))

    Invitation.objects.filter(
        request=service_request, provider=request.account, seen_at__isnull=True
    ).update(seen_at=timezone.now())

    return render(request, "dashboard/offer_form.html", {
        "request_obj": service_request,
        "client": AccountView(
            service_request.client, viewer_account=request.account, user=request.user
        ),
        "form": form,
        "existing": existing,
    })
