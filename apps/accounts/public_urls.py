"""URL-uri publice, indexabile. Structura e definitivă — slug-urile nu se schimbă."""

from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    path("reinigungskraft/", views.ProviderListView.as_view(), name="providers"),
    path("reinigungskraft/<slug:city>/", views.ProviderListView.as_view(), name="providers_city"),
    path("reinigungskraft/<slug:city>/<slug:category>/",
         views.ProviderListView.as_view(), name="providers_city_category"),
    path("profil/<slug:slug>/", views.PublicProfileView.as_view(), name="profile"),
]
