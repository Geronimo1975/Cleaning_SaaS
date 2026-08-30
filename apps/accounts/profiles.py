from django.core.exceptions import ValidationError
from django.db import models

from .enums import EntityType
from .models import Account


class Availability(models.TextChoices):
    FULL_TIME = "FULL_TIME", "Program complet"
    PART_TIME = "PART_TIME", "Part-time"
    WEEKENDS = "WEEKENDS", "Weekenduri"
    FLEXIBLE = "FLEXIBLE", "Flexibil"


class WorkerProfile(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="worker_profile"
    )
    years_experience = models.PositiveSmallIntegerField(default=0)
    availability = models.CharField(
        max_length=16, choices=Availability.choices, default=Availability.FLEXIBLE
    )
    hourly_rate_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    has_own_transport = models.BooleanField(default=False)
    has_own_equipment = models.BooleanField(default=False)
    willing_to_travel_km = models.PositiveSmallIntegerField(default=15)
    languages = models.CharField(max_length=120, blank=True, help_text="DE, EN, PL, RO ...")
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = "Profil prestator (PF)"
        verbose_name_plural = "Profiluri prestatori (PF)"

    def __str__(self) -> str:
        return f"Profil {self.account}"

    def clean(self):
        if self.account.entity_type != EntityType.INDIVIDUAL:
            raise ValidationError("WorkerProfile este valabil doar pentru persoane fizice.")


class CompanyProfile(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="company_profile"
    )
    employees_range = models.CharField(max_length=16, blank=True, help_text="1-5, 6-20, 21-50 ...")
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
    website = models.URLField(blank=True)
    # Prestatorul intră în locuința clientului. Fără acoperire, un furt omoară platforma.
    has_liability_insurance = models.BooleanField(default=False)
    insurance_valid_until = models.DateField(null=True, blank=True)
    # Curățenia de clădiri e Anlage B1 HwO — fără Meisterpflicht, dar cu
    # înregistrare la Handwerkskammer.
    hwk_registered = models.BooleanField(default=False, verbose_name="Înregistrat la HWK")

    class Meta:
        verbose_name = "Profil firmă"
        verbose_name_plural = "Profiluri firme"

    def __str__(self) -> str:
        return f"Profil {self.account}"

    def clean(self):
        if self.account.entity_type != EntityType.COMPANY:
            raise ValidationError("CompanyProfile este valabil doar pentru firme.")


class AccountService(models.Model):
    """Ce servicii oferă contul. Doar frunze din taxonomie."""

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="services")
    category = models.ForeignKey(
        "taxonomy.ServiceCategory", on_delete=models.PROTECT, related_name="accounts"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("account", "category"), name="uniq_account_service"),
        ]

    def clean(self):
        if not self.category.is_leaf:
            raise ValidationError({"category": "Doar categoriile-frunză sunt selectabile."})


class ServiceArea(models.Model):
    """Unde lucrează contul."""

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="areas")
    locality = models.ForeignKey(
        "geo.Locality", on_delete=models.PROTECT, related_name="accounts_serving"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("account", "locality"), name="uniq_service_area"),
        ]
