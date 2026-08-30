"""
Planificarea turelor.

Ideea centrală: orele din contract nu sunt o preferință, sunt un PLAFON LEGAL.
Un Minijob de 40 h/lună care primește 12 ore într-o săptămână nu e o problemă
de planificare — e o depășire a Geringfügigkeitsgrenze care transformă raportul
de muncă în unul asigurat obligatoriu. Planificatorul tratează bugetul de ore
ca pe o constrângere tare, nu ca pe un avertisment.

Al doilea set de constrângeri vine din Arbeitszeitgesetz: maximum 8 h pe zi
(§3), minimum 11 h de odihnă între ture (§5), duminica liberă (§9).
"""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Site(models.Model):
    """Obiectivul de curățat: o clădire, o reședință, un sediu."""

    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="sites"
    )
    name = models.CharField(max_length=160)
    locality = models.ForeignKey("geo.Locality", on_delete=models.PROTECT, related_name="sites")
    street = models.CharField(max_length=160, blank=True)
    postal_code = models.CharField(max_length=5, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Obiectiv"
        verbose_name_plural = "Obiective"

    def __str__(self) -> str:
        return self.name


class Zone(models.Model):
    """
    O suprafață cu propriul ritm de curățenie. Granularitatea la care se face
    planificarea — nu clădirea întreagă, ci „etajul 2, coridor + băi".
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(max_length=160)
    category = models.ForeignKey(
        "taxonomy.ServiceCategory", on_delete=models.PROTECT, related_name="zones"
    )
    description = models.CharField(
        max_length=300, blank=True,
        help_text="Instrucțiuni pentru lucrător — apar în Reinigungsplan și la check-in",
    )
    area_sqm = models.PositiveIntegerField(null=True, blank=True)
    minutes_per_visit = models.PositiveSmallIntegerField(
        help_text="Durata estimată a unei vizite"
    )
    visits_per_week = models.PositiveSmallIntegerField(default=1)
    # Zilele permise, ca listă de indici ISO (1=luni ... 7=duminică).
    allowed_weekdays = models.CharField(max_length=13, default="1,2,3,4,5")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("site", "name")
        verbose_name = "Zonă"
        verbose_name_plural = "Zone"

    def __str__(self) -> str:
        return f"{self.site.name} · {self.name}"

    @property
    def weekdays(self) -> list[int]:
        return [int(x) for x in self.allowed_weekdays.split(",") if x.strip()]

    @property
    def weekly_minutes(self) -> int:
        return self.minutes_per_visit * self.visits_per_week

    def clean(self):
        if not self.category.parent_id:
            raise ValidationError({"category": "Doar categoriile-frunză sunt selectabile."})
        bad = [d for d in self.weekdays if d < 1 or d > 7]
        if bad:
            raise ValidationError({"allowed_weekdays": "Zilele valide sunt 1–7."})


class Tour(models.Model):
    """
    O rundă: un singur lucrător, mai multe obiective, în ordine.

    Modelul per-obiectiv nu poate exprima asta — o `Zone` aparține unui singur
    `Site`, iar o tură arată spre o singură `Zone`. Treppenhausreinigung prin
    cinci blocuri într-o dimineață era, până acum, cinci ture independente care
    puteau ajunge la cinci oameni diferiți, în cinci momente ale zilei.

    Tura se planifică indivizibil: ori încape toată la un om, într-o zi, ori
    rămâne nealocată cu motiv. O rundă executată pe jumătate nu e o rundă.
    """

    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="tours"
    )
    name = models.CharField(max_length=160)
    allowed_weekdays = models.CharField(max_length=13, default="1,2,3,4,5")
    visits_per_week = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Rundă"
        verbose_name_plural = "Runde"

    def __str__(self) -> str:
        return self.name

    @property
    def weekdays(self) -> list[int]:
        return [int(x) for x in self.allowed_weekdays.split(",") if x.strip()]

    @property
    def total_minutes(self) -> int:
        """Lucru + deplasare. Timpul dintre obiective e timp de lucru."""
        return sum(
            stop.zone.minutes_per_visit + stop.travel_minutes
            for stop in self.stops.select_related("zone")
        )

    @property
    def localities(self) -> set[int]:
        return {stop.zone.site.locality_id for stop in self.stops.select_related("zone__site")}


class TourStop(models.Model):
    """
    O oprire din rundă. `travel_minutes` e deplasarea PÂNĂ la această oprire,
    zero la prima. Se numără ca timp de lucru — drumul dintre două obiective în
    timpul turei nu e drum spre serviciu.
    """

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="stops")
    zone = models.ForeignKey("Zone", on_delete=models.PROTECT, related_name="tour_stops")
    position = models.PositiveSmallIntegerField()
    travel_minutes = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("tour", "position")
        constraints = [
            models.UniqueConstraint(fields=("tour", "zone"), name="uniq_zone_per_tour"),
            models.UniqueConstraint(fields=("tour", "position"), name="uniq_position_per_tour"),
        ]
        verbose_name = "Oprire"
        verbose_name_plural = "Opriri"

    def __str__(self) -> str:
        return f"{self.tour.name} #{self.position} · {self.zone}"

    def clean(self):
        if self.zone_id and self.tour_id and self.zone.site.account_id != self.tour.account_id:
            raise ValidationError("Zona aparține altui cont decât runda.")


class PlanStatus(models.TextChoices):
    DRAFT = "DRAFT", "Ciornă"
    PUBLISHED = "PUBLISHED", "Publicat"
    ARCHIVED = "ARCHIVED", "Arhivat"


class ShiftPlan(models.Model):
    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="shift_plans"
    )
    week_start = models.DateField(help_text="Luni")
    status = models.CharField(max_length=12, choices=PlanStatus.choices, default=PlanStatus.DRAFT)
    # Ce nu a încăput: motivul, nu doar faptul.
    unmet_demand = models.JSONField(default=list, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-week_start",)
        constraints = [
            models.UniqueConstraint(fields=("account", "week_start"), name="uniq_plan_per_week"),
        ]
        verbose_name = "Plan săptămânal"
        verbose_name_plural = "Planuri săptămânale"

    def __str__(self) -> str:
        return f"{self.account} · săptămâna {self.week_start}"

    @property
    def week_end(self):
        return self.week_start + timedelta(days=6)

    @property
    def planned_minutes(self) -> int:
        return sum(s.duration_minutes for s in self.shifts.all())

    def clean(self):
        if self.week_start.isoweekday() != 1:
            raise ValidationError({"week_start": "Săptămâna începe luni."})


class ShiftStatus(models.TextChoices):
    PLANNED = "PLANNED", "Planificat"
    CONFIRMED = "CONFIRMED", "Confirmat"
    DECLINED = "DECLINED", "Refuzat"
    IN_PROGRESS = "IN_PROGRESS", "În desfășurare"
    DONE = "DONE", "Efectuat"
    MISSED = "MISSED", "Neefectuat"


class Shift(models.Model):
    plan = models.ForeignKey(ShiftPlan, on_delete=models.CASCADE, related_name="shifts")
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name="shifts")
    worker = models.ForeignKey(
        "accounts.Account", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="shifts",
    )
    date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField()

    # Apartenența la o rundă. `position` face ordinea vizibilă lucrătorului.
    tour = models.ForeignKey(
        Tour, null=True, blank=True, on_delete=models.SET_NULL, related_name="shifts"
    )
    position = models.PositiveSmallIntegerField(null=True, blank=True)
    travel_minutes = models.PositiveSmallIntegerField(
        default=0, help_text="Deplasare până la această oprire — timp de lucru"
    )

    status = models.CharField(
        max_length=12, choices=ShiftStatus.choices, default=ShiftStatus.PLANNED, db_index=True
    )
    # Evidența timpului de lucru nu e opțională: BAG 13.09.2022 (1 ABR 22/21)
    # + §3 Abs. 2 Nr. 1 ArbSchG obligă angajatorul să înregistreze TOT timpul
    # lucrat, nu doar orele suplimentare. Păstrare minimum 2 ani (§16 ArbZG).
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    actual_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    worker_note = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ("date", "start_time")
        indexes = [models.Index(fields=("plan", "worker", "date"))]
        verbose_name = "Tură"
        verbose_name_plural = "Ture"

    def __str__(self) -> str:
        return f"{self.date} {self.start_time} · {self.zone.name}"

    @property
    def hours(self) -> Decimal:
        return (Decimal(self.duration_minutes) / 60).quantize(Decimal("0.01"))

    @property
    def billable_minutes(self) -> int:
        """Timpul real dacă a fost pontat, altfel cel planificat."""
        return self.actual_minutes if self.actual_minutes is not None else self.duration_minutes

    @property
    def variance_minutes(self) -> int | None:
        """Diferența față de estimare. Baza pentru corectarea `minutes_per_visit`."""
        if self.actual_minutes is None:
            return None
        return self.actual_minutes - self.duration_minutes


class ShiftEvent(models.Model):
    """
    Jurnal append-only al pontajului. Înregistrarea timpului de lucru trebuie
    să fie verificabilă, deci evenimentele nu se modifică și nu se șterg —
    o corecție e un eveniment nou, nu o suprascriere.
    """

    class Kind(models.TextChoices):
        PUBLISHED = "PUBLISHED", "Plan publicat"
        CONFIRMED = "CONFIRMED", "Tură confirmată"
        DECLINED = "DECLINED", "Tură refuzată"
        CHECK_IN = "CHECK_IN", "Începere lucru"
        CHECK_OUT = "CHECK_OUT", "Încheiere lucru"
        CORRECTED = "CORRECTED", "Corecție de către angajator"
        MISSED = "MISSED", "Marcat neefectuat"

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="events")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    actor = models.ForeignKey(
        "accounts.Account", null=True, on_delete=models.SET_NULL, related_name="shift_events"
    )
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Eveniment tură"
        verbose_name_plural = "Evenimente tură"

    def save(self, *args, **kwargs):
        if self.pk:
            raise RuntimeError("Evenimentele de pontaj sunt imutabile.")
        super().save(*args, **kwargs)


class CalibrationStatus(models.TextChoices):
    PROPOSED = "PROPOSED", "Propusă"
    APPLIED = "APPLIED", "Aplicată"
    REJECTED = "REJECTED", "Respinsă"


class Confidence(models.TextChoices):
    LOW = "LOW", "Scăzută"
    MEDIUM = "MEDIUM", "Medie"
    HIGH = "HIGH", "Ridicată"


class ZoneCalibration(models.Model):
    """
    Propunere de corectare a estimării unei zone, calculată din pontaj.

    Se PROPUNE, nu se aplică. Motivul nu e prudență tehnică: `minutes_per_visit`
    e intrarea planificatorului, iar planificatorul produce obligații
    contractuale. O valoare care se mișcă singură face planul imprevizibil și
    ascunde exact semnalul interesant — că o zonă a început să dureze altfel.

    Istoricul rămâne: se vede cum a evoluat estimarea și pe ce date.
    """

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="calibrations")
    sample_size = models.PositiveSmallIntegerField()
    window_start = models.DateField()
    window_end = models.DateField()

    current_minutes = models.PositiveSmallIntegerField()
    suggested_minutes = models.PositiveSmallIntegerField()
    median_minutes = models.PositiveSmallIntegerField()
    dispersion_minutes = models.PositiveSmallIntegerField(
        help_text="Abaterea mediană absolută (MAD)"
    )
    confidence = models.CharField(max_length=8, choices=Confidence.choices)

    status = models.CharField(
        max_length=10, choices=CalibrationStatus.choices, default=CalibrationStatus.PROPOSED
    )
    decided_by = models.ForeignKey(
        "accounts.Account", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="calibration_decisions",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Calibrare zonă"
        verbose_name_plural = "Calibrări zone"
        constraints = [
            models.UniqueConstraint(
                fields=("zone",), condition=models.Q(status="PROPOSED"),
                name="uniq_open_calibration_per_zone",
            )
        ]

    def __str__(self) -> str:
        return f"{self.zone} · {self.current_minutes} → {self.suggested_minutes} min"

    @property
    def delta_minutes(self) -> int:
        return self.suggested_minutes - self.current_minutes

    @property
    def weekly_impact_minutes(self) -> int:
        """Cât se schimbă cererea săptămânală dacă propunerea e aplicată."""
        return self.delta_minutes * self.zone.visits_per_week
