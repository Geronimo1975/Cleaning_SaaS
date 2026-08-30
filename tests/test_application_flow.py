"""Lanțul care produce profiluri: anunț → candidatură → cont → profil public."""

import pytest
from django.test import Client

from apps.accounts.models import Account
from apps.jobs.models import Application


@pytest.fixture
def payload(norderstedt):
    return {
        "email": "neu@example.de", "full_name": "Petra Schulz",
        "phone": "+49 170 1112233", "locality": norderstedt.pk,
        "message": "Ich bewerbe mich.", "accept_terms": "on", "publish_profile": "on",
    }


@pytest.mark.django_db
class TestApplicationFlow:
    def test_anuntul_e_vizibil_fara_login(self, client, job):
        response = client.get(job.get_absolute_url())
        assert response.status_code == 200
        assert b"Gemeinschaftsfl" in response.content
        assert b"application/ld+json" in response.content

    def test_candidatura_creeaza_cont_si_profil(self, client, job, payload):
        client.post(f"/job/{job.slug}/bewerben/", payload, follow=True)
        account = Account.objects.get(display_name="Petra Schulz")
        assert account.entity_type == "INDIVIDUAL"
        assert account.capability_set() == {"WORKER", "CLIENT"}
        assert hasattr(account, "worker_profile")
        assert Application.objects.filter(applicant_account=account).exists()

    def test_consimtamintele_sunt_separate(self, client, job, payload):
        client.post(f"/job/{job.slug}/bewerben/", payload, follow=True)
        account = Account.objects.get(display_name="Petra Schulz")
        types = set(account.consents.values_list("consent_type", flat=True))
        assert types == {"TERMS", "PROFILE_PUBLICATION"}

    def test_fara_consimtamant_profilul_ramane_nepublicat(self, client, job, payload):
        payload.pop("publish_profile")
        client.post(f"/job/{job.slug}/bewerben/", payload, follow=True)
        account = Account.objects.get(display_name="Petra Schulz")
        assert account.status == "DRAFT"

    def test_parola_se_seteaza_prin_email_nu_in_formular(self, client, job, payload):
        client.post(f"/job/{job.slug}/bewerben/", payload, follow=True)
        account = Account.objects.get(display_name="Petra Schulz")
        assert not account.memberships.first().user.has_usable_password()

    def test_email_existent_nu_creeaza_al_doilea_cont(self, client, job, payload, worker):
        payload["email"] = "maria@example.de"
        response = client.post(f"/job/{job.slug}/bewerben/", payload)
        assert b"deja un cont" in response.content
        assert Account.objects.filter(display_name="Petra Schulz").count() == 0

    def test_profil_depublicat_raspunde_410_si_noindex(self, client, worker):
        from apps.accounts.services import unpublish_profile

        unpublish_profile(worker)
        response = client.get(worker.get_absolute_url())
        assert response.status_code == 410
        assert response.headers["X-Robots-Tag"] == "noindex"

    def test_anunt_expirat_raspunde_410(self, client, job):
        from datetime import timedelta

        from django.utils import timezone
        from apps.jobs.models import JobPosting

        JobPosting.objects.filter(pk=job.pk).update(
            valid_through=timezone.now() - timedelta(days=1)
        )
        assert client.get(job.get_absolute_url()).status_code == 410
