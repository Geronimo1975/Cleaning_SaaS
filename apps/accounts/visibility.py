"""
Drepturi de vizualizare.

Regula: NU expunem obiectul `Account` direct într-un template. Trecem întotdeauna
prin `AccountView`, care decide câmp cu câmp ce vede un anumit privitor.
Motivul e DSGVO: datele de contact ale unei persoane fizice sunt date personale,
iar „publicat" nu înseamnă „vizibil pentru oricine". Adresa și telefonul devin
vizibile abia când există o relație reală (o aplicare, mai târziu un contract).
"""

from __future__ import annotations

from enum import IntEnum

from django.apps import apps

from .enums import EntityType


class Relation(IntEnum):
    """Cine se uită, raportat la contul privit. Ordinea contează — se compară cu >=."""

    ANONYMOUS = 0      # vizitator nelogat
    AUTHENTICATED = 1  # utilizator logat, fără legătură cu contul
    ENGAGED = 2        # există o aplicare/ofertă între cele două conturi
    SELF = 3           # propriul cont
    STAFF = 4          # operator platformă


# Câmp -> nivelul minim de relație necesar pentru a-l vedea.
FIELD_POLICY: dict[str, Relation] = {
    # public, indexabil de Google
    "display_name": Relation.ANONYMOUS,
    "slug": Relation.ANONYMOUS,
    "entity_type": Relation.ANONYMOUS,
    "about": Relation.ANONYMOUS,
    "avatar": Relation.ANONYMOUS,
    "locality": Relation.ANONYMOUS,
    "verification_level": Relation.ANONYMOUS,
    "services": Relation.ANONYMOUS,
    "areas": Relation.ANONYMOUS,
    # date de firmă: publice prin lege (Impressum, §5 TMG) — dar doar pentru firme
    "legal_name": Relation.ANONYMOUS,
    "registration_number": Relation.ANONYMOUS,
    "vat_id": Relation.ANONYMOUS,
    # contact: doar după ce există o relație
    "phone": Relation.ENGAGED,
    "contact_email": Relation.ENGAGED,
    "street": Relation.ENGAGED,
    "postal_code": Relation.ENGAGED,
    # date fiscale/juridice: niciodată către alt cont
    "legal_status": Relation.SELF,
    "tax_number": Relation.SELF,
    "documents": Relation.SELF,
    "consents": Relation.SELF,
    "status": Relation.SELF,
}

# Excepție: pentru o PERSOANĂ FIZICĂ, datele „de firmă" nu există și nu se afișează.
INDIVIDUAL_HIDDEN = {"legal_name", "registration_number", "vat_id"}

# Un contract în ciornă nu e încă o relație — celălalt cont nu știe că există.
# Din momentul trimiterii spre semnare, ambele părți au nevoie de datele de contact.
ENGAGING_CONTRACT_STATUSES = ("SENT", "SIGNED")


def resolve_relation(target, viewer_account=None, user=None) -> Relation:
    if user is not None and user.is_authenticated and user.is_staff:
        return Relation.STAFF
    if viewer_account is None:
        return Relation.AUTHENTICATED if (user and user.is_authenticated) else Relation.ANONYMOUS
    if viewer_account.pk == target.pk:
        return Relation.SELF
    if _is_engaged(target, viewer_account):
        return Relation.ENGAGED
    return Relation.AUTHENTICATED


def _is_engaged(a, b) -> bool:
    """
    Există o legătură economică între cele două conturi?

    Două surse, nu una: o candidatură la un anunț ȘI un contract trimis spre
    semnare sau semnat. Un lucrător cu contract semnat trebuie să vadă datele
    de contact ale angajatorului chiar dacă nu a aplicat niciodată la un anunț
    (a fost invitat direct). Aici se adaugă și `Offer` când apare.
    """
    from django.db.models import Q

    Application = apps.get_model("jobs", "Application")
    applied = Application.objects.filter(
        (Q(applicant_account=a) & Q(job__account=b))
        | (Q(applicant_account=b) & Q(job__account=a))
    ).exists()
    if applied:
        return True

    ContractDraft = apps.get_model("contracts", "ContractDraft")
    contracted = ContractDraft.objects.filter(
        (Q(worker=a) & Q(employer=b)) | (Q(worker=b) & Q(employer=a)),
        status__in=ENGAGING_CONTRACT_STATUSES,
    ).exists()
    if contracted:
        return True

    # O ofertă depusă NU e suficientă — altfel oricine ar putea oferta la o
    # cerere doar ca să afle adresa clientului. Relația se ridică la atribuire.
    Offer = apps.get_model("marketplace", "Offer")
    return Offer.objects.filter(
        (Q(provider=a) & Q(request__client=b)) | (Q(provider=b) & Q(request__client=a)),
        status="WON",
    ).exists()


class AccountView:
    """
    Proiecție a unui Account pentru un anumit privitor.

    În template:  {{ view.phone }}  -> valoarea sau None
                  {% if view.can.phone %} ... {% endif %}
    """

    def __init__(self, account, viewer_account=None, user=None):
        self.account = account
        self.relation = resolve_relation(account, viewer_account, user)

    def can(self, field: str) -> bool:
        if (
            self.account.entity_type == EntityType.INDIVIDUAL
            and field in INDIVIDUAL_HIDDEN
        ):
            return False
        required = FIELD_POLICY.get(field, Relation.SELF)
        return self.relation >= required

    def get(self, field: str, default=None):
        if not self.can(field):
            return default
        return getattr(self.account, field, default)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self.get(name)

    def as_dict(self) -> dict:
        return {f: self.get(f) for f in FIELD_POLICY if self.can(f)}
