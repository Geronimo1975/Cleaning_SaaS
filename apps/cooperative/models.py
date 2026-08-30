"""
Stratul de guvernanță al cooperativei.

Platforma nu e proprietarul muncii, ci o Vermittlung între firme membre. Din asta
decurg două lucruri pe care codul trebuie să le exprime, nu doar discursul:

**Membrul e un Betrieb, nu o persoană cu mop.** O persoană fizică poate fi membru
doar dacă are statut de întreprinzător (Gewerbeanmeldung / Kleinunternehmer /
firmă). Altfel „membru" ar fi un eufemism pentru angajat, iar întreaga construcție
ar cădea în §7 SGB IV.

**Regulile de repartizare se votează, deci sunt date.** Ponderile după care se
ordonează ofertele erau un dicționar în cod — un vot al membrilor nu le putea
schimba fără un deploy. Aici devin rânduri datate, fiecare legată de hotărârea
care le-a adoptat, ca `contracts.WageFloor`.

Ce NU e aici: cotele sociale, taxa de intrare, comisionul platformei. Nu sunt
publicate de modelul după care ne ghidăm și nu se inventează.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Resolution(models.Model):
    """Hotărârea adunării generale care adoptă o regulă."""

    reference = models.CharField(max_length=64, unique=True, help_text="ex. Beschluss 2026-03")
    title = models.CharField(max_length=200)
    adopted_on = models.DateField()
    minutes_url = models.URLField(blank=True, help_text="Procesul-verbal")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-adopted_on",)
        verbose_name = "Hotărâre"
        verbose_name_plural = "Hotărâri"

    def __str__(self) -> str:
        return f"{self.reference} — {self.title}"


class MembershipStatus(models.TextChoices):
    APPLIED = "APPLIED", "Cerere depusă"
    ACTIVE = "ACTIVE", "Membru activ"
    SUSPENDED = "SUSPENDED", "Suspendat"
    RESIGNED = "RESIGNED", "Retras"


# Statutele juridice care pot deține o calitate de membru. Un Minijobber e
# angajatul cuiva, nu un Betrieb; un cont nedeclarat nu e nimic.
ELIGIBLE_LEGAL_STATUSES = {"SELBSTSTAENDIG", "KLEINUNTERNEHMER", "COMPANY"}


class CooperativeMembership(models.Model):
    """
    Calitatea de membru în cooperativă.

    ATENȚIE: nu are legătură cu `accounts.Membership`, care leagă un User de un
    Account. Numele seamănă, conceptele nu.
    """

    account = models.OneToOneField(
        "accounts.Account", on_delete=models.PROTECT, related_name="cooperative_membership"
    )
    member_number = models.CharField(max_length=16, unique=True)
    shares = models.PositiveSmallIntegerField(
        default=1, help_text="Cote sociale subscrise"
    )
    # Un membru, un vot — indiferent de cote — dacă statutul nu prevede altfel.
    voting_weight = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("1.00"))
    status = models.CharField(
        max_length=12, choices=MembershipStatus.choices, default=MembershipStatus.APPLIED
    )
    joined_on = models.DateField(null=True, blank=True)
    left_on = models.DateField(null=True, blank=True)
    admitted_by = models.ForeignKey(
        Resolution, null=True, blank=True, on_delete=models.SET_NULL, related_name="admissions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("member_number",)
        verbose_name = "Membru cooperativă"
        verbose_name_plural = "Membri cooperativă"

    def __str__(self) -> str:
        return f"{self.member_number} · {self.account.display_name}"

    @property
    def is_voting(self) -> bool:
        return self.status == MembershipStatus.ACTIVE

    def clean(self):
        if self.account_id and self.account.legal_status not in ELIGIBLE_LEGAL_STATUSES:
            raise ValidationError({
                "account": (
                    "Membru poate fi doar un Betrieb: Gewerbeanmeldung, "
                    "Kleinunternehmer sau firmă. "
                    f"Contul are statutul {self.account.get_legal_status_display()}."
                )
            })
        if self.left_on and self.joined_on and self.left_on < self.joined_on:
            raise ValidationError({"left_on": "Retragerea nu poate precede aderarea."})


DEFAULT_WEIGHTS = {
    "price": "0.30",
    "verification": "0.25",
    "experience": "0.20",
    "availability": "0.15",
    "proximity": "0.10",
}


class DispatchPolicy(models.Model):
    """
    Ponderile după care se ordonează ofertele — votate, datate, trasabile.

    Se rezolvă la publicarea cererii și se FIXEAZĂ pe ea. Altfel o schimbare de
    politică ar rescrie retroactiv clasamentul unei cereri deja publicate, iar
    prestatorul respins n-ar mai putea reconstitui de ce a pierdut.
    """

    name = models.CharField(max_length=96)
    weights = models.JSONField(default=dict)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    adopted_by = models.ForeignKey(
        Resolution, null=True, blank=True, on_delete=models.SET_NULL, related_name="policies"
    )
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-valid_from",)
        verbose_name = "Politică de repartizare"
        verbose_name_plural = "Politici de repartizare"

    def __str__(self) -> str:
        return f"{self.name} (de la {self.valid_from})"

    @classmethod
    def current(cls, on=None) -> "DispatchPolicy | None":
        on = on or timezone.localdate()
        # La aceeași `valid_from` câștigă rândul adăugat ultimul: o hotărâre nouă
        # care intră în vigoare în aceeași zi înlocuiește precedenta, nu se bate
        # cu ea pe o ordonare nedefinită.
        return cls.objects.filter(valid_from__lte=on).filter(
            models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=on)
        ).order_by("-valid_from", "-id").first()

    def as_weights(self) -> dict[str, Decimal]:
        return {key: Decimal(str(value)) for key, value in self.weights.items()}

    def clean(self):
        if set(self.weights) != set(DEFAULT_WEIGHTS):
            raise ValidationError({
                "weights": (
                    "Criteriile trebuie să fie exact: "
                    f"{', '.join(sorted(DEFAULT_WEIGHTS))}."
                )
            })
        total = sum(Decimal(str(v)) for v in self.weights.values())
        if total != Decimal("1"):
            raise ValidationError({"weights": f"Ponderile trebuie să însumeze 1,00 (acum {total})."})
