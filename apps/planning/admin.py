"""
Obiective, ture, pontaj.

`ShiftEvent` e jurnalul de pontaj: append-only prin `save()`, deci adminul îl
arată strict ca istoric. O corecție e un eveniment nou, niciodată o
suprascriere — altfel evidența timpului de lucru nu mai e verificabilă la un
control (§16 ArbZG).
"""

from django.contrib import admin

from .models import (
    Shift,
    ShiftEvent,
    ShiftPlan,
    Site,
    Zone,
    Tour,
    TourStop,
    ZoneCalibration,
)


class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 0
    autocomplete_fields = ("category",)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "locality", "postal_code", "is_active")
    list_filter = ("is_active", "locality")
    search_fields = ("name", "account__display_name")
    autocomplete_fields = ("account", "locality")
    list_select_related = ("account", "locality")
    inlines = (ZoneInline,)


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = (
        "name", "site", "category", "minutes_per_visit",
        "visits_per_week", "weekly_minutes", "is_active",
    )
    list_filter = ("is_active", "category")
    search_fields = ("name", "site__name")
    autocomplete_fields = ("site", "category")
    list_select_related = ("site", "category")


@admin.register(ShiftPlan)
class ShiftPlanAdmin(admin.ModelAdmin):
    list_display = ("account", "week_start", "status", "planned_minutes", "published_at")
    list_filter = ("status",)
    search_fields = ("account__display_name", "week_start")
    autocomplete_fields = ("account",)
    list_select_related = ("account",)
    date_hierarchy = "week_start"


class ShiftEventInline(admin.TabularInline):
    model = ShiftEvent
    extra = 0
    readonly_fields = ("kind", "actor", "payload", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = (
        "date", "start_time", "zone", "worker", "status",
        "duration_minutes", "actual_minutes", "variance_minutes",
    )
    list_filter = ("status", "date")
    search_fields = ("zone__name", "zone__site__name", "worker__display_name")
    autocomplete_fields = ("plan", "zone", "worker")
    list_select_related = ("zone__site", "worker", "plan")
    inlines = (ShiftEventInline,)
    date_hierarchy = "date"


@admin.register(ShiftEvent)
class ShiftEventAdmin(admin.ModelAdmin):
    """Jurnal. Se citește, nu se scrie — modelul refuză oricum orice update."""

    list_display = ("created_at", "shift", "kind", "actor")
    list_filter = ("kind",)
    list_select_related = ("shift__zone", "actor")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ZoneCalibration)
class ZoneCalibrationAdmin(admin.ModelAdmin):
    list_display = (
        "zone", "status", "current_minutes", "suggested_minutes",
        "median_minutes", "sample_size", "confidence", "decided_by", "decided_at",
    )
    list_filter = ("status", "confidence")
    autocomplete_fields = ("zone", "decided_by")
    list_select_related = ("zone__site", "decided_by")
    date_hierarchy = "created_at"


class TourStopInline(admin.TabularInline):
    model = TourStop
    extra = 0
    autocomplete_fields = ("zone",)
    ordering = ("position",)


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    """
    Rundele fixe: aceleași zone, în aceeași ordine, cu timpii de deplasare
    între ele. Ordinea opririlor e datele, nu o convenție de afișare — de asta
    `position` se editează aici, nu se recalculează.
    """

    list_display = ("name", "account", "visits_per_week", "allowed_weekdays")
    search_fields = ("name", "account__display_name")
    autocomplete_fields = ("account",)
    list_select_related = ("account",)
    inlines = (TourStopInline,)


@admin.register(TourStop)
class TourStopAdmin(admin.ModelAdmin):
    list_display = ("tour", "position", "zone", "travel_minutes")
    autocomplete_fields = ("tour", "zone")
    list_select_related = ("tour", "zone__site")
    ordering = ("tour", "position")
