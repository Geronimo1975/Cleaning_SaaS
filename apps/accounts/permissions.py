"""
Autorizare.

Nu folosim permisiunile per-model din Django. Ele sunt legate de `User`, iar la
noi dreptul vine din pereche: (contul activ are capabilitatea X) + (obiectul
aparține contului activ). Două mixin-uri acoperă tot.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class AccountRequiredMixin(LoginRequiredMixin):
    """Cere un cont activ. Fără el, userul e trimis la onboarding."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.account is None:
            return redirect("accounts:onboarding")
        return super().dispatch(request, *args, **kwargs)


class CapabilityRequiredMixin(AccountRequiredMixin):
    """
    `required_capability` = una singură, sau un tuplu (oricare dintre ele).
    Refuzul e 403, nu redirect: un cont fără capabilitate nu trebuie să afle
    ce există la acel URL.
    """

    required_capability: str | tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.account is not None:
            self._check(request)
        return super().dispatch(request, *args, **kwargs)

    def _check(self, request):
        required = self.required_capability
        if not required:
            return
        if isinstance(required, str):
            required = (required,)
        if not (set(required) & request.account.capability_set()):
            raise PermissionDenied("Contul activ nu are această capabilitate.")


class OwnedByAccountMixin:
    """
    Restrânge queryset-ul la obiectele contului activ. Se aplică pe TOATE
    view-urile de editare — altfel un ID ghicit în URL expune datele altcuiva.
    """

    account_field = "account"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(**{self.account_field: self.request.account})


def require_manage(membership):
    if not membership or not membership.can_manage:
        raise PermissionDenied("Este nevoie de rol de proprietar sau administrator.")
