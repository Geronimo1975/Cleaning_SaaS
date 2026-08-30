from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from apps.accounts.models import ReservedSlug

from .forms import ApplicationForm
from .models import JobPosting, JobStatus
from .services import apply_to_job


class JobListView(ListView):
    template_name = "jobs/list.html"
    context_object_name = "jobs"
    paginate_by = 20

    def get_queryset(self):
        qs = JobPosting.objects.filter(
            status=JobStatus.PUBLISHED, valid_through__gt=timezone.now()
        ).select_related("account", "locality", "category")
        if city := self.kwargs.get("city"):
            qs = qs.filter(locality__slug=city)
        return qs


class JobDetailView(DetailView):
    """
    Detaliile anunțului sunt vizibile FĂRĂ login. Doar aplicarea cere cont.
    Dacă descrierea e în spatele autentificării, anunțul nu se califică
    pentru Google for Jobs.
    """

    template_name = "jobs/detail.html"
    context_object_name = "job"
    queryset = JobPosting.objects.select_related("account", "locality__region", "category")

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            if ReservedSlug.objects.filter(slug=kwargs.get("slug")).exists():
                return HttpResponse(status=410)
            raise
        if not self.object.is_live:
            # Expirat sau închis: 410 + noindex, apoi eliminare prin Indexing API.
            response = render(request, "jobs/gone.html", {"job": self.object}, status=410)
            response["X-Robots-Tag"] = "noindex"
            return response
        JobPosting.objects.filter(pk=self.object.pk).update(
            views_count=models_f("views_count") + 1
        )
        return self.render_to_response(self.get_context_data(object=self.object))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = ApplicationForm(job=self.object, user=self.request.user)
        ctx["jsonld"] = render_jsonld(build_job_jsonld(self.object, self.request))
        return ctx


def models_f(name):
    from django.db.models import F

    return F(name)


def apply_view(request, slug):
    job = JobPosting.objects.filter(slug=slug).first()
    if not job or not job.is_live:
        raise Http404
    form = ApplicationForm(request.POST or None, job=job, user=request.user)
    if request.method == "POST" and form.is_valid():
        apply_to_job(job=job, data=form.cleaned_data, user=request.user, request=request)
        messages.success(
            request, "Candidatura a fost trimisă. Ți-am trimis un email cu pașii următori."
        )
        return redirect(job.get_absolute_url())
    return render(request, "jobs/detail.html", {"job": job, "form": form})


def render_jsonld(data: dict) -> str:
    """
    `json_script` emite type="application/json"; Google for Jobs cere
    application/ld+json. Serializăm manual și neutralizăm caracterele care
    ar putea închide tag-ul <script>.
    """
    import json

    from django.utils.safestring import mark_safe

    raw = json.dumps(data, ensure_ascii=False)
    for char, escaped in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026")):
        raw = raw.replace(char, escaped)
    return mark_safe(raw)


def build_job_jsonld(job, request) -> dict:
    """
    JSON-LD JobPosting — DOAR pe pagina individuală. Pe listări, Google penalizează.
    """
    base = f"{request.scheme}://{request.get_host()}"
    data = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": job.title,
        "description": job.description,
        "identifier": {"@type": "PropertyValue", "name": job.account.display_name,
                       "value": str(job.pk)},
        "datePosted": job.published_at.date().isoformat() if job.published_at else None,
        "validThrough": job.valid_through.isoformat(),
        "employmentType": job.employment_type,
        "hiringOrganization": {
            "@type": "Organization",
            "name": job.account.display_name,
            "sameAs": base + job.account.get_absolute_url(),
        },
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": job.locality.name,
                "addressRegion": job.locality.region.name,
                "postalCode": job.locality.postal_code,
                "addressCountry": "DE",
            },
        },
    }
    if job.salary_min:
        data["baseSalary"] = {
            "@type": "MonetaryAmount",
            "currency": job.salary_currency,
            "value": {
                "@type": "QuantitativeValue",
                "minValue": float(job.salary_min),
                "maxValue": float(job.salary_max or job.salary_min),
                "unitText": job.salary_unit,
            },
        }
    return data
