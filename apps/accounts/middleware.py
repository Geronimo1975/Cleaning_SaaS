"""
Contul activ.

Un user poate administra mai multe conturi (o firmă și profilul personal), iar un
cont poate avea mai multe capabilități. De aceea dashboard-ul NU se ramifică pe
`user.role` — se ramifică pe capabilitățile CONTULUI ACTIV.
"""

from apps.accounts.models import Account, Membership

SESSION_KEY = "active_account_id"


class ActiveAccountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.account = None
        request.membership = None
        if request.user.is_authenticated:
            request.membership = self._resolve(request)
            if request.membership:
                request.account = request.membership.account
        return self.get_response(request)

    def _resolve(self, request):
        qs = Membership.objects.select_related("account").filter(user=request.user)
        account_id = request.session.get(SESSION_KEY)
        if account_id:
            m = qs.filter(account_id=account_id).first()
            if m:
                return m
            request.session.pop(SESSION_KEY, None)
        m = qs.order_by("created_at").first()
        if m:
            request.session[SESSION_KEY] = m.account_id
        return m


def switch_account(request, account: Account) -> bool:
    if Membership.objects.filter(user=request.user, account=account).exists():
        request.session[SESSION_KEY] = account.pk
        return True
    return False
