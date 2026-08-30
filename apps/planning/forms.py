from django import forms

from apps.accounts.forms import ScopedLeaf, active_localities

from .models import Site, Zone


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ["name", "locality", "street", "postal_code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["locality"].queryset = active_localities()


WEEKDAYS = [(1, "Lu"), (2, "Ma"), (3, "Mi"), (4, "Jo"), (5, "Vi"), (6, "Sâ")]


class ZoneForm(forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAYS, widget=forms.CheckboxSelectMultiple,
        initial=[1, 2, 3, 4, 5], label="Zile permise",
        help_text="Duminica nu e selectabilă (§9 ArbZG).",
    )

    class Meta:
        model = Zone
        fields = ["site", "name", "category", "description", "area_sqm",
                  "minutes_per_visit", "visits_per_week"]

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = ScopedLeaf.queryset()
        self.fields["site"].queryset = Site.objects.filter(account=account, is_active=True)
        if self.instance.pk:
            self.fields["weekdays"].initial = self.instance.weekdays

    def clean(self):
        data = super().clean()
        if data.get("weekdays"):
            self.instance.allowed_weekdays = ",".join(sorted(data["weekdays"]))
        return data
