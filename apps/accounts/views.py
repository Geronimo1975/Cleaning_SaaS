from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, FormView, ListView

from apps.taxonomy.models import ServiceCategory

from .compliance import ConsentType
from .enums import AccountStatus, EntityType
from .forms import (
    AccountForm,
    CompanyIdentityForm,
    CompanyProfileForm,
    OnboardingForm,
    WorkerProfileForm,
)
from .middleware import switch_account
from .models import Account, ReservedSlug
from .permissions import AccountRequiredMixin
from .services import DEFAULT_CAPABILITIES, create_account, publish_profile, record_consent
from .visibility import AccountView


class OnboardingView(LoginRequiredMixin, FormView):
    """Primul pas după confirmarea emailului. Fără cont, nimic nu funcționează."""

    template_name = "accounts/onboarding.html"
    form_class = OnboardingForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.account is not None:
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        account = create_account(
            user=self.request.user,
            entity_type=data["entity_type"],
            display_name=data["display_name"],
            capabilities=DEFAULT_CAPABILITIES[data["kind"]],
            locality=data["locality"],
            phone=data.get("phone", ""),
        )
        record_consent(account, ConsentType.TERMS, True, self.request)
        switch_account(self.request, account)
        messages.success(self.request, "Contul a fost creat. Completează profilul.")
        return redirect("accounts:profile_edit")


class ProfileEditView(AccountRequiredMixin, FormView):
    """
    Un singur URL de editare. Formularul de profil se alege după entity_type —
    nu există /dashboard/worker/profile/ și /dashboard/company/profile/.
    """

    template_name = "accounts/profile_edit.html"

    def get_profile(self):
        acc = self.request.account
        return acc.worker_profile if acc.entity_type == EntityType.INDIVIDUAL else acc.company_profile

    def get_form_class(self):
        return (
            WorkerProfileForm
            if self.request.account.entity_type == EntityType.INDIVIDUAL
            else CompanyProfileForm
        )

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["instance"] = self.get_profile()
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        account = self.request.account
        ctx["account"] = account
        ctx["account_form"] = kwargs.get("account_form") or AccountForm(instance=account)
        if account.entity_type == EntityType.COMPANY:
            ctx["identity_form"] = CompanyIdentityForm(instance=account)
        ctx["is_published"] = account.status == AccountStatus.PUBLISHED
        return ctx

    def post(self, request, *args, **kwargs):
        account = request.account
        account_form = AccountForm(request.POST, request.FILES, instance=account)
        form = self.get_form()
        identity_form = (
            CompanyIdentityForm(request.POST, instance=account)
            if account.entity_type == EntityType.COMPANY
            else None
        )
        forms_ok = account_form.is_valid() and form.is_valid()
        if identity_form is not None:
            forms_ok = identity_form.is_valid() and forms_ok
        if not forms_ok:
            return self.render_to_response(
                self.get_context_data(form=form, account_form=account_form)
            )

        account_form.save()
        if identity_form is not None:
            identity_form.save()
        profile = form.save()
        if "legal_status" in form.cleaned_data:
            account.legal_status = form.cleaned_data["legal_status"]
            account.save(update_fields=["legal_status", "updated_at"])
        _sync_services(account, form.cleaned_data.get("services"))
        _sync_areas(account, form.cleaned_data.get("areas"))
        messages.success(request, "Profil salvat.")
        return redirect("accounts:profile_edit")


def _sync_services(account, categories):
    from .profiles import AccountService

    if categories is None:
        return
    account.services.all().delete()
    AccountService.objects.bulk_create(
        [AccountService(account=account, category=c) for c in categories]
    )


def _sync_areas(account, localities):
    from .profiles import ServiceArea

    if localities is None:
        return
    account.areas.all().delete()
    ServiceArea.objects.bulk_create(
        [ServiceArea(account=account, locality=l) for l in localities]
    )


class PublicProfileView(DetailView):
    """
    Profilul public. Trece OBLIGATORIU prin AccountView — obiectul Account nu
    ajunge niciodată în template.
    """

    template_name = "accounts/profile_public.html"
    context_object_name = "account"

    def get_queryset(self):
        return Account.objects.select_related("locality__region")

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            # Slug rezervat dar fără cont: a existat și a fost șters. 410, nu 404.
            if ReservedSlug.objects.filter(slug=kwargs.get("slug")).exists():
                return HttpResponse(status=410)
            raise
        if self.object.status != AccountStatus.PUBLISHED:
            # Depublicat: 410 + noindex. Un profil indexat nu dispare printr-un rând șters.
            response = render(request, "accounts/gone.html", status=410)
            response["X-Robots-Tag"] = "noindex"
            return response
        return self.render_to_response(self.get_context_data(object=self.object))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["view_"] = AccountView(
            self.object, viewer_account=self.request.account, user=self.request.user
        )
        ctx["services"] = ServiceCategory.objects.filter(
            accounts__account=self.object
        ).order_by("sort_order")
        ctx["deductible_35a"] = any(s.is_35a_eligible for s in ctx["services"])
        return ctx


class ProviderListView(ListView):
    """Directory public: oraș × categorie."""

    template_name = "accounts/provider_list.html"
    context_object_name = "accounts"
    paginate_by = 24

    def get_queryset(self):
        qs = Account.objects.published().providers().select_related("locality").distinct()
        if city := self.kwargs.get("city") or self.request.GET.get("city"):
            qs = qs.filter(areas__locality__slug=city)
        if cat := self.kwargs.get("category") or self.request.GET.get("category"):
            qs = qs.filter(services__category__slug=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["views"] = [
            AccountView(a, viewer_account=self.request.account, user=self.request.user)
            for a in ctx["accounts"]
        ]
        return ctx


class PublishToggleView(AccountRequiredMixin, FormView):
    form_class = OnboardingForm  # neutilizat; view-ul răspunde doar la POST

    def post(self, request, *args, **kwargs):
        from .services import unpublish_profile

        account = request.account
        if account.status == AccountStatus.PUBLISHED:
            unpublish_profile(account, request)
            messages.info(request, "Profilul a fost depublicat.")
        else:
            publish_profile(account, request)
            messages.success(request, "Profilul este public.")
        return redirect("accounts:profile_edit")


def switch_account_view(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if not switch_account(request, account):
        raise Http404
    return redirect("dashboard:home")


def verification_document_view(request, pk):
    """
    Descărcarea unui document de verificare, prin Django, cu verificare de drepturi.

    Politica e cea din `visibility.FIELD_POLICY`: `documents` cere `SELF`.
    Operatorii platformei (staff) văd tot, pentru că ei fac verificarea.
    """
    from django.http import FileResponse

    from .compliance import VerificationDocument

    if not request.user.is_authenticated:
        raise Http404

    document = get_object_or_404(
        VerificationDocument.objects.select_related("account"), pk=pk
    )
    is_owner = (
        request.account is not None and document.account_id == request.account.pk
    )
    if not (is_owner or request.user.is_staff):
        raise Http404

    response = FileResponse(document.file.open("rb"), as_attachment=True)
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Cache-Control"] = "private, no-store"
    return response
