"""
Operațiuni de business pe conturi.

Motivul pentru care nu stau în view-uri: crearea unui cont se întâmplă din trei
locuri diferite (onboarding după signup, aplicare la un anunț, import de
portofoliu) și trebuie să producă exact aceeași structură de fiecare dată.
"""

from django.db import transaction

from .enums import Capability, EntityType, LegalStatus
from .models import Account, Membership, User
from .compliance import ConsentRecord, ConsentType

POLICY_VERSION = "2026-09-01"


@transaction.atomic
def create_account(
    *,
    user: User,
    entity_type: str,
    display_name: str,
    capabilities: list[str],
    locality=None,
    legal_status: str = LegalStatus.UNDECLARED,
    **extra,
) -> Account:
    account = Account.objects.create(
        entity_type=entity_type,
        display_name=display_name,
        locality=locality,
        legal_status=legal_status,
        **extra,
    )
    Membership.objects.create(user=user, account=account)
    for cap in capabilities:
        account.grant(cap)
    _ensure_profile(account)
    return account


def _ensure_profile(account: Account):
    """Profilul se creează odată cu contul, gol. Un cont fără profil e o stare
    imposibil de reprezentat în dashboard."""
    from .profiles import CompanyProfile, WorkerProfile

    if account.entity_type == EntityType.INDIVIDUAL:
        WorkerProfile.objects.get_or_create(account=account)
    else:
        CompanyProfile.objects.get_or_create(account=account)


def record_consent(account, consent_type, granted, request=None, version=POLICY_VERSION):
    return ConsentRecord.objects.create(
        account=account,
        consent_type=consent_type,
        policy_version=version,
        granted=granted,
        ip_address=_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:300] if request else ""),
    )


def _ip(request):
    if not request:
        return None
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR")


def publish_profile(account, request=None):
    """Publicarea cere consimțământ explicit și separat — nu e inclusă în T&C."""
    record_consent(account, ConsentType.PROFILE_PUBLICATION, True, request)
    account.publish()
    return account


def unpublish_profile(account, request=None):
    record_consent(account, ConsentType.PROFILE_PUBLICATION, False, request)
    account.unpublish()
    return account


DEFAULT_CAPABILITIES = {
    "worker": [Capability.WORKER, Capability.CLIENT],
    "provider": [Capability.PROVIDER, Capability.CLIENT, Capability.EMPLOYER],
    "supplier": [Capability.SUPPLIER, Capability.CLIENT],
    "client": [Capability.CLIENT],
}
