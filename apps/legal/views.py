"""
Paginile legale obligatorii.

Datele operatorului NU sunt scrise în șabloane, ci vin din configurare. Motivul
nu e comoditatea: §5 TMG cere identitate EXACTĂ, iar un Impressum cu date
inventate e mai rău decât niciunul. Cât timp variabilele nu sunt completate,
paginile afișează vizibil ce lipsește, în loc să pretindă că e în regulă.
"""

from django.conf import settings
from django.views.generic import TemplateView

REQUIRED_OPERATOR_FIELDS = [
    ("name", "Numele complet al operatorului / firmei"),
    ("legal_form", "Forma juridică"),
    ("street", "Strada și numărul"),
    ("postal_code", "Cod poștal"),
    ("city", "Localitate"),
    ("email", "Adresă de email de contact"),
    ("phone", "Telefon"),
    ("represented_by", "Reprezentant legal (Vertretungsberechtigter)"),
]


class LegalPageView(TemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        operator = getattr(settings, "OPERATOR", {}) or {}
        ctx["operator"] = operator
        ctx["missing"] = [
            label for key, label in REQUIRED_OPERATOR_FIELDS if not operator.get(key)
        ]
        return ctx


class ImpressumView(LegalPageView):
    template_name = "legal/impressum.html"


class DatenschutzView(LegalPageView):
    template_name = "legal/datenschutz.html"


class AgbView(LegalPageView):
    template_name = "legal/agb.html"
