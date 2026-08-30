# Bekannte Mängel — verified defect and gap list

**Covers:** every defect and gap found while mapping this repository, each with a `file:line`,
a severity, and a note on what it takes to fix. Also lists the items that **used to be** gaps
and have since been fixed, so nobody reports them again.
**Stand: 2026-08-29.** Every row below was re-verified against the live tree on that date —
by opening the file, by running `django.test.Client`, or by querying the dev database. Items
from the dossiers that no longer reproduce were **dropped** and are listed in §0.

**Severity scale**
`S1` data/legal exposure or evidence loss · `S2` wrong output shipped to a user or to Google ·
`S3` crash / 500 on a reachable path · `S4` correctness or convention debt · `S5` cosmetic /
missing feature.

---

## 0. Already fixed — do NOT report these (Fakt)

The older dossiers (`scratchpad/dossier/*.md`) list these as missing. They now exist:

| Formerly reported | Current reality | Evidence |
|---|---|---|
| "No sitemap.xml" | **Exists and works.** `config/sitemaps.py` defines `JobSitemap`, `ProfileSitemap`, `DirectorySitemap`; `config/urls.py:15-21` mounts a sitemap **index** at `/sitemap.xml` plus `/sitemap-<section>.xml`. All four URLs verified 200 | `config/sitemaps.py`; runtime check |
| "No robots.txt" | **Exists and works.** `templates/robots.txt` served by a `TemplateView` at `config/urls.py:22-26`. Verified 200 `text/plain` | |
| "No Google Indexing API" | **Exists.** `apps/jobs/indexing.py` (enqueue / flush / transport), the `jobs.IndexingTask` model + migration `jobs/0002_indexingtask`, the `flush_indexing` management command, and the `GOOGLE_INDEXING_CREDENTIALS` setting | `apps/jobs/indexing.py`, `apps/jobs/models.py:124-154` |
| "`base.html` renders no messages block" | **It does.** `templates/base.html:9-13` | |
| "No management command anywhere" | **One exists**: `apps/jobs/management/commands/flush_indexing.py` | |
| "No tests for the sitemap / robots / devices" | **All three are covered.** `tests/test_seo.py` (14 tests), `tests/test_devices.py` (25) | `--collect-only` |
| "`apps.marketplace` / `apps.devices` do not exist" | **Both exist**, are in `INSTALLED_APPS`, and are tested (38 + 25 tests) | `config/settings.py:34-35` |
| Test count "100" / "149" | **190 tests pass** as of 2026-08-29 | `.venv/bin/python -m pytest -q` |
| Locality count "31" | **30 rows**, 17 active | live DB query |

Still true and still unfixed: **no `admin.py` anywhere**, `/` returns 404, unvalidated city
slugs, `PRIVATE_STORAGE_ROOT` unused, no `AuditLog`.

---

## 1. S1 — data exposure and evidence loss

### M1 · `PRIVATE_STORAGE_ROOT` is declared but never used → verification documents land in the publicly served `MEDIA_ROOT`

**Severity S1.**
`config/settings.py:118-119`:

```python
# Documentele de verificare NU stau în MEDIA_ROOT public.
PRIVATE_STORAGE_ROOT = BASE_DIR / "private"
```

`apps/accounts/compliance.py:22-27`:

```python
class VerificationDocument(models.Model):
    """NICIODATĂ public. Storage privat, cu termen de retenție."""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DocumentType.choices)
    file = models.FileField(upload_to="verification/%Y/%m/")     # <- no storage= argument
```

Verified 2026-08-29: `grep -rn "PRIVATE_STORAGE_ROOT" apps config tests` returns **only**
`config/settings.py:119`; `grep -rn "storage=" apps` returns **nothing**. The field therefore
uses the default `FileSystemStorage` at `MEDIA_ROOT = BASE_DIR / "media"`
(`config/settings.py:116`), and in `DEBUG` that directory is served publicly by
`static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` (`config/urls.py:35-36`).

**Consequence:** uploading an identity document or a Führungszeugnis today would publish it.
Both the docstring and the setting are a promise the code does not keep.

**Mitigating fact:** `VerificationDocument` is currently **completely unwired** — no form, no
view, no URL, no admin, no service references it (grep confirms usage only in `compliance.py`
and the migration). There is no upload flow, so nothing can be uploaded through the app yet.
That is why this is a latent S1, not an active breach — but it becomes active the moment anyone
adds an upload form.

**Vorschlag for the fix** (do not apply without asking):

```python
# apps/accounts/compliance.py
from django.core.files.storage import FileSystemStorage
from django.conf import settings

private_storage = FileSystemStorage(location=settings.PRIVATE_STORAGE_ROOT, base_url=None)

file = models.FileField(upload_to="verification/%Y/%m/", storage=private_storage)
```

plus a `@login_required` streaming view that checks `request.account` ownership, and a test
asserting the file is **not** reachable under `MEDIA_URL`. Changing `storage=` produces a
migration but does not move existing files.

### M2 · `AuditLog` does not exist

**Severity S1 (compliance gap).** Verified: `grep -rn "AuditLog" apps config tests` → nothing.
`PLAN-FAZA-0.md:157` specifies `AuditLog | actor, action, target, ip, created_at — doar
publicare / depublicare / verificare`. There is no such model, no table, no code.

The only audit-ish evidence that exists today:

| Evidence | Where | Guarantee |
|---|---|---|
| `ConsentRecord` | `apps/accounts/compliance.py:51-70` | append-only via `save()` guard |
| `ContractSignature` | `apps/contracts/models.py:256-281` | immutable via `save()` guard, carries `document_sha256` |
| `ShiftEvent` | `apps/planning/models.py:188-220` | append-only via `save()` guard — **but see M3** |

Nothing records who published or depublished a profile, who changed an `Application` status,
who granted or revoked a capability, or who reviewed a document.

**All three `save()` guards raise `RuntimeError`, not `ValidationError`,** and **none of them
blocks `queryset.update()` or `.delete()`.**

### M3 · Regenerating a plan silently destroys the Zeiterfassung journal

**Severity S1.** `apps/planning/services.py:109` — `plan.shifts.all().delete()` inside
`generate_week_plan(..., replace=True)`. `ShiftEvent.shift` is `on_delete=models.CASCADE`
(`apps/planning/models.py:204`), so every `CHECK_IN` / `CHECK_OUT` / `CORRECTED` event of that
week is deleted with it — **despite** `ShiftEvent.save()` declaring the journal immutable
(`:217-220`). `checked_in_at`, `checked_out_at` and `actual_minutes` go with them.

There is **no guard** against regenerating a week that contains `DONE` shifts, and
`tests/test_attendance.py:72-75` actively exercises this path on a published plan.

Under §16 Abs. 2 ArbZG the employer must keep working-time records for at least two years
(`apps/planning/attendance.py:11,22`, `RETENTION_YEARS = 2`), and `time_records()` computes and
displays a `retention_until` date — which nothing enforces.

**Vorschlag:** refuse regeneration when the week contains any shift with
`status in (DONE, MISSED)` or a non-null `checked_in_at`, unless an explicit
`force_delete_records=True` is passed and an audit row is written.

### M4 · `send_for_signature` has no status precondition → it can invalidate existing signatures

**Severity S1.** `apps/contracts/views.py:90` only checks
`contract.employer_id == request.account.pk` before calling `send_for_signature(contract)`.
`apps/contracts/services.py:25-33` has no status guard either. Posting `action=send` on an
already-`SIGNED` contract re-renders the body, writes a **new** `body_sha256`, and resets
`status = SENT` — silently invalidating every stored
`ContractSignature.document_sha256`, i.e. destroying the exact evidence the design docstring
(`services.py:43-47`) says it protects. The button is hidden by
`templates/dashboard/contract_detail.html:16`, but the POST handler is not.

**Vorschlag:** `if draft.status != DraftStatus.DRAFT: raise ValueError(...)` at the top of
`send_for_signature`, plus a test.

### M5 · The raw device token is pushed through the flash-message store

**Severity S1.** `apps/devices/views.py:41-44` and `:51-54`:

```python
messages.success(request, f"Echipament adăugat. Cheia se afișează O SINGURĂ DATĂ: {raw}")
messages.warning(request, f"Cheie nouă pentru {device.label} … : {raw}")
```

Only the SHA-256 hash is stored on `Device` (`token_hash`, `token_prefix`,
`apps/devices/models.py:57-58`), so this is the **one** place the plaintext exists. It travels
through the session-backed message store and into page HTML.

Do not log it, do not put it in a cacheable partial, and be careful if the message storage
backend ever changes to cookies.

---

## 2. S2 — wrong output shipped

### M6 · The `Site` row is still `example.com` → every sitemap `<loc>` is wrong

**Severity S2, launch blocker.** Verified 2026-08-29:
`Site.objects.values_list("id","domain","name")` → `[(1, "example.com", "example.com")]`.
`SITE_ID = 1` (`config/settings.py:98`). Actual output of `/sitemap-jobs.xml`:

```xml
<loc>http://example.com/job/reinigungskraft-norderstedt-bis-40-stdmonat/</loc>
```

The JSON-LD uses a **different** mechanism — `request.get_host()` (`apps/jobs/views.py:103`) —
and `templates/robots.txt` uses `request.get_host` too, so those two are host-correct while the
sitemap is not. Fix by updating the `Site` row per environment.

### M7 · Unknown, inactive and empty city/category slugs return **200**, not 404

**Severity S2.** Verified 2026-08-29:

| URL | Status |
|---|---|
| `/jobs/inexistent-oras/` | **200** (empty list) |
| `/reinigungskraft/nu-exista/` | **200** |
| `/reinigungskraft/nu-exista/nici-asta/` | **200** |

`JobListView.get_queryset` (`apps/jobs/views.py:23-24`) and `ProviderListView.get_queryset`
(`apps/accounts/views.py:186-189`) both filter on the raw slug with no `get_object_or_404` and
no `is_active` check. A **root** category slug is permanently empty by construction, because no
`AccountService` can point at a non-leaf.

This creates an unbounded space of indexable soft-404s — and it compounds with M13:
`DirectorySitemap` actively submits **443** of these URLs to Google today.

### M8 · `employmentType: "MINIJOB"` is not a value Google accepts

**Severity S2.** `apps/jobs/views.py:113` emits `job.employment_type` verbatim. Live output
confirms `"employmentType": "MINIJOB"`. The schema.org / Google-recognised set is
`FULL_TIME`, `PART_TIME`, `CONTRACTOR`, `TEMPORARY`, `INTERN`, `VOLUNTEER`, `PER_DIEM`, `OTHER`.
`FULL_TIME`, `PART_TIME`, `CONTRACTOR` and `TEMPORARY` happen to be valid; **`MINIJOB` is not.**

**The mapping belongs in `build_job_jsonld`, not in the model** — `Minijob` is a real German
product concept (§8a SGB IV) that must stay in the UI, in `EmploymentType` and in
`ContractType`. See `jobs-und-seo.md` §10 for the proposed mapping.

### M9 · The public UI mixes German and Romanian strings

**Severity S2.** `LANGUAGE_CODE = "de"` and `USE_I18N = True` (`config/settings.py:107,109`),
but there is **no `LocaleMiddleware`, no `LOCALE_PATHS`, no `locale/` directory and no `.po`
file** anywhere in the project. Strings wrapped in `gettext_lazy` that happen to exist in
Django's own German catalogue get translated; everything else renders as the Romanian source.

Verbatim from the rendered job page:

```html
<h1>Reinigungskraft Norderstedt (bis 40 Std./Monat)</h1>
<p>Seniorenresidenz Nord · Norderstedt · Minijob</p>
<p>14,25–15,00 EUR / oră</p>                     <!-- "oră" — Romanian for "hour" -->
<h2>Candidatură</h2>                             <!-- Romanian -->
<label for="id_email">E-Mail-Adresse:</label>    <!-- German, from Django's own catalogue -->
<label for="id_full_name">Nume complet:</label>  <!-- Romanian, untranslated -->
```

Sources of the Romanian on public pages: `JobPosting.salary_unit` choice labels
(`apps/jobs/models.py:42`), `templates/jobs/detail.html:9`, `templates/jobs/list.html:2-3`,
`templates/jobs/gone.html`, `templates/accounts/gone.html`,
`templates/accounts/profile_public.html:11`, `templates/accounts/provider_list.html:2-3`, and
the `_()`-wrapped labels in `apps/jobs/forms.py:19-32`.

**Do NOT "fix" the Romanian source strings** — that violates the repo's language convention
(see `architektur-und-konventionen.md` §5). The correct fix is a real `de` catalogue:
`LOCALE_PATHS`, `django.middleware.locale.LocaleMiddleware`, `makemessages -l de`, and German
translations for the public-facing strings. Dashboard copy stays Romanian.

### M10 · The §35a badge is shown without checking the provider's legal status

**Severity S2 (a tax claim shown to a consumer).** `apps/accounts/views.py:173`:

```python
ctx["deductible_35a"] = any(s.is_35a_eligible for s in ctx["services"])
```

rendered as `<strong>20 % steuerlich absetzbar (§35a EStG)</strong>`
(`templates/accounts/profile_public.html:9`). The flag comes purely from the **category**.

But `apps/accounts/forms.py:84` tells the worker that their legal status
*"Determină cine emite factura și dacă clientul poate deduce §35a."* — and §35a requires an
invoice and a bank transfer. A provider with `LegalStatus.UNDECLARED` who selects
`haushaltshilfe` still gets the badge on a public page.

Separately, the "20 % / €4,000" figures live **only** in a code comment
(`apps/taxonomy/models.py:19-20`) and in the German template string — there is no constant on
the profile side. (`apps/marketplace/models.py:169-174` *does* implement the cap for offers.)

---

## 3. S3 — reachable 500s

All five verified 2026-08-29 with an authenticated `django.test.Client`.

| # | Path | Exception | Cause |
|---|---|---|---|
| **M11** | `GET /dashboard/obiective/zona-noua/` | `apps.planning.models.Zone.site.RelatedObjectDoesNotExist: Zone has no site` | `templates/dashboard/site_form.html:2` renders `{{ view.form_class.Meta.model\|default:"Adaugă" }}`. The template engine calls the model **class**, instantiating a bare `Zone()`, whose `__str__` (`apps/planning/models.py:72`) dereferences `self.site`. The link is exposed at `templates/dashboard/sites.html:4`. No test covers it |
| **M12** | `GET /cont/cont/<pk>/activeaza/` (anonymous) | `TypeError: Field 'id' expected a number but got <SimpleLazyObject: AnonymousUser>` | `switch_account_view` (`apps/accounts/views.py:217-221`) is an **undecorated** function view; `switch_account` filters `Membership.objects.filter(user=request.user)` with `AnonymousUser`. Fix: `@login_required` |
| **M13a** | `GET /dashboard/candidaturi/?job=abc` | `ValueError: Field 'id' expected a number but got 'abc'` | `apps/jobs/dashboard_views.py:94-95` filters on the raw GET string |
| **M13b** | `GET /dashboard/planificare/?week=lol` and `/dashboard/pontaj/?week=lol` | `ValueError: Invalid isoformat string: 'lol'` | `_monday()` (`apps/planning/views.py:15-20`) calls `date.fromisoformat` unguarded — every planning page shares this |
| **M13c** | `GET /dashboard/echipamente/discrepante/?days=abc` | `ValueError: invalid literal for int() with base 10: 'abc'` | `apps/devices/views.py:72`. `?days=100000` is also an unbounded scan |
| **M14** | `GET /cont/profil/publicare/` (logged in, with an account) | `ImproperlyConfigured: TemplateResponseMixin requires either a definition of 'template_name' or an implementation of 'get_template_names()'` | `PublishToggleView` (`apps/accounts/views.py:201-214`) is POST-only **by intent** (`form_class = OnboardingForm  # neutilizat`) but nothing enforces it. Fix: `http_method_names = ["post"]` |
| **M15** | any call to `catalog.Product.get_absolute_url()` | `NoReverseMatch: 'catalog' is not a registered namespace` | `apps/catalog/models.py:87` reverses `catalog:product`; `apps.catalog` has no `urls.py` and is not included in `config/urls.py` |
| **M16** | `correct_minutes(shift, employer, -5, "…")` | `IntegrityError` from the DB CHECK — **not** caught by `except (ShiftError, ValueError)` in `apps/planning/views.py:207` | `apps/planning/attendance.py:147-165` validates neither sign nor ceiling. `int(request.POST.get("minutes", 0))` on an empty field also surfaces the raw English `invalid literal for int()` to a German/Romanian UI |

---

## 4. S4 — correctness and convention debt

### M17 · `Account.revoke()` is a soft flag that every query must account for

`apps/accounts/models.py:155-156`:

```python
def revoke(self, kind):
    self.capabilities.filter(kind=kind).update(is_active=False)
```

The `AccountCapability` row survives and still occupies the `uniq_capability` slot;
`grant()` reactivates it via `update_or_create` (`:149-153`). **Any query filtering on
`capabilities__kind=...` without `capabilities__is_active=True` matches revoked capabilities.**
The canonical safe form is `AccountQuerySet.with_capability()` (`:72-73`), which does both.
`capability_set()` (`:146-147`) also filters correctly.

Grep for `capabilities__kind` before adding a new query. **Severity S4** (silently over-broad
authorization queries).

### M18 · There is no `admin.py` anywhere in the project

Verified: `find apps -name admin.py` → **zero results**. `django.contrib.admin` is in
`INSTALLED_APPS` (`config/settings.py:14`) and `admin/` is routed (`config/urls.py:14`), but no
model is registered, so `/admin/` shows only auth / sites / allauth.

This directly contradicts three docstrings that promise it:

| Promise | Where |
|---|---|
| *"Restul se activează din admin, fără deploy"* (localities) | `apps/geo/migrations/0002_seed_localities.py:8` |
| *"se corectează din admin, fără deploy"* (wage floors) | `apps/contracts/migrations/0002_seed_wage_floors.py:8` |
| there is no reviewer UI for `VerificationDocument` or `verification_level` | `apps/accounts/compliance.py` |

**Consequence:** the only ways to activate a locality, correct a wage floor, or set a
`verification_level` are a data migration or `manage.py shell`. **Never tell a user "an admin
will approve it" or "change it in the admin".** **Severity S4** (operationally S2 — the
product's own documented workflows are unavailable).

### M19 · `/` returns 404 — there is no homepage route

Verified 2026-08-29: `GET /` → **404**. `config/urls.py:13-33` has no root pattern; the two
root-mounted includes (`apps.jobs.urls`, `apps.accounts.public_urls`) only claim
`jobs/`, `job/`, `reinigungskraft/` and `profil/`.

Worse: `LOGOUT_REDIRECT_URL = "/"` (`config/settings.py:105`), so **logging out lands the user
on a 404**. **Severity S3/S4.**

### M20 · `psycopg` and `dj-database-url` are declared/imported but not installed

- `pyproject.toml` declares `psycopg[binary]>=3.2` — **not installed** in `.venv`.
- `config/settings.py:79` imports `dj_database_url` (only when `DATABASE_URL` is set) — **not
  installed and not declared anywhere**.

Verified 2026-08-29: both raise `ModuleNotFoundError`. `pip` is not available inside the venv
(`No module named pip`), so neither can be installed from here.

**Consequence:** setting `DATABASE_URL` today crashes at import time with `ModuleNotFoundError:
No module named 'dj_database_url'`. Development on sqlite is unaffected. The `indexing` extra
(`google-auth`, `requests`) is likewise not installed — harmless, because `flush()` short-circuits
without `GOOGLE_INDEXING_CREDENTIALS`. `openpyxl` **is** installed (3.1.5) despite being an
extra, which is why the Reinigungsplan tests pass. **Severity S4.**

### M21 · `apply_view` renders the detail template without `jsonld`

`apps/jobs/views.py:80` passes only `{"job": job, "form": form}`. On a failed application POST
the page renders `<script type="application/ld+json"></script>` — an empty, invalid JSON-LD
block on a 200-status page. Any change to the detail template's structured data must account
for this second render path. **Severity S4.**

### M22 · The `{% if view.can.X %}` idiom advertised in the docstring is always false

`apps/accounts/visibility.py:119-120` documents `{% if view.can.phone %}`, but `can` is a
**method taking an argument** — in a template `view_.can` resolves to a bound method and
`.phone` on it silently fails. Verified 2026-08-29: `{% if v.can.display_name %}` renders the
`{% else %}` branch. The correct idiom is `{% if view_.phone %}`, as
`templates/accounts/profile_public.html:10` does. Also verified: `{{ v.phone }}` on a hidden
field renders the literal string `None`, and `{{ v.services }}` renders
`accounts.AccountService.None`. **Severity S4** (a docstring that teaches a bug).

### M23 · Severity in the contract gate is typed, not deduced from the message (fixed)

Formerly a substring test. `apps/contracts/services.py:26` now reads:

```python
blocking = [i.message for i in draft.compliance_report() if i.blocking]
```

`ContractDraft.compliance_report()` (`apps/contracts/models.py:197-249`) returns frozen
`ComplianceIssue(code, message, blocking)` dataclasses (`models.py:45-54`); `WAGE_FLOOR` is
`blocking = contract_type != WERKVERTRAG`, `MINIJOB_LIMIT` and `AUEG_LICENCE` are `True`,
`SCHEINSELBSTSTAENDIGKEIT` is `False`. Pinned by
`tests/test_contracts.py:43-50`. **No defect remains** — the entry is kept so nobody
"fixes" it back into a text test or flattens `WAGE_FLOOR` to a constant.

### M24 · `WorkerCapacity` is built per contract, not per person

`apps/planning/services.py:65-78` appends one row per signed `ContractDraft`. Two concurrent
contracts for the same human under the same employer give two independent weekly budgets and
two independent `per_day`/`day_end` dicts, so the §3 ArbZG 8 h/day check and the §5 rest check
are computed **per contract** — legally wrong, since ArbZG limits are per person. Untested.
**Severity S2/S4** (produces a legally non-compliant plan).

### M25 · Contracted hours are enforced weekly, never monthly

`build_capacities` converts monthly contract hours to a weekly average via
`WEEKS_PER_MONTH = Decimal("52")/Decimal("12")` (`services.py:31,67`) and nothing ever checks a
calendar-month total across plans. The Geringfügigkeitsgrenze is a **monthly** limit
(`apps/contracts/models.py:92-113`), so four heavy weeks in a five-week month can exceed the
monthly cap while every individual week passes. **Severity S2/S4.**

### M26 · `visits_per_week` is silently capped and the lost demand is invisible

`_visit_days` (`apps/planning/services.py:159-169`) caps with
`min(zone.visits_per_week, len(allowed))` and one visit per day. A zone with
`visits_per_week=10` on 5 allowed weekdays produces 5 shifts and **zero** `unmet_demand`
entries — while `capacity_report()`'s `demand_minutes` uses the **uncapped** `weekly_minutes`
(`:174-179`). The report and the plan disagree, with no signal. **Severity S4.**

### M27 · `mark_missed` does not clear `actual_minutes`

`apps/planning/attendance.py:168-175`. A `DONE` shift with 95 recorded minutes later marked
`MISSED` still holds `actual_minutes = 95`; `time_records` then reports `"actual": 0` and
`"variance": -25` in the same row (`:190-202`). The employer's audit table shows a difference
for a shift it claims was never worked. **Severity S4** (the table is the FKS artefact).

### M28 · `correct_minutes` does not call `_guard`

`apps/planning/attendance.py:147-165` checks only ownership and a non-empty reason. It accepts
a `PLANNED` shift and forces `DONE` with `checked_in_at = None` (a record with hours but no
timestamps), and it can resurrect a `DECLINED` or `MISSED` shift into `DONE`. **Severity S4.**

### M29 · Two clocks meet without conversion

`Shift.date` / `start_time` are naive local wall-clock (DST ignored — 07:00 is 07:00 on both
sides of the switch), while `checked_in_at` / `decided_at` / `published_at` are aware UTC.
`apps/planning/calibration.py:79` and `:93` compute `last_applied.decided_at.date()` — the
**UTC** date — and compare it with `timezone.localdate()` in Europe/Berlin. Between 00:00 and
02:00 CEST they disagree by one day, shifting both the cooldown and the window floor.
The correct form is `timezone.localtime(...).date()`. Do not "clean this up" without adding a
boundary test. **Severity S4.**

### M30 · `JobStatus.EXPIRED` is unreachable

Verified: it appears only at `apps/jobs/models.py:18` and in the migration. There is no cron, no
management command, no signal that transitions `PUBLISHED → EXPIRED`. Expiry is computed on the
fly by `is_live`, and `templates/dashboard/postings.html:10` fakes the display. Do not write
code that assumes `status == EXPIRED` matches a row. `AccountStatus.PENDING` / `SUSPENDED`,
`MembershipRole.ADMIN` / `MEMBER`, `PlanStatus.ARCHIVED`, `ConsentType.PRIVACY` / `MARKETING`
and `Account.verification_level` (never written) are the same class of dead state.
**Severity S4.**

### M31 · No email is sent anywhere in the apply flow

`apply_view`'s success message promises *"Ți-am trimis un email cu pașii următori"*
(`apps/jobs/views.py:77`) and `apply_to_job`'s docstring promises an activation link
(`apps/jobs/services.py:20-22`), but there is no `send_mail`, no allauth trigger and no signal.
The created user has an unusable password and no documented recovery path (allauth's password
reset would work but is not wired into the flow). Similarly,
`apps/planning/views.py:162` claims *"Angajatorul a fost informat."* on a shift decline —
nothing notifies anyone. The only `send_mail` in the project is `_notify_workers`
(`apps/planning/attendance.py:66-72`), with `fail_silently=True`, a console `EMAIL_BACKEND`
(`config/settings.py:122`) and no `DEFAULT_FROM_EMAIL` (so `from_email=None` resolves to
`webmaster@localhost`). **Severity S4** (messages that state a falsehood to the user).

### M32 · Model `clean()` methods that never run

| `clean()` | Why it never fires |
|---|---|
| `Account.clean()` (`apps/accounts/models.py:175-177`) | `create_account()` uses `objects.create()`, which does not call `full_clean()` |
| `AccountService.clean()` (`profiles.py:81-83`) | rows are created with `bulk_create` (`apps/accounts/views.py:122-124`) |
| `ServiceCategory.clean()` (`apps/taxonomy/models.py:40-42`) | no admin, no ModelForm for this model |
| `Zone.clean()` (`apps/planning/models.py:82-87`) | **this one does fire**, via `ZoneForm` — the exception |
| `ContractDraft.clean()` (`apps/contracts/models.py:251-253`) | only through the ModelForm; every fixture uses `objects.create()` |

Verified: `grep -rn "full_clean" apps tests` → nothing. Also note `bulk_create` in
`generate_week_plan` (`apps/planning/services.py:153`) bypasses `save()`, `full_clean()` and
signals for every generated `Shift`. **Severity S4.**

### M33 · Dead code and unused declarations

| Item | Where |
|---|---|
| `leaf_categories()` — defined, never called | `apps/accounts/forms.py:16-17` |
| `require_manage()`, `Membership.can_manage`, `Account.is_provider` (the last has one caller in marketplace) | `apps/accounts/permissions.py:60-62`, `models.py:224-226`, `:158-160` |
| `ApplicationForm.clean`'s duplicate check — `_existing_account` is never set | `apps/jobs/forms.py:49-56` |
| `Membership` imported but unused | `apps/jobs/services.py:8` |
| `from datetime import datetime` imported but unused | `apps/planning/views.py:101` |
| `Shift.hours` property — no references anywhere | `apps/planning/models.py:171-173` |
| `time_records(..., worker=…)` — the parameter works, no caller | `apps/planning/attendance.py:178` |
| `Zone.area_sqm`, `Zone.category` — stored, never used by the planner | `apps/planning/models.py:57,50` |
| `WorkerProfile.willing_to_travel_km`, `Locality.latitude/longitude` — all unused, all coordinates `None` | `apps/accounts/profiles.py:26`, `apps/geo/models.py:30-31` |
| `factory_boy`, `faker` — installed, never imported | `.venv` |
| `apps.catalog` — models only; no views, no URLs, no seed, zero rows | `apps/catalog/` |

**Severity S5.** Removing dead code is safe; removing `OwnedByAccountMixin` from
`PostingPublishView` is **not** (its own `get_queryset` shadows the mixin —
`apps/jobs/dashboard_views.py:58-59`).

---

## 5. S5 — cosmetic and missing feature

| # | Item | Where |
|---|---|---|
| M34 | **The dashboard account switcher returns 405.** `home.html:7` POSTs to `{% url 'dashboard:home' %}`; `DashboardHomeView` is a `TemplateView` with only `get`. Verified: `POST /dashboard/` → **405**. The working endpoint is `accounts:switch`, which nothing links to (and which is M12) | `templates/dashboard/home.html:7`, `apps/dashboard/views.py:45` |
| M35 | **`paginate_by` is set but no template paginates.** `JobListView` 20, `ProviderListView` 24, `CandidateListView` 50, `OpenRequestsView` 25 — none of their templates render `page_obj`/`paginator` controls. Row 51 is invisible | the four templates |
| M36 | **The candidates filter form does not preserve its own selection** — after filtering, both selects reset to "Toate…" | `templates/dashboard/candidates.html:3-9` |
| M37 | **Messages are rendered but unstyled and un-dismissible.** `base.html:9-13` prints a plain `<ul class="messages">`; nothing styles `.messages`/`.success`/`.error`, so an error looks exactly like a success. `static/` is empty | `templates/base.html` |
| M38 | **No canonical URL, meta description, OpenGraph or hreflang** on any public template | `templates/base.html` (16 lines, two blocks) |
| M39 | **`DirectorySitemap` has no `limit`, no `lastmod`, and no supply filter** — it emits the full 17 × 24 cartesian product (443 URLs today) whether or not any provider matches, and re-implements the leaf definition instead of reusing `ScopedLeaf.queryset()` | `config/sitemaps.py:54-78` |
| M40 | **The flat `/jobs/` index is in no sitemap** | `config/sitemaps.py:68` emits only `jobs:list_city` |
| M41 | **`views_count` counts bots and is never displayed.** No session dedupe, no bot filter, no rate limit; `grep views_count templates` → nothing. `DashboardContext.profile_views` returns a hard-coded `0` | `apps/jobs/views.py:51-53`, `apps/dashboard/views.py:38-39` |
| M42 | **`JobPosting.requirements` is captured but never displayed or emitted** — not in the template, not in the dashboard list, not in the JSON-LD | `apps/jobs/models.py:28` |
| M43 | **No HTML sanitiser** despite `help_text="HTML permis restrâns"`. `templates/jobs/detail.html:8` uses `\|linebreaks` (which escapes), but `build_job_jsonld` puts the raw string into JSON-LD, protected only by the three-character replacement in `render_jsonld`. Switching the template to `\|safe` would introduce stored XSS | `apps/jobs/models.py:27` |
| M44 | **`provider_list.html` hard-codes `/profil/{{ v.slug }}/`** instead of reversing `public:profile` | `templates/accounts/provider_list.html:3` |
| M45 | **N+1 on the provider directory.** `{{ v.locality }}` calls `Locality.__str__`, which dereferences `region`, while the view only does `select_related("locality")` | `apps/geo/models.py:44`, `apps/accounts/views.py:185` |
| M46 | **`site_form.html` is shared by two create views** and its `<h1>` prints a Python class repr — which is M11. Give a new create view its own template | `templates/dashboard/site_form.html` |
| M47 | **No `Site`/`Zone` edit or delete UI**, and no manual shift editing. `ZoneForm.__init__` carries dead `if self.instance.pk:` handling for an update view that does not exist | `apps/planning/views.py`, `forms.py:37-38` |
| M48 | **Several redirects hard-code `/dashboard/...` paths** instead of reversing, so renaming a URL segment breaks them with no `NoReverseMatch` warning. Grep the literal path | `apps/planning/views.py:43,57,80,133,171,209` |
| M49 | **Templates compare status against raw string literals** (`'DRAFT'`, `'PLANNED'`, `'PUBLISHED'`, `'IN_PROGRESS'`, `'CONFIRMED'`). Renaming a `TextChoices` **value** silently removes buttons. Rename labels freely; never rename values without grepping `templates/` | all dashboard templates |
| M50 | **`{% if r.variance %}` and `{% if s.actual_minutes %}` hide the value 0** — a perfectly on-estimate shift renders as `—` | `templates/dashboard/time_records.html`, `my_shifts.html` |
| M51 | **`my_shifts_view` has no capability check.** Any account gets 200 with an empty list. Intentional (workers hold `WORKER`, not `EMPLOYER`) — do not "harden" it into a 403 without checking `apps/dashboard/panels.py:60-61` | `apps/planning/views.py:136-181` |
| M52 | **Panels and view permissions disagree**: `sites`/`planning`/`time_records`/`calibration` are `EMPLOYER`-only panels but `EMPLOYER`-**or**-`PROVIDER` views. `Contractele mele` is gated on `WORKER` although `ContractListView` shows both sides | `apps/dashboard/panels.py:62-75` |
| M53 | **`active_template` sorts version strings lexicographically** (`"1.10"` < `"1.9"`) and is called without `language`, hard-wiring `"de"` | `apps/contracts/services.py:36-39`, `views.py:48` |
| M54 | **`compliance_issues()` is recomputed against *today's* wage table** on every detail-page load — a contract signed in 2025 starts showing "sub pragul legal" once a higher 2027 floor is seeded. No `checked_at` snapshot | `apps/contracts/views.py:77` |
| M55 | **No wage validation at all before 2025-01-01.** Two of the five seeded rows are still flagged `— DE CONFIRMAT` (`GENERAL` 13.90, `MinijobThreshold` 603.00). The 2026 `GEBAEUDE` gap is closed: `0005_wage_floor_2026.py` caps 14.25 € at 2025-12-31 and opens 15.00 € from 2026-01-01 | `apps/contracts/migrations/0002_seed_wage_floors.py`, `0005_wage_floor_2026.py` |
| M56 | **`X-Forwarded-For` is trusted unconditionally** in both `_ip()` helpers, and there are **two** of them — fixing one does not fix the other. `ContractSignature.ip_address` is evidence data | `apps/accounts/services.py:65-69`, `apps/contracts/services.py:72-76` |
| M57 | **No §4 ArbZG break handling, no §11 ArbZG weekly rest day, no overtime/night/Sunday/holiday surcharge logic, no absence/holiday/sick-leave model, no payroll output, no CSV/PDF export for an FKS audit, no retention enforcement, no recurrence engine** | `apps/planning/` — see `planning-und-kalibrierung.md` §9 |
| M58 | **The project is not under version control** — there is no `.git` directory, no `.gitignore`, no `.env.example`, no `Makefile`, no `requirements*.txt` | verified 2026-08-29 |

---

## 6. Pre-launch checklist derived from the above

Ordered by what blocks a public launch.

1. **M6** — set the `Site` row per environment, or every sitemap URL points at `example.com`.
2. **M19** — add a root route; `LOGOUT_REDIRECT_URL` currently lands on a 404.
3. **M1** — wire `PRIVATE_STORAGE_ROOT` before any `VerificationDocument` upload flow exists.
4. **M8** — map `employmentType` for the JSON-LD.
5. **M7 / M39** — decide 404 vs. 410 for unknown/inactive city and category slugs, and stop
   submitting 443 empty pages.
6. **M9** — add a real `de` catalogue for the public-facing strings (do not translate the
   Romanian sources in place).
7. **M4 / M3** — add the status guard to `send_for_signature` and the regeneration guard to
   `generate_week_plan`.
8. **M11 / M12 / M13 / M14** — fix the reachable 500s and add tests.
9. **M10** — join the §35a badge with `LegalStatus`, or reword it.
10. **M18** — write at least a minimal `admin.py` for `Locality`, `ServiceCategory`,
    `WageFloor` and `MinijobThreshold`, so the workflows the migrations promise actually exist.
11. **M20** — install `psycopg` **and** declare + install `dj-database-url` before touching
    `DATABASE_URL`.
12. **M55** — confirm the two remaining `— DE CONFIRMAT` wage rows (`GENERAL` 13.90 and the
    603.00 € Minijob threshold) against an official source.

---

## Quellen

- `/Users/Geronimo/Projects/Cleaning_SaaS/config/settings.py`, `config/urls.py`,
  `config/sitemaps.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py`, `compliance.py`,
  `visibility.py`, `views.py`, `services.py`, `forms.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/jobs/models.py`, `views.py`, `services.py`,
  `forms.py`, `dashboard_views.py`, `indexing.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`, `services.py`,
  `attendance.py`, `calibration.py`, `views.py`, `forms.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py`, `services.py`, `views.py`,
  `migrations/0002_seed_wage_floors.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/devices/views.py`, `models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/catalog/models.py`,
  `apps/geo/models.py`, `apps/taxonomy/models.py`, `apps/dashboard/panels.py`, `views.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/templates/base.html`, `templates/jobs/*`,
  `templates/accounts/*`, `templates/dashboard/*`
- `/Users/Geronimo/Projects/Cleaning_SaaS/pyproject.toml`, `.venv/lib/python3.12/site-packages`
- `PLAN-FAZA-0.md:157` (the specified but unimplemented `AuditLog`)
- `scratchpad/dossier/*.md` — cross-checked; stale rows dropped and recorded in §0
- Runtime verification 2026-08-29 (`django.test.Client` + `manage.py shell`): URL status codes
  and tracebacks for `/`, `/jobs/inexistent-oras/`, `/reinigungskraft/nu-exista/`,
  `/dashboard/obiective/zona-noua/`, `/cont/cont/<pk>/activeaza/`, `/cont/profil/publicare/`,
  `?job=abc`, `?week=lol`, `?days=abc`, `POST /dashboard/`; the `Site` row; the
  `DirectorySitemap` URL count; the seeded `WageFloor`/`MinijobThreshold`/`ContractTemplate`
  rows; `import psycopg` / `import dj_database_url`; `find apps -name admin.py`;
  `grep -rn "PRIVATE_STORAGE_ROOT|AuditLog|storage=|hx-" apps config tests templates`
