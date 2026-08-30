from django.db import models

from apps.common.models import TimeStampedModel


class Region(models.Model):
    """Bundesland. Listă închisă, populată prin data migration."""

    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    code = models.CharField(max_length=2, unique=True, help_text="HH, SH, NI ...")

    class Meta:
        ordering = ("name",)
        verbose_name = "Bundesland"
        verbose_name_plural = "Bundesländer"

    def __str__(self) -> str:
        return self.name


class Locality(TimeStampedModel):
    """
    Localitate. NICIODATĂ text liber — text liber distruge filtrarea și SEO-ul
    pe „Reinigungskraft {oraș}". Se activează progresiv prin `is_active`.
    """

    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="localities")
    name = models.CharField(max_length=96)
    slug = models.SlugField(max_length=96, unique=True)
    postal_code = models.CharField(max_length=5, blank=True, help_text="PLZ principal")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=False, db_index=True)
    sort_order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ("sort_order", "name")
        constraints = [
            models.UniqueConstraint(fields=("region", "name"), name="uniq_locality_per_region"),
        ]
        verbose_name = "Localitate"
        verbose_name_plural = "Localități"

    def __str__(self) -> str:
        return f"{self.name} ({self.region.code})"
