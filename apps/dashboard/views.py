from django.views.generic import TemplateView

from apps.accounts.permissions import AccountRequiredMixin
from apps.jobs.models import Application, ApplicationStatus, JobPosting, JobStatus

from .panels import metrics_for, panels_for


class DashboardContext:
    """Rezolvă metricile. Fiecare metodă corespunde unui `Metric.resolver`."""

    def __init__(self, account):
        self.account = account

    def open_postings(self):
        return JobPosting.objects.filter(
            account=self.account, status=JobStatus.PUBLISHED
        ).count()

    def new_applications(self):
        return Application.objects.filter(
            job__account=self.account, status=ApplicationStatus.NEW
        ).count()

    def my_applications(self):
        return Application.objects.filter(applicant_account=self.account).count()

    def contracted_hours(self):
        from django.db.models import Sum

        from apps.contracts.models import ContractDraft, DraftStatus

        total = ContractDraft.objects.filter(
            employer=self.account, status=DraftStatus.SIGNED
        ).aggregate(total=Sum("hours_per_month"))["total"]
        return total or 0

    def profile_views(self):
        return 0  # placeholder până la contorizare

    def published_products(self):
        return self.account.products.filter(is_published=True).count()


class DashboardHomeView(AccountRequiredMixin, TemplateView):
    """
    UN singur dashboard, compus din capabilitățile contului activ.
    Nu există /dashboard/worker/, /dashboard/client/ etc.
    """

    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        account = self.request.account
        caps = account.capability_set()
        resolver = DashboardContext(account)
        ctx["account"] = account
        ctx["panels"] = panels_for(caps)
        ctx["metrics"] = [
            {"label": m.label, "value": getattr(resolver, m.resolver)()}
            for m in metrics_for(caps)
        ]
        ctx["other_accounts"] = self.request.user.accounts.exclude(pk=account.pk)
        return ctx
