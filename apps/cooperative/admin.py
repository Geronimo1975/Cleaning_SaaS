"""
Cooperativa: hotărâri, membri, politici de repartizare.

Adminul e locul unde adunarea generală devine efectivă: o hotărâre votată se
introduce aici ca `Resolution`, iar politica de ponderi o referă. De aceea
ponderile sunt editabile — dar `valid_from` nu se retează peste o cerere deja
publicată, pentru că politica se fixează pe cerere la publicare.
"""

from django.contrib import admin

from .models import CooperativeMembership, DispatchPolicy, Resolution


@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    list_display = ("reference", "title", "adopted_on", "minutes_url")
    search_fields = ("reference", "title")
    date_hierarchy = "adopted_on"


@admin.register(CooperativeMembership)
class CooperativeMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "member_number", "account", "status", "shares",
        "voting_weight", "joined_on", "left_on", "admitted_by",
    )
    list_filter = ("status",)
    search_fields = ("member_number", "account__display_name")
    autocomplete_fields = ("account", "admitted_by")
    list_select_related = ("account", "admitted_by")

    def save_model(self, request, obj, form, change):
        """
        `clean()` verifică eligibilitatea (doar un Betrieb poate fi membru).
        Adminul rulează validarea prin formular, dar o rulăm explicit ca
        salvarea programatică din admin să nu ocolească regula.
        """
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(DispatchPolicy)
class DispatchPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "valid_from", "valid_to", "adopted_by", "note")
    search_fields = ("name", "note")
    autocomplete_fields = ("adopted_by",)
    list_select_related = ("adopted_by",)
    date_hierarchy = "valid_from"
