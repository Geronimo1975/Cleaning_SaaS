from django.db import models
from django.urls import reverse
from django.utils import timezone


class EmploymentType(models.TextChoices):
    FULL_TIME = "FULL_TIME", "Vollzeit"
    PART_TIME = "PART_TIME", "Teilzeit"
    MINIJOB = "MINIJOB", "Minijob"
    CONTRACTOR = "CONTRACTOR", "Selbstständig"
    TEMPORARY = "TEMPORARY", "Temporär"


class JobStatus(models.TextChoices):
    DRAFT = "DRAFT", "Ciornă"
    PUBLISHED = "PUBLISHED", "Publicat"
    CLOSED = "CLOSED", "Închis"
    EXPIRED = "EXPIRED", "Expirat"


class JobPosting(models.Model):
    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="job_postings"
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, editable=False)
    description = models.TextField(help_text="HTML permis restrâns")
    requirements = models.TextField(blank=True)

    category = models.ForeignKey(
        "taxonomy.ServiceCategory", on_delete=models.PROTECT, related_name="job_postings"
    )
    locality = models.ForeignKey(
        "geo.Locality", on_delete=models.PROTECT, related_name="job_postings"
    )
    employment_type = models.CharField(max_length=16, choices=EmploymentType.choices)

    salary_min = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default="EUR")
    salary_unit = models.CharField(
        max_length=8, choices=[("HOUR", "oră"), ("MONTH", "lună")], default="HOUR"
    )

    status = models.CharField(
        max_length=12, choices=JobStatus.choices, default=JobStatus.DRAFT, db_index=True
    )
    published_at = models.DateTimeField(null=True, blank=True)
    # Obligatoriu, nu opțional: Google penalizează anunțurile expirate lăsate live.
    valid_through = models.DateTimeField()
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-created_at")
        indexes = [models.Index(fields=("status", "locality", "category"))]
        verbose_name = "Anunț"
        verbose_name_plural = "Anunțuri"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from apps.accounts.models import ReservedSlug

            self.slug = ReservedSlug.claim(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("jobs:detail", kwargs={"slug": self.slug})

    @property
    def is_live(self) -> bool:
        return self.status == JobStatus.PUBLISHED and self.valid_through > timezone.now()


class ApplicationStatus(models.TextChoices):
    NEW = "NEW", "Nou"
    VIEWED = "VIEWED", "Văzut"
    SHORTLISTED = "SHORTLISTED", "Preselectat"
    REJECTED = "REJECTED", "Respins"
    HIRED = "HIRED", "Angajat"


class Application(models.Model):
    """
    Aplicarea e și mecanismul care creează contul + profilul public,
    și evenimentul care ridică relația la ENGAGED (vezi accounts.visibility).
    """

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name="applications")
    applicant_account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="applications"
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=12, choices=ApplicationStatus.choices, default=ApplicationStatus.NEW
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("job", "applicant_account"), name="uniq_application"),
        ]
        verbose_name = "Aplicare"
        verbose_name_plural = "Aplicări"


class IndexingAction(models.TextChoices):
    UPDATED = "URL_UPDATED", "Publicat / actualizat"
    DELETED = "URL_DELETED", "Eliminat"


class IndexingStatus(models.TextChoices):
    PENDING = "PENDING", "În așteptare"
    SENT = "SENT", "Trimis"
    FAILED = "FAILED", "Eșuat"


class IndexingTask(models.Model):
    """
    Coadă durabilă pentru Google Indexing API.

    De ce coadă și nu apel direct în view: publicarea unui anunț nu are voie să
    depindă de disponibilitatea unui API extern. Dacă Google e picat, anunțul se
    publică oricum, iar notificarea pleacă la următoarea golire a cozii.

    Google recomandă explicit Indexing API în locul sitemap-ului pentru
    `JobPosting` — diferența e între indexare în ~2 zile și în ~3 săptămâni.
    """

    url = models.URLField(max_length=500)
    action = models.CharField(max_length=12, choices=IndexingAction.choices)
    status = models.CharField(
        max_length=8, choices=IndexingStatus.choices, default=IndexingStatus.PENDING,
        db_index=True,
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [models.Index(fields=("status", "created_at"))]
        verbose_name = "Notificare de indexare"
        verbose_name_plural = "Notificări de indexare"

    def __str__(self) -> str:
        return f"{self.get_action_display()} · {self.url}"
