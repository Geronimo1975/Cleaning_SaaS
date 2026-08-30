"""
Izolarea între conturi. Un ID ghicit în URL nu trebuie să expună nimic —
și trebuie să dea 404, nu 403: un cont străin nu află nici că URL-ul există.
"""

import pytest

from apps.accounts.enums import Capability, EntityType
from apps.accounts.models import User
from apps.accounts.services import create_account
from apps.contracts.models import ContractDraft
from apps.contracts.services import active_template
from apps.jobs.models import Application


@pytest.fixture
def outsider(db, norderstedt):
    user = User.objects.create_user("altcineva@example.de", "parola-lunga-123")
    account = create_account(
        user=user, entity_type=EntityType.COMPANY, display_name="Alt SRL",
        capabilities=[Capability.EMPLOYER], locality=norderstedt,
    )
    account.user = user
    return account


@pytest.fixture
def application(db, job, worker):
    return Application.objects.create(job=job, applicant_account=worker)


@pytest.fixture
def contract(db, employer, worker, norderstedt):
    return ContractDraft.objects.create(
        employer=employer, worker=worker, template=active_template("MINIJOB"),
        contract_type="MINIJOB", start_date="2026-10-01", hours_per_month=40,
        hourly_wage="14.25", workplace=norderstedt,
    )


@pytest.mark.django_db
class TestIsolation:
    def test_strainul_nu_vede_candidatura(self, client, outsider, application):
        client.force_login(outsider.user)
        assert client.get(f"/dashboard/candidaturi/{application.pk}/").status_code == 404

    def test_strainul_nu_vede_contractul(self, client, outsider, contract):
        client.force_login(outsider.user)
        assert client.get(f"/dashboard/contracte/{contract.pk}/").status_code == 404

    def test_strainul_nu_editeaza_anuntul(self, client, outsider, job):
        client.force_login(outsider.user)
        assert client.get(f"/dashboard/anunturi/{job.pk}/").status_code == 404

    def test_angajatorul_isi_vede_propriile_date(self, client, employer, application, contract):
        client.force_login(employer.user)
        assert client.get(f"/dashboard/candidaturi/{application.pk}/").status_code == 200
        assert client.get(f"/dashboard/contracte/{contract.pk}/").status_code == 200

    def test_capabilitatea_lipsa_da_403(self, client, worker, job):
        """Prestatoarea are cont, dar nu e EMPLOYER."""
        client.force_login(worker.user)
        assert client.get("/dashboard/anunturi/").status_code == 403

    def test_prestatorul_isi_vede_contractul_primit(self, client, worker, contract):
        client.force_login(worker.user)
        assert client.get(f"/dashboard/contracte/{contract.pk}/").status_code == 200

    def test_fara_cont_esti_trimis_la_onboarding(self, client, db):
        user = User.objects.create_user("nou@example.de", "parola-lunga-123")
        client.force_login(user)
        response = client.get("/dashboard/")
        assert response.status_code == 302
        assert "onboarding" in response.url
