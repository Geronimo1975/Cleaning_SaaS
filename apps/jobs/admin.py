"""
Anunțuri și coada de indexare.

Coada e cea care contează operațional: o notificare rămasă `FAILED` înseamnă
un anunț pe care Google nu îl știe publicat, sau — mai rău — unul expirat pe
care încă îl crede activ. Fără admin, eșecul era invizibil.
"""

from django.contrib import admin

from .models import Application, IndexingStatus, IndexingTask, JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = (
        "title", "account", "locality", "category", "employment_type",
        "status", "published_at", "valid_through", "views_count",
    )
    list_filter = ("status", "employment_type", "locality", "category")
    search_fields = ("title", "slug", "account__display_name")
    autocomplete_fields = ("account", "locality", "category")
    list_select_related = ("account", "locality", "category")
    readonly_fields = ("slug", "views_count", "created_at", "updated_at")
    date_hierarchy = "published_at"


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant_account", "job", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("applicant_account__display_name", "job__title")
    autocomplete_fields = ("job", "applicant_account")
    list_select_related = ("job", "applicant_account")
    date_hierarchy = "created_at"


@admin.register(IndexingTask)
class IndexingTaskAdmin(admin.ModelAdmin):
    list_display = ("url", "action", "status", "attempts", "last_error", "created_at", "sent_at")
    list_filter = ("status", "action")
    search_fields = ("url",)
    readonly_fields = ("url", "action", "attempts", "last_error", "created_at", "sent_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    @admin.action(description="Repune în coadă (resetează încercările)")
    def requeue(self, request, queryset):
        updated = queryset.update(
            status=IndexingStatus.PENDING, attempts=0, last_error="", sent_at=None
        )
        self.message_user(request, f"{updated} notificări repuse în coadă.")

    actions = ("requeue",)
