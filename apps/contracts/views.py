from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from apps.accounts.enums import Capability
from apps.accounts.permissions import AccountRequiredMixin, CapabilityRequiredMixin
from apps.jobs.models import Application, ApplicationStatus

from .forms import ContractDraftForm, SignatureForm
from .models import ContractDraft, DraftStatus
from .services import active_template, send_for_signature, sign_contract


class ContractListView(AccountRequiredMixin, ListView):
    template_name = "dashboard/contracts.html"
    context_object_name = "contracts"

    def get_queryset(self):
        account = self.request.account
        return ContractDraft.objects.filter(
            employer=account
        ).select_related("worker", "workplace") | ContractDraft.objects.filter(
            worker=account
        ).select_related("employer", "workplace")


def contract_create(request, application_pk):
    """Contractul se naște dintr-o candidatură, nu din nimic."""
    application = get_object_or_404(
        Application.objects.select_related("job", "applicant_account"),
        pk=application_pk,
        job__account=request.account,
    )
    if Capability.EMPLOYER not in request.account.capability_set():
        raise Http404

    instance = ContractDraft(
        employer=request.account,
        worker=application.applicant_account,
        workplace=application.job.locality,
    )
    form = ContractDraftForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        draft = form.save(commit=False)
        draft.employer = request.account
        draft.worker = application.applicant_account
        draft.template = active_template(draft.contract_type)
        if draft.template is None:
            messages.error(request, "Nu există șablon activ pentru acest tip de contract.")
        else:
            draft.save()
            application.status = ApplicationStatus.HIRED
            application.save(update_fields=["status"])
            return redirect("dashboard:contract_detail", pk=draft.pk)
    return render(request, "dashboard/contract_form.html", {
        "form": form,
        "application": application,
        "issues": getattr(form, "compliance_issues", []),
    })


class ContractDetailView(AccountRequiredMixin, DetailView):
    template_name = "dashboard/contract_detail.html"
    context_object_name = "contract"

    def get_queryset(self):
        account = self.request.account
        return ContractDraft.objects.filter(employer=account) | ContractDraft.objects.filter(
            worker=account
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        contract = self.object
        account = self.request.account
        ctx["issues"] = contract.compliance_issues()
        ctx["is_employer"] = contract.employer_id == account.pk
        ctx["already_signed"] = contract.signatures.filter(account=account).exists()
        ctx["can_sign"] = (
            contract.status == DraftStatus.SENT and not ctx["already_signed"]
        )
        ctx["signature_form"] = SignatureForm()
        return ctx

    def post(self, request, *args, **kwargs):
        contract = self.get_object()
        action = request.POST.get("action")

        if action == "send" and contract.employer_id == request.account.pk:
            blocking = send_for_signature(contract)
            if blocking:
                for issue in blocking:
                    messages.error(request, issue)
            else:
                messages.success(request, "Contract trimis spre semnare.")
            return redirect("dashboard:contract_detail", pk=contract.pk)

        if action == "sign":
            form = SignatureForm(request.POST)
            if form.is_valid():
                try:
                    sign_contract(
                        contract, request.account, form.cleaned_data["signer_name"], request
                    )
                    messages.success(request, "Contract semnat.")
                except ValueError as exc:
                    messages.error(request, str(exc))
            return redirect("dashboard:contract_detail", pk=contract.pk)

        return redirect("dashboard:contract_detail", pk=contract.pk)
