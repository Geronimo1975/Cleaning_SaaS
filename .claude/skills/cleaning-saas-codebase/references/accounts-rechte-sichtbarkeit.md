# Accounts, Rechte, Sichtbarkeit — `apps.accounts`

**Covers:** `Account` / `Membership` / `AccountCapability`, `ActiveAccountMiddleware` and
`request.account`, the permission mixins and exactly which HTTP status each failure produces,
slug immutability and `ReservedSlug` as a global namespace, publish/unpublish and the
append-only `ConsentRecord`, and the `AccountView` / `FIELD_POLICY` visibility projection with
the `Relation` ordering and the correct template idiom.
**Stand: 2026-08-29.**
**Sources:** `apps/accounts/*.py`, `templates/accounts/*`, `tests/test_accounts.py`,
`tests/test_visibility.py`, `tests/test_isolation.py` — all opened and confirmed on 2026-08-29;
cross-checked against `scratchpad/dossier/accounts.md`.

---

## 1. Data model (Fakt)

`apps/accounts/models.py` ends with two star-imports **at the bottom** (`:246-247`):

```python
from .compliance import *   # noqa: E402,F401,F403
from .profiles import *     # noqa: E402,F401,F403
```

because `compliance.py` and `profiles.py` import `Account` from `models.py`. **Never move
these to the top.** For cross-app models inside `visibility.py`, use
`django.apps.apps.get_model(...)` instead — as `_is_engaged()` does (`visibility.py:90,98,108`).

### `Account` — `apps/accounts/models.py:79-177`

| Field | Type | Notes |
|---|---|---|
| `entity_type` | `CharField(16, choices=EntityType)` | `INDIVIDUAL` / `COMPANY`. Docstring says "imutabil după creare" — **nothing enforces it** |
| `legal_status` | `CharField(20, choices=LegalStatus, default=UNDECLARED)` | orthogonal to `Capability` |
| `display_name` | `CharField(128)` | |
| `slug` | `SlugField(140, unique=True, editable=False)` | claimed once, never changes |
| `legal_name`, `registration_number`, `vat_id`, `tax_number` | `CharField`, blank | `HRB`/`Gewerbeanmeldung`, `USt-IdNr.`, `Steuernummer` |
| `locality` | FK `geo.Locality`, `PROTECT`, nullable | `related_name="accounts"` |
| `street`, `postal_code`(**max 5**), `phone`, `contact_email`, `about`, `avatar` | | `postal_code` is German-PLZ-only |
| `status` | `CharField(16, choices=AccountStatus, default=DRAFT, db_index=True)` | |
| `verification_level` | `PositiveSmallIntegerField(choices=VerificationLevel, default=NONE)` | **never written by any code** |
| `published_at`, `unpublished_at`, `created_at`, `updated_at` | | |

`Meta`: `ordering = ("-created_at",)`, `verbose_name = "Cont"/"Conturi"`,
`indexes = [Index(("status", "entity_type"))]`.

### Enums — `apps/accounts/enums.py`

| Enum | Values (value, Romanian label) |
|---|---|
| `EntityType` | `INDIVIDUAL` "Persoană fizică", `COMPANY` "Firmă" |
| `Capability` | `WORKER`, `PROVIDER`, `SUPPLIER`, `CLIENT`, `EMPLOYER` |
| `LegalStatus` | `UNDECLARED` "Nedeclarat", `MINIJOB` "Minijob în gospodărie (§8a SGB IV)", `SELBSTSTAENDIG` "Selbstständig cu Gewerbeanmeldung", `KLEINUNTERNEHMER` "Kleinunternehmer (§19 UStG)", `COMPANY` "Firmă cu regim normal de TVA" |
| `AccountStatus` | `DRAFT`, `PENDING`, `PUBLISHED`, `SUSPENDED`, `UNPUBLISHED` |
| `VerificationLevel` (IntegerChoices) | `NONE=0`, `EMAIL=1`, `PHONE=2`, `DOCUMENTS=3` |
| `MembershipRole` | `OWNER`, `ADMIN`, `MEMBER` |

**Dead states (Fakt):** `AccountStatus.PENDING` and `SUSPENDED` are never assigned by any code.
The real machine is `DRAFT → PUBLISHED ⇄ UNPUBLISHED`. `MembershipRole.ADMIN` and `MEMBER` are
never assigned either — `create_account()` always makes an `OWNER`.

### `Membership` — `models.py:202-226`

`user` FK (CASCADE, `related_name="memberships"`), `account` FK (CASCADE,
`related_name="memberships"`), `role` (default `OWNER`), `created_at`.
`UniqueConstraint(("user","account"), name="uniq_membership")`.
`can_manage` property → role in `{OWNER, ADMIN}` — **no callers today**, like
`require_manage()` (`permissions.py:60-62`).

### `AccountCapability` — `models.py:229-243`

`account` FK, `kind`, `is_active` (default True), `created_at`.
`UniqueConstraint(("account","kind"), name="uniq_capability")`.

### Profiles — `apps/accounts/profiles.py`

| Model | Attaches to | Key fields |
|---|---|---|
| `WorkerProfile` (`:15-39`) | `OneToOne(Account)`, `related_name="worker_profile"` | `years_experience`, `availability`, `hourly_rate_min`, `has_own_transport`, `has_own_equipment`, `willing_to_travel_km` (default 15, **unused by any code**), `languages`, `bio`. `clean()` requires `entity_type == INDIVIDUAL` |
| `CompanyProfile` (`:42-65`) | `OneToOne(Account)`, `related_name="company_profile"` | `employees_range` (free text), `founded_year`, `website`, `has_liability_insurance`, `insurance_valid_until`, `hwk_registered` ("Înregistrat la HWK"). Comment at `:52-53`: building cleaning is **Anlage B1 HwO** — no Meisterpflicht, but Handwerkskammer registration |
| `AccountService` (`:68-83`) | FK `Account` `related_name="services"`, FK `taxonomy.ServiceCategory` `PROTECT` `related_name="accounts"` | `UniqueConstraint(("account","category"))`; `clean()` rejects non-leaf — **but `clean()` never runs**, see §7 |
| `ServiceArea` (`:86-97`) | FK `Account` `related_name="areas"`, FK `geo.Locality` `PROTECT` `related_name="accounts_serving"` | `UniqueConstraint(("account","locality"))` |

### Compliance — `apps/accounts/compliance.py`

`VerificationDocument` (`:22-41`): `account` FK `related_name="documents"`, `doc_type`
(`ID`, `POLIZEILICHES` = Führungszeugnis, `GEWERBE`, `HRB`, `INSURANCE`, `QUALIFICATION`),
`file = FileField(upload_to="verification/%Y/%m/")`, `status`, `reviewed_by`, `reviewed_at`,
`expires_at`, `delete_after` (`help_text="Retenție DSGVO"`).
Docstring: *"NICIODATĂ public. Storage privat, cu termen de retenție."*
**The docstring is a promise, not an implementation** — see `bekannte-maengel.md` §M1.
The model is also completely unwired: no form, no view, no URL, no service touches it.

`ConsentRecord` (`:51-70`): `account`, `consent_type` (`PROFILE_PUBLICATION`, `TERMS`,
`PRIVACY`, `MARKETING`), `policy_version`, `granted`, `ip_address`, `user_agent`, `created_at`.
`Meta.ordering = ("-created_at",)`.

```python
def save(self, *args, **kwargs):          # compliance.py:67-70
    if self.pk:
        raise RuntimeError("ConsentRecord este append-only.")
    super().save(*args, **kwargs)
```

Append-only: a withdrawal is a **new row with `granted=False`**, never an update.
DSGVO Art. 7(1) — you must be able to demonstrate consent as it was given, with its version.
Note the guard raises `RuntimeError`, not `ValidationError`, and `queryset.update()` bypasses
it entirely.

Only `TERMS` and `PROFILE_PUBLICATION` are ever recorded. `PRIVACY` and `MARKETING` are dead.

---

## 2. `ActiveAccountMiddleware` and `request.account` (Fakt)

`apps/accounts/middleware.py` — **whole file, 45 lines**, mounted **last** in `MIDDLEWARE`
(`config/settings.py:49`).

```python
SESSION_KEY = "active_account_id"

class ActiveAccountMiddleware:
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
```

Rules:

- `request.account` is `None` for anonymous users **and** for a logged-in user with no
  membership. Every FBV must handle both before calling `capability_set()`.
- Default active account = **oldest membership by `created_at`**.
- `switch_account(request, account) -> bool` (`:41-45`) verifies membership before writing the
  session key.
- Keep this middleware **last** — it needs `request.user` from `AuthenticationMiddleware`.

---

## 3. Permission mixins — exactly what each failure produces (Fakt)

`apps/accounts/permissions.py` — **whole file, 62 lines**. Module docstring (`:1-7`) states
Django's per-model permissions are deliberately unused because they attach to `User`; the right
here comes from the pair (active account has capability X) + (object belongs to active account).

| Mixin | Condition | Result |
|---|---|---|
| `AccountRequiredMixin(LoginRequiredMixin)` (`:14-20`) | not authenticated | **302** → `/accounts/login/?next=…` (from `LoginRequiredMixin`) |
| | authenticated, `request.account is None` | **302** → `accounts:onboarding` |
| `CapabilityRequiredMixin(AccountRequiredMixin)` (`:23-44`) | authenticated + account, `required_capability` not in `capability_set()` | **403** — `raise PermissionDenied("Contul activ nu are această capabilitate.")` |
| | `required_capability` falsy (`()`) | check skipped |
| `OwnedByAccountMixin` (`:47-57`) | object not owned by `request.account` | **404** — the queryset is filtered, so `get_object()` raises `Http404` |
| `require_manage(membership)` (`:60-62`) | membership missing or `role == MEMBER` | `PermissionDenied` — **no callers today** |

`required_capability` accepts a single string or a tuple meaning "any of":

```python
class SiteListView(CapabilityRequiredMixin, OwnedByAccountMixin, ListView):
    required_capability = (Capability.EMPLOYER, Capability.PROVIDER)   # planning/views.py:24
```

`OwnedByAccountMixin.account_field` defaults to `"account"`; override it, or override
`get_queryset()` entirely, when the FK path is different (`job__account=`, `plan__account=`,
`zone__site__account=`, `site__account=`).

**Why 404 and not 403 for a foreign object:** `tests/test_isolation.py:1-4` states it — a
foreign account must not even learn the URL exists. Tests:

| Test | Assertion |
|---|---|
| `test_strainul_nu_vede_candidatura` (`test_isolation.py:43`) | `/dashboard/candidaturi/<pk>/` → **404** |
| `test_strainul_nu_vede_contractul` (`:47`) | `/dashboard/contracte/<pk>/` → **404** |
| `test_strainul_nu_editeaza_anuntul` (`:51`) | `/dashboard/anunturi/<pk>/` → **404** |
| `test_capabilitatea_lipsa_da_403` (`:60`) | worker (no `EMPLOYER`) on `/dashboard/anunturi/` → **403** |
| `test_fara_cont_esti_trimis_la_onboarding` (`:69`) | user without account on `/dashboard/` → **302**, `"onboarding" in response.url` |

**Function-based views** do not get the mixins. The current shape is the `_guard()` helper at
`apps/devices/views.py:15-20`:

```python
def _guard(request):
    if request.account is None:
        return redirect("accounts:onboarding")
    if not ({Capability.EMPLOYER, Capability.PROVIDER} & request.account.capability_set()):
        raise PermissionDenied
    return None
```

used as `if (redirect_response := _guard(request)) is not None: return redirect_response`.
The older inline form is at `apps/planning/views.py:62-68`. Prefer the `_guard` shape.

**A panel is not a permission.** Hiding a `Panel` hides nothing — the URL still resolves.

---

## 4. Slug immutability and `ReservedSlug` (Fakt)

```python
# apps/accounts/models.py:132-140
def save(self, *args, **kwargs):
    # Slug-ul se generează O SINGURĂ DATĂ și nu se schimbă niciodată —
    # link-uri externe și poziții în Google depind de el.
    if not self.slug:
        self.slug = ReservedSlug.claim(self.display_name)
    super().save(*args, **kwargs)

def get_absolute_url(self) -> str:
    return reverse("public:profile", kwargs={"slug": self.slug})
```

```python
# apps/accounts/models.py:180-199
class ReservedSlug(models.Model):
    """Slug-urile nu se refolosesc niciodată, nici după depublicare."""
    slug = models.SlugField(max_length=140, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def claim(cls, source: str) -> str:
        from django.utils.text import slugify
        base = slugify(source)[:130] or "cont"
        candidate, i = base, 1
        while cls.objects.filter(slug=candidate).exists():
            i += 1
            candidate = f"{base}-{i}"
        cls.objects.create(slug=candidate)
        return candidate
```

Facts that follow:

1. **`ReservedSlug` is a global namespace across models.** `Account` (`models.py:136`),
   `JobPosting` (`apps/jobs/models.py:65-70`) and `catalog.Product`
   (`apps/catalog/models.py:79-84`) all claim from it. A new sluggable model must claim from it
   too, or it will create colliding public URLs.
2. **Truncation to 130 chars** while `JobPosting.slug` allows 200 — long German titles get a
   shorter slug than the column permits.
3. **`slugify()` strips German umlauts.** `slugify("Müller Gebäudereinigung")` →
   `mller-gebudereinigung`. No transliteration is configured. Existing slugs must **not** be
   "fixed".
4. **`claim()` writes its own row immediately** (`cls.objects.create`), outside any of the
   caller's rollback intent that does not wrap it in the same transaction.
5. The reserved row **survives** account deletion (there is no FK), which is what makes the
   "410 for a deleted account" branch work (`apps/accounts/views.py:154-156`).

Tests: `test_slugul_nu_se_schimba_la_redenumire` (`tests/test_accounts.py:17-22`),
`test_slugurile_nu_se_refolosesc` (`:24-31`).

---

## 5. Publish / unpublish, consent, and the 410 flow (Fakt)

### Services — `apps/accounts/services.py`

```python
POLICY_VERSION = "2026-09-01"                                    # :15

@transaction.atomic
def create_account(*, user, entity_type, display_name, capabilities,
                   locality=None, legal_status=LegalStatus.UNDECLARED, **extra) -> Account:
    account = Account.objects.create(...)                        # :29-35
    Membership.objects.create(user=user, account=account)        # :36
    for cap in capabilities: account.grant(cap)                  # :37-38
    _ensure_profile(account)                                     # :39
    return account

def publish_profile(account, request=None):                      # :72-76
    """Publicarea cere consimțământ explicit și separat — nu e inclusă în T&C."""
    record_consent(account, ConsentType.PROFILE_PUBLICATION, True, request)
    account.publish()
    return account

def unpublish_profile(account, request=None):                    # :79-82
    record_consent(account, ConsentType.PROFILE_PUBLICATION, False, request)
    account.unpublish()
    return account
```

- `_ensure_profile()` (`:43-51`) — `WorkerProfile` for `INDIVIDUAL`, `CompanyProfile`
  otherwise, via `get_or_create`. *"Un cont fără profil e o stare imposibil de reprezentat în
  dashboard."*
- `record_consent()` (`:54-62`) stores `policy_version`, `ip_address` (`_ip()` at `:65-69`
  takes the first hop of `HTTP_X_FORWARDED_FOR`) and `user_agent[:300]`. **Always pass
  `request`.**
- **Always create accounts through `create_account()`.** A bare `Account.objects.create()` in a
  view yields an account with no membership and no profile.
- Publication consent is **separate from T&C**, never bundled. The apply form carries it as its
  own non-required checkbox (`apps/jobs/forms.py:27-32`). Test:
  `tests/test_application_flow.py:35-45` asserts the consent set is exactly
  `{"TERMS", "PROFILE_PUBLICATION"}` and that without the checkbox the account stays `DRAFT`.

### `Account.publish()` / `unpublish()` — `models.py:163-173`

```python
def publish(self):
    self.status = AccountStatus.PUBLISHED
    self.published_at = timezone.now()
    self.unpublished_at = None
    self.save(update_fields=["status", "published_at", "unpublished_at", "updated_at"])

def unpublish(self):
    """Depublicare, nu ștergere: URL-ul răspunde 410 și slug-ul rămâne rezervat."""
    self.status = AccountStatus.UNPUBLISHED
    self.unpublished_at = timezone.now()
    self.save(update_fields=["status", "unpublished_at", "updated_at"])
```

### The 410 branches — `PublicProfileView.get()`, `apps/accounts/views.py:150-163`

```python
def get(self, request, *args, **kwargs):
    try:
        self.object = self.get_object()
    except Http404:
        # Slug rezervat dar fără cont: a existat și a fost șters. 410, nu 404.
        if ReservedSlug.objects.filter(slug=kwargs.get("slug")).exists():
            return HttpResponse(status=410)          # NO X-Robots-Tag here
        raise
    if self.object.status != AccountStatus.PUBLISHED:
        # Depublicat: 410 + noindex.
        response = render(request, "accounts/gone.html", status=410)
        response["X-Robots-Tag"] = "noindex"
        return response
    return self.render_to_response(self.get_context_data(object=self.object))
```

Three outcomes: **410 + noindex** (exists, not published) · **410 bare** (reserved slug, no row)
· **404** (never existed). The identical pattern is repeated for job postings at
`apps/jobs/views.py:39-50`. Tests: `tests/test_application_flow.py:58-64`,
`tests/test_seo.py:46-51`.

**Never `delete()` a published `Account`.** Deleting cascades to `Membership`,
`AccountCapability`, both profiles, `AccountService`, `ServiceArea`, `ConsentRecord` **and
`VerificationDocument`** — including the DSGVO consent evidence. `locality` and `category` FKs
are `PROTECT`, so localities and categories cannot be deleted while referenced.

---

## 6. Visibility — `AccountView` and `FIELD_POLICY` (Fakt)

`apps/accounts/visibility.py`. Module docstring (`:1-9`):

> *"Regula: NU expunem obiectul `Account` direct într-un template. Trecem întotdeauna prin
> `AccountView`, care decide câmp cu câmp ce vede un anumit privitor. Motivul e DSGVO: datele
> de contact ale unei persoane fizice sunt date personale, iar „publicat" nu înseamnă „vizibil
> pentru oricine"."*

### `Relation` — ordered IntEnum, compared with `>=` (`:20-27`)

| Value | Member | Meaning |
|---|---|---|
| 0 | `ANONYMOUS` | not logged in |
| 1 | `AUTHENTICATED` | logged in, no link to this account |
| 2 | `ENGAGED` | a real economic link exists |
| 3 | `SELF` | the viewer's own account |
| 4 | `STAFF` | platform operator (`user.is_staff`) |

**The ordering is the mechanism** — `AccountView.can()` is `self.relation >= required`. Do not
reorder, do not insert a member in the middle without re-reading every `FIELD_POLICY` row.

### `FIELD_POLICY` — `visibility.py:31-57` (complete, verbatim)

| Field | Minimum `Relation` | Rationale (from the inline comments) |
|---|---|---|
| `display_name` | `ANONYMOUS` | public, indexable by Google |
| `slug` | `ANONYMOUS` | |
| `entity_type` | `ANONYMOUS` | |
| `about` | `ANONYMOUS` | |
| `avatar` | `ANONYMOUS` | |
| `locality` | `ANONYMOUS` | |
| `verification_level` | `ANONYMOUS` | |
| `services` | `ANONYMOUS` | |
| `areas` | `ANONYMOUS` | |
| `legal_name` | `ANONYMOUS` | company data, public by law — Impressum, §5 TMG |
| `registration_number` | `ANONYMOUS` | idem |
| `vat_id` | `ANONYMOUS` | idem |
| `phone` | `ENGAGED` | contact: only once a relationship exists |
| `contact_email` | `ENGAGED` | idem |
| `street` | `ENGAGED` | idem |
| `postal_code` | `ENGAGED` | idem |
| `legal_status` | `SELF` | fiscal/legal: never to another account |
| `tax_number` | `SELF` | idem |
| `documents` | `SELF` | idem |
| `consents` | `SELF` | idem |
| `status` | `SELF` | idem |

Plus two module constants:

```python
INDIVIDUAL_HIDDEN = {"legal_name", "registration_number", "vat_id"}   # :60
ENGAGING_CONTRACT_STATUSES = ("SENT", "SIGNED")                        # :64
```

`INDIVIDUAL_HIDDEN` wins over everything: for an `INDIVIDUAL` account those three fields are
`False` for **every** relation, including `SELF` and `STAFF` (`visibility.py:127-134`).

**Fail-closed default:** `required = FIELD_POLICY.get(field, Relation.SELF)` (`:133`).
A field you add to `Account` is invisible everywhere until you add it here. Verified:
`AccountView(acc).zzz_unknown` → `None`.

### `resolve_relation()` and `_is_engaged()` — `:67-112`

```python
def resolve_relation(target, viewer_account=None, user=None) -> Relation:
    if user is not None and user.is_authenticated and user.is_staff:
        return Relation.STAFF
    if viewer_account is None:
        return Relation.AUTHENTICATED if (user and user.is_authenticated) else Relation.ANONYMOUS
    if viewer_account.pk == target.pk:
        return Relation.SELF
    if _is_engaged(target, viewer_account):
        return Relation.ENGAGED
    return Relation.AUTHENTICATED
```

`_is_engaged(a, b)` is the **single** engagement predicate. Three sources, in order
(`:88-112`, models fetched with `apps.get_model` to avoid circular imports):

1. `jobs.Application` in **either** direction between the two accounts (`:90-94`).
2. `contracts.ContractDraft` between them with `status in ("SENT", "SIGNED")` (`:98-102`) —
   a `DRAFT` contract is explicitly **not** a relationship: *"Un contract în ciornă nu e încă o
   relație — celălalt cont nu știe că există."* A worker invited directly, who never applied,
   still gets the employer's contact once the contract is out for signature.
3. `marketplace.Offer` with `status == "WON"` (`:108-112`). A **submitted** offer is
   deliberately not enough — *"altfel oricine ar putea oferta la o cerere doar ca să afle
   adresa clientului. Relația se ridică la atribuire."*

**When you add a new engagement source, add it here — nowhere else.**

### `AccountView` — `:115-147`

```python
class AccountView:
    def __init__(self, account, viewer_account=None, user=None):
        self.account = account
        self.relation = resolve_relation(account, viewer_account, user)

    def can(self, field: str) -> bool: ...
    def get(self, field: str, default=None): ...
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self.get(name)
    def as_dict(self) -> dict: ...
```

### Template idiom — the correct one and the two wrong ones (Fakt)

**Correct** (`templates/accounts/profile_public.html:10-11`):

```django
{% if view_.phone %}<p>Telefon: {{ view_.phone }}</p>
{% else %}<p><em>Datele de contact devin vizibile după o candidatură sau o comandă.</em></p>{% endif %}
```

A hidden field is `None`, which is falsy. The context key in `PublicProfileView` is **`view_`**
with a trailing underscore (`apps/accounts/views.py:167`) because `view` is already taken by
Django's `ContextMixin`.

**Wrong #1 — `{% if view_.can.phone %}` is ALWAYS FALSE.** The `AccountView` docstring at
`visibility.py:119-120` advertises it, but `can` is a *method taking an argument*; in a template
`view_.can` resolves to a bound method and `.phone` on it silently fails. Verified 2026-08-29:
`{% if v.can.display_name %}YES{% else %}NO{% endif %}` renders `NO`.

**Wrong #2 — printing a hidden field bare.** `{{ view_.phone }}` on a hidden field renders the
literal string `None`, not empty. Always guard with `{% if %}`.

**Wrong #3 — `{{ view_.services }}`** renders `accounts.AccountService.None` — `get()` returns
a `RelatedManager`, not a list. `as_dict()` has the same problem. Fetch related objects in the
view, as `PublicProfileView.get_context_data` does (`views.py:170-172`).

**Wrong #4 — a typo is silent.** `__getattr__` returns `None` for anything, so `view_.phne`
renders nothing and raises no error.

### Where `AccountView` is used (Fakt)

| Site | file:line | Relation typically |
|---|---|---|
| Public profile | `apps/accounts/views.py:167-169` | ANONYMOUS / AUTHENTICATED |
| Provider directory list | `apps/accounts/views.py:194-197` | one `AccountView` per row |
| Candidate detail (employer looking at an applicant) | `apps/jobs/dashboard_views.py:128-130` | **ENGAGED, not SELF** — the comment at `:126-127` is explicit: the employer sees contact data but not fiscal status or documents |
| Marketplace offer form (provider looking at a client) | `apps/marketplace/views.py:179-181` | AUTHENTICATED until the offer wins |

### Tests that pin this — `tests/test_visibility.py` (9 tests)

| Test | Asserts |
|---|---|
| `test_anonim_nu_vede_contactul_unei_persoane` (`:12`) | `relation == ANONYMOUS`; `display_name` visible; `phone is None`; `street is None` |
| `test_datele_de_firma_sunt_publice` (`:19`) | company `legal_name` visible anonymously |
| `test_persoana_fizica_nu_expune_campuri_de_firma` (`:23`) | `INDIVIDUAL_HIDDEN` beats `SELF` |
| `test_alt_cont_logat_nu_vede_contactul` (`:28`) | `relation == AUTHENTICATED`; `phone is None` |
| `test_candidatura_ridica_relatia_la_engaged` (`:33`) | one `Application` → `ENGAGED`, `phone` visible |
| `test_statutul_fiscal_ramane_privat_chiar_si_engaged` (`:39`) | `legal_status is None` at ENGAGED; `"MINIJOB"` at SELF |
| `test_contractul_semnat_ridica_relatia_la_engaged` (`:45`) | signed contract without any application → ENGAGED, `street` visible |
| `test_contractul_in_ciorna_nu_ridica_relatia` (`:54`) | `DRAFT` contract → `AUTHENTICATED`, `street is None` |
| `test_staff_vede_tot` (`:62`) | `is_staff` → `STAFF`, `legal_status` visible |

---

## 7. Views, forms and URLs (Fakt)

| View | file:line | Notes |
|---|---|---|
| `OnboardingView` | `views.py:25-49` | `LoginRequiredMixin` + `FormView`. Redirects to `dashboard:home` if an account already exists. Creates account, records `TERMS` consent, `switch_account()`, redirects to `accounts:profile_edit` |
| `ProfileEditView` | `views.py:52-113` | **One** edit URL. `get_form_class()` branches on `entity_type`; `post()` saves `AccountForm` + optional `CompanyIdentityForm` + the profile form, then `_sync_services` / `_sync_areas` |
| `PublicProfileView` | `views.py:138-174` | the 410 flow (§5); builds `view_`, `services`, `deductible_35a` |
| `ProviderListView` | `views.py:177-198` | `Account.objects.published().providers().select_related("locality").distinct()`; filters on `kwargs["city"]` / `kwargs["category"]` or the same GET params; `paginate_by = 24` (**no pagination UI in the template**) |
| `PublishToggleView` | `views.py:201-214` | POST-only by intent. `form_class = OnboardingForm  # neutilizat`. **No `template_name`** → a GET raises `ImproperlyConfigured` (verified) |
| `switch_account_view` | `views.py:217-221` | **undecorated function view**. An anonymous GET raises `TypeError` → 500 (verified). Nothing links to it |

`_sync_services` / `_sync_areas` (`views.py:116-135`) **delete all rows then `bulk_create`** —
which skips `save()` and `clean()`, so the "leaf categories only" rule is enforced solely by the
form queryset. A partial form submission wipes the account's services.

### URLs

`apps/accounts/urls.py` (`app_name = "accounts"`), mounted at `cont/`:

| Name | Path | Full URL |
|---|---|---|
| `onboarding` | `onboarding/` | `/cont/onboarding/` |
| `profile_edit` | `profil/` | `/cont/profil/` |
| `publish_toggle` | `profil/publicare/` | `/cont/profil/publicare/` |
| `switch` | `cont/<int:pk>/activeaza/` | `/cont/cont/<pk>/activeaza/` — note the **doubled `cont/`** |

`apps/accounts/public_urls.py` (`app_name = "public"`), mounted at the root.
Header comment: *"Structura e definitivă — slug-urile nu se schimbă."*

| Name | Path |
|---|---|
| `providers` | `/reinigungskraft/` |
| `providers_city` | `/reinigungskraft/<slug:city>/` |
| `providers_city_category` | `/reinigungskraft/<slug:city>/<slug:category>/` |
| `profile` | `/profil/<slug:slug>/` |

**None of these three directory routes validates its slug.** `/reinigungskraft/zzz/` → **200**
with an empty list (verified). See `bekannte-maengel.md` §M7.

### Forms — `apps/accounts/forms.py`

- `active_localities()` (`:12-13`) — `Locality.objects.filter(is_active=True).select_related("region")`
- `ScopedLeaf.queryset()` (`:20-23`) — `ServiceCategory.objects.exclude(parent=None).filter(is_active=True)`
- `leaf_categories()` (`:16-17`) — **dead code**, never called
- `OnboardingForm` (`:34-48`) — `kind` radio (`ACCOUNT_KINDS`, `:26-31`), `display_name`,
  `locality`, `phone`; `clean()` derives `entity_type`
- `AccountForm` (`:51-60`) — the shared `Account` fields
- `CompanyIdentityForm` (`:63-75`) — Impressum data (§5 TMG); restricts `legal_status` to
  `{KLEINUNTERNEHMER, COMPANY}`
- `WorkerProfileForm` (`:78-110`) — restricts `legal_status` to
  `{UNDECLARED, MINIJOB, SELBSTSTAENDIG, KLEINUNTERNEHMER}`; `services` / `areas`
  `ModelMultipleChoiceField`s narrowed in `__init__`
- `CompanyProfileForm` (`:113-137`) — `website = URLField(assume_scheme="https")`

---

## 8. Conventions checklist for this subsystem

1. Never add a `role` field to `User` or `Account`. New abilities = `Capability` members +
   `AccountCapability` rows + `PANELS` rows.
2. Never put economic data on `User`.
3. Never read `request.user` for authorization in a business view — use `request.account` and
   `request.membership`.
4. Entry check = `AccountRequiredMixin` / `CapabilityRequiredMixin`; queryset scoping =
   `OwnedByAccountMixin` or an explicit filter. Missing capability 403, foreign object 404.
5. Never hand an `Account` to a template — wrap in `AccountView`, context key `view_`.
6. A new `Account` field is private until it is in `FIELD_POLICY`; add company-only fields to
   `INDIVIDUAL_HIDDEN` too.
7. Never write a slug by hand; never regenerate one. `ReservedSlug.claim()` only.
8. Never delete a published account — depublicate (410 + noindex).
9. Every consent is a new `ConsentRecord`. Never `update()` one. Always pass `request`. Bump
   `POLICY_VERSION` (`services.py:15`) when the policy text changes.
10. Create accounts only through `create_account()`.
11. Filter every capability query on `is_active=True`; `.distinct()` after `providers()`.
12. Keep `ActiveAccountMiddleware` last in `MIDDLEWARE`.
13. Keep the `compliance`/`profiles` star-imports at the **bottom** of `models.py`; use
    `apps.get_model()` for cross-app models in `visibility.py`.

---

## Quellen

- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/enums.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/middleware.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/permissions.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/visibility.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/services.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/compliance.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/profiles.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/views.py`, `forms.py`, `urls.py`,
  `public_urls.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/jobs/dashboard_views.py:125-131`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/marketplace/views.py:179-181`
- `/Users/Geronimo/Projects/Cleaning_SaaS/templates/accounts/profile_public.html`,
  `provider_list.html`, `gone.html`
- `/Users/Geronimo/Projects/Cleaning_SaaS/tests/test_accounts.py`, `test_visibility.py`,
  `test_isolation.py`, `test_application_flow.py`
- `scratchpad/dossier/accounts.md` (rules R1–R22, gotchas, gaps)
- Runtime checks 2026-08-29: template `can.` idiom, `AccountView` unknown-field fallback,
  anonymous `switch_account_view`, `PublishToggleView` GET
