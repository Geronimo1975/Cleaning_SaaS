from django.conf import settings
from django.db import models

from .models import Account


class DocumentType(models.TextChoices):
    ID = "ID", "Act de identitate"
    POLIZEILICHES = "POLIZEILICHES", "Führungszeugnis (cazier)"
    GEWERBE = "GEWERBE", "Gewerbeanmeldung"
    HRB = "HRB", "Extras Handelsregister"
    INSURANCE = "INSURANCE", "Poliță de răspundere civilă"
    QUALIFICATION = "QUALIFICATION", "Calificare / certificat"


class DocumentStatus(models.TextChoices):
    PENDING = "PENDING", "În verificare"
    APPROVED = "APPROVED", "Aprobat"
    REJECTED = "REJECTED", "Respins"


def private_storage():
    """Storage în afara rădăcinii servite de Nginx."""
    from django.core.files.storage import storages

    return storages["private"]


class VerificationDocument(models.Model):
    """NICIODATĂ public. Storage privat, cu termen de retenție."""

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DocumentType.choices)
    file = models.FileField(upload_to="verification/%Y/%m/", storage=private_storage)
    status = models.CharField(
        max_length=12, choices=DocumentStatus.choices, default=DocumentStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    delete_after = models.DateField(null=True, blank=True, help_text="Retenție DSGVO")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Document de verificare"
        verbose_name_plural = "Documente de verificare"


class ConsentType(models.TextChoices):
    PROFILE_PUBLICATION = "PROFILE_PUBLICATION", "Publicarea profilului"
    TERMS = "TERMS", "Termeni și condiții"
    PRIVACY = "PRIVACY", "Politica de confidențialitate"
    MARKETING = "MARKETING", "Comunicări de marketing"


class ConsentRecord(models.Model):
    """Append-only. Nu se actualizează niciodată — se adaugă un rând nou."""

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField(max_length=24, choices=ConsentType.choices)
    policy_version = models.CharField(max_length=16)
    granted = models.BooleanField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Consimțământ"
        verbose_name_plural = "Consimțăminte"

    def save(self, *args, **kwargs):
        if self.pk:
            raise RuntimeError("ConsentRecord este append-only.")
        super().save(*args, **kwargs)
