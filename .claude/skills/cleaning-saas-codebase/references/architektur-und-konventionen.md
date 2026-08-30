# Architektur und Konventionen — Cleaning_SaaS

**Covers:** repository layout, the Account-vs-User decision, capabilities-as-rows, the
service-layer convention, the language split, settings inventory, exact dependency versions,
the migration graph, and the commands that work.
**Stand: 2026-08-29.**
**Sources:** the live tree at `/Users/Geronimo/Projects/Cleaning_SaaS` (every `file:line`
below was opened and confirmed on 2026-08-29), plus
`scratchpad/dossier/_verified-ground-truth.md` and `scratchpad/dossier/testing-config.md`.

---

## 1. Repository layout (Fakt)

```
/Users/Geronimo/Projects/Cleaning_SaaS
├── manage.py                 stock Django 5, unmodified
├── pyproject.toml            PEP 621 metadata + ruff config. NO [tool.pytest.ini_options]
├── pytest.ini                the ONLY pytest config
├── db.sqlite3                dev database
├── PLAN-FAZA-0.md            Romanian planning doc — STALE for geography (see §9)
├── prompt1.md                Romanian planning doc
├── apps/                     all Django apps, namespaced `apps.<name>`
├── config/                   settings, urls, sitemaps, wsgi, asgi
├── templates/                ALL templates live here, OUTSIDE the apps
├── static/                   EMPTY
└── tests/                    ALL tests live here, at the repo root, NO __init__.py
```

**Non-negotiable structural facts:**

- Templates live **outside** the apps, in the project-level `templates/` directory
  (`config/settings.py:57` — `"DIRS": [BASE_DIR / "templates"]`). `APP_DIRS` is also `True`
  (`:58`) but **no app has a `templates/` directory**. Do not create one.
- Tests live in `/tests/` at the repo root. There is no `apps/*/tests.py` and no
  `apps/*/tests/` package. `tests/` has **no `__init__.py`**.
- Dashboard templates live in `templates/dashboard/` regardless of which app owns the view.
- There is **no `admin.py` in the entire project** (verified: `find apps -name admin.py` →
  zero results), even though `django.contrib.admin` is in `INSTALLED_APPS`
  (`config/settings.py:14`) and `admin/` is routed (`config/urls.py:14`).

### Apps inventory

| App | `verbose_name` (`apps.py`) | What it owns | Public URLs? |
|---|---|---|---|
| `apps.accounts` | `Conturi` | `User`, `Account`, `Membership`, `AccountCapability`, `ReservedSlug`, `WorkerProfile`, `CompanyProfile`, `AccountService`, `ServiceArea`, `VerificationDocument`, `ConsentRecord`; middleware, permissions, visibility | yes (`public_urls.py`) |
| `apps.geo` | `Geografie` | `Region`, `Locality` | no |
| `apps.taxonomy` | `Taxonomie servicii` | `ServiceCategory` | no |
| `apps.jobs` | `Anunțuri` | `JobPosting`, `Application`, `IndexingTask`; indexing queue | yes (`urls.py`, mounted at root) |
| `apps.catalog` | `Catalog materiale` | `ProductCategory`, `Product`, `ProductImage` — **inert** | no |
| `apps.contracts` | `Contracte` | `WageFloor`, `MinijobThreshold`, `ContractTemplate`, `ContractDraft`, `ContractSignature` | no |
| `apps.planning` | `Planificare` | `Site`, `Zone`, `ShiftPlan`, `Shift`, `ShiftEvent`, `ZoneCalibration` | no |
| `apps.devices` | `Echipamente` | `Device`, `TelemetrySession`; `POST /api/telemetry/` | API only |
| `apps.marketplace` | `Bursă de servicii` | `ServiceRequest`, `Offer`, `Invitation` | no |
| `apps.dashboard` | `Dashboard` | `PANELS`, `METRICS`, `DashboardHomeView`, **the single route table for everything behind login** | no |

`apps/dashboard/` has **no models** — only `panels.py`, `views.py`, `urls.py` and an empty
`migrations/` package.

---

## 2. The Account-vs-User decision (Fakt)

`apps/accounts/models.py:40-65`:

```python
class User(AbstractUser):
    """
    User face DOAR autentificare. Fără `role`, fără date economice, fără profil.
    Tot ce e economic atârnă de Account.
    """
    username = None
    first_name = None
    last_name = None
    email = models.EmailField("Email", unique=True)
    USERNAME_FIELD = "email"
```

- `AUTH_USER_MODEL = "accounts.User"` (`config/settings.py:83`).
- Login is by email, no username: `ACCOUNT_LOGIN_METHODS = {"email"}` (`:99`).
- `User.accounts` is a **property**, not a relation: `Account.objects.filter(memberships__user=self)`
  (`models.py:63-65`).
- **`Account` has no `user` field.** The link is `Membership`
  (`models.py:202-226`, `related_name="memberships"`). Reach the user with
  `account.memberships.first().user`.

**Why:** the docstring at `models.py:41-44` and the rationale carried into the dossiers — a
later KYC account at a payment processor attaches to the legal entity, not to a login. One
human can administer a company account and a personal account from one login.

### `request.account` and `request.membership`

`apps/accounts/middleware.py:14-38` (`ActiveAccountMiddleware`, **last in `MIDDLEWARE`**,
`config/settings.py:49`):

- Sets `request.account = None` and `request.membership = None` on every request.
- For an authenticated user, resolves the membership from `request.session["active_account_id"]`
  (`SESSION_KEY`, `middleware.py:11`), falling back to the oldest membership by `created_at`
  and re-seeding the session key.
- Switch with `switch_account(request, account)` (`middleware.py:41-45`) — returns `False` if
  the user has no membership on that account.

**Convention:** inside a business view, read `request.account` for identity and
`request.membership` for the role in that account. Do not branch on `request.user`.

---

## 3. Capabilities as rows (Fakt)

`apps/accounts/enums.py:11-21`:

```python
class Capability(models.TextChoices):
    """
    Ce POATE FACE contul. Rânduri în AccountCapability, niciodată o coloană `role`.
    O firmă care e și prestator, și cumpărător de materiale primește două rânduri.
    """
    WORKER    = "WORKER",   "Prestator persoană fizică"
    PROVIDER  = "PROVIDER", "Prestator firmă"
    SUPPLIER  = "SUPPLIER", "Furnizor de materiale"
    CLIENT    = "CLIENT",   "Beneficiar"
    EMPLOYER  = "EMPLOYER", "Angajator (publică anunțuri)"
```

- Storage: `AccountCapability(account, kind, is_active)` with
  `UniqueConstraint(("account", "kind"), name="uniq_capability")` (`models.py:229-243`).
- API on `Account` (`models.py:143-160`): `has_capability(kind)`, `capability_set()`,
  `grant(kind)` (`update_or_create`, flips `is_active` back on), `revoke(kind)`,
  `is_provider` (WORKER or PROVIDER).
- `AccountQuerySet.providers()` (`models.py:75-76`) is a queryset **OR** over a join —
  always append `.distinct()` (as `apps/accounts/views.py:185` does).

**Trap (Fakt):** `revoke()` at `models.py:155-156` is
`self.capabilities.filter(kind=kind).update(is_active=False)` — a **soft flag**. The row
survives and still occupies the unique slot. Any query filtering on
`capabilities__kind=...` **must** also filter `capabilities__is_active=True`, exactly as
`with_capability()` does (`models.py:72-73`).

`DEFAULT_CAPABILITIES` for onboarding (`apps/accounts/services.py:85-90`):

| Onboarding `kind` | Granted capabilities | Resulting `entity_type` |
|---|---|---|
| `worker` | `WORKER`, `CLIENT` | `INDIVIDUAL` |
| `provider` | `PROVIDER`, `CLIENT`, `EMPLOYER` | `COMPANY` |
| `supplier` | `SUPPLIER`, `CLIENT` | `COMPANY` |
| `client` | `CLIENT` | `INDIVIDUAL` |

(`entity_type` derived in `OnboardingForm.clean`, `apps/accounts/forms.py:42-48`.)

---

## 4. The service-layer convention (Fakt)

Business operations that happen from more than one place live in a `services.py`, not in a
view. The rationale is stated verbatim at `apps/accounts/services.py:1-7`: account creation
happens from onboarding, from applying to a job, and (later) from portfolio import, and must
produce the same structure every time.

| Module | Entry points |
|---|---|
| `apps/accounts/services.py` | `create_account()` (`@transaction.atomic`, `:18-40`), `_ensure_profile()`, `record_consent()`, `publish_profile()`, `unpublish_profile()`, `DEFAULT_CAPABILITIES` |
| `apps/jobs/services.py` | `apply_to_job()` (`@transaction.atomic`, `:16-35`), `_resolve_account()` |
| `apps/jobs/indexing.py` | `enqueue()`, `flush()`, `_transport()`, `absolute_url()` |
| `apps/contracts/services.py` | `render_contract()`, `send_for_signature()`, `active_template()`, `sign_contract()` |
| `apps/planning/services.py` | `build_capacities()`, `generate_week_plan()` (`@transaction.atomic`), `capacity_report()` |
| `apps/planning/attendance.py` | `publish_plan()`, `confirm_shift()`, `decline_shift()`, `check_in()`, `check_out()`, `correct_minutes()`, `mark_missed()`, `time_records()` |
| `apps/planning/calibration.py` | `analyze_zone()`, `propose_calibrations()`, `apply_calibration()`, `reject_calibration()`, `pending_impact()` |
| `apps/planning/reinigungsplan.py` | `zone_rows()`, `build_workbook()`, `filename()` |
| `apps/devices/services.py` | `authenticate_device()`, `ingest_session()`, `match_shift()`, `find_discrepancies()`, `utilisation()` |
| `apps/marketplace/services.py` | `publish_request()`, `submit_offer()`, `withdraw_offer()`, `award_warnings()`, `award_offer()`, `contract_type_for()` (`:133`), `create_contract_from_offer()` (`:149`) — the marketplace→contracts seam that turns a won `Offer` into a `ContractDraft`, pinned by `tests/test_marketplace.py::TestContractSeam` — `cancel_request()`, `expire_requests()` |
| `apps/marketplace/scoring.py` | `score_offers()`, `suggest_providers()`, `ScoredOffer` |

**Convention:** services raise a domain exception (`ShiftError`, `TelemetryError`,
`MarketplaceError` — all `ValueError` subclasses) or return a **list of reasons**, never a
bare boolean. Views catch and turn them into `messages.error`.

**Known inconsistency (Fakt):** the job-posting publish/close transition is inline in a view
(`apps/jobs/dashboard_views.py:55-77`) with no `publish_posting()` service — inconsistent with
the convention the project states about itself.

---

## 5. The language split (Fakt — preserve exactly)

| Layer | Language | Evidence |
|---|---|---|
| Public/indexable URL segments | German | `apps/jobs/urls.py:8-11` (`jobs/`, `job/<slug>/`, `bewerben/`); `apps/accounts/public_urls.py:10-14` (`reinigungskraft/`, `profil/`) |
| Dashboard URL segments | Romanian | `apps/dashboard/urls.py:16-50` (`anunturi/`, `candidaturi/`, `contracte/`, `obiective/`, `planificare/`, `turele-mele/`, `pontaj/`, `calibrare/`, `echipamente/`, `discrepante/`, `cereri/`, `bursa/`) and `apps/accounts/urls.py:8-11` (`onboarding/`, `profil/`, `publicare/`, `activeaza/`) mounted at `cont/` |
| Comments, docstrings | Romanian | every module header |
| `verbose_name`, choice labels, `help_text` | Romanian | `models.py:125-126` `"Cont"/"Conturi"`; `JobStatus.DRAFT = "Ciornă"` |
| Python identifiers, class names, enum members, URL `name=` | English | `JobPosting`, `Capability.EMPLOYER`, `name="posting_publish"` |
| Seeded data, contract text, public copy, legal terms | German | `apps/taxonomy/migrations/0003_seed_categories.py`, `apps/contracts/migrations/0003_seed_templates.py` |

**Sanctioned exception:** a named German artefact keeps its German name even inside the
Romanian dashboard — `path("obiective/<int:pk>/reinigungsplan.xlsx", …)`
(`apps/dashboard/urls.py:34-35`) and the link text
`Reinigungsplan herunterladen (XLSX)` (`templates/dashboard/sites.html:7`). Apply the same rule
to `Arbeitsvertrag`, `Impressum`, `Stundennachweis` if you add them.

**Reality check (Fakt):** the rendered public UI is currently a German/Romanian **mixture**.
`LANGUAGE_CODE = "de"` and `USE_I18N = True` (`config/settings.py:107,109`) but there is **no
`LocaleMiddleware`, no `LOCALE_PATHS`, no `locale/` directory and no `.po` file**. Strings
wrapped in `gettext_lazy` that happen to exist in Django's own German catalogue get translated
(`_("Email")` renders `E-Mail-Adresse:`); everything else renders as the Romanian source
(`_("Nume complet")` → `Nume complet:`). Do **not** "fix" the Romanian source strings — add a
real `de` catalogue if this must be solved. See `bekannte-maengel.md` §M9.

---

## 6. Settings inventory — `config/settings.py` (134 lines, Fakt)

| Lines | Setting | Value / note |
|---|---|---|
| 6-7 | `BASE_DIR`, `load_dotenv(BASE_DIR / ".env")` | **no `.env` file exists**; all defaults apply |
| 9 | `SECRET_KEY` | `os.getenv("SECRET_KEY", "dev-only-not-a-secret")` |
| 10 | `DEBUG` | `os.getenv("DEBUG", "1") == "1"` → **True by default** |
| 11 | `ALLOWED_HOSTS` | default `"localhost,127.0.0.1,testserver"` — `testserver` is required by the test suite |
| 13-37 | `INSTALLED_APPS` | admin, auth, contenttypes, sessions, messages, staticfiles, **sites**, **sitemaps**; `allauth`, `allauth.account`, `django_htmx`; then the 10 local apps |
| 39-50 | `MIDDLEWARE` | security, sessions, common, csrf, auth, messages, clickjacking, `allauth.account.middleware.AccountMiddleware`, `django_htmx.middleware.HtmxMiddleware`, **`apps.accounts.middleware.ActiveAccountMiddleware` last** |
| 54-68 | `TEMPLATES` | `DIRS=[BASE_DIR/"templates"]`, `APP_DIRS=True`, context processors: debug, **request**, auth, messages. No custom context processor. |
| 72-81 | `DATABASES` | sqlite3 at `BASE_DIR/db.sqlite3`; if `DATABASE_URL` is set it imports `dj_database_url` — **not installed**, so that path raises `ModuleNotFoundError` |
| 83-87 | `AUTH_USER_MODEL`, `AUTHENTICATION_BACKENDS` | `accounts.User`; ModelBackend + allauth backend |
| 89-95 | `AUTH_PASSWORD_VALIDATORS` | includes `MinimumLengthValidator` with **`min_length: 10`** |
| 98-105 | allauth | `SITE_ID = 1`; `ACCOUNT_LOGIN_METHODS = {"email"}`; `ACCOUNT_SIGNUP_FIELDS = ["email*","password1*","password2*"]`; `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`; `ACCOUNT_UNIQUE_EMAIL = True`; `ACCOUNT_RATE_LIMITS = {"login_failed": "5/5m"}`; `LOGIN_REDIRECT_URL = "/dashboard/"`; `LOGOUT_REDIRECT_URL = "/"` (**which 404s**) |
| 107-110 | i18n/tz | `LANGUAGE_CODE = "de"`, `TIME_ZONE = "Europe/Berlin"`, `USE_I18N = True`, `USE_TZ = True` |
| 112-116 | static/media | `STATIC_URL = "static/"`, `STATIC_ROOT = BASE_DIR/"staticfiles"`, `STATICFILES_DIRS = [BASE_DIR/"static"]` (**empty dir**), `MEDIA_URL = "media/"`, `MEDIA_ROOT = BASE_DIR/"media"` |
| 118-119 | `PRIVATE_STORAGE_ROOT` | `BASE_DIR / "private"` — **declared and never used**. See `bekannte-maengel.md` §M1 |
| 121-122 | misc | `DEFAULT_AUTO_FIELD = BigAutoField`; `EMAIL_BACKEND = console` |
| 124-130 | production hardening | `if not DEBUG:` → `SECURE_SSL_REDIRECT`, secure cookies, HSTS 31536000 + subdomains + preload |
| 134 | `GOOGLE_INDEXING_CREDENTIALS` | `os.getenv(..., "")`. Empty = the indexing queue accumulates and `flush()` is a no-op. |

Settings that are **not** configured: `DEFAULT_FROM_EMAIL`, `LOCALE_PATHS`, `LOGGING`,
`CACHES`, `SESSION_ENGINE`, `STORAGES`, `CSRF_TRUSTED_ORIGINS`.

### Root URLconf — `config/urls.py` (Fakt)

```python
urlpatterns = [
    path("admin/", admin.site.urls),                                                # :14
    path("sitemap.xml", sitemap_index, {"sitemaps": SITEMAPS}, name="sitemap_index"),
    path("sitemap-<section>.xml", sitemap, {"sitemaps": SITEMAPS},
         name="django.contrib.sitemaps.views.sitemap"),                             # :16-21
    path("robots.txt", TemplateView.as_view(template_name="robots.txt",
         content_type="text/plain"), name="robots"),                                # :22-26
    path("accounts/", include("allauth.urls")),                                     # :27
    path("api/telemetry/", telemetry_ingest, name="telemetry_ingest"),              # :28
    path("dashboard/", include("apps.dashboard.urls")),                             # :29
    path("cont/", include("apps.accounts.urls")),                                   # :30
    path("", include("apps.jobs.urls")),                                            # :31
    path("", include("apps.accounts.public_urls")),                                 # :32
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    # :35-36
```

Two includes are mounted at the site **root** (`:31-32`). Adding a top-level route to
`apps/jobs/urls.py` claims a global prefix for the whole site — coordinate with
`reinigungskraft/` and `profil/` in `public_urls.py`.

`app_name` namespaces in use: `jobs`, `public`, `accounts`, `dashboard`.
`catalog` is referenced by `Product.get_absolute_url()` but **is not registered** — that call
raises `NoReverseMatch` today.

Live status codes, verified 2026-08-29 with `django.test.Client` against the dev DB:

| URL | Status |
|---|---|
| `/` | **404** |
| `/jobs/` · `/jobs/<any-slug>/` | 200 (an unknown city slug does **not** 404) |
| `/job/<slug>/` | 200 |
| `/reinigungskraft/` · `/reinigungskraft/<any>/` · `/reinigungskraft/<any>/<any>/` | 200 |
| `/profil/<published-slug>/` | 200 |
| `/profil/<unpublished-slug>/` | 410 + `X-Robots-Tag: noindex` |
| `/sitemap.xml` · `/sitemap-jobs.xml` · `/sitemap-profiles.xml` · `/sitemap-directory.xml` | 200 |
| `/robots.txt` | 200 `text/plain` |
| `/dashboard/` (anon) | 302 → `/accounts/login/?next=/dashboard/` |

---

## 7. Dependencies — exact versions (Fakt)

Python **3.12.13**, venv at `/Users/Geronimo/Projects/Cleaning_SaaS/.venv`.
Installed distributions, read from `.venv/lib/python3.12/site-packages` on 2026-08-29:

| Distribution | Version |
|---|---|
| `asgiref` | 3.12.1 |
| `django` | **5.2.17** |
| `django_allauth` | 65.19.1 |
| `django_htmx` | 1.29.0 |
| `et_xmlfile` | 2.0.0 |
| `factory_boy` | 3.3.3 (installed, **unused**) |
| `faker` | 40.37.0 (installed, **unused**) |
| `iniconfig` | 2.3.0 |
| `openpyxl` | 3.1.5 |
| `packaging` | 26.3 |
| `pillow` | 12.3.0 |
| `pluggy` | 1.6.0 |
| `pygments` | 2.21.0 |
| `pytest` | 9.1.1 |
| `pytest_django` | 4.14.0 |
| `python_dotenv` | 1.2.3 |
| `sqlparse` | 0.6.0 |

**Declared in `pyproject.toml` but NOT installed:** `psycopg[binary]>=3.2`.
**Imported by `config/settings.py:79` but not declared anywhere and not installed:**
`dj_database_url`.
**Optional extras, not installed:** `indexing = ["google-auth>=2.35", "requests>=2.32"]`,
`export = ["openpyxl>=3.1"]` — note `openpyxl` **is** installed despite being an extra, which
is why `tests/test_reinigungsplan.py` passes.
`pip` is **not available inside the venv** (`No module named pip`).

`[tool.ruff]`: `line-length = 100`, `target-version = "py312"`. Ruff itself is not installed.

`pyproject.toml` pins `django>=5.1,<6.0`; the actual runtime is 5.2.17 and migration headers say
`Generated by Django 5.2.17`. Do not "correct" those headers.

---

## 8. Migration graph (Fakt)

| App | Migrations | Depends on |
|---|---|---|
| `geo` | `0001_initial`, `0002_seed_localities` | `dependencies = []` |
| `taxonomy` | `0001_initial`, `0002_servicecategory_is_35a_eligible`, `0003_seed_categories` | `dependencies = []` |
| `accounts` | `0001_initial` | `auth.0012…`, `geo.0001`, `taxonomy.0001` |
| `jobs` | `0001_initial`, `0002_indexingtask` | `accounts.0001`, `geo.0001`, `taxonomy.0001` |
| `catalog` | `0001_initial` | `accounts.0001` |
| `contracts` | `0001_initial`, `0002_seed_wage_floors`, `0003_seed_templates`, `0004_fix_template_titles`, `0005_wage_floor_2026` | `accounts.0001`, **`geo.0002_seed_localities`** |
| `planning` | `0001_initial`, `0002_shift_actual_minutes_shift_checked_in_at_and_more`, `0003_zonecalibration`, `0004_zone_description` | `accounts.0001`, **`geo.0002_seed_localities`**, **`taxonomy.0003_seed_categories`** |
| `devices` | `0001_initial` | `accounts.0001`, **`planning.0003_zonecalibration`** |
| `marketplace` | `0001_initial` | `accounts.0001`, **`geo.0002_seed_localities`**, **`taxonomy.0003_seed_categories`** |
| `dashboard` | none (empty `migrations/` package) | — |

**Consequence:** four apps depend on the *data* migrations of `geo` and `taxonomy`, not just
their schema. Renaming or squashing `geo/0002` or `taxonomy/0003` breaks the migration graph of
half the project.

**Convention for new seed data:** a `RunPython(forwards, backwards)` migration with a
module-level constant list, `update_or_create(slug=…, defaults={…})` for idempotency,
`apps.get_model(...)` for historical models, and a `backwards` that deletes exactly the slugs
derived from the same constant. Never `bulk_create` reference data. Details and worked
examples in `contracts-referenzdaten-ui.md` §3.

---

## 9. Documents in the repo that are stale (Fakt)

`PLAN-FAZA-0.md` still describes the **Romanian** market: `County → Locality → District`,
Bucharest sectors, Cluj/Timișoara/Iași, and URLs `/curatenie/{localitate}/`. The implementation
pivoted to Germany: `Region → Locality` and `/reinigungskraft/{city}/`. Read the code, not the
plan, for geography. The plan's taxonomy section still matches the 24 leaves (translated).

---

## 10. Commands (Fakt, all confirmed 2026-08-29)

```bash
cd /Users/Geronimo/Projects/Cleaning_SaaS

.venv/bin/python manage.py check                    # System check identified no issues
.venv/bin/python manage.py showmigrations
.venv/bin/python manage.py migrate
.venv/bin/python -m pytest -q                       # 190 passed
.venv/bin/python -m pytest -q tests/test_seo.py     # one module
.venv/bin/python -m pytest -q --create-db           # after adding a seed migration
.venv/bin/python manage.py runserver 8099 --noreload
.venv/bin/python manage.py flush_indexing --limit 100
.venv/bin/python manage.py shell -c "…"             # the only way to edit reference data today
```

`.venv/bin/python` must be called directly or the venv activated first — `python` on `PATH` is
Homebrew's 3.12 without Django.

---

## Quellen

- `/Users/Geronimo/Projects/Cleaning_SaaS/config/settings.py`, `config/urls.py`,
  `config/sitemaps.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/manage.py`, `pyproject.toml`, `pytest.ini`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/*/apps.py`, `apps/*/models.py`,
  `apps/*/services.py`, `apps/*/urls.py`, `apps/*/migrations/0001_initial.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py`,
  `apps/accounts/enums.py`, `apps/accounts/middleware.py`, `apps/accounts/services.py`,
  `apps/accounts/forms.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/templates/`, `/tests/`
- `.venv/lib/python3.12/site-packages/*.dist-info` (version list)
- `scratchpad/dossier/_verified-ground-truth.md`
- `scratchpad/dossier/testing-config.md` (file map, "files that do NOT exist" list)
- `scratchpad/dossier/accounts.md` (conventions 1-15)
