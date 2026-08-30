"""
Google Indexing API.

Trei straturi separate, intenționat:

  enqueue()   — pune în coadă. Rulează în tranzacția care publică anunțul.
  flush()     — golește coada. Rulează dintr-un cron, nu dintr-un request.
  _transport  — apelul HTTP propriu-zis. Singurul loc care știe de Google.

Fără credențiale configurate, `enqueue` funcționează normal și `flush` nu face
nimic — dezvoltarea locală și testele nu au nevoie de un service account.
"""

from django.conf import settings
from django.utils import timezone

from .models import IndexingAction, IndexingStatus, IndexingTask

ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPE = "https://www.googleapis.com/auth/indexing"
MAX_ATTEMPTS = 5


def enqueue(url: str, action: str) -> IndexingTask:
    """Idempotent pe (url, action) cât timp notificarea e încă în așteptare."""
    task, _ = IndexingTask.objects.get_or_create(
        url=url, action=action, status=IndexingStatus.PENDING
    )
    return task


def absolute_url(request, obj) -> str:
    return request.build_absolute_uri(obj.get_absolute_url())


def flush(limit: int = 100, transport=None) -> dict:
    """
    Trimite notificările în așteptare. Returnează un raport, nu aruncă:
    e apelată dintr-un cron și un eșec nu are voie să oprească restul cozii.
    """
    from apps.legal.publication import missing_operator_fields, operator_is_configured

    # Nu împingem URL-uri către Google cât timp Impressum-ul e invalid.
    if not operator_is_configured():
        return {
            "skipped": "operator nedeclarat (§5 TMG): "
                       + ", ".join(missing_operator_fields()),
            "sent": 0,
            "failed": 0,
        }

    transport = transport or _transport
    if transport is _transport and not _credentials_path():
        return {"skipped": "GOOGLE_INDEXING_CREDENTIALS nu e configurat", "sent": 0, "failed": 0}

    sent = failed = 0
    tasks = IndexingTask.objects.filter(status=IndexingStatus.PENDING)[:limit]
    for task in tasks:
        task.attempts += 1
        try:
            transport(task.url, task.action)
        except Exception as exc:  # noqa: BLE001 — orice eșec e doar un retry
            task.last_error = str(exc)[:300]
            if task.attempts >= MAX_ATTEMPTS:
                task.status = IndexingStatus.FAILED
            failed += 1
        else:
            task.status = IndexingStatus.SENT
            task.sent_at = timezone.now()
            task.last_error = ""
            sent += 1
        task.save(update_fields=["status", "attempts", "last_error", "sent_at"])
    return {"sent": sent, "failed": failed}


def _credentials_path():
    return getattr(settings, "GOOGLE_INDEXING_CREDENTIALS", "") or None


def _transport(url: str, action: str) -> None:
    """Apelul real. Importurile sunt locale ca dependența să rămână opțională."""
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(
        _credentials_path(), scopes=[SCOPE]
    )
    response = AuthorizedSession(credentials).post(
        ENDPOINT, json={"url": url, "type": action}, timeout=15
    )
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")


__all__ = ["IndexingAction", "absolute_url", "enqueue", "flush"]
