"""
Cereri de serviciu, oferte, invitații.

Ofertele nu se editează din admin: scorul și departajarea sunt deterministe
pe baza valorilor depuse, iar o corecție manuală ar face rezultatul
neexplicabil față de prestatorii care au pierdut.
"""

from django.contrib import admin

from .models import Invitation, Offer, ServiceRequest


class OfferInline(admin.TabularInline):
    model = Offer
    extra = 0
    readonly_fields = ("provider", "status", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("__str__", "client", "category", "locality", "status", "created_at")
    list_filter = ("status", "category", "locality")
    search_fields = ("client__display_name",)
    autocomplete_fields = ("client", "category", "locality")
    list_select_related = ("client", "category", "locality")
    inlines = (OfferInline,)
    date_hierarchy = "created_at"


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("provider", "request", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("provider__display_name",)
    autocomplete_fields = ("provider", "request")
    list_select_related = ("provider", "request")

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("provider", "request", "created_at")
    search_fields = ("provider__display_name",)
    autocomplete_fields = ("provider", "request")
    list_select_related = ("provider", "request")
