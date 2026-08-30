import hashlib

from django.template import Context, Template

from .models import ContractDraft, ContractTemplate, DraftStatus


def render_contract(draft: ContractDraft) -> ContractDraft:
    """Îngheață textul contractului. După asta, șablonul poate fi schimbat liber."""
    template = Template(draft.template.body)
    body = template.render(Context({
        "title": draft.template.title,
        "employer": draft.employer,
        "worker": draft.worker,
        "draft": draft,
        "monthly_gross": draft.monthly_gross,
        "workplace": draft.workplace,
    }))
    draft.rendered_body = body
    draft.body_sha256 = hashlib.sha256(body.encode()).hexdigest()
    draft.save(update_fields=["rendered_body", "body_sha256", "updated_at"])
    return draft


def send_for_signature(draft: ContractDraft) -> list[str]:
    blocking = [i.message for i in draft.compliance_report() if i.blocking]
    if blocking:
        return blocking
    render_contract(draft)
    draft.status = DraftStatus.SENT
    draft.save(update_fields=["status", "updated_at"])
    return []


def active_template(contract_type, language="de") -> ContractTemplate | None:
    return ContractTemplate.objects.filter(
        contract_type=contract_type, language=language, is_active=True
    ).order_by("-version").first()


def sign_contract(draft: ContractDraft, account, signer_name: str, request=None):
    """
    Semnătură electronică simplă. Se semnează HASH-UL textului înghețat — dacă
    documentul s-ar schimba după semnare, hash-ul stocat nu ar mai corespunde
    și falsul ar fi demonstrabil.
    """
    from .models import ContractSignature, DraftStatus

    if draft.status != DraftStatus.SENT:
        raise ValueError("Contractul nu este trimis spre semnare.")
    if account.pk not in (draft.employer_id, draft.worker_id):
        raise ValueError("Doar părțile contractului pot semna.")
    if draft.signatures.filter(account=account).exists():
        raise ValueError("Ai semnat deja acest contract.")

    signature = ContractSignature.objects.create(
        contract=draft,
        account=account,
        signer_name=signer_name,
        document_sha256=draft.body_sha256,
        ip_address=_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:300] if request else ""),
    )
    signed_by = set(draft.signatures.values_list("account_id", flat=True))
    if {draft.employer_id, draft.worker_id} <= signed_by:
        draft.status = DraftStatus.SIGNED
        draft.save(update_fields=["status", "updated_at"])
    return signature


def _ip(request):
    if not request:
        return None
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR")
