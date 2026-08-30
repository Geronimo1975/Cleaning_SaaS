# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Load the project skills first

`.claude/skills/` holds eight skills written specifically for this repo. They are the
authoritative convention source and override generic Django/marketplace/payroll advice.
Load them **before** reading or editing code:

| Order | Skill | When |
|---|---|---|
| 1 | `gebaeudereinigung-domain` | Always — product thesis, naming rules, industry vocabulary, which apps exist vs. don't |
| 2 | `cleaning-saas-codebase` | Always — the eight hard rules, verified `file:line` map, `references/` sub-documents |
| 3 | `gr-vermittlungsmodell` | Operating model: Genossenschaft of independent Betriebe + central Vermittlung |
| 3 | `gr-marktplatz-dispatch` | `apps/marketplace`, `/dashboard/cereri/`, `/dashboard/bursa/` |
| 3 | `gr-einsatzplanung` | `apps/planning` roster side, `/dashboard/planificare/`, Reinigungsplan export |
| 3 | `gr-zeiterfassung` | `apps/planning/attendance.py`, `/dashboard/pontaj/`, `apps/devices` |
| 3 | `gr-tarif-und-lohn` | `WageFloor`, `MinijobThreshold`, `compliance_issues`, wages anywhere |
| 3 | `gr-auftrag-und-faktura` | Customer/order/quote/invoice layer — **spec for code that does not exist yet** |

`SKILLS.md` (repo root) lists the relevant global skills and plugins.

## Commands

There is no `pip` inside the venv and no `requirements.txt`; the venv is pre-built.

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 8099 --noreload

.venv/bin/python -m pytest -q                                  # 324 tests
.venv/bin/python -m pytest tests/test_planning.py              # one file
.venv/bin/python -m pytest tests/test_planning.py::TestGenerateWeekPlan::test_x   # one test
.venv/bin/python -m pytest -k "minijob and not tour"           # by expression

.venv/bin/python manage.py flush_indexing --limit 100          # cron: Google Indexing queue
.venv/bin/python manage.py expire_requests --dry-run           # cron: close stale requests
```

- `pytest.ini` sets `--reuse-db`. After adding a migration, drop the cached test DB
  (`rm -f .pytest_cache/… ` is not enough — use `--create-db`).
- `pyproject.toml` configures ruff (`line-length = 100`, `py312`) but ruff is not in the venv.
  Run it through `uvx ruff check apps config tests --select E,F,I` — the wider default rule
  set flags ~250 issues that are mostly Django idiom (mutable class attributes on `ModelAdmin`),
  so keep the explicit `--select`.
- Python 3.12.13, Django 5.2.17 (`pyproject.toml` only pins `>=5.1,<6.0`).
- **Postgres is the default**, resolved through `dj_database_url.config()` with
  `CONN_MAX_AGE=600`. Without `DATABASE_URL`, it falls back to SQLite for local convenience —
  but CI and production both run Postgres, and so should anything you trust.
- Optional extras in `pyproject.toml`: `indexing` (google-auth, for the Indexing API),
  `export` (openpyxl, for the Reinigungsplan XLSX), `monitoring` (sentry-sdk). Missing extras
  degrade gracefully — they never stop the app from booting.
- The repo **is** under git. Author commits normally; the working tree is shared with other
  sessions, so run `git log --oneline -3` and `git status` before writing files.

## Architecture

Server-rendered Django. No API layer (except one device-ingestion endpoint in
`apps/devices/api.py`, authenticated by hashed device token), no JS build step. Templates live
only in `/templates/`, never per-app. `django_htmx` is installed but no template uses `hx-*` yet.

**The admin is for compliance, not for operations.** Every app has an `admin.py`, but the
division is deliberate: work that belongs to a user — posting a job, planning a week, awarding
an offer, signing a contract — happens in the dashboard, and you should never answer "change it
in the admin". The admin exists for the things a platform *operator* does and nothing else can:
reviewing `VerificationDocument`s (the files are private-storage, so `file` is readonly and
never in `list_display`), reading `ConsentRecord` and `ShiftEvent` journals (registered
read-only — an editable consent record is not evidence), updating `WageFloor` /
`MinijobThreshold` when the law changes, activating a `Locality` or `ServiceCategory`, and
re-queueing a failed `IndexingTask`. A signed `ContractDraft` becomes fully readonly and
undeletable; `Device.token_hash` is excluded from the form. `tests/test_admin.py` opens every
changelist and fails if a local model has neither an admin nor an explicit exemption.

### Identity: `User` authenticates, `Account` does everything else

`User` (`apps/accounts/models.py`) has no `username`, no name fields, no `role` — email login
only. Every economic fact hangs off `Account`, linked by `Membership`. `ActiveAccountMiddleware`
resolves one active account per request into `request.account` / `request.membership`.

Abilities are **rows** in `AccountCapability` (WORKER / PROVIDER / SUPPLIER / CLIENT / EMPLOYER),
never a column. `LegalStatus` (UNDECLARED / MINIJOB / SELBSTSTAENDIG / KLEINUNTERNEHMER /
COMPANY) is an orthogonal axis that decides who the legal payer is, who invoices, and whether
a contract can be generated at all. The dashboard is assembled from `apps/dashboard/panels.py`
— a data table keyed by capability — so a two-capability account sees the union of panels,
not a fifth hand-written dashboard.

Authorization = *(active account has capability X)* AND *(object belongs to active account)*,
via `apps/accounts/permissions.py`. Missing capability → 403. Foreign object → 404, never 403.

### Visibility: never pass an `Account` to a template

`apps/accounts/visibility.py` projects an account through `AccountView` for a specific viewer.
`FIELD_POLICY` maps each field to a minimum `Relation` (ANONYMOUS < AUTHENTICATED < ENGAGED <
SELF < STAFF). Contact data unlocks only at ENGAGED, which is earned by an `Application`, a
`ContractDraft` in SENT/SIGNED, or a **won** `Offer` — a merely submitted offer does not count,
or bidding would become an address-harvesting tool. **A new `Account` field is invisible until
you add it to `FIELD_POLICY`** (default is `Relation.SELF`).

### Legal constraints are dated rows, never constants

`contracts.WageFloor`, `contracts.MinijobThreshold` and `cooperative.DispatchPolicy` all follow
the same shape: `valid_from` / `valid_to` + a `current(on=...)` classmethod, seeded by data
migration. Always resolve against the **date the work happens** (`draft.start_date`, the shift
day), never `today`. Never hardcode a euro amount or a weight dictionary.

`ContractDraft.compliance_report()` returns `ComplianceIssue(code, message, blocking)` —
severity is a property of the finding, not inferred from text. The sector minimum wage blocks
an employment contract but only warns on a Werkvertrag. `send_for_signature()` refuses on any
blocking issue. `EngagementModel.TEMP_AGENCY` (AÜG) is permanently blocked in code until a
licence exists.

### Frozen documents and append-only journals

Anything with legal weight is written once and never mutated:

- `ContractDraft.rendered_body` + `body_sha256` — the template text is copied at generation;
  editing a `ContractTemplate` afterwards cannot rewrite signed contracts. `ContractSignature`
  signs the hash and raises on re-save.
- `ShiftEvent` — append-only pontaj journal (BAG 13.09.2022 / §16 ArbZG). A correction is a
  new `CORRECTED` event, never an overwrite.
- `ConsentRecord` — raises `RuntimeError` on update.
- `ServiceRequest.dispatch_policy` — the scoring weights are pinned at publication, so a later
  member vote cannot retroactively reorder a request that was already bid on.

### The cross-app pipeline

```
marketplace.ServiceRequest --publish--> Invitation (suggestion only)
        |                                   Offer --score_offers--> award
        |                                                             |
        |                          create_contract_from_offer --> contracts.ContractDraft
        |                                                             | (both sign)
        +-- activate_recurring_request --> planning.Site + Zone <------+
                                                  |
                     planning.services.generate_week_plan --> ShiftPlan + Shift
                                                  |
                     attendance.publish_plan / check_in / check_out --> ShiftEvent
                                                  |
                     calibration --> ZoneCalibration (proposed, never auto-applied)
                     devices telemetry --> discrepancy check (verification, not calibration)
```

Two seams carry the design load:

- **`create_contract_from_offer`** derives the contract from the winning offer's own numbers
  (`estimated_minutes × visits_per_month → hours_per_month`, `implied_hourly → hourly_wage`),
  so nobody retypes anything. `contract_type_for()` raises if `LegalStatus` is UNDECLARED.
- **`activate_recurring_request`** creates `Site`/`Zone` **in the winning provider's account**
  and refuses non-weekly frequencies, because `Zone` only counts visits per week. It
  deliberately does **not** create shifts — planning belongs to the member firm.

### The planner is a constrained greedy allocator, not an optimizer

`apps/planning/services.py`. If a visit cannot fit without breaking a rule it stays
**unallocated** and lands in `ShiftPlan.unmet_demand` with a per-worker reason. Hard
constraints: contracted-hours budget (a legal ceiling, not a preference), 8 h/day (§3 ArbZG),
11 h rest (§5 ArbZG), no Sunday (§9 ArbZG), worker must serve the site's locality. Capacity
comes **only** from SIGNED contracts — planning never creates employment relationships.

`Tour` is placed first and all-or-nothing: one worker, one day, consecutive stops. Travel time
between stops is working time and counts against the budget. A published plan is never silently
rewritten (`replace=True` required).

### No automatic dispatch — by design

`apps/marketplace` can *suggest* providers (`suggest_providers` → `Invitation`) but never
assigns work. Auto-allocating work to a natural person meets the §7 SGB IV
Scheinselbstständigkeit criteria and approaches Arbeitnehmerüberlassung, which requires a
Bundesagentur für Arbeit licence. Do not add auto-assignment. Likewise `generate_week_plan`
allocates only within one employer — cross-firm allocation would be AÜG.

### Public surface and SEO

URLs are permanent. `ReservedSlug.claim()` is a **single global namespace** shared by `Account`,
`JobPosting` and `catalog.Product`; a slug is claimed once and never reused, including after
depublication. Published objects are **never deleted** — they are depublished and their URL
answers **410 + `X-Robots-Tag: noindex`** (`apps/jobs/views.py`, `apps/accounts/views.py`).

`config/sitemaps.py` only lists URLs that return 200; `DirectorySitemap` generates the
city × category pages that actually rank. `apps/jobs/indexing.py` is a three-layer durable
queue (`enqueue` in-transaction / `flush` from cron / `_transport` the only Google-aware code)
so publishing never depends on an external API being up. Without
`GOOGLE_INDEXING_CREDENTIALS`, `enqueue` works and `flush` no-ops.

Job detail pages must stay readable without login or they fail Google for Jobs.

There is no root route: `GET /` returns **404**. `config/urls.py` mounts only `admin/`,
`sitemap.xml`, `robots.txt`, `accounts/` (allauth), `api/telemetry/`, `dashboard/`, `cont/`,
and the two public URLconfs.

### Telemetry verifies, it does not measure

`apps/devices`: token-authenticated `POST /api/telemetry/` (Bearer, hash-compared, no session —
a machine has no user). Vacuum runtime is **not** cleaning time; it is a lower bound and a
discrepancy signal. Calibration reads pontaj only, uses median + MAD (never the mean), needs a
dual threshold (≥15 % and ≥10 min), a minimum sample, and a cooldown — and always *proposes*.

## Language split — preserve it, do not "translate" either side

| Layer | Language |
|---|---|
| Public/indexable URL segments | German — `/jobs/`, `/job/<slug>/bewerben/`, `/reinigungskraft/`, `/profil/` |
| Dashboard URL segments | Romanian — `/dashboard/anunturi/`, `/contracte/`, `/obiective/`, `/planificare/`, `/turele-mele/`, `/pontaj/`, `/calibrare/`, `/cereri/`, `/bursa/` |
| Comments, docstrings, `verbose_name`, choice labels, test names | Romanian |
| Python identifiers, model/field names, URL `name=` | English |
| Seeded domain data, contract text, public copy, legal terms | German |

Sanctioned exception: a named German artefact keeps its name inside the dashboard —
`obiective/<pk>/reinigungsplan.xlsx`.

## Reference data is seeded by data migration only

`geo.Region`/`Locality`, `taxonomy.ServiceCategory`, `contracts.WageFloor`/`ContractTemplate`,
`cooperative.DispatchPolicy` — all populated by numbered data migrations
(`0002_seed_localities`, `0003_seed_categories`, `0002_seed_wage_floors`, …). Localities and
categories are always `PROTECT` FKs, never free text; free text destroys both filtering and the
"Reinigungskraft {city}" SEO surface. Taxonomy is max two levels and only leaves are selectable.

## Tests

`tests/` (19 files, 324 tests), pytest-django, fixtures in `tests/conftest.py` — real seeded
localities (`norderstedt`, `pinneberg`) and categories (`treppenhausreinigung`,
`haushaltshilfe`) fetched by slug, plus `employer` / `worker` / `client_account` /
`make_provider` / `signed_contract` / `make_offer` factories. Test names and docstrings are
Romanian. `tests/test_isolation.py` is the cross-account authorization contract;
`tests/test_visibility.py` guards `FIELD_POLICY`; `tests/test_queries.py` asserts that query
counts stay *constant* in N for the three list-shaped code paths that used to be N+1
(`find_discrepancies`, `utilisation`, `suggest_providers`) — it compares two sizes rather than
pinning a number, so a legitimate added `select_related` does not break it.

## Storage

`MEDIA_ROOT` is served directly by Nginx without passing through Django, so verification
documents (ID, Führungszeugnis) go to the separate `"private"` storage alias backed by
`PRIVATE_STORAGE_ROOT`, outside the served root, behind an ownership-checking view. The
`private` volume is deliberately *not* mounted into the Nginx container — if a
`location /private/` ever appears in `deploy/nginx.conf`, that is a security bug, not an
optimisation.

## Observability

Everything logs to stdout; containers have no log files. `django.db.backends` stays at
`WARNING` even when `LOG_LEVEL=DEBUG` — turn SQL on deliberately with `SQL_DEBUG=1` when you
are actually hunting an N+1. `django.request` is at `ERROR`: 4xx is noise, 5xx is an incident.
Sentry activates only with `SENTRY_DSN` set and the `monitoring` extra installed, always with
`send_default_pii=False` — an error report carrying provider phone numbers is a GDPR problem,
not a debugging aid.

`/healthz/` (`config/health.py`, routed before every public page so it answers even while the
§5 TMG publication gate is closed) checks the database *and* the age of the indexing queue.
That second check is the point: `flush_indexing` being dead for three weeks looks exactly like
a healthy site from the outside. Only the database decides the HTTP code (503); a stale queue
reports `degraded` on 200, because restarting the container does not fix it. Note for compose
healthchecks: reach it with the real `Host` header — `ALLOWED_HOSTS` rejects `127.0.0.1` and
you get a 400 that reads as "unhealthy".

## Shared model bases

`apps/common.TimeStampedModel` is applied to the 10 models that genuinely get edited over time
(`Site`, `Zone`, `Shift`, `WorkerProfile`, `CompanyProfile`, `WageFloor`, `MinijobThreshold`,
`Locality`, `ServiceCategory`, `ProductCategory`). It is deliberately **not** applied to
append-only journals (`ConsentRecord`, `ShiftEvent`, `ContractSignature`, `IndexingTask` —
their `save()` refuses updates, so an `updated_at` would be an invitation to break that), to
join tables (`AccountService`, `ServiceArea`, `TourStop`), or to models with their own clock
(`TelemetrySession`, `User`). `tests/test_common.py` pins both lists.
