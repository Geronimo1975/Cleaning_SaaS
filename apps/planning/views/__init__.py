"""
Vederile de planificare, pe domenii.

Fișierul unic de 310 de linii crescuse prin adăugiri succesive — planificare,
pontaj, calibrare, export — fiecare cu propriul bloc de importuri la mijlocul
fișierului. Numele publice rămân aceleași: `apps.planning.views.X` funcționează
ca înainte, inclusiv în `dashboard/urls.py`.
"""

from .attendance import my_shifts_view, publish_plan_view, time_records_view
from .calibration import calibration_view
from .export import reinigungsplan_view
from .planning import planning_view
from .sites import SiteCreateView, SiteListView, ZoneCreateView

__all__ = [
    "SiteCreateView",
    "SiteListView",
    "ZoneCreateView",
    "calibration_view",
    "my_shifts_view",
    "planning_view",
    "publish_plan_view",
    "reinigungsplan_view",
    "time_records_view",
]
