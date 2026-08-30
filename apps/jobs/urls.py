from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("jobs/", views.JobListView.as_view(), name="list"),
    path("jobs/<slug:city>/", views.JobListView.as_view(), name="list_city"),
    path("job/<slug:slug>/", views.JobDetailView.as_view(), name="detail"),
    path("job/<slug:slug>/bewerben/", views.apply_view, name="apply"),
]
