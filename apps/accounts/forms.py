from django import forms
from django.utils.translation import gettext_lazy as _

from apps.geo.models import Locality
from apps.taxonomy.models import ServiceCategory

from .enums import EntityType, LegalStatus
from .models import Account
from .profiles import CompanyProfile, WorkerProfile


def active_localities():
    return Locality.objects.filter(is_active=True).select_related("region")


def leaf_categories():
    return ScopedLeaf.queryset()


class ScopedLeaf:
    @staticmethod
    def queryset():
        return ServiceCategory.objects.exclude(parent=None).filter(is_active=True)


ACCOUNT_KINDS = [
    ("worker", _("Lucrez pe cont propriu (persoană fizică)")),
    ("provider", _("Reprezint o firmă de curățenie")),
    ("supplier", _("Vând materiale și produse de curățenie")),
    ("client", _("Caut servicii de curățenie")),
]


class OnboardingForm(forms.Form):
    """Un singur pas după înregistrare. Alegerea determină entity_type + capabilități."""

    kind = forms.ChoiceField(choices=ACCOUNT_KINDS, widget=forms.RadioSelect, label=_("Cine ești"))
    display_name = forms.CharField(max_length=128, label=_("Nume afișat"))
    locality = forms.ModelChoiceField(queryset=active_localities(), label=_("Localitate"))
    phone = forms.CharField(max_length=32, required=False, label=_("Telefon"))

    def clean(self):
        data = super().clean()
        kind = data.get("kind")
        data["entity_type"] = (
            EntityType.INDIVIDUAL if kind in {"worker", "client"} else EntityType.COMPANY
        )
        return data


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["display_name", "locality", "street", "postal_code", "phone",
                  "contact_email", "about", "avatar"]
        widgets = {"about": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["locality"].queryset = active_localities()


class CompanyIdentityForm(forms.ModelForm):
    """Datele de Impressum. Publice prin lege pentru firme (§5 TMG)."""

    class Meta:
        model = Account
        fields = ["legal_name", "registration_number", "vat_id", "tax_number", "legal_status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legal_status"].choices = [
            (v, l) for v, l in LegalStatus.choices
            if v in {LegalStatus.KLEINUNTERNEHMER, LegalStatus.COMPANY}
        ]


class WorkerProfileForm(forms.ModelForm):
    legal_status = forms.ChoiceField(
        label=_("Cum lucrezi"),
        choices=[(v, l) for v, l in LegalStatus.choices
                 if v in {LegalStatus.UNDECLARED, LegalStatus.MINIJOB,
                          LegalStatus.SELBSTSTAENDIG, LegalStatus.KLEINUNTERNEHMER}],
        help_text=_("Determină cine emite factura și dacă clientul poate deduce §35a."),
    )
    services = forms.ModelMultipleChoiceField(
        queryset=ServiceCategory.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple, label=_("Servicii oferite"),
    )
    areas = forms.ModelMultipleChoiceField(
        queryset=Locality.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple, label=_("Zone deservite"),
    )

    class Meta:
        model = WorkerProfile
        fields = ["years_experience", "availability", "hourly_rate_min",
                  "has_own_transport", "has_own_equipment", "willing_to_travel_km",
                  "languages", "bio"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["services"].queryset = ScopedLeaf.queryset()
        self.fields["areas"].queryset = active_localities()
        if self.instance.pk:
            acc = self.instance.account
            self.fields["legal_status"].initial = acc.legal_status
            self.fields["services"].initial = [s.category_id for s in acc.services.all()]
            self.fields["areas"].initial = [a.locality_id for a in acc.areas.all()]


class CompanyProfileForm(forms.ModelForm):
    website = forms.URLField(required=False, assume_scheme="https", label=_("Website"))
    services = forms.ModelMultipleChoiceField(
        queryset=ServiceCategory.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple, label=_("Servicii oferite"),
    )
    areas = forms.ModelMultipleChoiceField(
        queryset=Locality.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple, label=_("Zone deservite"),
    )

    class Meta:
        model = CompanyProfile
        fields = ["employees_range", "founded_year", "website",
                  "has_liability_insurance", "insurance_valid_until", "hwk_registered"]
        widgets = {"insurance_valid_until": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["services"].queryset = ScopedLeaf.queryset()
        self.fields["areas"].queryset = active_localities()
        if self.instance.pk:
            acc = self.instance.account
            self.fields["services"].initial = [s.category_id for s in acc.services.all()]
            self.fields["areas"].initial = [a.locality_id for a in acc.areas.all()]
