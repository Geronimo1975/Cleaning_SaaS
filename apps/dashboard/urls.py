from django.urls import path

from apps.billing import views as billing_views
from apps.contracts import views as contract_views
from apps.devices import views as device_views
from apps.jobs import dashboard_views as job_views
from apps.marketplace import views as market_views
from apps.planning import tours as tour_views
from apps.planning import views as planning_views

from .views import DashboardHomeView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    # anunțuri
    path("anunturi/", job_views.PostingListView.as_view(), name="postings"),
    path("anunturi/nou/", job_views.PostingCreateView.as_view(), name="posting_create"),
    path("anunturi/<int:pk>/", job_views.PostingUpdateView.as_view(), name="posting_edit"),
    path("anunturi/<int:pk>/publicare/", job_views.PostingPublishView.as_view(),
         name="posting_publish"),
    # candidaturi
    path("candidaturi/", job_views.CandidateListView.as_view(), name="candidates"),
    path("candidaturi/<int:pk>/", job_views.CandidateDetailView.as_view(),
         name="candidate_detail"),
    # contracte
    path("contracte/", contract_views.ContractListView.as_view(), name="contracts"),
    path("contracte/din-candidatura/<int:application_pk>/", contract_views.contract_create,
         name="contract_create"),
    path("contracte/<int:pk>/", contract_views.ContractDetailView.as_view(),
         name="contract_detail"),
    # obiective și planificare
    path("obiective/", planning_views.SiteListView.as_view(), name="sites"),
    path("obiective/nou/", planning_views.SiteCreateView.as_view(), name="site_create"),
    path("obiective/<int:pk>/reinigungsplan.xlsx", planning_views.reinigungsplan_view,
         name="site_reinigungsplan"),
    path("obiective/zona-noua/", planning_views.ZoneCreateView.as_view(), name="zone_create"),
    path("runde/", tour_views.tours_view, name="tours"),
    path("runde/<int:pk>/", tour_views.tour_detail_view, name="tour_detail"),
    path("planificare/", planning_views.planning_view, name="planning"),
    path("planificare/<int:pk>/publicare/", planning_views.publish_plan_view,
         name="plan_publish"),
    path("turele-mele/", planning_views.my_shifts_view, name="my_shifts"),
    path("pontaj/", planning_views.time_records_view, name="time_records"),
    path("calibrare/", planning_views.calibration_view, name="calibration"),
    path("echipamente/", device_views.device_list_view, name="devices"),
    path("echipamente/discrepante/", device_views.discrepancies_view, name="discrepancies"),
    # bursă
    path("cereri/", market_views.MyRequestsView.as_view(), name="requests"),
    path("cereri/noua/", market_views.request_create_view, name="request_create"),
    path("cereri/<int:pk>/", market_views.request_detail_view, name="request_detail"),
    path("bursa/", market_views.OpenRequestsView.as_view(), name="open_requests"),
    path("bursa/<int:pk>/oferta/", market_views.offer_view, name="offer"),
    # --- Comenzi (stratul comercial) --------------------------------
    path("clienti/", billing_views.CustomerListView.as_view(), name="customers"),
    path("comenzi/", billing_views.OrderListView.as_view(), name="orders"),
    path("comenzi/<int:pk>/", billing_views.OrderDetailView.as_view(), name="order_detail"),
    path("comenzi/<int:pk>/stare/", billing_views.order_transition_view,
         name="order_transition"),
]
