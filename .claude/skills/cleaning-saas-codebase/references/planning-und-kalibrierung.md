# Planung, Zeiterfassung, Kalibrierung, Geräte — `apps.planning` + `apps.devices`

**Covers:** the planning models, the weekly-plan algorithm, the attendance (Pontaj) state
machine, the calibration engine, and the telemetry layer — condensed to what an editor of this
repo needs.
**Stand: 2026-08-29.**
**Sources:** `apps/planning/*.py`, `apps/devices/*.py`, `templates/dashboard/*`,
`tests/test_planning.py`, `tests/test_attendance.py`, `tests/test_calibration.py`,
`tests/test_devices.py`, `tests/test_reinigungsplan.py` — all opened and confirmed 2026-08-29;
cross-checked against `scratchpad/dossier/planning-core.md`, `planning-attendance.md`,
`planning-calibration.md`.

> **For the German domain rules** — what ArbZG actually requires, what a Dienstplan must
> contain, how Zeiterfassung must be kept for a Zoll/FKS audit, Ruhepausen, Zuschläge — use the
> sibling skills **`gr-einsatzplanung`** and **`gr-zeiterfassung`**. This file is about how
> *this repository* implements a subset of them, and where it does not.

---

## 1. Models — `apps/planning/models.py` (Fakt)

Module docstring (`:1-12`) states the governing idea:

> *"Ideea centrală: orele din contract nu sunt o preferință, sunt un PLAFON LEGAL. Un Minijob
> de 40 h/lună care primește 12 ore într-o săptămână nu e o problemă de planificare — e o
> depășire a Geringfügigkeitsgrenze care transformă raportul de muncă în unul asigurat
> obligatoriu. […] Al doilea set de constrângeri vine din Arbeitszeitgesetz: maximum 8 h pe zi
> (§3), minimum 11 h de odihnă între ture (§5), duminica liberă (§9)."*

| Model | file:line | Key fields | Notes |
|---|---|---|---|
| `Site` (Obiectiv) | `:21-39` | `account` FK CASCADE `related_name="sites"`, `name`, `locality` FK PROTECT, `street`, `postal_code(5)`, `is_active` | the building/residence being cleaned |
| `Zone` (Zonă) | `:42-87` | `site` FK CASCADE `related_name="zones"`, `name`, `category` FK `taxonomy.ServiceCategory` PROTECT, `description(300)`, `area_sqm` (**never used in any calculation**), `minutes_per_visit`, `visits_per_week` (default 1), `allowed_weekdays` (`CharField(13)`, default `"1,2,3,4,5"`, ISO indices 1=Mon…7=Sun), `is_active` | the planning granularity — not the whole building, but "floor 2, corridor + toilets" |
| `ShiftPlan` | `:96-128` | `account` FK, `week_start` (must be a Monday), `status` (`DRAFT`/`PUBLISHED`/`ARCHIVED`), `unmet_demand` (**JSONField**, default `list`), `published_at`, `created_at`. `UniqueConstraint(("account","week_start"))` | `ARCHIVED` is never assigned |
| `Shift` (Tură) | `:140-185` | `plan` FK CASCADE `related_name="shifts"`, `zone` FK PROTECT, `worker` FK `accounts.Account` `SET_NULL`, `date` (`DateField`), `start_time` (`TimeField`), `duration_minutes`, `status`, `checked_in_at`, `checked_out_at`, `actual_minutes`, `worker_note(300)`. `indexes=[Index(("plan","worker","date"))]` | comment `:154-156` cites **BAG 13.09.2022 (1 ABR 22/21)** + **§3 Abs. 2 Nr. 1 ArbSchG** and **§16 ArbZG** 2-year retention |
| `ShiftEvent` | `:188-220` | `shift` FK **CASCADE**, `kind` (`PUBLISHED`/`CONFIRMED`/`DECLINED`/`CHECK_IN`/`CHECK_OUT`/`CORRECTED`/`MISSED`), `actor` FK `SET_NULL`, `payload` JSONField, `created_at` | **append-only**: `save()` raises `RuntimeError` if `self.pk` |
| `ZoneCalibration` | `:235-292` | `zone` FK CASCADE `related_name="calibrations"`, `sample_size`, `window_start/end`, `current_minutes`, `suggested_minutes`, `median_minutes`, `dispersion_minutes` (MAD), `confidence`, `status`, `decided_by`, `decided_at`, `decision_note(300)`. **Partial** `UniqueConstraint(("zone",), condition=Q(status="PROPOSED"))` | one open proposal per zone |

`ShiftStatus` (`:131-137`): `PLANNED` · `CONFIRMED` · `DECLINED` · `IN_PROGRESS` · `DONE` ·
`MISSED`.
`CalibrationStatus` (`:223-226`): `PROPOSED` · `APPLIED` · `REJECTED`.
`Confidence` (`:229-232`): `LOW` · `MEDIUM` · `HIGH`.

Useful derived properties:

```python
Zone.weekdays          -> list[int]   # models.py:74-76, parses allowed_weekdays
Zone.weekly_minutes    -> int         # :78-80,  minutes_per_visit * visits_per_week
ShiftPlan.week_end     -> date        # :118-120
ShiftPlan.planned_minutes -> int      # :122-124, PYTHON-side sum, loads every row
Shift.hours            -> Decimal     # :171-173, UNREFERENCED anywhere
Shift.billable_minutes -> int         # :175-178, actual_minutes or duration_minutes
Shift.variance_minutes -> int | None  # :180-185, actual - planned
ZoneCalibration.delta_minutes          # :285-287
ZoneCalibration.weekly_impact_minutes  # :289-292, delta * zone.visits_per_week
```

---

## 2. The planner — `apps/planning/services.py` (Fakt)

Docstring (`:1-15`): *"Nu e un optimizator matematic — e un repartizor lacom cu constrângeri
tari. […] dacă o vizită nu încape fără să spargă o regulă, rămâne NEALOCATĂ și apare în raport
cu motivul."*

### Constants — `:27-31`

| Constant | Value | Basis |
|---|---|---|
| `MAX_DAILY_MINUTES` | `480` | §3 ArbZG (8 h; 10 h only with compensation within 6 months) |
| `MIN_REST_MINUTES` | `11 * 60` | §5 ArbZG |
| `SUNDAY` | `7` | §9 ArbZG |
| `DAY_START` | `time(7, 0)` | all shifts stack from 07:00 |
| `WEEKS_PER_MONTH` | `Decimal("52") / Decimal("12")` | monthly contract hours → weekly budget |

### Capacity comes only from signed contracts — `build_capacities()` `:51-79`

```python
contracts = (ContractDraft.objects
             .filter(employer=account, status=DraftStatus.SIGNED, start_date__lte=week_end)
             .exclude(end_date__lt=week_start)
             .select_related("worker"))
weekly = int(Decimal(contract.hours_per_month) * 60 / WEEKS_PER_MONTH)
localities = set(contract.worker.areas.values_list("locality_id", flat=True)) \
             or {contract.workplace_id}
```

Docstring: *"Fără contract semnat, un om nu poate fi planificat — planificarea nu e locul unde
se creează raporturi de muncă."*

**Load-bearing subtlety:** the served-locality set falls back to `{contract.workplace_id}` only
when the worker has **zero** `ServiceArea` rows. Add one `ServiceArea` elsewhere and the worker
stops serving the contract's workplace. `tests/test_planning.py:111-119` exploits this.

**Known modelling error:** `WorkerCapacity` is built **per contract, not per person**
(`:65-78`). Two concurrent contracts for the same human give two independent weekly budgets and
two independent `per_day`/`day_end` dicts, so the 8 h/day and 11 h rest checks are computed per
contract — legally wrong, since ArbZG limits are per person. Untested.

### The refusal predicate — `_fits()` `:82-95`

Returns the **reason string**, or `None` if the shift fits:

| Reason (Romanian, verbatim) | Rule |
|---|---|
| `"nu deservește localitatea"` | locality mismatch |
| `f"buget săptămânal epuizat ({cap.weekly_minutes} min contractate)"` | contract-hour ceiling |
| `"ar depăși 8 h într-o zi (§3 ArbZG)"` | §3 ArbZG |
| `"sub 11 h de odihnă față de tura anterioară (§5 ArbZG)"` | §5 ArbZG |

The §5 check is **effectively dead code** with the current `DAY_START = 07:00` and
`MAX_DAILY_MINUTES = 480`: the previous day can end at most at 15:00, and 07:00 next day is
16 h later. Do not cite it as "implemented" and do not assume it protects you if you ever make
start times configurable.

### `generate_week_plan(account, week_start, replace=False)` — `:98-156`

1. Rejects a non-Monday `week_start` with a **bare `ValueError`** (`:100-101`).
2. `get_or_create` the plan. If it exists and is `PUBLISHED` and `replace` is False, raises
   `ValueError("Planul e publicat. Regenerarea cere confirmare explicită.")` (`:107-108`).
3. Otherwise `plan.shifts.all().delete()` (`:109`).
4. Zones sorted `-minutes_per_visit` — heavy tasks first, they fit less easily (`:115`).
5. For each visit day, workers sorted by `-remaining`; the first that `_fits` gets it.
6. Unallocated visits go into `plan.unmet_demand` as
   `{"zone", "site", "date", "minutes", "reasons": {worker_name: reason}}` (`:134-140`).
7. `Shift.objects.bulk_create(shifts)` (`:153`) — **bypasses `save()`, `full_clean()` and
   signals**. Anything you need enforced on a generated `Shift` must be true at construction.

`_visit_days()` (`:159-169`) spreads visits evenly across the allowed weekdays, excluding
Sunday. **`visits_per_week` is silently capped** by `min(visits_per_week, len(allowed))` and by
one visit per day — a zone with `visits_per_week=10` on 5 allowed days produces 5 shifts and
**zero** `unmet_demand` entries, while `capacity_report()`'s `demand_minutes` uses the uncapped
`weekly_minutes`. Report and plan disagree.

`capacity_report(account, week_start)` — `:172-188` — returns
`{demand_minutes, supply_minutes, workers, deficit_minutes, utilisation}` (both sums computed
in Python, not with `.aggregate()`).

---

## 3. Attendance / Pontaj — `apps/planning/attendance.py` (Fakt)

Docstring (`:1-12`) cites **BAG 13.09.2022 (1 ABR 22/21)** on **§3 Abs. 2 Nr. 1 ArbSchG** —
the employer must record *all* working time, not only overtime — and **§16 Abs. 2 ArbZG** for
the 2-year retention. `RETENTION_YEARS = 2` (`:22`).

`class ShiftError(ValueError)` (`:25-26`) — every state-transition refusal.

### `_guard(shift, account, allowed)` — `:82-88`

Three conditions, in order: the shift belongs to the account · the plan is `PUBLISHED` · the
current status is in `allowed`. Applied by `confirm_shift`, `decline_shift`, `check_in`,
`check_out` — **but not by `correct_minutes` or `mark_missed`**.

### Transitions

| Function | file:line | From | To | Event written |
|---|---|---|---|---|
| `publish_plan(plan, actor, notify=True)` | `:29-45` | `DRAFT` | `PUBLISHED` | one `PUBLISHED` event per shift; refuses an already-published plan and a plan with no shifts |
| `confirm_shift(shift, account)` | `:91-97` | `PLANNED` | `CONFIRMED` | `CONFIRMED` |
| `decline_shift(shift, account, reason="")` | `:100-110` | `PLANNED`/`CONFIRMED` | `DECLINED` | `DECLINED` with `payload={"reason": …}` |
| `check_in(shift, account, now=None)` | `:113-124` | `PLANNED`/`CONFIRMED` | `IN_PROGRESS` | `CHECK_IN` with `payload={"at": iso}` |
| `check_out(shift, account, now=None, note="")` | `:127-144` | `IN_PROGRESS` | `DONE` | `CHECK_OUT` with `{"at","minutes"}`; computes `actual_minutes = (now - checked_in_at) // 60`; refuses `now <= checked_in_at` |
| `correct_minutes(shift, employer_account, minutes, reason)` | `:147-165` | any | `DONE` | `CORRECTED` with `{"from","to","reason"}`; requires `plan.account == employer` **and a non-empty reason**; **does not call `_guard`** |
| `mark_missed(shift, employer_account)` | `:168-175` | any | `MISSED` | `MISSED`; **does not clear `actual_minutes`** |

`_notify_workers(plan)` (`:48-74`) sends **one email per worker, not per shift**, with subject
`f"Dein Einsatzplan ab {plan.week_start:%d.%m.%Y}"` and body opening `"Deine Einsätze:\n\n"` —
German, because it goes to the worker. `fail_silently=True`; workers with no address are
skipped; `publish_plan` discards the returned count. `EMAIL_BACKEND` is the console backend and
`DEFAULT_FROM_EMAIL` is unset, so `from_email=None` resolves to `webmaster@localhost`.

### `time_records(account, start, end, worker=None)` — `:178-205`

The audit view — *"ce trebuie să poți arăta la un control (Zoll / FKS)"*. Returns
`{"rows": [...], "totals_minutes": {worker_id: minutes}, "retention_until": end + 730 days}`.
Each row carries `worker`, `date`, `site`, `zone`, `planned`, `actual`, `variance`, `status`.
Only `DONE` and `MISSED` shifts are included; a `MISSED` shift contributes `actual = 0`.
The `worker=` parameter works but **has no caller**.

---

## 4. Calibration — `apps/planning/calibration.py` (Fakt)

Docstring (`:1-19`) states four design decisions:

1. **Median, not mean** — one 300-minute shift (a flood, a handover) would poison the estimate.
2. **Double threshold** — the deviation must be **both** relative (≥ 15 %) **and** absolute
   (≥ 10 min).
3. **Minimum sample, and a window that starts at the last *applied* calibration** — otherwise
   you measure the error of an estimate that no longer exists and the system oscillates.
4. **A cooldown after applying**, for the same reason.

### Constants — `:36-40`

| Constant | Value |
|---|---|
| `MIN_SAMPLE` | `5` |
| `MIN_RELATIVE_DEVIATION` | `0.15` |
| `MIN_ABSOLUTE_DEVIATION` | `10` |
| `COOLDOWN_DAYS` | `28` |
| `MAX_LOOKBACK_DAYS` | `180` |

### `analyze_zone(zone, today=None) -> Analysis` — `:83-132`

1. Window start = `max(today - 180d, last_applied.decided_at.date())` (`_window_start`, `:74-80`).
2. If a calibration was applied **less than 28 days ago**, bail out with
   `"Calibrat recent; se așteaptă 28 de zile de date noi."` (`:91-97`).
3. Collect `actual_minutes` of `DONE` shifts of that zone in the window.
4. If fewer than 5 → `"Prea puține ture pontate (n/5)."`
5. Compute `median` (`_median`, `:61-66`) and `dispersion` = **MAD** (`_mad`, `:69-71`).
6. **Bail-out** at `:118`:
   ```python
   if abs(deviation) < MIN_ABSOLUTE_DEVIATION or relative < MIN_RELATIVE_DEVIATION:
       ... return analysis     # not actionable
   ```
   Read this as: **actionable requires BOTH thresholds**. Changing `or` to `and` inverts the
   whole policy.
7. Otherwise set `suggested_minutes = round(median)` and a confidence.

`_confidence(sample, dispersion, median)` — `:135-142`, where `spread = dispersion / median`:

| Confidence | Condition |
|---|---|
| `HIGH` | `sample >= 12` **and** `spread <= 0.15` |
| `MEDIUM` | `sample >= 8` **and** `spread <= 0.30` |
| `LOW` | otherwise |

Sample size gates before consistency: fourteen identical shifts give `HIGH`, six identical
shifts give `LOW`. That gate is the point.

**`round()` is banker's rounding.** `round(120.5) == 120`, `round(127.5) == 128`.
`tests/test_calibration.py` depends on the first. Do not switch to `int(median + 0.5)` or
`ROUND_HALF_UP` without expecting test churn.

### `propose_calibrations(account, today=None)` — `:145-186`

For every active zone on an active site:
- not actionable → an existing `PROPOSED` row is auto-rejected with
  `"Retrasă automat: datele noi nu o mai susțin."`
- actionable and an identical proposal exists → skip
- actionable and a different proposal exists → reject it with
  `"Înlocuită de o propunere mai recentă."` and create the new one

### `apply_calibration` / `reject_calibration` — `:189-219`

Both require `status == PROPOSED` and `calibration.zone.site.account_id == actor.pk`, and both
raise a plain `ValueError`. `apply_calibration` writes
`zone.save(update_fields=["minutes_per_visit"])` — which **skips `Zone.clean()`**.

**The proposal is never applied automatically.** The `ZoneCalibration` docstring (`:236-245`)
gives the reason: `minutes_per_visit` is the planner's input and the planner produces
contractual obligations; a value that moves on its own makes the plan unpredictable and hides
the interesting signal.

**Applying does not change existing shifts.** `Shift.duration_minutes` was snapshotted at
generation time (`services.py:147`); only a regeneration picks up the new value — which is what
the flash message says (*"Regenerează planul ca să se aplice."*, `views.py:266`) and which is
dangerous on a published week (see §7 P1/P2).

`pending_impact(account)` — `:222-237` — returns
`{count, weekly_delta_minutes, increases, decreases}`. `weekly_delta_minutes` is a **signed
net** — `+120` and `−120` net to `0`. Never present it alone as "how much work changed".

---

## 5. Telemetry — `apps.devices` (Fakt)

Module docstring (`apps/devices/models.py:1-15`) states the governing principle:

> *"timpul de funcționare al unui aspirator nu este timpul de curățenie."* In a 120-minute
> visit the vacuum may run 25. Telemetry therefore **confirms** that work happened, surfaces
> **discrepancies**, and gives an objective **lower bound** — it is a source of VERIFICATION,
> **not** a source of calibration, and not a replacement for Zeiterfassung.

| Model | file:line | Notes |
|---|---|---|
| `Device` | `:38-91` | `account` FK, `kind` (`VACUUM`/`SCRUBBER`/`POLISHER`/`STEAM`/`OTHER`), `label`, `manufacturer`, `model_name`, `serial_number`, `site` FK `planning.Site` `SET_NULL` ("Obiectivul unde staționează"), `status` (`ACTIVE`/`MAINTENANCE`/`RETIRED`), `token_hash` (unique, `editable=False`), `token_prefix(8)`, `last_seen_at`. `hash_token()` = SHA-256; `issue_token()` returns the raw key **once**; `is_online` = seen within 86400 s |
| `TelemetrySession` | `:94-136` | `device` FK, `external_id`, `started_at`, `ended_at`, `runtime_minutes`, `area_sqm`, `battery_start/end`, `error_code`, `raw_payload` JSONField, `shift` FK `planning.Shift` `SET_NULL` `related_name="telemetry_sessions"`, `received_at`. `UniqueConstraint(("device","external_id"))` makes ingestion idempotent |

### The ingest endpoint — `POST /api/telemetry/` (`apps/devices/api.py`)

Auth is `Authorization: Bearer <raw token>`, compared **on the hash** — a database read does not
let you forge telemetry (`api.py:1-7`, `services.py:23-31`). `@csrf_exempt @require_POST`.

| Condition | Status |
|---|---|
| bad / missing / retired token | **401** |
| malformed JSON or non-object body | **400** |
| `TelemetryError` from `ingest_session` | **422** |
| new session created | **201** |
| duplicate `external_id` | **200** |

Response body: `{"id", "created", "matched_shift", "runtime_minutes"}`.

`ingest_session()` (`services.py:34-75`) requires `external_id`, `started_at`, `ended_at`;
rejects `ended <= started`, a start more than 5 minutes in the future, and a `runtime_minutes`
that exceeds the reported interval by more than 1.

`match_shift()` (`services.py:89-106`) is deliberately conservative: candidates are the
account's shifts within ±1 day (narrowed to the device's site when set), and a session is
attached **only if exactly one** candidate overlaps within `MATCH_TOLERANCE = 2 h`. Two
candidates → no attribution.

`find_discrepancies(account, start, end)` (`services.py:130-177`) compares pontaj against
runtime for `DONE` shifts with `actual_minutes`:

| Kind | Condition |
|---|---|
| `NO_TELEMETRY` | no sessions **and** the site has an `ACTIVE` device |
| `LOW_ACTIVITY` | `device_minutes / actual_minutes < SUSPICIOUS_RATIO` (`0.10`, `services.py:16`) |
| `OVER_RUNTIME` | `device_minutes > actual_minutes` |

Docstring: *"Nu produce sancțiuni — produce întrebări."*

`utilisation(account, start, end)` (`:186-200`) — per device: session count, runtime minutes,
m², error count, online flag.

---

## 6. Views, URLs, templates (Fakt)

`apps/planning/views.py` is organised in **three banner-separated sections** with mid-file
imports carrying `# noqa: E402` (`:101-118`, `:228-235`, `:291-293`). That layout is
deliberate — do not "tidy" it without checking ruff (`line-length = 100`, `py312`). Note
`from datetime import datetime` at `:101` is unused.

| Route (`apps/dashboard/urls.py`) | View | Guard |
|---|---|---|
| `/dashboard/obiective/` | `SiteListView` (`planning/views.py:23-30`) | `CapabilityRequiredMixin`, `(EMPLOYER, PROVIDER)` + `OwnedByAccountMixin` |
| `/dashboard/obiective/nou/` | `SiteCreateView` (`:33-43`) | same |
| `/dashboard/obiective/zona-noua/` | `ZoneCreateView` (`:46-57`) | same — **currently a 500, see §7 P8** |
| `/dashboard/obiective/<pk>/reinigungsplan.xlsx` | `reinigungsplan_view` (`:296-310`) | FBV; `get_object_or_404(Site, pk, account=request.account)` |
| `/dashboard/planificare/` | `planning_view` (`:60-96`) | FBV, inline guard |
| `/dashboard/planificare/<pk>/publicare/` | `publish_plan_view` (`:121-133`) | FBV; relies on `get_object_or_404(..., account=request.account)` — **`account=None` for anonymous just yields 404** |
| `/dashboard/turele-mele/` | `my_shifts_view` (`:136-181`) | FBV — **no capability check**, any account gets 200 with an empty list. Intentional (workers hold `WORKER`, not `EMPLOYER`) |
| `/dashboard/pontaj/` | `time_records_view` (`:184-223`) | FBV, `EMPLOYER` or `PROVIDER` |
| `/dashboard/calibrare/` | `calibration_view` (`:238-287`) | FBV, `EMPLOYER` or `PROVIDER` |
| `/dashboard/echipamente/` | `devices.views.device_list_view` (`:23-64`) | `_guard()` |
| `/dashboard/echipamente/discrepante/` | `devices.views.discrepancies_view` (`:67-82`) | `_guard()` |

`_monday(value)` (`planning/views.py:15-20`) parses `?week=` with `date.fromisoformat` — a
garbage value is a **500** on every planning page.

All state changes are `POST` + `name="action"` + PRG redirect. The redirects **hard-code
`/dashboard/...` literal paths** (`views.py:43,57,80,133,171,209`) rather than reversing —
renaming a URL segment breaks them with no `NoReverseMatch` to warn you. Grep the literal path.

Templates involved: `dashboard/sites.html`, `dashboard/site_form.html` (shared by two create
views), `dashboard/planning.html`, `dashboard/my_shifts.html`, `dashboard/time_records.html`,
`dashboard/calibration.html`, `dashboard/devices.html`, `dashboard/discrepancies.html`.
They compare status against **raw string literals** (`'PLANNED'`, `'DRAFT'`, `'IN_PROGRESS'`) —
renaming a `TextChoices` **value** silently removes buttons with no Python error. Rename labels
freely; never rename values without grepping `templates/`.

---

## 7. Traps that bite (Fakt — each verified)

| # | Trap | Evidence |
|---|---|---|
| P1 | **Regenerating a plan destroys the Zeiterfassung journal.** `plan.shifts.all().delete()` cascades to `ShiftEvent` (`models.py:204`, CASCADE) and wipes `checked_in_at`/`checked_out_at`/`actual_minutes` — legally required evidence under §16 Abs. 2 ArbZG. There is **no guard** against regenerating a week containing `DONE` shifts. | `services.py:109`; `tests/test_attendance.py:72-75` exercises this path on a published plan |
| P2 | **`generate_week_plan(replace=True)` leaves the plan `PUBLISHED`**, emits no new `PUBLISHED` events and sends no emails (only `unmet_demand` is saved). Workers see a different week with nothing in the journal saying when. | `services.py:154-155` |
| P3 | **Pressing "Regenerează planul" on a published week is a 500.** `planning_view` calls `generate_week_plan(...)` without `replace=True` and without `try/except`, and the service raises a bare `ValueError`. The calibration success message tells the user to do exactly this. | `views.py:73-80`, `services.py:107-108`, `views.py:263-267` |
| P4 | **`ShiftError` is a `ValueError`.** A broad `except ValueError` swallows every business rule; conversely `except ShiftError` does **not** catch `generate_week_plan`'s bare `ValueError`. | `attendance.py:25-26`, `services.py:108` |
| P5 | **`ShiftEvent` immutability only blocks `.save()` on a loaded instance.** `.update()`, `.delete()` and cascade deletes are unguarded. It also blocks a no-op `save(update_fields=[...])`. | `models.py:217-220` |
| P6 | **`mark_missed` does not clear `actual_minutes`.** A `DONE` shift with 95 recorded minutes later marked `MISSED` still holds 95; `time_records` then reports `actual: 0` and `variance: -25` in the same row. | `attendance.py:168-175`, `:190-202` |
| P7 | **`correct_minutes` does not call `_guard`.** It accepts a `PLANNED` shift and forces `DONE` with `checked_in_at = None`; it can resurrect a `DECLINED` or `MISSED` shift; a negative value is an uncaught `IntegrityError` (500); an empty `minutes` field surfaces the raw English `invalid literal for int()`. | `attendance.py:147-165`, `views.py:194-209` |
| P8 | **`/dashboard/obiective/zona-noua/` is a 500 today.** `site_form.html:2` renders `{{ view.form_class.Meta.model|default:"Adaugă" }}`; the template engine calls the model class, instantiating a bare `Zone()`, whose `__str__` dereferences `self.site` → `Zone.site.RelatedObjectDoesNotExist: Zone has no site`. The link is exposed at `sites.html:4`. No test covers it. | verified 2026-08-29 |
| P9 | **`ZoneForm.clean()` writes `self.instance.allowed_weekdays` directly** with `",".join(sorted(data["weekdays"]))` on **strings** — lexicographic sort, safe only while values are single digits 1–6. Adding `allowed_weekdays` to `Meta.fields` would silently overwrite it. | `forms.py:40-44` |
| P10 | **Sunday exists in three layers with one rule.** `ZoneForm.WEEKDAYS` stops at 6 (`forms.py:18`), `Zone.clean()` accepts 7 (`models.py:85-87`), `_visit_days` strips 7 (`services.py:161`). Change all three or none. | |
| P11 | **`actual_minutes` is `PositiveSmallIntegerField`** (max 32767 ≈ 22.7 days). A check-in never checked out for three weeks overflows on save. `correct_minutes` takes any `int` from the POST with no ceiling; SQLite does not enforce the range that PostgreSQL will. | `models.py:159` |
| P12 | **Two clocks.** `Shift.date`/`start_time` are naive local wall-clock (DST ignored); `checked_in_at`/`checked_out_at`/`decided_at` are aware UTC. `_window_start` and the cooldown use `decided_at.date()` — the **UTC** date — while `today` is `timezone.localdate()` in Europe/Berlin. Between 00:00 and 02:00 CEST they disagree by a day. | `services.py:144`, `calibration.py:79,93` |
| P13 | **The POST-redirect in both attendance views loses the week.** The forms post no `week` field, and the redirect re-parses `request.GET`, empty on a POST, so `_monday(None)` falls back to today's Monday. | `views.py:171,209` |
| P14 | **`{% if r.variance %}` and `{% if s.actual_minutes %}` hide the value 0.** A perfectly on-estimate shift renders as `—`. | dashboard templates |
| P15 | **`calibration_view` is O(zones × ~3) queries** — `analyze_zone` runs once per active zone on every GET and issues the same `calibrations.filter(status=APPLIED)` query twice (`calibration.py:76` and `:91`). No caching, no index on `status` or `zone__site__account`. | `views.py:285` |
| P16 | **The scan's zone filter and the page's zone filter differ.** `propose_calibrations` requires `site__is_active=True` (`calibration.py:151`); the view's `analyses` list does not (`views.py:275-277`). Zones on a deactivated site show a verdict but can never get a proposal. | |
| P17 | **`_login_email` picks `memberships…first()` with no ordering.** `Membership.Meta` defines none, so for a multi-membership worker the notification address is whatever the DB returns first. | `attendance.py:77-79` |
| P18 | **`device_list_view` puts a secret in a flash message.** The raw device token goes through the session-backed message store and into page HTML — the only place the plaintext ever exists. Do not log it, do not put it in a cacheable partial, be careful if the message storage backend ever changes to cookies. | `apps/devices/views.py:41-44`, `:51-54` |
| P19 | **`?days=` on `/dashboard/echipamente/discrepante/` is unvalidated.** `?days=abc` → 500; `?days=100000` → unbounded scan. | `apps/devices/views.py:72` |
| P20 | **`apps.devices` reads planning models.** `ShiftStatus`, `Shift.actual_minutes/date/start_time/duration_minutes` and `Site` all have an out-of-app consumer. Grep both apps before renaming any of them. `devices/0001_initial` depends on `planning.0003_zonecalibration`. | `apps/devices/services.py`, `models.py`, `forms.py` |

---

## 8. Reinigungsplan XLSX export — `apps/planning/reinigungsplan.py` (Fakt)

Docstring (`:1-10`): the competition sells an empty Excel template with four columns —
**Bereich, Leistung, Beschreibung, Reinigungsfrequenz**. This exports the same four **filled
from real objective data**, plus duration per visit and weekly minutes. *"Documentul e pentru
client și pentru lucrător, deci e în germană."*

Headers (`HEADERS`, `:18-26`) with column widths:
`Bereich / Ort` (34) · `Leistung` (30) · `Beschreibung` (46) · `Reinigungsfrequenz` (22) ·
`Dauer je Einsatz` (18) · `Wochentage` (18) · `Minuten / Woche` (16).

`WEEKDAY_DE` (`:16`): `{1:"Mo",2:"Di",3:"Mi",4:"Do",5:"Fr",6:"Sa",7:"So"}`.
`frequency_label()` (`:29-34`): `>= 7` → `"täglich"`, `1` → `"1× wöchentlich"`, else
`"{n}× wöchentlich"`.
`build_workbook()` (`:57-96`): title `f"Reinigungsplan — {site.name}"` at A1 (14 pt bold),
address at A2, header row 4 with fill `1F3A5F` and white bold text, a `Summe` row, freeze panes
below the header.
`filename()` (`:99-102`): `f"reinigungsplan-{slugify(site.name)}.xlsx"`.

`openpyxl` is imported **inside** `build_workbook` so the dependency stays optional (it is in
the `export` extra — and happens to be installed here, 3.1.5).

---

## 9. Gaps in this subsystem (Fakt — none of these are marked TODO in the code)

The code contains **zero** `TODO`/`FIXME`/`XXX` markers. These are gaps evidenced by absence:

1. No `Site`/`Zone` **edit or delete** UI — only create + list. `ZoneForm.__init__` carries
   dead `if self.instance.pk:` handling for an update view that does not exist.
2. No manual shift editing — a planner cannot move a shift, change its worker or split it.
3. No re-assignment after a decline. `DECLINED` is terminal, the work vanishes from the
   schedule and does **not** re-enter `unmet_demand`.
4. No employer notification on decline, despite the message *"Angajatorul a fost informat."*
   (`views.py:162`). That message is currently false.
5. No absence / holiday / sick-leave model. `ContractDraft.vacation_days` exists but planning
   never reads it; a worker on holiday is fully allocatable.
6. **§4 ArbZG breaks are not modelled** — no `break_minutes`; `check_out` bills the whole
   elapsed span. The only path to a break-corrected figure is a manual `correct_minutes`.
7. **§11 ArbZG** (one rest day per week / max 6 consecutive days) is not implemented.
8. Contracted hours are enforced **weekly**, never monthly — but the Geringfügigkeitsgrenze is
   a **monthly** limit. Four heavy weeks in a 5-week month can exceed the monthly cap while
   every individual week passes.
9. No geography or travel time. `WorkerProfile.willing_to_travel_km` and
   `Locality.latitude/longitude` are unused; back-to-back shifts at different sites get zero
   travel buffer.
10. `Zone.area_sqm` and `Zone.category` are stored but never used by the planner — no
    m²/hour productivity model and no skill matching against `AccountService`.
11. No payroll or cost layer. `ContractDraft.hourly_wage` exists; no planning code multiplies
    minutes by a wage.
12. No export for a real FKS audit — `time_records` produces an HTML table, no CSV/PDF.
13. No retention enforcement. `retention_until` is displayed; nothing archives, deletes or
    blocks early deletion (see P1).
14. No recurrence engine, no cron, no Celery, no roll-forward. Next week's plan exists only if
    a human clicks "Generează planul".
15. `PlanStatus.ARCHIVED` is never assigned.
16. No admin registration for any planning or devices model.
17. No index on `ShiftEvent(shift, kind)`.
18. No test covers the §5 rest rule, `SiteForm`/`ZoneForm`, or `_notify_workers`' fallback to
    `_login_email`.

---

## Quellen

- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`, `services.py`,
  `attendance.py`, `calibration.py`, `reinigungsplan.py`, `views.py`, `forms.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/devices/models.py`, `services.py`, `api.py`,
  `views.py`, `forms.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/dashboard/urls.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/templates/dashboard/sites.html`, `site_form.html`
- `/Users/Geronimo/Projects/Cleaning_SaaS/tests/test_planning.py`, `test_attendance.py`,
  `test_calibration.py`, `test_devices.py`, `test_reinigungsplan.py`
- `scratchpad/dossier/planning-core.md`, `planning-attendance.md`, `planning-calibration.md`
- Runtime check 2026-08-29: `/dashboard/obiective/zona-noua/` traceback
- Sibling skills for the German rules: `gr-einsatzplanung`, `gr-zeiterfassung`
