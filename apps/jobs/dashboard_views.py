"""Dashboard-ul angajatorului: anunțuri și candidaturi."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.accounts.enums import Capability
from apps.accounts.permissions import CapabilityRequiredMixin, OwnedByAccountMixin
from apps.accounts.visibility import AccountView

from .forms import JobPostingForm
from .indexing import IndexingAction, absolute_url, enqueue
from .models import Application, ApplicationStatus, JobPosting, JobStatus


class PostingListView(CapabilityRequiredMixin, OwnedByAccountMixin, ListView):
    required_capability = Capability.EMPLOYER
    template_name = "dashboard/postings.html"
    context_object_name = "postings"
    model = JobPosting

    def get_queryset(self):
        from django.db.models import Count

        return (
            super()
            .get_queryset()
            .select_related("locality", "category")
            .annotate(application_count=Count("applications"))
        )


class PostingCreateView(CapabilityRequiredMixin, CreateView):
    required_capability = Capability.EMPLOYER
    template_name = "dashboard/posting_form.html"
    form_class = JobPostingForm
    success_url = reverse_lazy("dashboard:postings")

    def form_valid(self, form):
        form.instance.account = self.request.account
        messages.success(self.request, "Anunț salvat ca ciornă. Publică-l când e gata.")
        return super().form_valid(form)


class PostingUpdateView(CapabilityRequiredMixin, OwnedByAccountMixin, UpdateView):
    required_capability = Capability.EMPLOYER
    template_name = "dashboard/posting_form.html"
    form_class = JobPostingForm
    model = JobPosting
    success_url = reverse_lazy("dashboard:postings")


class PostingPublishView(CapabilityRequiredMixin, OwnedByAccountMixin, View):
    required_capability = Capability.EMPLOYER
    model = JobPosting

    def get_queryset(self):
        return JobPosting.objects.filter(account=self.request.account)

    def post(self, request, pk):
        posting = get_object_or_404(self.get_queryset(), pk=pk)
        if posting.status == JobStatus.PUBLISHED:
            posting.status = JobStatus.CLOSED
            enqueue(absolute_url(request, posting), IndexingAction.DELETED)
            messages.info(request, "Anunț închis. URL-ul răspunde 410 și iese din sitemap.")
        else:
            if posting.valid_through <= timezone.now():
                messages.error(request, "Setează o dată de expirare în viitor înainte de publicare.")
                return redirect("dashboard:posting_edit", pk=pk)
            posting.status = JobStatus.PUBLISHED
            posting.published_at = posting.published_at or timezone.now()
            enqueue(absolute_url(request, posting), IndexingAction.UPDATED)
            messages.success(request, "Anunț publicat.")
        posting.save(update_fields=["status", "published_at", "updated_at"])
        return redirect("dashboard:postings")


class CandidateListView(CapabilityRequiredMixin, ListView):
    """Candidaturile la anunțurile contului activ, nu la toate anunțurile."""

    required_capability = Capability.EMPLOYER
    template_name = "dashboard/candidates.html"
    context_object_name = "applications"
    paginate_by = 50

    def get_queryset(self):
        qs = Application.objects.filter(
            job__account=self.request.account
        ).select_related("job", "applicant_account__locality")
        if status := self.request.GET.get("status"):
            qs = qs.filter(status=status)
        if job := self.request.GET.get("job"):
            qs = qs.filter(job_id=job)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = ApplicationStatus.choices
        ctx["postings"] = JobPosting.objects.filter(account=self.request.account)
        return ctx


class CandidateDetailView(CapabilityRequiredMixin, DetailView):
    required_capability = Capability.EMPLOYER
    template_name = "dashboard/candidate_detail.html"
    context_object_name = "application"

    def get_queryset(self):
        return Application.objects.filter(
            job__account=self.request.account
        ).select_related("job", "applicant_account__worker_profile")

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.object.status == ApplicationStatus.NEW:
            Application.objects.filter(pk=self.object.pk).update(
                status=ApplicationStatus.VIEWED
            )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        candidate = self.object.applicant_account
        # Chiar și aici trecem prin AccountView: relația e ENGAGED, nu SELF.
        # Angajatorul vede contactul, dar nu statutul fiscal sau documentele.
        ctx["candidate"] = AccountView(
            candidate, viewer_account=self.request.account, user=self.request.user
        )
        ctx["profile"] = getattr(candidate, "worker_profile", None)
        ctx["contracts"] = candidate.contracts_received.filter(employer=self.request.account)
        ctx["next_statuses"] = ApplicationStatus.choices
        return ctx

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        status = request.POST.get("status")
        if status in ApplicationStatus.values:
            application.status = status
            application.save(update_fields=["status"])
            messages.success(request, "Statut actualizat.")
        return redirect("dashboard:candidate_detail", pk=application.pk)
