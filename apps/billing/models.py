"""
Stratul comercial, partea de comenzi.

`Customer` e o RELAȚIE între două conturi (prestator ↔ beneficiar), nu o a doua
tabelă de părți: USt-IdNr., adresa, forma juridică rămân pe `accounts.Account`.
`Order` (Auftrag) e containerul de care se vor lega ofertele și facturile.
`DocumentSequence` ține numerotarea per prestator, per tip, per an.
"""

from django.core.exceptions import ValidationError
from django.db import models

from .enums import ContractKind, DocumentType, OrderStatus


class Customer(models.Model):
    provider = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="customers",
        verbose_name="Prestator",
    )
    account = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="customer_of",
        verbose_name="Beneficiar",
    )
    customer_number = models.CharField("Număr client", max_length=32, blank=True)
    contact_person = models.CharField("Persoană de contact", max_length=160, blank=True)
    is_active = models.BooleanField("Activ", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("account__display_name",)
        constraints = [
            models.UniqueConstraint(fields=("provider", "account"), name="uniq_customer"),
            models.CheckConstraint(
                condition=~models.Q(provider=models.F("account")), name="customer_not_self"
            ),
        ]
        verbose_name = "Client"
        verbose_name_plural = "Clienți"

    def __str__(self):
        return f"{self.account} @ {self.provider}"


class DocumentSequence(models.Model):
    """Numerotare per prestator, per tip de document, per an. Se alocă sub lock
    în `numbering.allocate()`, niciodată din `pk`."""

    provider = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="document_sequences"
    )
    document_type = models.CharField(max_length=16, choices=DocumentType.choices)
    year = models.PositiveSmallIntegerField()
    prefix = models.CharField("Prefix", max_length=8, default="A")
    next_number = models.PositiveIntegerField("Următorul număr", default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "document_type", "year"), name="uniq_sequence"
            ),
        ]
        verbose_name = "Serie de numerotare"
        verbose_name_plural = "Serii de numerotare"

    def __str__(self):
        return f"{self.prefix}-{self.year} → {self.next_number}"


class Order(models.Model):
    """Auftrag. Obiectivul (`planning.Site`) există deja — nu se dublează aici."""

    provider = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="orders",
        verbose_name="Prestator",
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="orders", verbose_name="Client"
    )
    site = models.ForeignKey(
        "planning.Site", on_delete=models.PROTECT, related_name="orders",
        verbose_name="Obiectiv",
    )
    category = models.ForeignKey(
        "taxonomy.ServiceCategory", on_delete=models.PROTECT, related_name="orders",
        verbose_name="Tip de serviciu",
    )
    order_number = models.CharField("Număr comandă", max_length=32)
    title = models.CharField("Titlu", max_length=200)
    start_date = models.DateField("Început")
    end_date = models.DateField("Sfârșit", null=True, blank=True)
    contract_kind = models.CharField(
        "Natura contractului", max_length=16, choices=ContractKind.choices,
        default=ContractKind.DIENSTVERTRAG,
    )
    # Abnahme (§641 BGB). Are sens doar la Werkvertrag.
    accepted_at = models.DateTimeField("Recepție", null=True, blank=True)
    status = models.CharField(
        "Stare", max_length=12, choices=OrderStatus.choices,
        default=OrderStatus.ACTIVE, db_index=True,
    )
    source_offer = models.ForeignKey(
        "marketplace.Offer", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="orders", verbose_name="Oferta câștigătoare",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-start_date", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "order_number"), name="uniq_order_number_per_provider"
            ),
            # Idempotența la activare e garantată de bază, nu doar de verificarea din services.
            models.UniqueConstraint(
                fields=("source_offer",),
                condition=models.Q(source_offer__isnull=False),
                name="uniq_order_per_offer",
            ),
        ]
        verbose_name = "Comandă"
        verbose_name_plural = "Comenzi"

    def __str__(self):
        return f"{self.order_number} — {self.title}"

    def clean(self):
        errors = {}
        if self.site_id and self.site.account_id != self.provider_id:
            errors["site"] = "Obiectivul aparține altui cont."
        if self.customer_id and self.customer.provider_id != self.provider_id:
            errors["customer"] = "Clientul aparține altui prestator."
        if self.category_id and not self.category.parent_id:
            errors["category"] = "Doar categoriile-frunză sunt selectabile."
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "Sfârșitul nu poate fi înaintea începutului."
        if errors:
            raise ValidationError(errors)
