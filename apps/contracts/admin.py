"""
Admin pentru contracte.

Pragurile salariale și limita Minijob se schimbă anual — de asta sunt rânduri
cu valabilitate în timp, nu constante în cod, și de asta trebuie editabile de
aici. Fără admin, comentariul „se actualizează fără deploy" din model era fals.

Contractele semnate, în schimb, sunt readonly: `rendered_body` e textul înghețat
la generare, iar o editare din admin ar rescrie retroactiv ce a semnat cineva.
"""

from django.contrib import admin

from .models import (
    ContractDraft,
    ContractSignature,
    ContractTemplate,
    DraftStatus,
    MinijobThreshold,
    WageFloor,
)


@admin.register(WageFloor)
class WageFloorAdmin(admin.ModelAdmin):
    list_display = ("kind", "hourly_amount", "valid_from", "valid_to", "source_note")
    list_filter = ("kind",)


@admin.register(MinijobThreshold)
class MinijobThresholdAdmin(admin.ModelAdmin):
    list_display = ("monthly_limit", "valid_from", "valid_to", "source_note")


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ("contract_type", "version", "language", "title", "is_active", "created_at")
    list_filter = ("contract_type", "language", "is_active")


class SignatureInline(admin.TabularInline):
    model = ContractSignature
    extra = 0
    readonly_fields = (
        "account", "signer_name", "signed_at", "document_sha256", "ip_address", "user_agent"
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ContractDraft)
class ContractDraftAdmin(admin.ModelAdmin):
    list_display = (
        "worker", "employer", "contract_type", "status",
        "start_date", "hours_per_month", "hourly_wage", "monthly_gross",
    )
    list_filter = ("status", "contract_type")
    search_fields = ("worker__display_name", "employer__display_name")
    autocomplete_fields = ("worker", "employer", "workplace")
    list_select_related = ("worker", "employer")
    inlines = (SignatureInline,)
    date_hierarchy = "start_date"

    @admin.display(description="Brut lunar")
    def monthly_gross(self, obj):
        return f"{obj.monthly_gross} €"

    def get_readonly_fields(self, request, obj=None):
        """Un contract semnat nu se mai editează — nici măcar de un superuser."""
        base = ("rendered_body", "body_sha256", "created_at", "updated_at")
        if obj and obj.status == DraftStatus.SIGNED:
            return base + tuple(
                f.name for f in obj._meta.fields if f.name not in {"id"} and f.name not in base
            )
        return base

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.status == DraftStatus.SIGNED)
