---
name: cleaning-saas-codebase
description: >
  Always load before reading or editing anything in /Users/Geronimo/Projects/Cleaning_SaaS —
  the Django 5.2 SaaS for the German Gebäudereinigung market (Hamburg / Schleswig-Holstein).
  Fires on apps/accounts, apps/jobs, apps/planning, apps/contracts, apps/marketplace,
  apps/devices, apps/geo, apps/taxonomy, apps/dashboard, config/ and tests/; on Account,
  AccountView, JobPosting, ShiftPlan, ContractDraft, WageFloor, ServiceRequest and the other
  models in those apps; on Reinigungskraft, Minijob, Einsatzplanung, Zeiterfassung,
  §35a EStG, ArbZG, AÜG, DSGVO; and on tasks like "add a dashboard page", "add a locality",
  "write a test", "fix the sitemap".
  Overrides generic Django advice: no admin.py, no app-level templates, no role column, a
  German-URL / Romanian-dashboard language split, and a mandatory AccountView projection.
  Skipping it produces code that leaks personal data, breaks indexed URLs, or violates the
  language convention.
metadata:
  author: Geronimo
  target: Cleaning_SaaS (Django 5.2, German Gebäudereinigung market)
  repo_root: /Users/Geronimo/Projects/Cleaning_SaaS
  sources: pland.app (crawled 2026-08-29, 237 pages) + repository code
---

# Cleaning_SaaS — the always-load skill for this repository

**Stand: 2026-08-29.** Every claim below was checked against the live tree, not against a
plan document. Where the repo and a dossier disagree, the repo wins — it is edited
concurrently. Re-verify a `file:line` before you rely on it.

Product framing (owner's words): "Lieferando/courier agency + PlanD" — (1) Marktplatz,
(2) Dispatch, (3) Betrieb. See "What exists / what does not" below for which layer is real.

---

## The eight rules you must not break

1. **No `role` column, ever.** Abilities are rows in `AccountCapability`
   (`apps/accounts/models.py:229-243`). Grant with `account.grant(kind)`, read with
   `request.account.capability_set()`. `revoke()` is a **soft flag**
   (`models.py:155-156`) — every capability query must carry `is_active=True`.
2. **No economic data on `User`.** `User` is login only (`apps/accounts/models.py:40-65`;
   `username`/`first_name`/`last_name` are `None`). Everything hangs off `Account`.
3. **Never hand an `Account` to a template.** Wrap it:
   `AccountView(account, viewer_account=request.account, user=request.user)`
   (`apps/accounts/visibility.py:115-147`). Any new `Account` field is invisible until you add
   it to `FIELD_POLICY` — the default is `Relation.SELF` (`visibility.py:133`).
   In templates use `{% if view_.phone %}`, **never** `{% if view_.can.phone %}` (always false).
4. **Slugs are claimed once, globally, and never reused.** `ReservedSlug.claim(source)`
   (`apps/accounts/models.py:186-196`) is a project-wide namespace shared by `Account`,
   `JobPosting` and `catalog.Product`. `Account.save()` only claims when `self.slug` is empty.
5. **Never delete a published `Account` or `JobPosting`. Depublicate.** The pattern is
   410 + `X-Robots-Tag: noindex` and the row survives
   (`apps/accounts/views.py:150-163`, `apps/jobs/views.py:39-50`).
6. **Authorization = (active account has capability X) AND (object belongs to active account).**
   Missing capability → **403**. Foreign object → **404**, never 403 (do not reveal existence).
   `apps/accounts/permissions.py:14-62`; tests at `tests/test_isolation.py:41-74`.
7. **Localities and service categories are never free text.** Always a `PROTECT` FK, always
   filtered through `active_localities()` / `ScopedLeaf.queryset()`
   (`apps/accounts/forms.py:12-23`). Reference data is seeded by **data migrations only**.
8. **Preserve the language split. Do not "translate" either side.**

| Layer | Language | Example |
|---|---|---|
| Public/indexable URL segments | **German** | `/jobs/`, `/job/<slug>/bewerben/`, `/reinigungskraft/`, `/profil/` |
| Dashboard URL segments | **Romanian** | `/dashboard/anunturi/`, `/candidaturi/`, `/contracte/`, `/obiective/`, `/planificare/`, `/turele-mele/`, `/pontaj/`, `/calibrare/`, `/echipamente/`, `/cereri/`, `/bursa/` |
| Comments, docstrings, `verbose_name`, choice labels, test names | **Romanian** | `verbose_name = "Anunț"` |
| Python identifiers, model/field names, URL `name=` | **English** | `JobPosting`, `name="posting_publish"` |
| Seeded domain data, contract text, public copy, legal terms | **German** | `Treppenhaus- und Gemeinschaftsflächenreinigung`, `§35a EStG` |

Sanctioned exception: a named German artefact keeps its German name inside the dashboard —
`obiective/<pk>/reinigungsplan.xlsx` (`apps/dashboard/urls.py:34-35`).

---

## What exists / what does not (verified 2026-08-29)

| Layer | Status | Where |
|---|---|---|
| **1 Marktplatz** (customer posts a need) | **Partial** — `apps.marketplace` exists: `ServiceRequest` → `Offer` → award, with multi-criteria scoring and `Invitation` as a *suggestion*, not an assignment. Dashboard-only; no public marketplace URL. An **awarded** `Offer` can generate a `ContractDraft` via `create_contract_from_offer()` (`services.py:149`), with the contract type chosen by `contract_type_for()` (`services.py:133`) — covered by `tests/test_marketplace.py::TestContractSeam`. | `apps/marketplace/` |
| **1b Recruitment job board** | **Exists** — `apps.jobs`. This is a **supply** funnel (Stellenanzeige / Bewerbung), NOT the customer-order marketplace. | `apps/jobs/` |
| **2 Dispatch** | **Deliberately absent.** No automatic allocation, by design — `apps/marketplace/models.py:10-14` cites §7 SGB IV (Scheinselbstständigkeit) and AÜG licensing. Do not add auto-assignment. | — |
| **3 Betrieb: Einsatzplanung** | **Exists** — weekly greedy planner under hard ArbZG + contract-hour constraints. | `apps/planning/services.py` |
| **3 Betrieb: Zeiterfassung** | **Exists** — check-in/out, append-only `ShiftEvent`, employer corrections, `time_records()`. | `apps/planning/attendance.py` |
| **3 Betrieb: Kalibrierung** | **Exists** — median/MAD estimate correction, proposed never auto-applied. | `apps/planning/calibration.py` |
| **3 Betrieb: Geräte/Telemetrie** | **Exists** — `apps.devices`, token-authenticated `POST /api/telemetry/`, discrepancy detection. Verification, **not** calibration. | `apps/devices/` |
| **3 Betrieb: Verträge** | **Exists** — templates, wage-floor gate, frozen body + SHA-256, simple e-signature. | `apps/contracts/` |
| **Kunde / Objekt(-Kunde) / Auftrag / Angebot / Rechnung** | **Do not exist.** There is `planning.Site` (Objekt) but no customer entity, no order, no quote, no invoice, no payroll, no Qualität/Material module. | — |
| **`apps.catalog`** | **Inert.** Models only; no views, no URLs, zero rows. `Product.get_absolute_url()` raises `NoReverseMatch`. | `apps/catalog/models.py:87` |
| **Admin UI** | **Does not exist.** `django.contrib.admin` is installed and routed but there is **no `admin.py` anywhere**. Never tell a user "change it in the admin". | verified: `find apps -name admin.py` → empty |
| **Homepage** | `GET /` → **404**. There is no root route. | `config/urls.py:13-33` |
| **HTMX** | Installed (`django_htmx` app + middleware) but **zero `hx-*` attributes** and `htmx.js` is never loaded. There is no HTMX convention yet. | verified: `grep -rn "hx-" templates/` → empty |

---

## Environment and commands

```bash
cd /Users/Geronimo/Projects/Cleaning_SaaS
.venv/bin/python manage.py check          # -> no issues
.venv/bin/python manage.py migrate
.venv/bin/python -m pytest -q             # 190 passed (2026-08-29)
.venv/bin/python manage.py runserver 8099 --noreload
.venv/bin/python manage.py flush_indexing --limit 100
```

Python 3.12.13; Django **5.2.17** (`pyproject.toml` only pins `>=5.1,<6.0`). No `.git`, no
`.env`, no `pip` inside the venv. `psycopg` and `dj-database-url` are **not installed** —
setting `DATABASE_URL` crashes at `config/settings.py:79`.

---

## Reference files — route here before writing code

| If the task touches… | Read |
|---|---|
| Project layout, settings inventory, service-layer convention, dependency versions, language rules, migration graph | `references/architektur-und-konventionen.md` |
| `Account`, `Membership`, `AccountCapability`, `ActiveAccountMiddleware`, permission mixins, slugs, publish/unpublish, consent, `AccountView`/`FIELD_POLICY` visibility | `references/accounts-rechte-sichtbarkeit.md` |
| `JobPosting`, `Application`, the apply→account→profile chain, JSON-LD, 410+noindex, sitemap, robots.txt, Google Indexing queue | `references/jobs-und-seo.md` |
| `Site`/`Zone`/`ShiftPlan`/`Shift`/`ShiftEvent`, the planner, Zeiterfassung, `ZoneCalibration`, telemetry | `references/planning-und-kalibrierung.md` |
| `ContractDraft`, `WageFloor`, `MinijobThreshold`, `ContractTemplate`; `apps/geo`+`apps/taxonomy`+`apps/catalog` seeding; dashboard panels, templates, adding a page | `references/contracts-referenzdaten-ui.md` |
| Writing or fixing a test, conftest fixtures, assertion style | `references/testing.md` |
| "Is this a known bug?", pre-launch checklist, anything that looks broken | `references/bekannte-maengel.md` |

**Sibling skills** (domain rules, not code): `gebaeudereinigung-domain`, `gr-tarif-und-lohn`,
`gr-zeiterfassung`, `gr-einsatzplanung`, `gr-auftrag-und-faktura`, `gr-marktplatz-dispatch`.
Use those for *what the German rule is*; use this skill for *how this repo implements it*.

---

## Statement types used throughout the references

- **Fakt** — sourced from the code (`file:line`) or from pland.app (URL cited).
- **Vorschlag** — a design proposal for code that does not exist yet.
- **Ungeprüft** — domain knowledge added here that the sources do not cover.

Legal content in this skill is **reference material, not legal advice**. Tarif and statutory
values change annually; every table carries its Stand and its source.

---

## Fast checklist before you commit an edit here

1. Did you add a field to `Account`? → add it to `FIELD_POLICY`, and to `INDIVIDUAL_HIDDEN`
   if it is company-only.
2. Did you add a view under `/dashboard/`? → `CapabilityRequiredMixin` (or the FBV `_guard`
   shape at `apps/devices/views.py:15-20`) **and** an account-scoped queryset **and** a
   `Panel` row in `apps/dashboard/panels.py`. A hidden panel is not a permission.
3. Did you add a `Capability`? → add its `PANELS` rows; do not add an `{% if %}` to a template.
4. Did you touch a public URL segment or a slug? → it is permanent. Changing it is an SEO
   regression, not a rename.
5. Did you add reference data? → data migration with `update_or_create(slug=…)`, historical
   models via `apps.get_model(...)`, and a `backwards` derived from the same constant.
6. Did you touch the live/expired predicate? → it exists in four places
   (`apps/jobs/models.py:75-77`, `apps/jobs/views.py:20-22`, `config/sitemaps.py:31-33`,
   `apps/jobs/views.py:71`). They must not drift.
7. Run `.venv/bin/python -m pytest -q`. 190 tests must still pass.
