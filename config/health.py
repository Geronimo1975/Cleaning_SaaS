"""
Endpoint de sănătate.

Nu returnează „ok" pe încredere: verifică baza de date și se uită dacă
notificările de indexare chiar pleacă. Fără al doilea punct, `flush_indexing`
poate fi mort de trei săptămâni fără ca nimic să semnaleze — coada crește în
tăcere, iar anunțurile nu ajung la Google.

Rutat sub `/healthz/`, în afara paginilor indexabile, cu noindex și fără cache.
"""

from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache


def _database() -> tuple[bool, str]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:  # noqa: BLE001 — orice eșec înseamnă „indisponibil"
        return False, str(exc)[:200]
    return True, "ok"


def _indexing_queue() -> tuple[bool, dict]:
    """
    Coada e „sănătoasă" dacă nimic nu stă în ea mai mult decât intervalul de
    golire. Nu e o eroare fatală — site-ul funcționează — dar e exact genul de
    defecțiune tăcută pentru care există acest endpoint.
    """
    from apps.jobs.models import IndexingStatus, IndexingTask

    cutoff = timezone.now() - timedelta(minutes=settings.INDEXING_STALE_MINUTES)
    pending = IndexingTask.objects.filter(status=IndexingStatus.PENDING)
    stale = pending.filter(created_at__lt=cutoff).count()
    failed = IndexingTask.objects.filter(status=IndexingStatus.FAILED).count()
    return stale == 0, {
        "pending": pending.count(),
        "stale": stale,
        "failed": failed,
        "stale_after_minutes": settings.INDEXING_STALE_MINUTES,
    }


@never_cache
def healthz(request):
    db_ok, db_detail = _database()
    queue_ok, queue_detail = _indexing_queue() if db_ok else (True, {})

    # Doar baza de date decide codul HTTP: orchestratorul repornește
    # containerul pe 503, iar o coadă întârziată nu se repară prin repornire.
    status = 200 if db_ok else 503
    payload = {
        "status": "ok" if (db_ok and queue_ok) else ("degraded" if db_ok else "down"),
        "checks": {
            "database": {"ok": db_ok, "detail": db_detail},
            "indexing_queue": {"ok": queue_ok, **queue_detail},
        },
    }
    response = JsonResponse(payload, status=status)
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
