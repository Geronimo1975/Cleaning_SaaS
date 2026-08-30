from django.core.exceptions import ValidationError
from django.db import models


class ServiceCategory(models.Model):
    """
    Adâncime maximă 2. Doar frunzele sunt selectabile.
    Vocabular comun între profil, anunț și — în v2 — cererea de serviciu.
    """

    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    name = models.CharField(max_length=128)
    name_de = models.CharField(max_length=128, blank=True, help_text="Denumire publică (DE)")
    slug = models.SlugField(max_length=128, unique=True)
    sort_order = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True, db_index=True)
    # §35a EStG: clientul privat deduce 20% din manoperă, max. 4.000 €/an, pentru
    # haushaltsnahe Dienstleistungen. Condiție: factură + plată bancară.
    # E cel mai puternic argument împotriva concurentului real (Schwarzarbeit),
    # deci trebuie să fie o proprietate a categoriei, nu text de marketing.
    is_35a_eligible = models.BooleanField(
        "Deductibil §35a EStG", default=False,
        help_text="Serviciu casnic deductibil de clientul privat",
    )

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name = "Categorie serviciu"
        verbose_name_plural = "Categorii servicii"

    def __str__(self) -> str:
        return self.name_de or self.name

    @property
    def is_leaf(self) -> bool:
        return self.parent_id is not None

    def clean(self) -> None:
        if self.parent and self.parent.parent_id is not None:
            raise ValidationError({"parent": "Taxonomia are maximum două niveluri."})
