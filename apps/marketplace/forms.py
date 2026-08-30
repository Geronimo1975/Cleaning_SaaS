from django import forms
from django.utils import timezone

from apps.accounts.forms import ScopedLeaf, active_localities
from apps.contracts.models import WageFloor

from .models import Offer, ServiceRequest


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ["title", "category", "locality", "postal_code", "area_sqm", "rooms",
                  "frequency", "earliest_start", "description", "has_pets",
                  "supplies_provided", "offers_close_at"]
        widgets = {
            "earliest_start": forms.DateInput(attrs={"type": "date"}),
            "offers_close_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }
        help_texts = {
            "area_sqm": "Obligatoriu — fără suprafață, ofertele nu sunt comparabile.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = ScopedLeaf.queryset()
        self.fields["locality"].queryset = active_localities()

    def clean_offers_close_at(self):
        value = self.cleaned_data["offers_close_at"]
        if value <= timezone.now():
            raise forms.ValidationError("Termenul trebuie să fie în viitor.")
        return value


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["price_per_visit", "estimated_minutes", "includes_supplies",
                  "earliest_start", "message"]
        widgets = {
            "earliest_start": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "price_per_visit": "Preț per vizită (€)",
            "estimated_minutes": "Durata estimată (minute)",
        }

    def clean(self):
        data = super().clean()
        minutes = data.get("estimated_minutes")
        price = data.get("price_per_visit")
        if minutes and price:
            hourly = price * 60 / minutes
            # Pragul NU se scrie în cod: se rezolvă din tabelul datat, la data la
            # care ar începe prestația. Un prestator independent își pune prețul
            # liber, dar sub pragul de ramură e aproape sigur o durată estimată greșit.
            start = data.get("earliest_start") or timezone.localdate()
            floor = WageFloor.current(WageFloor.Kind.GEBAEUDE, start)
            if floor and hourly < floor:
                self.add_error(
                    "price_per_visit",
                    f"Prețul implicit e {hourly:.2f} €/oră, sub pragul de ramură de "
                    f"{floor} € valabil la {start:%d.%m.%Y}. Verifică durata estimată.",
                )
        return data
