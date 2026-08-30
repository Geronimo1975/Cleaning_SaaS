"""Catalogul dealerilor. Rămâne închis până există dealeri reali."""

from django.contrib import admin

from .models import Product, ProductCategory, ProductImage


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "sort_order")
    search_fields = ("name", "slug")
    list_select_related = ("parent",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "seller", "category", "brand", "price_net",
        "vat_rate", "stock_quantity", "is_published",
    )
    list_filter = ("is_published", "category", "brand")
    search_fields = ("name", "sku", "ean", "brand", "seller__display_name")
    autocomplete_fields = ("seller", "category")
    list_select_related = ("seller", "category")
    readonly_fields = ("slug", "created_at", "updated_at")
    inlines = (ProductImageInline,)
