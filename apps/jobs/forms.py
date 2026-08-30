from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import active_localities
from apps.accounts.models import User

from .models import Application, JobPosting


class ApplicationForm(forms.Form):
    """
    Formularul de aplicare ESTE formularul de înregistrare.

    Motivul e mecanismul din faza 0: anunțul aduce omul, aplicarea îi creează
    contul, contul devine profil public, directory-ul crește. Dacă aplicarea ar
    cere „creează-ți întâi cont", se pierde exact pasul care produce profiluri.
    """

    email = forms.EmailField(label=_("Email"))
    full_name = forms.CharField(max_length=128, label=_("Nume complet"))
    phone = forms.CharField(max_length=32, label=_("Telefon"))
    locality = forms.ModelChoiceField(queryset=active_localities(), label=_("Localitate"))
    message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}), required=False, label=_("Mesaj")
    )
    accept_terms = forms.BooleanField(label=_("Accept termenii și politica de confidențialitate"))
    # Consimțământ SEPARAT, niciodată inclus în T&C: publicarea profilului
    # înseamnă expunerea numelui unei persoane fizice într-un director indexat.
    publish_profile = forms.BooleanField(
        required=False,
        label=_("Vreau ca profilul meu să fie public și vizibil pentru beneficiari"),
    )

    def __init__(self, *args, job: JobPosting, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.job = job
        self.user = user if (user and user.is_authenticated) else None
        if self.user:
            del self.fields["email"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                _("Există deja un cont cu acest email. Autentifică-te pentru a aplica.")
            )
        return email

    def clean(self):
        data = super().clean()
        account = getattr(self, "_existing_account", None)
        if account and Application.objects.filter(
            job=self.job, applicant_account=account
        ).exists():
            raise forms.ValidationError(_("Ai aplicat deja la acest anunț."))
        return data


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ["title", "description", "requirements", "category", "locality",
                  "employment_type", "salary_min", "salary_max", "salary_unit",
                  "valid_through"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8}),
            "requirements": forms.Textarea(attrs={"rows": 4}),
            "valid_through": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.forms import ScopedLeaf

        self.fields["category"].queryset = ScopedLeaf.queryset()
        self.fields["locality"].queryset = active_localities()

    def clean(self):
        data = super().clean()
        lo, hi = data.get("salary_min"), data.get("salary_max")
        if lo and hi and lo > hi:
            self.add_error("salary_max", _("Maximul nu poate fi sub minim."))
        return data
