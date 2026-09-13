"""Enumerările stratului comercial. Membri în engleză, etichete în română/germană."""

from django.db import models


class DocumentType(models.TextChoices):
    # Se extinde cu tipurile de facturi când apare modulul de facturare.
    ORDER = "ORDER", "Auftrag"


class OrderStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Activă"
    SUSPENDED = "SUSPENDED", "Suspendată"
    COMPLETED = "COMPLETED", "Încheiată"
    CANCELLED = "CANCELLED", "Anulată"


class ContractKind(models.TextChoices):
    """Natura juridică a Auftrag-ului față de client. Altă axă decât
    `contracts.ContractType`, care clasifică relația cu lucrătorul."""

    DIENSTVERTRAG = "DIENSTVERTRAG", "Dienstvertrag (§611 BGB)"
    WERKVERTRAG = "WERKVERTRAG", "Werkvertrag (§631 BGB)"
