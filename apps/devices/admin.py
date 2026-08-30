"""
Echipamente și telemetrie.

`token_hash` nu apare niciodată: cheia se compară pe hash tocmai ca o citire a
bazei să nu permită emiterea de telemetrie falsă. Un admin care ar afișa-o ar
anula măsura.
"""

from django.contrib import admin

from .models import Device, TelemetrySession


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "account", "site", "kind", "status", "is_online")
    list_filter = ("status", "kind")
    search_fields = ("account__display_name", "site__name")
    autocomplete_fields = ("account", "site")
    list_select_related = ("account", "site")
    exclude = ("token_hash",)

    @admin.display(boolean=True, description="Online")
    def is_online(self, obj):
        return obj.is_online


@admin.register(TelemetrySession)
class TelemetrySessionAdmin(admin.ModelAdmin):
    list_display = ("device", "started_at", "runtime_minutes", "area_sqm", "error_code", "shift")
    list_filter = ("error_code",)
    autocomplete_fields = ("device", "shift")
    list_select_related = ("device", "shift")
    date_hierarchy = "started_at"

    def has_add_permission(self, request):
        return False  # telemetria vine de la aparat, nu de la o persoană

    def has_change_permission(self, request, obj=None):
        return False
