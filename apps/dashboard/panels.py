"""
Dashboard-ul, definit ca date, nu ca patru template-uri paralele.

Un cont cu două capabilități (prestator + cumpărător de materiale) vede reuniunea
panourilor, nu un al cincilea dashboard scris de mână. Adăugarea unei capabilități
noi înseamnă un rând aici, nu un `if` într-un template.
"""

from dataclasses import dataclass

from apps.accounts.enums import Capability


@dataclass(frozen=True)
class Panel:
    key: str
    title: str
    description: str
    url_name: str
    capability: str
    icon: str = ""
    order: int = 100

    @property
    def url(self) -> str | None:
        """Panourile fără rută încă implementată se afișează, dar nu sunt linkuri."""
        if not self.url_name:
            return None
        from django.urls import NoReverseMatch, reverse

        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            return None


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    capability: str
    resolver: str  # numele metodei din DashboardContext


PANELS: list[Panel] = [
    # --- Beneficiar -------------------------------------------------
    Panel("requests", "Cererile mele", "Publică o nevoie și primește oferte",
          "dashboard:requests", Capability.CLIENT, order=10, icon="file"),
    Panel("providers", "Caută prestatori", "Filtrează după oraș și serviciu",
          "public:providers", Capability.CLIENT, order=20, icon="search"),
    Panel("orders", "Comenzi materiale", "Istoricul comenzilor din catalog",
          "", Capability.CLIENT, order=30, icon="box"),
    Panel("open_requests", "Bursa de cereri", "Cereri deschise pe zona și serviciile tale",
          "dashboard:open_requests", Capability.WORKER, order=12, icon="search"),
    Panel("open_requests_co", "Bursa de cereri", "Cereri deschise pe zona și serviciile tale",
          "dashboard:open_requests", Capability.PROVIDER, order=12, icon="search"),
    # --- Prestator (PF și firmă) ------------------------------------
    Panel("my_profile", "Profilul public", "Ce văd beneficiarii despre tine",
          "accounts:profile_edit", Capability.WORKER, order=10, icon="user"),
    Panel("my_shifts", "Turele mele", "Program, confirmare și pontaj",
          "dashboard:my_shifts", Capability.WORKER, order=15, icon="clock"),
    Panel("my_applications", "Contractele mele", "Contracte primite și semnate",
          "dashboard:contracts", Capability.WORKER, order=20, icon="file"),
    Panel("company_profile", "Profilul firmei", "Date publice, asigurare, servicii",
          "accounts:profile_edit", Capability.PROVIDER, order=10, icon="building"),
    Panel("team", "Echipa", "Utilizatorii care administrează contul",
          "", Capability.PROVIDER, order=40, icon="users"),
    Panel("customers", "Clienți", "Beneficiarii pentru care execuți comenzi",
          "dashboard:customers", Capability.PROVIDER, order=50, icon="users"),
    Panel("service_orders", "Comenzi", "Aufträge în execuție, suspendate, încheiate",
          "dashboard:orders", Capability.PROVIDER, order=52, icon="file"),
    Panel("customers_w", "Clienți", "Beneficiarii pentru care execuți comenzi",
          "dashboard:customers", Capability.WORKER, order=50, icon="users"),
    Panel("service_orders_w", "Comenzi", "Aufträge în execuție, suspendate, încheiate",
          "dashboard:orders", Capability.WORKER, order=52, icon="file"),
    Panel("sites", "Obiective și zone", "Ce se curăță, cât durează, cât de des",
          "dashboard:sites", Capability.EMPLOYER, order=30, icon="building"),
    Panel("tours", "Runde", "Un lucrător, mai multe obiective, în ordine",
          "dashboard:tours", Capability.EMPLOYER, order=31, icon="route"),
    Panel("planning", "Planificare săptămânală", "Ture generate în limita orelor contractate",
          "dashboard:planning", Capability.EMPLOYER, order=35, icon="calendar"),
    Panel("time_records", "Pontaj", "Evidența timpului de lucru (§16 ArbZG)",
          "dashboard:time_records", Capability.EMPLOYER, order=36, icon="clock"),
    Panel("calibration", "Calibrare estimări", "Ce spune pontajul despre duratele planificate",
          "dashboard:calibration", Capability.EMPLOYER, order=37, icon="gauge"),
    Panel("devices", "Echipamente", "Aspiratoare și mașini — utilizare și chei de acces",
          "dashboard:devices", Capability.EMPLOYER, order=38, icon="cpu"),
    Panel("discrepancies", "Verificare încrucișată", "Pontaj vs. funcționarea echipamentelor",
          "dashboard:discrepancies", Capability.EMPLOYER, order=39, icon="alert"),
    # --- Angajator --------------------------------------------------
    Panel("postings", "Anunțuri de angajare", "Creează, publică, închide",
          "dashboard:postings", Capability.EMPLOYER, order=10, icon="briefcase"),
    Panel("candidates", "Candidaturi primite", "Aplicările la anunțurile tale",
          "dashboard:candidates", Capability.EMPLOYER, order=20, icon="users"),
    # --- Furnizor materiale -----------------------------------------
    Panel("products", "Produsele mele", "Postează și actualizează catalogul",
          "", Capability.SUPPLIER, order=10, icon="box"),
    Panel("stock", "Stoc și prețuri", "Actualizare în masă",
          "", Capability.SUPPLIER, order=20, icon="box"),
]

METRICS: list[Metric] = [
    Metric("open_postings", "Anunțuri active", Capability.EMPLOYER, "open_postings"),
    Metric("new_applications", "Candidaturi noi", Capability.EMPLOYER, "new_applications"),
    Metric("profile_views", "Vizualizări profil", Capability.WORKER, "profile_views"),
    Metric("my_applications", "Aplicări trimise", Capability.WORKER, "my_applications"),
    Metric("published_products", "Produse publicate", Capability.SUPPLIER, "published_products"),
    Metric("contracted_hours", "Ore contractate / lună", Capability.EMPLOYER, "contracted_hours"),
]


def panels_for(capabilities: set[str]) -> list[Panel]:
    return sorted(
        (p for p in PANELS if p.capability in capabilities),
        key=lambda p: (p.order, p.title),
    )


def metrics_for(capabilities: set[str]) -> list[Metric]:
    return [m for m in METRICS if m.capability in capabilities]
