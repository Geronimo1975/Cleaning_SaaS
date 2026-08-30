"""
Adminul e interfața de conformitate: aici se verifică documente, se citesc
consimțămintele și se actualizează pragurile salariale. Un `list_display` greșit
nu apare la `manage.py check` — apare ca 500 în fața operatorului. De asta
fiecare changelist se deschide efectiv într-un test.
"""

import pytest
from django.contrib import admin
from django.contrib.messages.storage.cookie import CookieStorage
from django.urls import reverse

from apps.accounts.compliance import ConsentRecord, VerificationDocument
from apps.accounts.models import User


@pytest.fixture
def staff_client(client, db):
    user = User.objects.create_superuser("admin@example.de", "parola-lunga-123")
    client.force_login(user)
    return client


def _urls():
    for model, _ in admin.site._registry.items():
        meta = model._meta
        yield pytest.param(
            f"admin:{meta.app_label}_{meta.model_name}_changelist",
            id=f"{meta.app_label}.{meta.model_name}",
        )


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", list(_urls()))
def test_changelist_se_deschide(staff_client, url_name):
    assert staff_client.get(reverse(url_name)).status_code == 200


@pytest.mark.django_db
def test_toate_modelele_au_admin():
    """
    Un model fără admin e un model pe care nimeni nu îl poate inspecta în
    producție. Lista de excepții e explicită, ca adăugarea unui model nou să
    forțeze o decizie, nu o omisiune.
    """
    from django.apps import apps as django_apps

    exempt = {
        "accounts.AccountCapability",  # editat inline pe Account
        "accounts.AccountService",     # idem
        "accounts.ServiceArea",        # idem
        "contracts.ContractSignature",  # inline readonly pe contract
        "catalog.ProductImage",        # inline pe produs
    }
    registered = {f"{m._meta.app_label}.{m.__name__}" for m in admin.site._registry}
    local = {
        f"{m._meta.app_label}.{m.__name__}"
        for m in django_apps.get_models()
        if m._meta.app_label in {c.label for c in django_apps.get_app_configs()
                                 if c.name.startswith("apps.")}
    }
    assert not (local - registered - exempt)


@pytest.mark.django_db
class TestConformitate:
    def test_consimtamintele_nu_se_pot_edita(self):
        """Un consimțământ editabil nu mai e dovadă."""
        opts = admin.site._registry[ConsentRecord]
        assert not opts.has_add_permission(None)
        assert not opts.has_change_permission(None)
        assert not opts.has_delete_permission(None)

    def test_documentul_de_verificare_nu_expune_fisierul(self):
        """
        Storage-ul privat nu are `base_url`; un link în admin ar arunca, iar un
        act de identitate descărcabil dintr-o listă nu e o scăpare de randare,
        e o scurgere de date.
        """
        opts = admin.site._registry[VerificationDocument]
        assert "file" in opts.readonly_fields
        assert "file" not in opts.list_display

    def test_aprobarea_ridica_nivelul_de_verificare(self, staff_client, worker, rf):
        from apps.accounts.compliance import DocumentStatus, DocumentType
        from apps.accounts.enums import VerificationLevel

        doc = VerificationDocument.objects.create(
            account=worker, doc_type=DocumentType.ID, file="verification/2026/08/x.pdf"
        )
        request = rf.post("/admin/")
        request.user = User.objects.get(email="admin@example.de")
        request._messages = CookieStorage(request)
        opts = admin.site._registry[VerificationDocument]
        opts.approve(request, VerificationDocument.objects.filter(pk=doc.pk))

        doc.refresh_from_db()
        worker.refresh_from_db()
        assert doc.status == DocumentStatus.APPROVED
        assert doc.reviewed_by == request.user
        assert doc.reviewed_at is not None
        assert worker.verification_level == VerificationLevel.DOCUMENTS

    def test_contractul_semnat_devine_readonly(self, signed_contract, rf):
        from apps.contracts.models import ContractDraft

        draft = signed_contract()
        opts = admin.site._registry[ContractDraft]
        readonly = opts.get_readonly_fields(rf.get("/admin/"), draft)
        assert "hourly_wage" in readonly and "rendered_body" in readonly
        assert not opts.has_delete_permission(rf.get("/admin/"), draft)
