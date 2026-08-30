from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("onboarding/", views.OnboardingView.as_view(), name="onboarding"),
    path("profil/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("profil/publicare/", views.PublishToggleView.as_view(), name="publish_toggle"),
    path("cont/<int:pk>/activeaza/", views.switch_account_view, name="switch"),
    path("documente/<int:pk>/", views.verification_document_view, name="document"),
]
