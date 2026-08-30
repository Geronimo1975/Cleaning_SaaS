"""
Healthcheck.

Rostul lui nu e „răspunde 200", ci să facă vizibilă exact defecțiunea tăcută:
coada de indexare care nu se mai golește. Un site care merge perfect, dar ale
cărui anunțuri nu ajung la Google de trei săptămâni, arată identic din afară.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.jobs.indexing import enqueue
from apps.jobs.models import IndexingAction, IndexingStatus, IndexingTask


@pytest.mark.django_db
class TestHealthz:
    def test_raspunde_ok_cu_baza_disponibila(self, client):
        r = client.get("/healthz/")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["checks"]["database"]["ok"] is True

    def test_nu_e_indexabil_si_nu_se_cachează(self, client):
        r = client.get("/healthz/")
        assert r["X-Robots-Tag"] == "noindex, nofollow"
        assert "no-cache" in r["Cache-Control"]

    def test_coada_recenta_nu_e_intarziere(self, client):
        enqueue("https://example.de/job/x/", IndexingAction.UPDATED)
        body = client.get("/healthz/").json()
        assert body["status"] == "ok"
        assert body["checks"]["indexing_queue"]["pending"] == 1
        assert body["checks"]["indexing_queue"]["stale"] == 0

    def test_coada_blocata_da_degraded_dar_ramane_200(self, client, settings):
        """
        Repornirea containerului nu golește coada, deci nu are rost să
        semnalăm 503 — orchestratorul ar reporni la nesfârșit ceva ce
        funcționează.
        """
        settings.INDEXING_STALE_MINUTES = 60
        task = enqueue("https://example.de/job/x/", IndexingAction.UPDATED)
        IndexingTask.objects.filter(pk=task.pk).update(
            created_at=timezone.now() - timedelta(hours=3)
        )

        r = client.get("/healthz/")
        assert r.status_code == 200, "coada întârziată nu se repară prin repornire"
        body = r.json()
        assert body["status"] == "degraded"
        assert body["checks"]["indexing_queue"]["ok"] is False
        assert body["checks"]["indexing_queue"]["stale"] == 1

    def test_numara_si_esecurile_definitive(self, client):
        task = enqueue("https://example.de/job/x/", IndexingAction.UPDATED)
        IndexingTask.objects.filter(pk=task.pk).update(status=IndexingStatus.FAILED)
        assert client.get("/healthz/").json()["checks"]["indexing_queue"]["failed"] == 1

    def test_baza_indisponibila_da_503(self, client, monkeypatch):
        import config.health as health

        monkeypatch.setattr(health, "_database", lambda: (False, "connection refused"))
        r = client.get("/healthz/")
        assert r.status_code == 503
        assert r.json()["status"] == "down"


@pytest.mark.django_db
class TestLogging:
    def test_sql_ramane_pe_warning_implicit(self, settings):
        """La DEBUG global, SQL-ul ar îneca restul log-urilor."""
        assert settings.LOGGING["loggers"]["django.db.backends"]["level"] == "WARNING"

    def test_codul_propriu_are_logger(self, settings):
        assert "apps" in settings.LOGGING["loggers"]


@pytest.mark.django_db
def test_cache_configurat(settings):
    """Fără REDIS_URL, cache local — dar configurat explicit, nu implicit."""
    assert settings.CACHES["default"]["BACKEND"].endswith(
        ("LocMemCache", "RedisCache")
    )
