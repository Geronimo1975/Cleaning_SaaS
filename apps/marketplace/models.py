"""
Bursa de servicii: cerere → oferte → atribuire.

Două lucruri o deosebesc de un simplu formular de contact:

**Cererea e standardizată.** Fără tip × suprafață × frecvență, ofertele nu sunt
comparabile, iar „bursa fără negociere" devine o licitație pe orb. Câmpurile de
mai jos nu sunt opționale din acest motiv.

**Nu există alocare automată.** Sistemul poate SUGERA prestatori, dar fiecare
decide singur dacă ofertează și la ce preț. În Germania, un sistem care
repartizează munca unei persoane fizice bifează criteriile §7 SGB IV
(Scheinselbstständigkeit) și se apropie de Arbeitnehmerüberlassung — care cere
licență de la Bundesagentur für Arbeit.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Frequency(models.TextChoices):
    ONE_TIME = "ONE_TIME", "O singură dată"
    WEEKLY = "WEEKLY", "Săptămânal"
    BIWEEKLY = "BIWEEKLY", "La două săptămâni"
    MONTHLY = "MONTHLY", "Lunar"


VISITS_PER_MONTH = {
    Frequency.ONE_TIME: Decimal("1"),
    Frequency.WEEKLY: Decimal("4.33"),
    Frequency.BIWEEKLY: Decimal("2.17"),
    Frequency.MONTHLY: Decimal("1"),
}


class RequestStatus(models.TextChoices):
    DRAFT = "DRAFT", "Ciornă"
    OPEN = "OPEN", "Deschisă"
    AWARDED = "AWARDED", "Atribuită"
    # Dauerauftrag în curs: contractul e semnat, obiectivul există la prestator.
    # `AWARDED` însemna doar „s-a ales cineva", nu „se execută".
    ACTIVE = "ACTIVE", "În execuție"
    CANCELLED = "CANCELLED", "Anulată"
    EXPIRED = "EXPIRED", "Expirată"


class ServiceRequest(models.Model):
    client = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="service_requests"
    )
    category = models.ForeignKey(
        "taxonomy.ServiceCategory", on_delete=models.PROTECT, related_name="requests"
    )
    locality = models.ForeignKey(
        "geo.Locality", on_delete=models.PROTECT, related_name="requests"
    )
    postal_code = models.CharField(max_length=5, blank=True)

    # Specificația standardizată — fără ea ofertele nu se pot compara.
    area_sqm = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], help_text="Suprafața de curățat"
    )
    rooms = models.PositiveSmallIntegerField(null=True, blank=True)
    frequency = models.CharField(max_length=12, choices=Frequency.choices)
    preferred_weekdays = models.CharField(max_length=13, blank=True, default="")
    earliest_start = models.DateField()

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    has_pets = models.BooleanField(default=False)
    supplies_provided = models.BooleanField(
        default=False, verbose_name="Materialele sunt puse la dispoziție de client"
    )

    status = models.CharField(
        max_length=12, choices=RequestStatus.choices, default=RequestStatus.DRAFT, db_index=True
    )
    offers_close_at = models.DateTimeField(help_text="După acest moment nu se mai ofertează")
    published_at = models.DateTimeField(null=True, blank=True)
    awarded_offer = models.OneToOneField(
        "Offer", null=True, blank=True, on_delete=models.SET_NULL, related_name="won_request"
    )
    # Politica de repartizare se fixează la publicare. Dacă membrii votează alte
    # ponderi mâine, clasamentul acestei cereri rămâne cel după care s-a ofertat.
    dispatch_policy = models.ForeignKey(
        "cooperative.DispatchPolicy", null=True, blank=True, on_delete=models.PROTECT,
        related_name="requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("status", "locality", "category"))]
        verbose_name = "Cerere de serviciu"
        verbose_name_plural = "Cereri de serviciu"

    def __str__(self) -> str:
        return self.title

    @property
    def is_open(self) -> bool:
        return self.status == RequestStatus.OPEN and self.offers_close_at > timezone.now()

    @property
    def visits_per_month(self) -> Decimal:
        return VISITS_PER_MONTH[self.frequency]

    @property
    def is_35a_eligible(self) -> bool:
        """Deducerea se aplică serviciilor casnice, la client privat."""
        from apps.accounts.enums import EntityType

        return self.category.is_35a_eligible and self.client.entity_type == EntityType.INDIVIDUAL

    def clean(self):
        if self.category_id and not self.category.parent_id:
            raise ValidationError({"category": "Alege un serviciu concret, nu o categorie."})


class OfferStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Depusă"
    WITHDRAWN = "WITHDRAWN", "Retrasă"
    WON = "WON", "Câștigătoare"
    LOST = "LOST", "Neselectată"


class Offer(models.Model):
    """
    O ofertă, nu o negociere. Prestatorul își pune prețul o dată; clientul alege
    pe mai multe criterii, nu neapărat cel mai mic preț.
    """

    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="offers")
    provider = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="offers"
    )
    price_per_visit = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    estimated_minutes = models.PositiveSmallIntegerField()
    includes_supplies = models.BooleanField(default=True)
    earliest_start = models.DateField()
    message = models.TextField(blank=True)

    status = models.CharField(
        max_length=12, choices=OfferStatus.choices, default=OfferStatus.SUBMITTED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("price_per_visit",)
        constraints = [
            models.UniqueConstraint(fields=("request", "provider"), name="uniq_offer_per_provider"),
        ]
        verbose_name = "Ofertă"
        verbose_name_plural = "Oferte"

    def __str__(self) -> str:
        return f"{self.provider} · {self.price_per_visit} €/vizită"

    @property
    def monthly_price(self) -> Decimal:
        return (self.price_per_visit * self.request.visits_per_month).quantize(Decimal("0.01"))

    @property
    def implied_hourly(self) -> Decimal:
        """Prețul pe oră implicit — singura bază reală de comparație între oferte."""
        if not self.estimated_minutes:
            return Decimal("0")
        return (self.price_per_visit * 60 / self.estimated_minutes).quantize(Decimal("0.01"))

    @property
    def deduction_35a(self) -> Decimal:
        """20% din manoperă, plafonat la 4.000 €/an (§35a Abs. 2 EStG)."""
        if not self.request.is_35a_eligible:
            return Decimal("0")
        yearly = self.monthly_price * 12
        return min(yearly * Decimal("0.20"), Decimal("4000.00")).quantize(Decimal("0.01"))


class Invitation(models.Model):
    """
    Sugestie către un prestator, NU repartizare. Prestatorul decide singur dacă
    ofertează și la ce preț — vezi nota din capul modulului.
    """

    request = models.ForeignKey(
        ServiceRequest, on_delete=models.CASCADE, related_name="invitations"
    )
    provider = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="invitations"
    )
    score = models.DecimalField(max_digits=5, decimal_places=2)
    reasons = models.JSONField(default=dict, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-score",)
        constraints = [
            models.UniqueConstraint(fields=("request", "provider"), name="uniq_invitation"),
        ]
        verbose_name = "Sugestie"
        verbose_name_plural = "Sugestii"
