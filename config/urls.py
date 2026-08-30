from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import index as sitemap_index
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from .sitemaps import SITEMAPS

from apps.devices.api import ingest as telemetry_ingest

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap_index, {"sitemaps": SITEMAPS}, name="sitemap_index"),
    path(
        "sitemap-<section>.xml",
        sitemap,
        {"sitemaps": SITEMAPS},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
    path("accounts/", include("allauth.urls")),
    path("api/telemetry/", telemetry_ingest, name="telemetry_ingest"),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", include("apps.legal.urls")),
    path("cont/", include("apps.accounts.urls")),
    path("", include("apps.jobs.urls")),
    path("", include("apps.accounts.public_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
