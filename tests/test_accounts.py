import pytest

from apps.accounts.enums import Capability, EntityType
from apps.accounts.models import Account
from apps.accounts.services import create_account, unpublish_profile


@pytest.mark.django_db
class TestAccounts:
    def test_rolurile_sunt_randuri_nu_coloane(self, employer):
        assert employer.capability_set() == {Capability.EMPLOYER, Capability.CLIENT}
        employer.grant(Capability.SUPPLIER)
        assert Capability.SUPPLIER in employer.capability_set()
        employer.revoke(Capability.SUPPLIER)
        assert Capability.SUPPLIER not in employer.capability_set()

    def test_slugul_nu_se_schimba_la_redenumire(self, worker):
        original = worker.slug
        worker.display_name = "Maria Nowak"
        worker.save()
        worker.refresh_from_db()
        assert worker.slug == original

    def test_slugurile_nu_se_refolosesc(self, db, worker, norderstedt):
        user = worker.memberships.first().user
        second = create_account(
            user=user, entity_type=EntityType.INDIVIDUAL,
            display_name="Maria Ionescu", capabilities=[Capability.WORKER],
            locality=norderstedt,
        )
        assert second.slug != worker.slug

    def test_profilul_se_creeaza_odata_cu_contul(self, worker, employer):
        assert hasattr(worker, "worker_profile")
        assert hasattr(employer, "company_profile")

    def test_depublicarea_pastreaza_randul(self, worker):
        unpublish_profile(worker)
        worker.refresh_from_db()
        assert worker.status == "UNPUBLISHED"
        assert Account.objects.filter(pk=worker.pk).exists()
        assert worker.unpublished_at is not None


@pytest.mark.django_db
class TestPrivateDocuments:
    """
    Documentele de verificare nu ajung niciodată în MEDIA_ROOT, pe care Nginx îl
    servește fără să treacă prin Django. Un Führungszeugnis public e o breșă,
    nu un bug de stil.
    """

    def _doc(self, account):
        from django.core.files.base import ContentFile

        from apps.accounts.compliance import DocumentType, VerificationDocument

        doc = VerificationDocument(account=account, doc_type=DocumentType.ID)
        doc.file.save("cazier.pdf", ContentFile(b"%PDF-1.4 secret"), save=True)
        return doc

    def test_fisierul_nu_e_in_media_root(self, worker, settings):
        doc = self._doc(worker)
        path = doc.file.storage.path(doc.file.name)
        assert str(settings.PRIVATE_STORAGE_ROOT) in path
        assert str(settings.MEDIA_ROOT) not in path

    def test_proprietarul_isi_descarca_documentul(self, client, worker):
        doc = self._doc(worker)
        client.force_login(worker.memberships.first().user)
        response = client.get(f"/cont/documente/{doc.pk}/")
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "private, no-store"

    def test_alt_cont_primeste_404(self, client, worker, employer):
        doc = self._doc(worker)
        client.force_login(employer.memberships.first().user)
        assert client.get(f"/cont/documente/{doc.pk}/").status_code == 404

    def test_anonimul_primeste_404(self, client, worker):
        doc = self._doc(worker)
        assert client.get(f"/cont/documente/{doc.pk}/").status_code == 404

    def test_staff_verifica_documentele(self, client, worker, employer):
        doc = self._doc(worker)
        user = employer.memberships.first().user
        user.is_staff = True
        user.save()
        client.force_login(user)
        assert client.get(f"/cont/documente/{doc.pk}/").status_code == 200
