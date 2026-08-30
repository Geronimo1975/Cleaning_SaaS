"""Fluxul de aplicare: aplicare → cont → profil public."""

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.compliance import ConsentType
from apps.accounts.enums import Capability, EntityType
from apps.accounts.models import Account, Membership
from apps.accounts.services import create_account, publish_profile, record_consent

from .models import Application

User = get_user_model()


@transaction.atomic
def apply_to_job(*, job, data, user=None, request=None) -> Application:
    """
    Idempotent pe (job, cont). Creează userul și contul dacă e nevoie.
    Parola se setează prin linkul de activare trimis pe email — nu cerem
    parolă în formularul de aplicare, pentru că fiecare câmp în plus
    scade rata de aplicare.
    """
    account = _resolve_account(data, user)

    if data.get("publish_profile"):
        publish_profile(account, request)
    record_consent(account, ConsentType.TERMS, True, request)

    application, _created = Application.objects.get_or_create(
        job=job,
        applicant_account=account,
        defaults={"message": data.get("message", "")},
    )
    return application


def _resolve_account(data, user):
    if user and user.is_authenticated:
        account = Account.objects.filter(memberships__user=user).first()
        if account:
            return account
        return create_account(
            user=user,
            entity_type=EntityType.INDIVIDUAL,
            display_name=data["full_name"],
            capabilities=[Capability.WORKER, Capability.CLIENT],
            locality=data["locality"],
            phone=data.get("phone", ""),
        )

    new_user = User.objects.create_user(email=data["email"], password=None)
    new_user.set_unusable_password()
    new_user.save(update_fields=["password"])
    return create_account(
        user=new_user,
        entity_type=EntityType.INDIVIDUAL,
        display_name=data["full_name"],
        capabilities=[Capability.WORKER, Capability.CLIENT],
        locality=data["locality"],
        phone=data.get("phone", ""),
        contact_email=data["email"],
    )
