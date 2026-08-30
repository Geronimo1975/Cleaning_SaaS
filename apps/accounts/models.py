from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .enums import (
    AccountStatus,
    Capability,
    EntityType,
    LegalStatus,
    MembershipRole,
    VerificationLevel,
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, password, **extra):
        if not email:
            raise ValueError("Emailul este obligatoriu.")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create(email, password, **extra)


class User(AbstractUser):
    """
    User face DOAR autentificare. Fără `role`, fără date economice, fără profil.
    Tot ce e economic atârnă de Account.
    """

    username = None
    first_name = None
    last_name = None
    email = models.EmailField("Email", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Utilizator"
        verbose_name_plural = "Utilizatori"

    def __str__(self) -> str:
        return self.email

    @property
    def accounts(self):
        return Account.objects.filter(memberships__user=self)


class AccountQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=AccountStatus.PUBLISHED)

    def with_capability(self, kind):
        return self.filter(capabilities__kind=kind, capabilities__is_active=True)

    def providers(self):
        return self.with_capability(Capability.WORKER) | self.with_capability(Capability.PROVIDER)


class Account(models.Model):
    """
    Entitatea centrală. Profil, anunțuri, produse, iar mai târziu contul KYC la
    procesatorul de plăți — toate atârnă aici, nu de User.
    """

    entity_type = models.CharField(max_length=16, choices=EntityType.choices)
    legal_status = models.CharField(
        max_length=20, choices=LegalStatus.choices, default=LegalStatus.UNDECLARED
    )
    display_name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=140, unique=True, editable=False)

    legal_name = models.CharField(max_length=200, blank=True, help_text="Denumire în registru")
    registration_number = models.CharField(
        max_length=64, blank=True, help_text="HRB / Gewerbeanmeldung"
    )
    vat_id = models.CharField(max_length=20, blank=True, help_text="USt-IdNr. (DE...)")
    tax_number = models.CharField(max_length=32, blank=True, help_text="Steuernummer")

    locality = models.ForeignKey(
        "geo.Locality", null=True, blank=True, on_delete=models.PROTECT, related_name="accounts"
    )
    street = models.CharField(max_length=160, blank=True)
    postal_code = models.CharField(max_length=5, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    contact_email = models.EmailField(blank=True)
    about = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)

    status = models.CharField(
        max_length=16, choices=AccountStatus.choices, default=AccountStatus.DRAFT, db_index=True
    )
    verification_level = models.PositiveSmallIntegerField(
        choices=VerificationLevel.choices, default=VerificationLevel.NONE
    )
    published_at = models.DateTimeField(null=True, blank=True)
    unpublished_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Cont"
        verbose_name_plural = "Conturi"
        indexes = [models.Index(fields=("status", "entity_type"))]

    def __str__(self) -> str:
        return self.display_name

    def save(self, *args, **kwargs):
        # Slug-ul se generează O SINGURĂ DATĂ și nu se schimbă niciodată —
        # link-uri externe și poziții în Google depind de el.
        if not self.slug:
            self.slug = ReservedSlug.claim(self.display_name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("public:profile", kwargs={"slug": self.slug})

    # --- capabilities -------------------------------------------------
    def has_capability(self, kind) -> bool:
        return self.capabilities.filter(kind=kind, is_active=True).exists()

    def capability_set(self) -> set[str]:
        return set(self.capabilities.filter(is_active=True).values_list("kind", flat=True))

    def grant(self, kind):
        obj, _ = AccountCapability.objects.update_or_create(
            account=self, kind=kind, defaults={"is_active": True}
        )
        return obj

    def revoke(self, kind):
        self.capabilities.filter(kind=kind).update(is_active=False)

    @property
    def is_provider(self) -> bool:
        return bool(self.capability_set() & {Capability.WORKER, Capability.PROVIDER})

    # --- publicare ----------------------------------------------------
    def publish(self):
        self.status = AccountStatus.PUBLISHED
        self.published_at = timezone.now()
        self.unpublished_at = None
        self.save(update_fields=["status", "published_at", "unpublished_at", "updated_at"])

    def unpublish(self):
        """Depublicare, nu ștergere: URL-ul răspunde 410 și slug-ul rămâne rezervat."""
        self.status = AccountStatus.UNPUBLISHED
        self.unpublished_at = timezone.now()
        self.save(update_fields=["status", "unpublished_at", "updated_at"])

    def clean(self):
        if self.entity_type == EntityType.INDIVIDUAL and self.legal_status == LegalStatus.COMPANY:
            raise ValidationError({"legal_status": "O persoană fizică nu poate avea statut de firmă."})


class ReservedSlug(models.Model):
    """Slug-urile nu se refolosesc niciodată, nici după depublicare."""

    slug = models.SlugField(max_length=140, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def claim(cls, source: str) -> str:
        from django.utils.text import slugify

        base = slugify(source)[:130] or "cont"
        candidate, i = base, 1
        while cls.objects.filter(slug=candidate).exists():
            i += 1
            candidate = f"{base}-{i}"
        cls.objects.create(slug=candidate)
        return candidate

    def __str__(self) -> str:
        return self.slug


class Membership(models.Model):
    """Leagă un User de un Account. Un user poate administra mai multe conturi."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(
        max_length=16, choices=MembershipRole.choices, default=MembershipRole.OWNER
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "account"), name="uniq_membership"),
        ]
        verbose_name = "Membru cont"
        verbose_name_plural = "Membri cont"

    def __str__(self) -> str:
        return f"{self.user} @ {self.account} ({self.role})"

    @property
    def can_manage(self) -> bool:
        return self.role in {MembershipRole.OWNER, MembershipRole.ADMIN}


class AccountCapability(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="capabilities")
    kind = models.CharField(max_length=16, choices=Capability.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("account", "kind"), name="uniq_capability"),
        ]
        verbose_name = "Capabilitate"
        verbose_name_plural = "Capabilități"

    def __str__(self) -> str:
        return f"{self.account} · {self.kind}"


# Modelele din `compliance` și `profiles` trebuie importate ca Django să le
# înregistreze — dar ele importă `Account` de aici, deci importul poate sta doar
# la final. Explicit, nu prin `*`: un wildcard aduce în namespace și tot ce
# importă ele (`models`, `settings`, `ValidationError`), iar la o coliziune de
# nume ultimul import câștigă în tăcere.
from .compliance import (  # noqa: E402
    ConsentRecord,
    ConsentType,
    DocumentStatus,
    DocumentType,
    VerificationDocument,
)
from .profiles import (  # noqa: E402
    AccountService,
    Availability,
    CompanyProfile,
    ServiceArea,
    WorkerProfile,
)

__all__ = [
    "Account",
    "AccountCapability",
    "AccountService",
    "Availability",
    "CompanyProfile",
    "ConsentRecord",
    "ConsentType",
    "DocumentStatus",
    "DocumentType",
    "Membership",
    "ReservedSlug",
    "ServiceArea",
    "User",
    "VerificationDocument",
    "WorkerProfile",
]
