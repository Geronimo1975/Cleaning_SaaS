"""
Site-ul de marketing — paginile publice de prezentare (germană).

Structura și textul vin din docs/superpowers/plans/2026-09-12-marketing-site-wordpress.md
(Task 6); în loc de WordPress, paginile sunt servite direct de Django, cu același CSS
ca restul suprafeței publice. Niciun model: conținutul e static în șabloane.
"""

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import ContactForm, DownloadForm


class StartView(TemplateView):
    template_name = "marketing/start.html"


class LeistungenView(TemplateView):
    template_name = "marketing/leistungen.html"


class BetriebeView(TemplateView):
    template_name = "marketing/betriebe.html"


class ReinigungskraefteView(TemplateView):
    template_name = "marketing/reinigungskraefte.html"


class AuftraggeberView(TemplateView):
    template_name = "marketing/auftraggeber.html"


class KontaktView(FormView):
    """Formular de contact: trimite pe emailul operatorului (OPERATOR_EMAIL)."""

    template_name = "marketing/kontakt.html"
    form_class = ContactForm
    success_url = reverse_lazy("marketing:kontakt")

    def form_valid(self, form):
        data = form.cleaned_data
        operator = getattr(settings, "OPERATOR", {}) or {}
        recipient = operator.get("email") or settings.DEFAULT_FROM_EMAIL
        send_mail(
            subject=f"[Kontakt] {data['subject']}",
            message=f"Von: {data['name']} <{data['email']}>\n\n{data['message']}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
        )
        messages.success(self.request, "Vielen Dank — wir melden uns in Kürze.")
        return super().form_valid(form)


class BlogView(TemplateView):
    template_name = "marketing/blog.html"


class ReinigungsplanVorlageView(FormView):
    """
    Articol + lead magnet: șablonul gol de Reinigungsplan (XLSX).

    Descărcarea se trimite pe email — modelul pland — dar linkul apare și pe pagină
    după trimitere, ca să nu depindă de livrarea emailului.
    """

    template_name = "marketing/blog_reinigungsplan.html"
    form_class = DownloadForm
    success_url = reverse_lazy("marketing:blog_reinigungsplan")
    download = "downloads/reinigungsplan-vorlage.xlsx"

    def form_valid(self, form):
        url = self.request.build_absolute_uri(static(self.download))
        send_mail(
            subject="Ihre Reinigungsplan-Vorlage",
            message=f"Vielen Dank. Hier ist Ihre Vorlage: {url}\n\nIhr ProFM-Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[form.cleaned_data["email"]],
        )
        messages.success(self.request, "Vielen Dank — die Vorlage ist unterwegs an Ihre E-Mail.")
        return super().form_valid(form)
