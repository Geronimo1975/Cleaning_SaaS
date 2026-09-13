"""URL-uri publice, în germană — permanente, ca tot ce e indexabil."""

from django.urls import path

from . import views

app_name = "marketing"

urlpatterns = [
    path("", views.StartView.as_view(), name="start"),
    path("leistungen/", views.LeistungenView.as_view(), name="leistungen"),
    path("fuer-betriebe/", views.BetriebeView.as_view(), name="betriebe"),
    path(
        "fuer-reinigungskraefte/",
        views.ReinigungskraefteView.as_view(),
        name="reinigungskraefte",
    ),
    path("fuer-auftraggeber/", views.AuftraggeberView.as_view(), name="auftraggeber"),
    path("kontakt/", views.KontaktView.as_view(), name="kontakt"),
    path("blog/", views.BlogView.as_view(), name="blog"),
    path(
        "blog/reinigungsplan-vorlage/",
        views.ReinigungsplanVorlageView.as_view(),
        name="blog_reinigungsplan",
    ),
]
