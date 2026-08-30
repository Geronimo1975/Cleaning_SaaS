"""
Sitemap-uri.

Regula unică: în sitemap intră DOAR ce răspunde 200. Un anunț expirat sau un
profil depublicat răspunde 410 — dacă rămâne în sitemap, Google raportează
eroare pe tot fișierul, iar pentru `JobPosting` asta afectează indexarea
anunțurilor valide.

Pentru anunțuri, sitemap-ul e plasa de siguranță, nu canalul principal:
Google recomandă Indexing API pentru `JobPosting` (indexare în ~2 zile în loc
de ~3 săptămâni).
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.geo.models import Locality
from apps.jobs.models import JobPosting, JobStatus
from apps.taxonomy.models import ServiceCategory


class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    limit = 5000

    def items(self):
        return (
            JobPosting.objects.filter(
                status=JobStatus.PUBLISHED, valid_through__gt=timezone.now()
            )
            .select_related("locality")
            .order_by("-published_at")
        )

    def lastmod(self, obj):
        return obj.updated_at


class ProfileSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    limit = 5000

    def items(self):
        return Account.objects.published().providers().distinct().order_by("-published_at")

    def lastmod(self, obj):
        return obj.updated_at


class DirectorySitemap(Sitemap):
    """
    Paginile de listare oraș × categorie — paginile pe care se caută efectiv
    („Reinigungskraft Norderstedt"). Doar localitățile active.
    """

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        cities = list(Locality.objects.filter(is_active=True).order_by("sort_order"))
        leaves = list(ServiceCategory.objects.filter(is_active=True, parent__isnull=False))
        urls = [("public:providers", {})]
        urls += [("public:providers_city", {"city": c.slug}) for c in cities]
        urls += [("jobs:list_city", {"city": c.slug}) for c in cities]
        urls += [
            ("public:providers_city_category", {"city": c.slug, "category": s.slug})
            for c in cities
            for s in leaves
        ]
        return urls

    def location(self, item):
        name, kwargs = item
        return reverse(name, kwargs=kwargs)


SITEMAPS = {
    "jobs": JobSitemap,
    "profiles": ProfileSitemap,
    "directory": DirectorySitemap,
}
