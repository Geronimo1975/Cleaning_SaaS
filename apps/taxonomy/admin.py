"""
Taxonomia e tabel, nu enum: se adaugă categorii fără deploy. Slug-urile rămân
stabile pentru SEO, deci nu se editează.
"""

from django.contrib import admin

from .models import ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "name_de", "parent", "is_35a_eligible", "is_active", "sort_order")
    list_filter = ("is_active", "is_35a_eligible", "parent")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "name_de", "slug")
    list_select_related = ("parent",)
    readonly_fields = ("slug",)
