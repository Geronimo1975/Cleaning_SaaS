"""URL-uri publice, în germană — sunt paginile pe care le caută un utilizator german."""

from django.urls import path

from . import views

app_name = "legal"

urlpatterns = [
    path("impressum/", views.ImpressumView.as_view(), name="impressum"),
    path("datenschutz/", views.DatenschutzView.as_view(), name="datenschutz"),
    path("agb/", views.AgbView.as_view(), name="agb"),
]
