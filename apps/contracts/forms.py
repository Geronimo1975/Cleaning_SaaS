from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import active_localities

from .models import ContractDraft, ContractType


class ContractDraftForm(forms.ModelForm):
    class Meta:
        model = ContractDraft
        fields = ["contract_type", "start_date", "end_date", "hours_per_month",
                  "hourly_wage", "workplace", "probation_months", "vacation_days"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "hours_per_month": _("Ore pe lună"),
            "hourly_wage": _("Salariu orar brut (€)"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["workplace"].queryset = active_localities()
        self.fields["contract_type"].choices = ContractType.choices

    def clean(self):
        data = super().clean()
        # Verificările legale rulează pe o instanță ne-salvată: unitatea vede
        # problema în formular, nu după ce a creat contractul.
        if not self.errors:
            probe = ContractDraft(
                employer=self.instance.employer_id and self.instance.employer or None,
                **{k: v for k, v in data.items()},
            )
            probe.employer = self.instance.employer
            probe.worker = self.instance.worker
            self.compliance_issues = probe.compliance_issues()
        return data


class SignatureForm(forms.Form):
    signer_name = forms.CharField(max_length=160, label=_("Numele tău complet"))
    confirm = forms.BooleanField(
        label=_("Confirm că am citit contractul și îl semnez electronic")
    )
