# Implementierung Django — models, services, publication flow, timezones, recipes

Covers: the real models and services in `apps/planning` with their exact fields, the plan
publication flow end to end, timezone handling under `TIME_ZONE = "Europe/Berlin"` + `USE_TZ`,
and step-by-step recipes for the most likely changes.

**Stand: 2026-08-29.** Every line number was read from the working tree on that date; the repo is
edited concurrently, so re-open the file before citing a line. Runtime facts verified with
`/Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python`.

---

## 1. Environment, verified

| Fact | Value |
|---|---|
| Python | 3.12.13, venv at `/Users/Geronimo/Projects/Cleaning_SaaS/.venv` |
| Django | **5.2.17** installed; `pyproject.toml` only pins `django>=5.1,<6.0` |
| Also installed | `django_allauth 65.19.1`, `django_htmx 1.29.0`, `factory_boy 3.3.3`, `faker 40.37.0`, `pillow 12.3.0`, `pytest 9.1.1`, `pytest_django 4.14.0`, `openpyxl 3.1.5`, `sqlparse 0.6.0` |
| Not installed | `psycopg`, `dj-database-url` — declared/imported but absent. `config/settings.py` imports `dj_database_url` only when `DATABASE_URL` is set, so dev works; setting `DATABASE_URL` today crashes with `ImportError` |
| `pip` inside the venv | not available (`No module named pip`) |
| DB | sqlite `db.sqlite3` |
| Test suite | `.venv/bin/python -m pytest` → **190 passed** (~80 s, verified 2026-08-29 — re-run and record the count yourself, the suite grows) |
| `pytest.ini` | `DJANGO_SETTINGS_MODULE=config.settings`, `python_files=test_*.py`, `addopts=-q --reuse-db`, `testpaths=tests` |
| ruff | `line-length = 100`, `target-version = "py312"` (`pyproject.toml`) |
| Migrations chain (planning) | `0001_initial` → `0002_shift_actual_minutes_shift_checked_in_at_and_more` → `0003_zonecalibration` → `0004_zone_description` |

Commands that work:

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py showmigrations
.venv/bin/python -m pytest -q
.venv/bin/python manage.py runserver 8099 --noreload
```

`INSTALLED_APPS` local block (`config/settings.py:26-37`): `apps.accounts`, `apps.geo`,
`apps.taxonomy`, `apps.jobs`, `apps.catalog`, `apps.contracts`, `apps.planning`, `apps.devices`,
`apps.marketplace`, `apps.dashboard`.

---

## 2. File map of `apps/planning`

| Path | Lines | Role | Key symbols |
|---|---|---|---|
| `models.py` | 292 | 6 models + 5 module-level `TextChoices` + 1 nested enum | `Site`, `Zone`, `PlanStatus`, `ShiftPlan`, `ShiftStatus`, `Shift`, `ShiftEvent` (+ `ShiftEvent.Kind`), `CalibrationStatus`, `Confidence`, `ZoneCalibration` |
| `services.py` | 188 | weekly plan generation + capacity report | `MAX_DAILY_MINUTES`, `MIN_REST_MINUTES`, `SUNDAY`, `DAY_START`, `WEEKS_PER_MONTH`, `WorkerCapacity`, `build_capacities`, `_fits`, `generate_week_plan`, `_visit_days`, `capacity_report` |
| `attendance.py` | 205 | publication, notification, lifecycle, working-time register | `RETENTION_YEARS`, `ShiftError`, `publish_plan`, `_notify_workers`, `_login_email`, `_guard`, `confirm_shift`, `decline_shift`, `check_in`, `check_out`, `correct_minutes`, `mark_missed`, `time_records` |
| `calibration.py` | 237 | estimate calibration | see `references/kalibrierung.md` |
| `reinigungsplan.py` | 102 | XLSX export | `WEEKDAY_DE`, `HEADERS`, `frequency_label`, `zone_rows`, `build_workbook`, `filename` |
| `views.py` | 310 | 3 CBVs + 6 FBVs (+ the `_monday` helper), all dashboard-side | `_monday`, `SiteListView`, `SiteCreateView`, `ZoneCreateView`, `planning_view`, `publish_plan_view`, `my_shifts_view`, `time_records_view`, `calibration_view`, `reinigungsplan_view` |
| `forms.py` | 44 | 2 ModelForms | `SiteForm`, `WEEKDAYS`, `ZoneForm` |
| `apps.py` | 7 | AppConfig | `PlanningConfig` (`name = "apps.planning"`, `verbose_name = "Planificare"`, `default_auto_field = "django.db.models.BigAutoField"`) |
| `migrations/` | 4 files | auto-generated only — no hand-written data migration in this app |

**There is no `admin.py`, no app-level `urls.py`, no signals, no management commands, no
`tasks.py`, no Celery.** `find apps -name "admin.py"` returns nothing across the whole project;
`find apps -type d -name management` returns only `apps/jobs/management` — `apps/planning` has no management commands.

Routes live only in `apps/dashboard/urls.py:32-42` under `app_name = "dashboard"`, mounted at
`path("dashboard/", include("apps.dashboard.urls"))` (`config/urls.py`).

---

## 3. Models — exact fields

### `Site` — `models.py:21-39` (table `planning_site`)

`account` FK Account CASCADE `related_name="sites"` · `name` CharField(160) ·
`locality` FK geo.Locality PROTECT `related_name="sites"` · `street` CharField(160, blank) ·
`postal_code` CharField(5, blank) · `is_active` BooleanField(True).
`Meta`: `ordering = ("name",)`, `verbose_name = "Obiectiv"`. `__str__` → `self.name`.
No `clean()`, no constraints, no indexes.

### `Zone` — `models.py:42-87` (table `planning_zone`)

`site` FK Site CASCADE `related_name="zones"` · `name` CharField(160) ·
`category` FK taxonomy.ServiceCategory PROTECT `related_name="zones"` ·
`description` CharField(300, blank, help_text `"Instrucțiuni pentru lucrător — apar în
Reinigungsplan și la check-in"`) · `area_sqm` PositiveIntegerField(null, blank) ·
`minutes_per_visit` PositiveSmallIntegerField(help_text `"Durata estimată a unei vizite"`) ·
`visits_per_week` PositiveSmallIntegerField(default 1) ·
`allowed_weekdays` CharField(13, default `"1,2,3,4,5"`) · `is_active` BooleanField(True).
`Meta`: `ordering = ("site", "name")`, `verbose_name = "Zonă"`.
Properties `weekdays` (`:74-76`) and `weekly_minutes` (`:78-80`); `clean()` at `:82-87`.

### `ShiftPlan` — `models.py:96-128` (table `planning_shiftplan`)

`account` FK CASCADE `related_name="shift_plans"` · `week_start` DateField(help_text `"Luni"`) ·
`status` CharField(12, `PlanStatus.choices`, default DRAFT) — **no `db_index`** ·
`unmet_demand` JSONField(default list, blank) · `published_at` DateTimeField(null, blank) ·
`created_at` DateTimeField(auto_now_add).
`Meta`: `ordering = ("-week_start",)`, `UniqueConstraint(("account","week_start"),
name="uniq_plan_per_week")`.
`week_end` `:118-120` · `planned_minutes` `:122-124` (Python-side sum over `shifts.all()`,
**not** an aggregate) · `clean()` `:126-128` rejects a non-Monday.

### `Shift` — `models.py:140-185` (table `planning_shift`)

`plan` FK ShiftPlan CASCADE `related_name="shifts"` · `zone` FK Zone **PROTECT**
`related_name="shifts"` · `worker` FK Account null/blank **SET_NULL** `related_name="shifts"` ·
`date` DateField · `start_time` TimeField · `duration_minutes` PositiveSmallIntegerField ·
`status` CharField(12, `ShiftStatus.choices`, default PLANNED, **`db_index=True`**) ·
`checked_in_at` / `checked_out_at` DateTimeField(null, blank) ·
`actual_minutes` PositiveSmallIntegerField(null, blank) · `worker_note` CharField(300, blank).
`Meta`: `ordering = ("date", "start_time")`, `indexes = [Index(("plan","worker","date"))]`
(DB name `planning_sh_plan_id_cf0cb0_idx`), `verbose_name = "Tură"`.

Properties: `hours` (`:171-173`, Decimal, based on **planned** duration, **referenced nowhere**),
`billable_minutes` (`:175-178`, `actual_minutes` if set else `duration_minutes`),
`variance_minutes` (`:180-185`, `actual_minutes - duration_minutes` or `None`).

**No `clean()` on `Shift` and no DB constraint** tying `date` into
`plan.week_start … week_start+6` — `tests/test_calibration.py:53-66` deliberately violates it.

**`actual_minutes` is `PositiveSmallIntegerField`** (max 32767 ≈ 22.7 days). A worker who checks
in and never checks out for three weeks overflows on save; `correct_minutes` accepts any int from
the POST body with no upper bound.

### `ShiftEvent` — `models.py:188-220` (table `planning_shiftevent`)

`shift` FK Shift CASCADE `related_name="events"` · `kind` CharField(12, `Kind.choices`) ·
`actor` FK Account **`null=True` but NOT `blank=True`** SET_NULL `related_name="shift_events"` ·
`payload` JSONField(default dict, blank) · `created_at` DateTimeField(auto_now_add).
`Meta`: `ordering = ("created_at",)`. No constraints, no indexes.

`Kind` (`:195-202`): `PUBLISHED` „Plan publicat" · `CONFIRMED` „Tură confirmată" · `DECLINED`
„Tură refuzată" · `CHECK_IN` „Începere lucru" · `CHECK_OUT` „Încheiere lucru" · `CORRECTED`
„Corecție de către angajator" · `MISSED` „Marcat neefectuat".

The immutability enforcement, `:217-220`:

```python
def save(self, *args, **kwargs):
    if self.pk:
        raise RuntimeError("Evenimentele de pontaj sunt imutabile.")
    super().save(*args, **kwargs)
```

It raises `RuntimeError`, not `ValidationError`/`ShiftError`. It blocks `.save()` on a loaded
instance but **does not** block `QuerySet.update()` or `.delete()`, and cascade deletes happen
silently.

`payload` shapes actually written: `DECLINED` → `{"reason": reason[:300]}` (`attendance.py:106-109`);
`CHECK_IN` → `{"at": now.isoformat()}` (`:120-123`); `CHECK_OUT` → `{"at": …, "minutes": …}`
(`:140-143`); `CORRECTED` → `{"from": previous, "to": minutes, "reason": reason[:300]}`
(`:161-164`); `PUBLISHED`, `CONFIRMED`, `MISSED` → `{}` (default).

### Enums and their column widths — the trap

| Enum | Column | `max_length` | Longest current value |
|---|---|---|---|
| `PlanStatus` (`:90-93`) | `ShiftPlan.status` | 12 | `"PUBLISHED"` (9) |
| `ShiftStatus` (`:131-137`) | `Shift.status` | 12 | **`"IN_PROGRESS"` (11)** — one character of headroom |
| `ShiftEvent.Kind` (`:195-202`) | `ShiftEvent.kind` | 12 | `"PUBLISHED"` / `"CORRECTED"` (9) |
| `CalibrationStatus` (`:223-226`) | `ZoneCalibration.status` | 10 | `"PROPOSED"` / `"REJECTED"` (8) |
| `Confidence` (`:229-232`) | `ZoneCalibration.confidence` | 8 | `"MEDIUM"` (6) |

Any new value longer than the column needs an `AlterField` migration on that field.

`PlanStatus.ARCHIVED` is defined and **never assigned anywhere** — there is no archival flow.

---

## 4. The publication flow, end to end

```
1. employer opens  GET  /dashboard/planificare/?week=YYYY-MM-DD
                        views.planning_view:60-96
                        → capacity_report(account, week_start)     services.py:172-188
                        → renders dashboard/planning.html

2. employer POSTs  POST /dashboard/planificare/?week=…
                        views.planning_view:73-80
                        → generate_week_plan(account, week_start)  services.py:98-156
                          @transaction.atomic
                          a. reject non-Monday                      :100-101
                          b. ShiftPlan.get_or_create                :103
                          c. if existed: refuse if PUBLISHED and not replace; else
                             plan.shifts.all().delete()             :104-109
                          d. build_capacities                       :111
                          e. zones ordered -minutes_per_visit       :112-116
                          f. per zone × _visit_days: first fitting capacity wins,
                             else append to `unmet`                 :121-141
                          g. Shift.objects.bulk_create(shifts)      :153
                          h. plan.save(update_fields=["unmet_demand"])  :154-155
                        → messages.success("Plan generat: N ture, M vizite nealocate.")
                        → redirect ?week=…

3. employer POSTs  POST /dashboard/planificare/<pk>/publicare/
                        views.publish_plan_view:121-133
                        → publish_plan(plan, actor=account)         attendance.py:29-45
                          @transaction.atomic
                          a. refuse if already PUBLISHED            :31-32
                          b. refuse if plan.shifts is empty         :33-34
                          c. status=PUBLISHED, published_at=now()
                             save(update_fields=["status","published_at"])  :36-38
                          d. ONE ShiftEvent(PUBLISHED) per shift, individual create() calls  :40-41
                          e. _notify_workers(plan)                  :43-44
                        → messages.success("Plan publicat. N ture trimise lucrătorilor.")
                        → redirect ?week=…

4. worker opens    GET  /dashboard/turele-mele/?week=…
                        views.my_shifts_view:136-181
                        filter(worker=account, plan__status=PUBLISHED, date in week)

5. worker POSTs    confirm | decline | check_in | check_out        attendance.py:91-144
                        each: _guard → mutate → append ShiftEvent

6. employer opens  GET  /dashboard/pontaj/?week=…
                        views.time_records_view:184-223
                        → time_records(account, week_start, week_end)  attendance.py:178-205
                        → POST correct | missed                        attendance.py:147-175
```

### `bulk_create` is the reason model-level validation cannot save you

`services.py:153` uses `Shift.objects.bulk_create(shifts)`. That **bypasses `save()`,
`full_clean()` and every signal**. Anything you need enforced on a generated `Shift` must be
correct at construction time (`services.py:145-148`).

### Publication side effects, exactly

* `plan.status = PUBLISHED`, `plan.published_at = timezone.now()`.
* One `ShiftEvent(kind=PUBLISHED, actor=actor)` per shift — a **loop of individual
  `create()` calls**, not `bulk_create` (because `ShiftEvent.save()` is overridden).
* One email per worker, sent **synchronously inside the publish transaction**, `fail_silently=True`.
  German subject and body, see `references/zuteilung-und-vertretung.md` §5.1.
* `publish_plan(plan, notify=False)` skips only the email. Tests use the default.

### `publish_plan_view` authorisation is thin

`views.py:121-133`: the **only** check is
`get_object_or_404(ShiftPlan, pk=pk, account=request.account)`. There is no capability check and
no `request.account is None` check — an anonymous user matches `account=None`, which matches
nothing, so they get a 404. **Do not copy that pattern into a view where `account` can be
nullable and still match something.**

### The regeneration hole

`generate_week_plan(replace=True)` deletes and rebuilds the shifts but **saves only
`unmet_demand`** (`services.py:154-155`). Therefore:

1. `status` stays `PUBLISHED` and `published_at` is unchanged.
2. No new `PUBLISHED` events are emitted and no email is sent — workers instantly see a
   completely different set of shifts and nothing in the journal says when.
3. `plan.shifts.all().delete()` **CASCADE-deletes `ShiftEvent`** (`models.py:204`) and wipes
   `checked_in_at` / `checked_out_at` / `actual_minutes`. On a week where people already worked,
   this destroys legally required working-time evidence (§16 ArbZG). **There is no guard against
   regenerating a week containing `DONE` shifts.**
4. `TelemetrySession.shift` is `SET_NULL` (`apps/devices/models.py:115`), so telemetry survives
   with `shift = NULL` and is never re-matched — matching happens only once, at ingestion.

`tests/test_attendance.py:72-75` asserts that the regeneration *works*, not that anyone was told.

---

## 5. Views

| View | file:line | URL | Gate | Notes |
|---|---|---|---|---|
| `SiteListView` | `views.py:23-30` | `/dashboard/obiective/` | `CapabilityRequiredMixin` + `OwnedByAccountMixin`, `(EMPLOYER, PROVIDER)` | `get_queryset()` adds `.prefetch_related("zones__category")` |
| `SiteCreateView` | `:33-43` | `/dashboard/obiective/nou/` | same mixin | `form_valid()` sets `form.instance.account` **before** `super()`; `get_success_url()` returns the hard-coded `"/dashboard/obiective/"` |
| `ZoneCreateView` | `:46-57` | `/dashboard/obiective/zona-noua/` | same mixin | `get_form_kwargs()` injects `account`; that is the **only** isolation for zones, because `ZoneForm` narrows `site` to the account's active sites (`forms.py:36`) |
| `planning_view` | `:60-96` | `/dashboard/planificare/` | inline: `account is None` → onboarding redirect; then `{EMPLOYER, PROVIDER}` else `PermissionDenied` (imported *inside* the function at `:66`) | POST generates; GET builds a 7-day `grid` |
| `publish_plan_view` | `:121-133` | `/dashboard/planificare/<pk>/publicare/` | ownership only | non-POST → `redirect("dashboard:planning")` |
| `my_shifts_view` | `:136-181` | `/dashboard/turele-mele/` | **no capability gate** (intentional) | POST dispatch on `action`; `today = timezone.localdate()` in context |
| `time_records_view` | `:184-223` | `/dashboard/pontaj/` | `{EMPLOYER, PROVIDER}` | catches `(ShiftError, ValueError)` — the `ValueError` catch is what turns a garbage `minutes` field into a flash message instead of a 500 |
| `calibration_view` | `:238-287` | `/dashboard/calibrare/` | `{EMPLOYER, PROVIDER}` | the only view using a **named** redirect (`redirect("dashboard:calibration")`) — copy this one |
| `reinigungsplan_view` | `:296-310` | `/dashboard/obiective/<pk>/reinigungsplan.xlsx` | `account is None` → `PermissionDenied`; then `get_object_or_404(Site, pk=pk, account=account)` | returns `FileResponse(as_attachment=True, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")` |

**`my_shifts_view` POST table** (`views.py:153-171`), after
`get_object_or_404(Shift, pk=request.POST.get("shift"), worker=request.account)`:

| `action` | call | message |
|---|---|---|
| `confirm` | `confirm_shift(shift, request.account)` | success `"Tură confirmată."` |
| `decline` | `decline_shift(shift, request.account, request.POST.get("reason", ""))` | **info** `"Tură refuzată. Angajatorul a fost informat."` — *nothing is actually sent* |
| `check_in` | `check_in(shift, request.account)` | success `"Pontaj început."` |
| `check_out` | `check_out(shift, request.account, note=request.POST.get("note", ""))` | success `f"Pontaj încheiat: {shift.actual_minutes} min."` |

**`_monday`** (`views.py:15-20`) parses `?week=YYYY-MM-DD` (or `date.today()` when absent) and
snaps to that ISO week's Monday. It uses `date.today()` — **server-local, not
`timezone.localdate()`** — and a malformed `?week=lol` raises `ValueError` → HTTP 500. Every
planning page shares this.

**Import layout.** `views.py` has three banner-separated mid-file import blocks, each marked
`# noqa: E402`: attendance at `:101-118` (including `from datetime import datetime` at `:101`
which is **never used**), calibration at `:228-235`, Reinigungsplan at `:291-293`. That layout is
deliberate; do not "tidy" it without checking ruff.

---

## 6. Permission primitives

* `apps.accounts.middleware.ActiveAccountMiddleware` is **last** in `MIDDLEWARE`
  (`config/settings.py:49`) and sets `request.account` and `request.membership` on **every**
  request; both are `None` for anonymous users (`apps/accounts/middleware.py:18-25`).
* `AccountRequiredMixin(LoginRequiredMixin)` (`apps/accounts/permissions.py:14-20`) — an
  authenticated user without an account is redirected to `accounts:onboarding`.
* `CapabilityRequiredMixin(AccountRequiredMixin)` (`:23-44`) — `required_capability` is a str or
  a tuple; **any** match wins; failure raises `PermissionDenied` (403), deliberately not a
  redirect: *„un cont fără capabilitate nu trebuie să afle ce există la acel URL."*
* `OwnedByAccountMixin` (`:47-57`) — `get_queryset()` filters by
  `**{self.account_field: self.request.account}`, `account_field = "account"` by default.
* `Capability` (`apps/accounts/enums.py:11-21`): `WORKER`, `PROVIDER`, `SUPPLIER`, `CLIENT`,
  `EMPLOYER`.
* **Never add a `role` column or a per-model Django permission** — the rule is stated at
  `apps/accounts/permissions.py:1-7`.

---

## 7. Date and time under `Europe/Berlin` + `USE_TZ`

`config/settings.py:107-110`:

```python
LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
```

`django.middleware.locale.LocaleMiddleware` is **not** installed, there are no `.po` files and no
`LOCALE_PATHS`, so the `de` locale affects only Django-supplied formats/labels — every project
string is hard-coded Romanian or German.

**The subsystem deliberately runs two clocks.**

**Clock 1 — naive local planning clock.** `Shift.date` (`DateField`) + `Shift.start_time`
(`TimeField`) carry no timezone at all. `generate_week_plan` builds
`datetime.combine(day, DAY_START)` (`services.py:144`) — a **naive** datetime — only to derive
`.time()` for the field and to fill `cap.day_end`. That naive value is never persisted, so Django
never emits `RuntimeWarning: DateTimeField received a naive datetime`. The 11 h-rest arithmetic
(`services.py:90-94`) compares two naive datetimes, which is internally consistent. **DST is
ignored**: a shift at 07:00 is 07:00 wall-clock in Berlin on both sides of the March/October
switch — which is the correct behaviour for a roster.

**Clock 2 — aware attendance clock.** `checked_in_at`, `checked_out_at`, `published_at`,
`decided_at`, `created_at` are `DateTimeField`s written with `timezone.now()` (UTC-aware, stored
as UTC). `check_out` compares two aware datetimes (`attendance.py:131`) — safe. `actual_minutes`
is a true elapsed-time delta computed with **floor** division
(`int((now - shift.checked_in_at).total_seconds() // 60)`, `attendance.py:133`), so a shift
spanning a DST switch yields real elapsed minutes, not wall-clock minutes.

**Boundary points where the two clocks meet:**

| Where | Code | Verdict |
|---|---|---|
| `my_shifts_view` "can I check in yet" | `today = timezone.localdate()` (`views.py:180`) compared in the template as `{% if s.date <= today %}` (`my_shifts.html:24`) | **correct** — `date` vs `date` in Berlin local time |
| `views._monday` | `date.today()` (`views.py:19`) | **suspect** — server-local, coincides with Berlin only when the server TZ is Berlin. Prefer `timezone.localdate()` if you touch this line |
| `calibration._window_start` / cooldown | `last_applied.decided_at.date()` (`calibration.py:79, 93`) | **off-by-one risk** — that is the **UTC** date of an aware datetime; between midnight and 01:00/02:00 Berlin it is the previous calendar day. Correct form: `timezone.localtime(...).date()`. Do not change it without a boundary test |
| `time_records`' `retention_until` | `end + timedelta(days=365 * RETENTION_YEARS)` (`attendance.py:205`) | **leap-year-naive** — a flat 730 days. `tests/test_attendance.py` asserts only `>= 730` |
| `devices._overlaps` | `timezone.make_aware(datetime.combine(shift.date, shift.start_time))` (`apps/devices/services.py:109-117`) | **the one place** that bridges the naive planning clock into the aware clock. On the March switch a 02:xx `start_time` is a *non-existent* local time and on the October switch it is *ambiguous*; `zoneinfo` resolves rather than raising, but the result is fold-dependent |

**No recurrence rules exist.** No RRULE, no `dateutil.rrule`, no recurring-shift model.
Recurrence is declared per zone (`visits_per_week` + `allowed_weekdays`) and materialised **one
week at a time** by `_visit_days` inside `generate_week_plan`. Each week is an independent
`ShiftPlan`; nothing rolls forward and there is no scheduler to generate next week's plan.

---

## 8. Conventions when extending

1. **Authorisation = capability + ownership.** Use `CapabilityRequiredMixin` +
   `OwnedByAccountMixin` on CBVs, or the inline
   `if not ({Capability.EMPLOYER, Capability.PROVIDER} & request.account.capability_set()):
   raise PermissionDenied` pattern on FBVs (`views.py:64-68`, `:188-189`, `:242-243`).
2. **Always scope querysets by the tenant** — `account=`, `site__account=`, `plan__account=`,
   `zone__site__account=`. Never trust a pk from `request.POST` or the URL without adding the
   account filter to `get_object_or_404`.
3. **Business logic in `services.py` / `attendance.py` / `calibration.py`, never in views.**
   Every mutating service is `@transaction.atomic` and saves with explicit `update_fields=[...]`.
4. **Refusals return a reason string, not a boolean** (`_fits`,
   `ContractDraft.compliance_issues()`). The employer must see *why*.
5. **Unallocatable work goes to `plan.unmet_demand`, never into an over-budget shift.** Keep the
   exact dict shape `{"zone","site","date","minutes","reasons"}`.
6. **Legal constants get a named module constant with the paragraph in the comment.** Annually
   changing amounts belong in DB rows with `valid_from`/`valid_to` (`apps/contracts/models.py:57-113`).
7. **`ShiftEvent` is append-only.** Any state change a labour inspector could care about must
   create an event; never mutate one, never delete one.
8. **Raise `ShiftError` (a `ValueError` subclass) for illegal shift transitions**, catch it in
   the view. Calibration decisions raise plain `ValueError` — match the module you are editing
   rather than "harmonising" them.
9. **Language split** — see SKILL.md P12.
10. **New enums are `models.TextChoices` at module level in `models.py`** (except
    `ShiftEvent.Kind`, which is nested inside its model — keep it there).
11. **Truncate free text in the service, not the form**: `reason[:300]` / `note[:300]`
    (`attendance.py:104, 108, 138, 163`; `calibration.py:203, 217`).
12. **Tests are Romanian snake_case method names** with a module docstring stating *the rule the
    tests defend* — see `tests/test_planning.py:1-7`. Reuse the `tests/conftest.py` fixtures:
    `employer`, `worker`, `norderstedt`, `pinneberg`, `category`, `signed_contract`,
    `next_monday`. Anchor planning tests on `MONDAY = date(2026, 10, 5)`, calibration tests on
    `timezone.localdate()`.
13. **URL names are English, paths are Romanian**, and they are all registered in
    `apps/dashboard/urls.py`.
14. **Prefer `reverse()` / `{% url %}` for new redirects.** Existing planning views hard-code
    `"/dashboard/…/"` strings; `calibration_view` is the one that uses `redirect("dashboard:calibration")`.
15. **Dashboard tiles are data**, one `Panel(...)` row in `apps/dashboard/panels.py` — see the
    docstring at `panels.py:1-7`.

---

## 9. Recipes

### Recipe 1 — add a field to `Shift` (worked example: `break_minutes`, §4 ArbZG)

1. **Model** — `apps/planning/models.py`, inside `class Shift`, after `duration_minutes`
   (line 149) so field order mirrors the planning fields:

```python
    # §4 ArbZG: 30 min pauză după 6 h, 45 min după 9 h. Pauza NU e timp de lucru.
    break_minutes = models.PositiveSmallIntegerField(default=0)
```

Use `null=True, blank=True` instead if it must be nullable, like `actual_minutes` (`:159`).

2. **Adjust derived properties** if it changes billing. `billable_minutes` (`:175-178`) becomes:

```python
    @property
    def billable_minutes(self) -> int:
        """Timpul real dacă a fost pontat, altfel cel planificat, minus pauza."""
        base = self.actual_minutes if self.actual_minutes is not None else self.duration_minutes
        return max(0, base - self.break_minutes)
```

That single change moves `my_shifts_view`'s `done_minutes` (`views.py:173`) **and**
`time_records`' `totals_minutes` (`attendance.py:203`) at once — intended, both go through
`billable_minutes`.

3. **Populate it where shifts are created** — `services.py:145-148`:

```python
            shifts.append(Shift(
                plan=plan, zone=zone, worker_id=candidate.account_id, date=day,
                start_time=start.time(), duration_minutes=zone.minutes_per_visit,
                break_minutes=_statutory_break(zone.minutes_per_visit),
            ))
```

`bulk_create` skips `save()`/`full_clean()` — the value must be correct at construction time.

4. **Write it at check-out** — `attendance.py:127-144`. Add it to both the assignment block
   **and** the `save(update_fields=[...])` list, and put the raw value in the `CHECK_OUT`
   payload so the journal stays self-describing:

```python
    shift.save(update_fields=["checked_out_at", "actual_minutes", "status", "worker_note", "break_minutes"])
    ShiftEvent.objects.create(
        shift=shift, kind=ShiftEvent.Kind.CHECK_OUT, actor=account,
        payload={"at": now.isoformat(), "minutes": minutes, "break": shift.break_minutes},
    )
```

**Every `save(update_fields=[...])` in `attendance.py` is explicit — forgetting to add the new
field there is the #1 way this change silently no-ops.**

5. **Surface it in the register** — `attendance.py:193-202`, add `"break": shift.break_minutes,`
   to the row dict, plus a `<th>Pauză</th>` and `<td>{{ r.break }} min</td>` in
   `templates/dashboard/time_records.html:9-15`.
6. **Migration** (do NOT run it unless asked):
   `.venv/bin/python manage.py makemigrations planning` → expect `0005_shift_break_minutes.py`.
7. **Test** in `tests/test_attendance.py`, Romanian name:

```python
    def test_pauza_nu_intra_in_timpul_facturabil(self, shift, worker):
        start = timezone.now()
        check_in(shift, worker, now=start)
        check_out(shift, worker, now=start + timedelta(minutes=150))
        shift.refresh_from_db()
        assert shift.billable_minutes == 150 - shift.break_minutes
```

### Recipe 2 — add a hard planning rule (worked example: §11 ArbZG, max 6 consecutive days)

1. **Constant** next to the block at `services.py:27-31`:

```python
MAX_CONSECUTIVE_DAYS = 6         # §11 ArbZG: cel puțin o zi liberă pe săptămână
```

2. **Per-worker state** — extend `WorkerCapacity` (`services.py:34-48`) only if you need new
   state. For this rule nothing new is needed: `per_day.keys()` already records the worked days.
3. **The check goes into `_fits`** (`services.py:82-95`) and must return a **Romanian reason
   string naming the paragraph**, matching its neighbours:

```python
    worked = sorted(set(cap.per_day) | {day})
    run = 1
    for prev, nxt in zip(worked, worked[1:]):
        run = run + 1 if (nxt - prev).days == 1 else 1
        if run > MAX_CONSECUTIVE_DAYS:
            return "a 7-a zi lucrătoare consecutivă (§11 ArbZG)"
```

Place it **after** the locality and budget checks so the cheapest/most-informative refusal still
wins.

4. **Nothing else changes** — `generate_week_plan` already funnels every refusal into
   `reasons[cap.name]` and then into `plan.unmet_demand` (`services.py:124-141`), and
   `templates/dashboard/planning.html:39-46` already renders arbitrary reason dicts.
5. **Test** in `tests/test_planning.py::TestPlanGeneration`, mirroring
   `test_nu_depaseste_8_ore_pe_zi` (`:86-97`):

```python
    def test_a_saptea_zi_consecutiva_nu_se_aloca(self, employer, signed_contract, zone):
        signed_contract(hours="200")
        zone(minutes=60, visits=7, weekdays="1,2,3,4,5,6")
        plan = generate_week_plan(employer, MONDAY)
        assert plan.shifts.count() <= 6
```

6. Document it in the module docstring list at `services.py:9-15`, which currently enumerates
   exactly five hard constraints.

### Recipe 3 — add a `ShiftStatus` value and a lifecycle transition (worked example: `CANCELLED`)

1. **Enum** — `models.py:131-137`: `CANCELLED = "CANCELLED", "Anulat"` (9 chars, fits
   `max_length=12`).
2. **Transition function** in `attendance.py`, shaped like `mark_missed` (`:168-175`) because
   this is an employer action:

```python
@transaction.atomic
def cancel_shift(shift: Shift, employer_account, reason: str) -> Shift:
    if shift.plan.account_id != employer_account.pk:
        raise ShiftError("Doar angajatorul poate anula o tură.")
    if shift.status in {ShiftStatus.DONE, ShiftStatus.IN_PROGRESS}:
        raise ShiftError(f"Tura este în starea {shift.get_status_display()}.")
    shift.status = ShiftStatus.CANCELLED
    shift.save(update_fields=["status"])
    ShiftEvent.objects.create(
        shift=shift, kind=ShiftEvent.Kind.CANCELLED, actor=employer_account,
        payload={"reason": reason[:300]},
    )
    return shift
```

3. **Event kind** — add `CANCELLED = "CANCELLED", "Tură anulată"` to `ShiftEvent.Kind`
   (`models.py:195-202`); 9 chars ≤ `max_length=12`.
4. **Decide whether the status is "open" or "closed", then update all four enumerations:**
   * `attendance.py:185` — `status__in=[DONE, MISSED]` (the register)
   * `views.py:214` — `.exclude(status__in=[DONE, MISSED])` ("Ture neîncheiate")
   * `calibration.py:101` — `status=ShiftStatus.DONE` (calibration sample)
   * `views.py:173` — `if s.status == ShiftStatus.DONE` (worker's weekly total)

   and grep `apps/devices` — `find_discrepancies` filters `status=ShiftStatus.DONE`
   (`apps/devices/services.py:130-177`).
5. **Wire the POST action** in `time_records_view` (`views.py:194-209`) next to
   `"correct"` / `"missed"`, and add the button to `templates/dashboard/time_records.html:25-29`.
6. **URL/name**: none needed — the action rides on the existing `/dashboard/pontaj/` POST.
7. **Migration**: `makemigrations planning` produces an `AlterField` on `Shift.status` and
   `ShiftEvent.kind` (choices changed). Django records choice changes even though they are not
   DDL on sqlite.

### Recipe 4 — add a `Zone` field that steers the planner (worked example: `earliest_start`)

1. **Model** — `models.py`, in `class Zone` after `allowed_weekdays` (line 63):

```python
    # Unele obiective nu pot fi curățate înainte de închiderea programului.
    earliest_start = models.TimeField(null=True, blank=True)
```

2. **Form** — add `"earliest_start"` to `ZoneForm.Meta.fields` (`forms.py:30-31`). Note that
   `weekdays` is **declared, not in `Meta.fields`**, and is folded into `allowed_weekdays` inside
   `clean()` (`forms.py:40-44`) — copy that pattern only for fields needing a non-model widget.
3. **Planner** — `services.py:143-151`, replace the fixed `DAY_START` base:

```python
            base = datetime.combine(day, zone.earliest_start or DAY_START)
            start_minutes = candidate.per_day.get(day, 0)
            start = base + timedelta(minutes=start_minutes)
```

   ⚠️ **This makes the §5 rest check reachable for the first time**, and `cap.per_day`
   (a minutes-worked counter) stops being a valid offset from `DAY_START`. You must then track
   `cap.day_end[day]` as the real cursor instead of `per_day`.
4. **Templates** — add a column to `templates/dashboard/sites.html:8-14`; consider adding it to
   `HEADERS`/`zone_rows` in `reinigungsplan.py` too.
5. `makemigrations planning` → `0005_zone_earliest_start.py`. Extend the `zone` factory fixture
   in `tests/test_planning.py:35-43`.

### Recipe 5 — make a published plan regenerable from the dashboard

`planning_view` currently calls `generate_week_plan(request.account, week_start)` with
`replace=False` and does **not** catch `ValueError` (`views.py:74`), so pressing "Regenerează
planul" on a published week is a **500**. Minimal fix:

```python
    if request.method == "POST":
        replace = request.POST.get("replace") == "1"
        try:
            plan = generate_week_plan(request.account, week_start, replace=replace)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect(f"/dashboard/planificare/?week={week_start.isoformat()}")
```

plus `<input type="hidden" name="replace" value="1">` behind a confirmation in
`templates/dashboard/planning.html:16-20`.

**Do not ship only that.** Before it is correct you must also:

* refuse to delete shifts that are `DONE` or `IN_PROGRESS` (working-time evidence, §16 ArbZG);
* emit fresh `ShiftEvent`s for what changed, or re-run `publish_plan`;
* re-notify the affected workers (`_notify_workers`'s `by_worker` grouping,
  `attendance.py:50-53`, is already the right shape).

See §4 "The regeneration hole".

### Recipe 6 — add a Site/Zone edit view (the missing CRUD)

There is **no `SiteUpdateView` / `ZoneUpdateView` and no delete view anywhere**, yet
`ZoneForm.__init__` already contains the edit-path code
`if self.instance.pk: self.fields["weekdays"].initial = self.instance.weekdays`
(`forms.py:37-38`).

1. Add `SiteUpdateView(CapabilityRequiredMixin, OwnedByAccountMixin, UpdateView)` — the
   `OwnedByAccountMixin` is what stops a guessed pk from exposing another tenant's Objekt.
2. For zones, `OwnedByAccountMixin` will not work directly (`Zone` has no `account` field): set
   `account_field = "site__account"` or override `get_queryset()` with
   `Zone.objects.filter(site__account=self.request.account)`.
3. **Give the update views their own template.** `templates/dashboard/site_form.html` is 5 lines,
   shared by both create views, and its `<h1>` renders `{{ view.form_class.Meta.model }}` — a
   Python class repr like `<class 'apps.planning.models.Site'>`. Adding a third and fourth view
   to it makes that wart worse.
4. **Deletion must be a soft delete.** `Zone` is `PROTECT`-referenced by `Shift`
   (`models.py:142`), so a hard delete of a zone with history raises. Use `is_active = False` —
   the generator, the calibration scan and the Reinigungsplan export all already filter on it.
5. Add routes to `apps/dashboard/urls.py` next to the existing ones (`:32-36`), Romanian paths,
   English names.

### Recipe 7 — replace the Python-side sums with aggregates

`ShiftPlan.planned_minutes` (`models.py:122-124`) and `capacity_report`'s `demand`
(`services.py:174-179`) are Python-side `sum()` calls that load every row. If you convert them:

* `planned_minutes` → `self.shifts.aggregate(models.Sum("duration_minutes"))["duration_minutes__sum"] or 0`.
  Watch out: `templates/dashboard/planning.html:23` renders it, and the planning view already
  iterates `plan.shifts` for the grid (`views.py:85-86`), so the aggregate adds a query rather
  than saving one on that page.
* `capacity_report`'s demand cannot become a plain aggregate without care — it must stay
  `minutes_per_visit * visits_per_week` summed, i.e.
  `.aggregate(total=Sum(F("minutes_per_visit") * F("visits_per_week")))`. Note the report is
  already *wrong* in a different way (it uses the **uncapped** weekly minutes while the plan caps
  visits at `len(allowed)` weekdays), so fix the semantics before optimising the query.

---

## 10. Gotchas ranked by how often they bite

1. **Regenerating a plan destroys the attendance journal** (§4). No guard exists.
2. **`generate_week_plan(replace=True)` leaves the plan `PUBLISHED`, emits no events and sends no
   email.**
3. **Pressing "Regenerează planul" on a published week is a 500** (Recipe 5).
4. **The §5 (11 h rest) rule is dead code** with the current `DAY_START` and `MAX_DAILY_MINUTES`.
5. **`visits_per_week` is silently capped** by `min(zone.visits_per_week, len(allowed))` and by
   one-visit-per-day; the lost demand does not appear in `unmet_demand`, and `capacity_report`
   disagrees with the plan.
6. **One `WorkerCapacity` per contract, not per person** — the ArbZG limits are computed per
   contract, which is legally wrong. Untested.
7. **`bulk_create` bypasses `save()`, `full_clean()` and signals.**
8. **`ShiftEvent` immutability only blocks `.save()` on a loaded instance** — `QuerySet.update()`,
   `.delete()` and cascades are unguarded.
9. **Template status comparisons use raw strings** — `{% if plan.status == 'DRAFT' %}`
   (`planning.html:24`), `{% if s.status == 'PLANNED' %}` (`my_shifts.html:16`),
   `{% elif s.status == 'IN_PROGRESS' %}` (`:28`). Renaming a `TextChoices` **value** breaks the
   UI with no Python error.
10. **`ZoneForm.clean()` writes `self.instance.allowed_weekdays` directly** because `weekdays` is
    not a model field; `construct_instance` only touches `Meta.fields`, which is why the
    assignment survives. Adding `allowed_weekdays` to `Meta.fields` would overwrite it.
11. **`ZoneForm` never offers Sunday, `Zone.clean()` accepts 7, the planner strips it** — three
    layers, one rule.
12. **`request.account` is `None` for anonymous users.** The FBVs redirect to onboarding, except
    `publish_plan_view`, which relies on `get_object_or_404(..., account=None)` returning 404.
13. **`_monday` raises on garbage input** → 500 on every planning page.
14. **`actual_minutes` is a `PositiveSmallIntegerField`** (max 32767); `correct_minutes` has no
    upper bound.
15. **`correct_minutes` forces `status = DONE`** (`attendance.py:159`) even for a shift never
    checked in, and does **not** call `_guard` — it can resurrect a `DECLINED` or `MISSED` shift
    into `DONE`.
16. **`time_records`' `totals_minutes` can be keyed by `None`** (`attendance.py:203`) when an
    unassigned shift is marked `MISSED`.
17. **`calibration_view` runs `analyze_zone` once per active zone on every GET** — O(zones × 3)
    queries, no caching.
18. **`ShiftEvent.actor` is `null=True` but not `blank=True`** — a ModelForm over `ShiftEvent`
    would require it. Nothing builds one today.
19. **`site_form.html` is shared by two create views** and its `<h1>` prints a class repr.
20. **`apps.devices` reads planning models** — grep both apps before renaming `ShiftStatus`,
    `Shift.actual_minutes`, `Shift.date`/`start_time`/`duration_minutes` or `Site`.
    `apps/devices/migrations/0001_initial.py:13` depends on `planning.0003_zonecalibration`.
21. **`PlanStatus.ARCHIVED` is never used.** Do not assume an archival flow.
22. **`Shift.hours` is referenced nowhere.** `Zone.area_sqm` is editable via `ZoneForm.Meta.fields` (`forms.py:30`) but is never used in any calculation — no planner, calibration or export code reads it.

---

## 11. Cross-subsystem coupling: `apps.devices`

The **only** module outside `apps.planning` that imports planning models. It changes the blast
radius of any `Shift` / `Site` edit.

| Planning object | Consumer | Definition |
|---|---|---|
| `planning.Site` | `devices.Device.site` | `ForeignKey("planning.Site", null=True, blank=True, on_delete=SET_NULL, related_name="devices", help_text="Obiectivul unde staționează")` — `apps/devices/models.py:49` |
| `planning.Shift` | `devices.TelemetrySession.shift` | `ForeignKey("planning.Shift", null=True, blank=True, on_delete=SET_NULL, related_name="telemetry_sessions")` — `apps/devices/models.py:115` |
| `Shift`, `ShiftStatus` | `apps/devices/services.py:9` | `from apps.planning.models import Shift, ShiftStatus` |
| `Site` | `apps/devices/forms.py:3` | scopes `site` to `Site.objects.filter(account=account, is_active=True)` — same tenant pattern as `ZoneForm` |
| migration order | `apps/devices/migrations/0001_initial.py:13` | `('planning', '0003_zonecalibration')` |

What it reads: `match_shift` (`services.py:89-106`) selects shifts of the same account within
±1 day, optionally narrowed by `zone__site_id=device.site_id`, and **returns a match only if
exactly one shift overlaps** (`matches[0] if len(matches) == 1 else None`). `_overlaps`
(`:109-117`) uses `MATCH_TOLERANCE = timedelta(hours=2)` (`:14`). `find_discrepancies`
(`:130-177`) reads `status=DONE, actual_minutes__isnull=False` and compares `actual_minutes`
against summed `runtime_minutes`, with `SUSPICIOUS_RATIO = 0.10` (`:16`) yielding
`kind="LOW_ACTIVITY"`, a `DONE` shift with no session at a site that has active devices yielding
`"NO_TELEMETRY"`, and more device minutes than clocked minutes yielding `"OVER_RUNTIME"`.

**The boundary is stated explicitly** at `apps/devices/models.py:1-15`: *„telemetria e sursă de
VERIFICARE, nu sursă de calibrare"*. Do **not** wire `TelemetrySession.runtime_minutes` into
`apps/planning/calibration.py`.

---

## 12. Templates

All planning templates extend `templates/base.html` — a 16-line skeleton with `<html lang="de">`,
`<title>{% block title %}Cleaning SaaS{% endblock %}</title>`, a `{% if messages %}` block at
`:9-13` and a single `{% block content %}` at `:14`. **No CSS, no JS, no htmx attribute
anywhere**, despite `django_htmx` being installed (`config/settings.py:25, 48`) — every
interaction is a full form POST + redirect.

| Template | Lines | Notes |
|---|---|---|
| `dashboard/sites.html` | 16 | per site: `<h2>{{ s.name }} — {{ s.locality.name }}</h2>`, the Reinigungsplan download link, and a zone table `Zonă / Serviciu / Instrucțiuni / Durată / Vizite/săpt. / Total/săpt.` Empty states `Nicio zonă definită.` / `Niciun obiectiv.` |
| `dashboard/site_form.html` | 5 | shared by **both** create views; `<h1>` renders a class repr |
| `dashboard/planning.html` | 48 | week nav, `Capacitate` block, deficit warning (*„orele contractate sunt plafon legal"*), generate button (disabled when `not zones`), publish form shown only `{% if plan.status == 'DRAFT' %}`, the 7-day grid, the `Vizite nealocate` table iterating `u.reasons.items` |
| `dashboard/my_shifts.html` | 36 | per-shift `<article>` with confirm/decline, check-in gated on `{% if s.date <= today %}`, check-out with a `note` input; empty state `Nicio tură publicată pentru această săptămână.` (asserted as `b"Nicio tur"` by `tests/test_attendance.py`) |
| `dashboard/time_records.html` | 32 | the compliance disclaimer (`BAG 1 ABR 22/21, §3 ArbSchG`, retention `§16 ArbZG`), the `Înregistrări` table, and the `Ture neîncheiate` table whose per-row form carries `minutes` + `reason` and two submit buttons (`action=correct`, `action=missed`) |
| `dashboard/calibration.html` | 51 | see `references/kalibrierung.md` §7 |

Dashboard tiles (`apps/dashboard/panels.py:60-79`):
`Panel("my_shifts", "Turele mele", "Program, confirmare și pontaj", "dashboard:my_shifts",
Capability.WORKER, order=15)` · `Panel("sites", "Obiective și zone", …, Capability.EMPLOYER,
order=30)` · `Panel("planning", "Planificare săptămânală", "Ture generate în limita orelor
contractate", …, order=35)` · `Panel("time_records", "Pontaj", "Evidența timpului de lucru
(§16 ArbZG)", …, order=36)` · `Panel("calibration", "Calibrare estimări", …, order=37)` ·
`Panel("devices", …, order=38)` · `Panel("discrepancies", …, order=39)`.

---

## Quellen

Repository (read 2026-08-29, paths relative to `/Users/Geronimo/Projects/Cleaning_SaaS`):

* `apps/planning/models.py` (292 lines), `services.py` (188), `attendance.py` (205),
  `calibration.py` (237), `reinigungsplan.py` (102), `views.py` (310), `forms.py` (44),
  `apps.py` (7)
* `apps/planning/migrations/0001_initial.py`, `0002_shift_actual_minutes_shift_checked_in_at_and_more.py`,
  `0003_zonecalibration.py`, `0004_zone_description.py`
* `apps/accounts/permissions.py` 1-62, `apps/accounts/middleware.py` 14-38,
  `apps/accounts/enums.py` 11-21, `apps/accounts/models.py` 89-159, `apps/accounts/profiles.py` 86-97
* `apps/contracts/models.py` 79-178
* `apps/devices/models.py` 1-15, 49, 115; `apps/devices/services.py` 9, 14, 16, 89-180;
  `apps/devices/forms.py` 3; `apps/devices/migrations/0001_initial.py` 13
* `apps/dashboard/urls.py` 1-51, `apps/dashboard/panels.py` 1-110
* `config/settings.py` 20-64, 107-122; `config/urls.py`
* `templates/base.html`, `templates/dashboard/{sites,site_form,planning,my_shifts,time_records,calibration}.html`
* `tests/conftest.py` (92 lines), `tests/test_planning.py` (199), `tests/test_attendance.py` (199),
  `tests/test_calibration.py` (224), `tests/test_reinigungsplan.py` (98)
* `pytest.ini`, `pyproject.toml`

Runtime verification (2026-08-29, `.venv/bin/python`): `pytest` → 190 passed;
`Decimal("40")*60/(Decimal("52")/Decimal("12"))` → 553; the `_visit_days` spread table;
`round(120.5) == 120`; `openpyxl.__version__ == "3.1.5"`.

No pland.app page is cited in this file — it is entirely repository-derived.
