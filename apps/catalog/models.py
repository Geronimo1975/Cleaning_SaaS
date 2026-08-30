"""
Catalogul dealerilor.

Dealerul își postează produsele aici; site-ul le expune integral. NU e un
WooCommerce sincronizat — sursa de adevăr e această bază de date, iar paginile
publice se generează direct din ea.

Faza 0: modelele există, dar catalogul rămâne închis (`Product.is_published`
implicit False). Se deschide când există dealeri reali.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from apps.common.models import TimeStampedModel


class ProductCategory(TimeStampedModel):
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    sort_order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name_plural = "Categorii produse"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """
    Preț cu TVA separat de prețul net: clientul privat compară brut, firma compară
    net. Ambele trebuie afișabile fără recalcul în template.
    """

    seller = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, editable=False)
    sku = models.CharField(max_length=64, blank=True)
    ean = models.CharField(max_length=14, blank=True)
    brand = models.CharField(max_length=96, blank=True)
    description = models.TextField(blank=True)

    price_net = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("19.00"))
    unit = models.CharField(max_length=16, default="Stück")
    pack_size = models.CharField(max_length=32, blank=True, help_text="ex. 5 L, 12x750 ml")

    stock_quantity = models.IntegerField(default=0)
    min_order_quantity = models.PositiveSmallIntegerField(default=1)
    is_published = models.BooleanField(default=False, db_index=True)

    # Produse chimice: fișa de securitate e obligatorie (REACH / CLP).
    safety_datasheet = models.FileField(upload_to="sds/", blank=True)
    hazard_pictograms = models.CharField(max_length=120, blank=True, help_text="GHS02, GHS07 ...")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        indexes = [models.Index(fields=("is_published", "category"))]
        verbose_name = "Produs"
        verbose_name_plural = "Produse"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from apps.accounts.models import ReservedSlug

            self.slug = ReservedSlug.claim(f"{self.brand} {self.name}".strip())
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def price_gross(self) -> Decimal:
        return (self.price_net * (1 + self.vat_rate / 100)).quantize(Decimal("0.01"))


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/%Y/%m/")
    alt_text = models.CharField(max_length=160, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order",)
