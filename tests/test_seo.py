"""
Sitemap + robots. Contractul verificat aici: în sitemap intră DOAR ce răspunde
200. Un anunț expirat sau un profil depublicat răspunde 410, iar prezența lui
în sitemap ar strica raportarea pentru tot fișierul.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.services import unpublish_profile
from apps.jobs.models import JobStatus


@pytest.mark.django_db
class TestSitemap:
    def test_indexul_listeaza_sectiunile(self, client):
        r = client.get("/sitemap.xml")
        assert r.status_code == 200
        body = r.content.decode()
        for section in ("sitemap-jobs.xml", "sitemap-profiles.xml", "sitemap-directory.xml"):
            assert section in body

    def test_anuntul_activ_e_in_sitemap(self, client, job):
        body = client.get("/sitemap-jobs.xml").content.decode()
        assert job.get_absolute_url() in body

    def test_anuntul_expirat_iese_din_sitemap_si_da_410(self, client, job):
        job.valid_through = timezone.now() - timedelta(days=1)
        job.save(update_fields=["valid_through"])
        assert job.get_absolute_url() not in client.get("/sitemap-jobs.xml").content.decode()
        r = client.get(job.get_absolute_url())
        assert r.status_code == 410
        assert r["X-Robots-Tag"] == "noindex"

    def test_anuntul_inchis_iese_din_sitemap(self, client, job):
        job.status = JobStatus.CLOSED
        job.save(update_fields=["status"])
        assert job.get_absolute_url() not in client.get("/sitemap-jobs.xml").content.decode()

    def test_profilul_publicat_e_in_sitemap(self, client, worker):
        body = client.get("/sitemap-profiles.xml").content.decode()
        assert worker.get_absolute_url() in body

    def test_profilul_depublicat_iese_din_sitemap_si_da_410(self, client, worker):
        unpublish_profile(worker)
        assert worker.get_absolute_url() not in client.get("/sitemap-profiles.xml").content.decode()
        r = client.get(worker.get_absolute_url())
        assert r.status_code == 410
        assert r["X-Robots-Tag"] == "noindex"

    def test_directorul_contine_paginile_de_oras(self, client, norderstedt):
        body = client.get("/sitemap-directory.xml").content.decode()
        assert f"/reinigungskraft/{norderstedt.slug}/" in body
        assert f"/jobs/{norderstedt.slug}/" in body


@pytest.mark.django_db
def test_robots_indica_sitemapul_si_blocheaza_dashboardul(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Disallow: /dashboard/" in body
    assert "/sitemap.xml" in body


@pytest.mark.django_db
class TestIndexingQueue:
    """
    Contractul: publicarea nu depinde de Google. Notificarea intră în coadă în
    tranzacția care publică, iar trimiterea e o operațiune separată.
    """


    def _publish(self, client, employer, job):
        client.force_login(employer.user)
        return client.post(f"/dashboard/anunturi/{job.pk}/publicare/")

    def test_publicarea_pune_url_updated_in_coada(self, client, employer, job):
        from apps.jobs.models import IndexingAction, IndexingStatus, IndexingTask

        job.status = JobStatus.DRAFT
        job.save(update_fields=["status"])
        IndexingTask.objects.all().delete()
        self._publish(client, employer, job)
        task = IndexingTask.objects.get()
        assert task.action == IndexingAction.UPDATED
        assert task.status == IndexingStatus.PENDING
        assert task.url.endswith(job.get_absolute_url())

    def test_inchiderea_pune_url_deleted_in_coada(self, client, employer, job):
        from apps.jobs.models import IndexingAction, IndexingTask

        IndexingTask.objects.all().delete()
        self._publish(client, employer, job)  # job e PUBLISHED -> se închide
        assert IndexingTask.objects.get().action == IndexingAction.DELETED

    def test_flush_marcheaza_trimis(self, db):
        from apps.jobs.indexing import enqueue, flush
        from apps.jobs.models import IndexingAction, IndexingStatus

        task = enqueue("https://example.de/job/x/", IndexingAction.UPDATED)
        calls = []
        assert flush(transport=lambda u, a: calls.append((u, a)))["sent"] == 1
        task.refresh_from_db()
        assert task.status == IndexingStatus.SENT
        assert calls == [("https://example.de/job/x/", IndexingAction.UPDATED)]

    def test_esecul_lasa_sarcina_in_coada_pentru_retry(self, db):
        from apps.jobs.indexing import enqueue, flush
        from apps.jobs.models import IndexingAction, IndexingStatus

        task = enqueue("https://example.de/job/x/", IndexingAction.UPDATED)

        def boom(url, action):
            raise RuntimeError("HTTP 503")

        assert flush(transport=boom)["failed"] == 1
        task.refresh_from_db()
        assert task.status == IndexingStatus.PENDING
        assert task.attempts == 1
        assert "503" in task.last_error

    def test_renunta_dupa_max_incercari(self, db):
        from apps.jobs.indexing import MAX_ATTEMPTS, enqueue, flush
        from apps.jobs.models import IndexingAction, IndexingStatus

        task = enqueue("https://example.de/job/x/", IndexingAction.UPDATED)

        def boom(url, action):
            raise RuntimeError("HTTP 400")

        for _ in range(MAX_ATTEMPTS):
            flush(transport=boom)
        task.refresh_from_db()
        assert task.status == IndexingStatus.FAILED

    def test_fara_credentiale_flush_nu_face_nimic(self, db, settings):
        from apps.jobs.indexing import enqueue, flush
        from apps.jobs.models import IndexingAction, IndexingStatus

        settings.GOOGLE_INDEXING_CREDENTIALS = ""
        task = enqueue("https://example.de/job/x/", IndexingAction.UPDATED)
        assert flush()["sent"] == 0
        task.refresh_from_db()
        assert task.status == IndexingStatus.PENDING
