"""
Admin pentru identitate și conformitate.

Două reguli care nu sunt negociabile aici:

1. Documentele de verificare NU se descarcă din admin. Fișierele stau într-un
   storage privat, fără `base_url` — orice încercare de a randa `file.url` ar
   arunca. Se afișează doar numele și metadatele; conținutul se vede printr-o
   vedere dedicată, care lasă urmă.
2. Consimțămintele sunt append-only. Adminul le arată, nu le modifică — un
   consimțământ editabil nu mai e o dovadă.
"""

from django.contrib import admin, messages
from django.utils import timezone

from .compliance import ConsentRecord, DocumentStatus, VerificationDocument
from .enums import VerificationLevel
from .models import Account, AccountCapability, Membership, ReservedSlug, User
from .profiles import AccountService, CompanyProfile, ServiceArea, WorkerProfile


class CapabilityInline(admin.TabularInline):
    model = AccountCapability
    extra = 0


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ("user",)


class ServiceInline(admin.TabularInline):
    model = AccountService
    extra = 0
    autocomplete_fields = ("category",)


class AreaInline(admin.TabularInline):
    model = ServiceArea
    extra = 0
    autocomplete_fields = ("locality",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "display_name", "entity_type", "legal_status", "locality",
        "status", "verification_level", "published_at",
    )
    list_filter = ("status", "entity_type", "legal_status", "verification_level")
    search_fields = ("display_name", "legal_name", "slug", "vat_id", "contact_email")
    autocomplete_fields = ("locality",)
    # Slug-ul nu se schimbă niciodată: link-uri externe și poziții în Google
    # depind de el. Nici din admin.
    readonly_fields = ("slug", "published_at", "unpublished_at", "created_at", "updated_at")
    inlines = (CapabilityInline, MembershipInline, ServiceInline, AreaInline)
    list_select_related = ("locality",)

    @admin.action(description="Depublică (410 + noindex, slug rezervat)")
    def unpublish(self, request, queryset):
        for account in queryset:
            account.unpublish()
        self.message_user(request, f"{queryset.count()} profiluri depublicate.")

    actions = ("unpublish",)


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    """
    Coada de verificare. `file` e readonly intenționat — vezi nota din capul
    modulului.
    """

    list_display = (
        "account", "doc_type", "status", "filename",
        "reviewed_by", "reviewed_at", "expires_at", "delete_after",
    )
    list_filter = ("status", "doc_type")
    search_fields = ("account__display_name", "account__slug")
    autocomplete_fields = ("account",)
    readonly_fields = ("file", "filename", "created_at", "reviewed_by", "reviewed_at")
    list_select_related = ("account", "reviewed_by")
    date_hierarchy = "created_at"

    @admin.display(description="Fișier")
    def filename(self, obj) -> str:
        return obj.file.name.rsplit("/", 1)[-1] if obj.file else "—"

    def has_add_permission(self, request):
        return False  # documentele se încarcă de către titularul contului

    @admin.action(description="Aprobă și ridică nivelul de verificare")
    def approve(self, request, queryset):
        count = 0
        for doc in queryset.select_related("account"):
            doc.status = DocumentStatus.APPROVED
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save(update_fields=["status", "reviewed_by", "reviewed_at"])
            account = doc.account
            if account.verification_level < VerificationLevel.DOCUMENTS:
                account.verification_level = VerificationLevel.DOCUMENTS
                account.save(update_fields=["verification_level", "updated_at"])
            count += 1
        self.message_user(request, f"{count} documente aprobate.", messages.SUCCESS)

    @admin.action(description="Respinge")
    def reject(self, request, queryset):
        updated = queryset.update(
            status=DocumentStatus.REJECTED, reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} documente respinse.", messages.WARNING)

    actions = ("approve", "reject")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    """Append-only: se citește, nu se scrie. Un consimțământ editabil nu e dovadă."""

    list_display = (
        "account", "consent_type", "granted", "policy_version", "ip_address", "created_at"
    )
    list_filter = ("consent_type", "granted", "policy_version")
    search_fields = ("account__display_name", "account__slug")
    list_select_related = ("account",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ("account", "years_experience", "availability", "has_own_transport")
    search_fields = ("account__display_name",)
    autocomplete_fields = ("account",)
    list_select_related = ("account",)


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("account", "employees_range", "has_liability_insurance", "insurance_valid_until")
    list_filter = ("has_liability_insurance",)
    search_fields = ("account__display_name",)
    autocomplete_fields = ("account",)
    list_select_related = ("account",)


@admin.register(ReservedSlug)
class ReservedSlugAdmin(admin.ModelAdmin):
    """Doar de citit: un slug eliberat înseamnă un URL care se poate refolosi."""

    list_display = ("slug", "created_at")
    search_fields = ("slug",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "account", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "account__display_name")
    autocomplete_fields = ("user", "account")
    list_select_related = ("user", "account")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    User face doar autentificare. Datele economice sunt pe Account — deci aici
    nu se editează nimic despre profil, doar starea contului de login.
    """

    list_display = ("email", "is_active", "is_staff", "date_joined", "last_login")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email",)
    readonly_fields = ("date_joined", "last_login", "password")
    ordering = ("-date_joined",)
