"""
Navigația, disponibilă pe fiecare pagină.

Panourile erau calculate doar în vederea de pornire, deci orice altă pagină din
dashboard nu știa ce meniu să arate. Aici devin context global — aceeași sursă
unică (`panels.py`), filtrată pe capabilitățile contului activ.
"""

from .panels import panels_for


def navigation(request):
    account = getattr(request, "account", None)
    if account is None:
        return {"nav_groups": [], "nav_account": None}

    panels = [p for p in panels_for(account.capability_set()) if p.url]

    # Deduplicare pe URL: „Bursa de cereri" e înregistrată de două ori, o dată
    # pentru WORKER și o dată pentru PROVIDER. Un cont cu ambele n-are nevoie
    # să o vadă de două ori în meniu.
    seen, unique = set(), []
    for panel in panels:
        if panel.url in seen:
            continue
        seen.add(panel.url)
        unique.append(panel)

    return {
        "nav_panels": unique,
        "nav_account": account,
        "nav_other_accounts": request.user.accounts.exclude(pk=account.pk),
    }
