"""
Comenzi, clienți, serii de numerotare. Operatorul corectează un prefix greșit
pe o serie; tot restul (starea comenzii, clienții) se face din dashboard.
"""

from django.contrib import admin

from .models import Customer, DocumentSequence, Order


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("account", "provider", "customer_number", "is_active")
    list_filter = ("is_active",)
    search_fields = ("account__display_name", "provider__display_name", "customer_number")
    autocomplete_fields = ("provider", "account")
    list_select_related = ("provider", "account")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "title", "provider", "customer", "site", "status",
                    "start_date")
    list_filter = ("status", "contract_kind")
    search_fields = ("order_number", "title", "provider__display_name")
    autocomplete_fields = ("provider", "customer", "site", "category")
    readonly_fields = ("order_number", "source_offer", "created_at")
    list_select_related = ("provider", "customer__account", "site")
    date_hierarchy = "start_date"


@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    list_display = ("provider", "document_type", "year", "prefix", "next_number")
    list_filter = ("document_type", "year")
    autocomplete_fields = ("provider",)
    list_select_related = ("provider",)
