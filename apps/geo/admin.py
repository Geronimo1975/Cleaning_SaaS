"""
Localitățile sunt listă închisă, populată prin data migration. Adminul le
activează sau le dezactivează — `is_active` decide ce orașe apar în directory
și în sitemap. Adăugarea unui oraș nou nu are nevoie de deploy.
"""

from django.contrib import admin

from .models import Locality, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "code")
    search_fields = ("name", "code")


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "postal_code", "is_active", "sort_order")
    list_filter = ("is_active", "region")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "slug", "postal_code")
    list_select_related = ("region",)
    # Slug-ul e în URL-uri indexate (/reinigungskraft/{oraș}/) — nu se schimbă.
    readonly_fields = ("slug",)
