"""
Poarta de publicare.

Un site german accesibil public fără Impressum valid (§5 TMG) e motiv clasic de
Abmahnung. Cum toată strategia de achiziție e indexarea în Google, riscul nu e
teoretic: exact conținutul pe care vrem să-l indexăm ar fi cel care atrage
problema.

De aceea indexarea NU e o setare separată, pe care cineva să uite s-o schimbe.
E derivată din completitudinea datelor operatorului: cât timp Impressum-ul se
autodenunță ca invalid, site-ul cere `noindex` și nu notifică Google. În clipa
în care variabilele `OPERATOR_*` sunt completate, poarta se deschide singură.
"""

from django.conf import settings

REQUIRED = ("name", "street", "postal_code", "city", "email", "phone", "represented_by")


def operator_is_configured() -> bool:
    operator = getattr(settings, "OPERATOR", {}) or {}
    return all(operator.get(field) for field in REQUIRED)


def missing_operator_fields() -> list[str]:
    operator = getattr(settings, "OPERATOR", {}) or {}
    return [field for field in REQUIRED if not operator.get(field)]


class PublicationGateMiddleware:
    """Adaugă `X-Robots-Tag: noindex` cât timp operatorul nu e declarat."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not operator_is_configured():
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
