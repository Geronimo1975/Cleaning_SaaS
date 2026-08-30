from django import forms

from apps.planning.models import Site

from .models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["label", "kind", "manufacturer", "model_name", "serial_number",
                  "site", "status"]

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["site"].queryset = Site.objects.filter(account=account, is_active=True)
        self.fields["site"].required = False
