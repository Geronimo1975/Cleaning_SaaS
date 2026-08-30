# Die Implementierung in apps/planning — was wirklich im Code steht

Covers: the attendance engine as it is actually coded — every guard, every state
transition, the `actual_minutes` computation, what the 22 tests lock in — followed by the
gap list against the legal requirements in `rechtsgrundlagen.md` and
`stundenzettel-und-berechnung.md`.

**Stand:** 2026-08-29, files read directly at that moment. The repo is **not under
version control** (no `.git`) and is being edited concurrently — **re-open every file
before relying on a line number here.**

**Correction up front:** the brief for this skill assumed the implementation contains
"tolerance windows, distance checks and rounding". **It does not.** A grep
across `apps/`, `config/` and `tests/` for `lat`, `lng`, `latitude`, `longitude`, `geo`,
`geofen`, `distance`, `haversine`, `radius`, `ceil` returns no attendance hit at all;
the only `toleran`/`round` hits are `MATCH_TOLERANCE` (`apps/devices/services.py:14`,
used at `:115-116` to attach telemetry sessions to a shift window) and
`round(ratio, 2)` (`:162`, `:171`) — neither rounds recorded minutes.
`apps/planning/attendance.py` itself contains no geofence, distance check, tolerance
window or rounding logic. `actual_minutes` is raw floor-division minutes and nothing else. Those
three features are competitor behaviour (see `stundenzettel-und-berechnung.md` §6a and
`geofence-und-dsgvo.md` §2), not this codebase.

Labels: **Fakt** (file:line) · **Vorschlag** · **Ungeprüft**.

---

## 1. File map

| Path | Lines | Role |
|---|---|---|
| `apps/planning/attendance.py` | 205 | the whole service layer; module-level functions, no classes |
| `apps/planning/models.py` | 292 | `Site`, `Zone`, `PlanStatus`, `ShiftPlan`, `ShiftStatus`, `Shift`, `ShiftEvent`, `ZoneCalibration` |
| `apps/planning/views.py` | 310 | `publish_plan_view` (`:121`), `my_shifts_view` (`:136`), `time_records_view` (`:184`) |
| `apps/planning/services.py` | 188 | the planner that produces the `Shift` rows attendance operates on |
| `apps/planning/calibration.py` | 237 | **consumer**: reads `actual_minutes` of `DONE` shifts (`:99-104`) |
| `apps/devices/services.py` | 200 | **second consumer**: cross-checks pontaj against machine runtime (`:130-178`) |
| `apps/dashboard/urls.py` | 51 | `plan_publish` (`:38`), `my_shifts` (`:40`), `time_records` (`:41`) |
| `apps/dashboard/panels.py` | 110 | tiles `my_shifts` (`:60-61`), `time_records` (`:72-73`) |
| `templates/dashboard/my_shifts.html` | 36 | worker UI |
| `templates/dashboard/time_records.html` | 32 | employer UI |
| `tests/test_attendance.py` | 199 | 22 tests, 5 classes |

There is **no `apps/planning/admin.py`** — none of these models is registered in the
Django admin, which is what currently prevents an out-of-band edit of a `Shift`.

---

## 2. Data model (Fakt)

### `ShiftStatus` — `apps/planning/models.py:131-137`

```python
class ShiftStatus(models.TextChoices):
    PLANNED = "PLANNED", "Planificat"
    CONFIRMED = "CONFIRMED", "Confirmat"
    DECLINED = "DECLINED", "Refuzat"
    IN_PROGRESS = "IN_PROGRESS", "În desfășurare"
    DONE = "DONE", "Efectuat"
    MISSED = "MISSED", "Neefectuat"
```

The labels are Romanian **and user-visible**: they appear in the error text
`f"Tura este în starea {shift.get_status_display()}."` (`attendance.py:88`) and in the
`status` column of every `time_records()` row (`attendance.py:201`).

### `PlanStatus` — `apps/planning/models.py:90-93`

`DRAFT` / `PUBLISHED` / `ARCHIVED`. **`ARCHIVED` is never assigned anywhere** in the
codebase. Attendance treats anything that is not `PUBLISHED` as unworkable.

### `Shift` attendance columns — `apps/planning/models.py:151-160`

```python
status = models.CharField(max_length=12, choices=ShiftStatus.choices,
                          default=ShiftStatus.PLANNED, db_index=True)
# Evidența timpului de lucru nu e opțională: BAG 13.09.2022 (1 ABR 22/21)
# + §3 Abs. 2 Nr. 1 ArbSchG obligă angajatorul să înregistreze TOT timpul
# lucrat, nu doar orele suplimentare. Păstrare minimum 2 ani (§16 ArbZG).
checked_in_at = models.DateTimeField(null=True, blank=True)
checked_out_at = models.DateTimeField(null=True, blank=True)
actual_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
worker_note = models.CharField(max_length=300, blank=True)
```

`Meta`: `ordering = ("date", "start_time")`, `indexes = [Index(fields=("plan", "worker",
"date"))]` (`:162-166`).

Derived properties:

| Property | Definition | Line |
|---|---|---|
| `hours` | `(Decimal(duration_minutes) / 60).quantize(Decimal("0.01"))` — the **planned** hours, not the worked ones | `:171-173` |
| `billable_minutes` | `actual_minutes if actual_minutes is not None else duration_minutes` | `:175-178` |
| `variance_minutes` | `None` if not clocked, else `actual_minutes - duration_minutes` | `:180-185` |

**Watch out for `billable_minutes`.** It silently falls back to the *planned* duration
when nothing was clocked. It is only ever reached for `DONE` shifts inside
`time_records()` (`attendance.py:192`), where `actual_minutes` is always set — but any
new caller must not assume it means "measured".

`actual_minutes` is a `PositiveSmallIntegerField`: max 32767 minutes. Fine per shift,
wrong for any monthly aggregate.

### `ShiftEvent` — `apps/planning/models.py:188-220`

```python
class Kind(models.TextChoices):
    PUBLISHED = "PUBLISHED", "Plan publicat"
    CONFIRMED = "CONFIRMED", "Tură confirmată"
    DECLINED  = "DECLINED",  "Tură refuzată"
    CHECK_IN  = "CHECK_IN",  "Începere lucru"
    CHECK_OUT = "CHECK_OUT", "Încheiere lucru"
    CORRECTED = "CORRECTED", "Corecție de către angajator"
    MISSED    = "MISSED",    "Marcat neefectuat"
```

Fields: `shift` FK (CASCADE, `related_name="events"`), `kind`, `actor` FK to
`accounts.Account` (`null=True`, `SET_NULL`), `payload = JSONField(default=dict)`,
`created_at = auto_now_add`. `Meta.ordering = ("created_at",)`.

The immutability guard, verbatim (`:217-220`):

```python
def save(self, *args, **kwargs):
    if self.pk:
        raise RuntimeError("Evenimentele de pontaj sunt imutabile.")
    super().save(*args, **kwargs)
```

Note what this does and does not do: it blocks a **re-save of a loaded instance**. It
does **not** block `ShiftEvent.objects.filter(...).update(...)`, `.delete()`, or a raw
SQL update — those bypass `save()` entirely. **Never add such a call.**

---

## 3. The service layer, function by function (Fakt)

Module constant: `RETENTION_YEARS = 2` (`attendance.py:22`).
Exception type: `class ShiftError(ValueError)` — "Tranziție de stare nepermisă."
(`:25-26`).

### `publish_plan(plan, actor=None, notify=True)` — `attendance.py:29-45`

`@transaction.atomic`. Raises `ShiftError` if already `PUBLISHED` (`:31-32`) or if the
plan has no shifts (`:33-34`). Sets `status=PUBLISHED` and `published_at=timezone.now()`,
saving with `update_fields=["status", "published_at"]`. Then writes **one
`ShiftEvent(kind=PUBLISHED)` per shift** (`:40-41`). Then `_notify_workers(plan)`.

### `_notify_workers(plan)` — `attendance.py:48-74`

Groups shifts by `worker_id` and sends **one email per worker, not one per shift**
(docstring `:49`; asserted by `tests/test_attendance.py:57`). Recipient is
`worker.contact_email or _login_email(worker)` (`:58`), where `_login_email` reads the
first membership's user email (`:77-79`); a worker with neither is skipped silently
(`:59-60`). The subject and body are **German** — `f"Dein Einsatzplan ab
{plan.week_start.strftime('%d.%m.%Y')}"` and `"Deine Einsätze:\n\n"` (`:67-68`) — while
the rest of the module is Romanian. That is the language convention working as intended:
user-facing domain text is German.
`fail_silently=True` (`:71`): a bad SMTP config will not break publishing, and will not
be noticed either.

### `_guard(shift, account, allowed)` — `attendance.py:82-88`

The single authorisation choke point for all worker actions. Three checks, in order:

```python
if shift.worker_id != account.pk:            raise ShiftError("Tura nu îți aparține.")
if shift.plan.status != PlanStatus.PUBLISHED: raise ShiftError("Planul nu este publicat.")
if shift.status not in allowed:               raise ShiftError(f"Tura este în starea {shift.get_status_display()}.")
```

### `confirm_shift(shift, account)` — `attendance.py:91-97`

`_guard(..., {PLANNED})` → `status = CONFIRMED`, `update_fields=["status"]`, event
`CONFIRMED`.

### `decline_shift(shift, account, reason="")` — `attendance.py:100-110`

`_guard(..., {PLANNED, CONFIRMED})` → `status = DECLINED`, `worker_note = reason[:300]`,
event `DECLINED` with `payload={"reason": reason[:300]}`. The reason is **optional** here
(unlike a correction).

### `check_in(shift, account, now=None)` — `attendance.py:113-124`

`_guard(..., {PLANNED, CONFIRMED})` — note a worker may check in **without confirming
first**. `now = now or timezone.now()`. Writes `checked_in_at = now`,
`status = IN_PROGRESS`, event `CHECK_IN` with `payload={"at": now.isoformat()}`.

**No date check.** Nothing in the service prevents checking in on a shift dated next
month; the only date gating is cosmetic, in the template:
`{% if s.date <= today %}` (`templates/dashboard/my_shifts.html:24`). A direct POST
bypasses it.

**No location, no device, no IP is recorded.**

### `check_out(shift, account, now=None, note="")` — `attendance.py:127-144`

The core computation:

```python
_guard(shift, account, {ShiftStatus.IN_PROGRESS})
now = now or timezone.now()
if now <= shift.checked_in_at:
    raise ShiftError("Încheierea nu poate fi înaintea începerii.")
minutes = int((now - shift.checked_in_at).total_seconds() // 60)
shift.checked_out_at = now
shift.actual_minutes = minutes
shift.status = ShiftStatus.DONE
if note:
    shift.worker_note = note[:300]
shift.save(update_fields=["checked_out_at", "actual_minutes", "status", "worker_note"])
ShiftEvent.objects.create(shift=shift, kind=ShiftEvent.Kind.CHECK_OUT, actor=account,
                          payload={"at": now.isoformat(), "minutes": minutes})
```

Properties of this computation, stated precisely:
- **Gross elapsed time.** Breaks are included, because breaks are not recorded.
- **Floor, not round.** `// 60` truncates: 119 s → 1 minute. Systematically favours the
  employer by up to 59 seconds per shift.
- **No rounding to any unit** — no quarter hour, no half hour, no Soll-Zeit.
- **No upper bound.** A forgotten check-out produces a shift of arbitrary length, capped
  only by `PositiveSmallIntegerField` (32767) — beyond which the save raises a database
  error rather than a domain error.
- **No 8-hour warning.** `MAX_DAILY_MINUTES = 480` (`apps/planning/services.py:27`) is
  applied only when the planner allocates (`services.py:88`), never at check-out.
- **Equality is rejected**, not just inversion: `now <= checked_in_at` raises, so a
  zero-minute shift is impossible.
- The `note` is stored on `Shift.worker_note`, overwriting any decline reason, and it is
  **not** copied into the event payload — unlike `decline_shift`, which does copy it.

### `correct_minutes(shift, employer_account, minutes, reason)` — `attendance.py:147-165`

Docstring (`:149-152`): "Corecția angajatorului. Nu suprascrie discret: valoarea veche
rămâne în jurnal, ca înregistrarea să rămână verificabilă."

```python
if shift.plan.account_id != employer_account.pk:
    raise ShiftError("Doar angajatorul poate corecta pontajul.")
if not reason:
    raise ShiftError("Corecția are nevoie de motiv.")
previous = shift.actual_minutes
shift.actual_minutes = minutes
shift.status = ShiftStatus.DONE
shift.save(update_fields=["actual_minutes", "status"])
ShiftEvent.objects.create(shift=shift, kind=ShiftEvent.Kind.CORRECTED, actor=employer_account,
                          payload={"from": previous, "to": minutes, "reason": reason[:300]})
```

Behaviour worth knowing before you extend it:
- It **forces `status = DONE`** whatever the prior state. An employer can therefore turn
  a `PLANNED` or `MISSED` shift into a completed one with a reason — which is how the
  UI's "Ture neîncheiate" table works
  (`templates/dashboard/time_records.html:19-31`).
- `checked_in_at` / `checked_out_at` are **not** touched, so after a correction the
  timestamps and `actual_minutes` can disagree. The event journal is what reconciles
  them.
- `minutes` is **not validated**: no lower bound beyond the field's `PositiveSmallInteger`
  constraint, no upper bound, no plausibility check against `duration_minutes`. The view
  passes `int(request.POST.get("minutes", 0))` (`apps/planning/views.py:200`) — an empty
  or non-numeric field raises `ValueError`, which the view catches (`:207`).
- It is **unbounded in time and count**: a shift can be corrected any number of times,
  years later. There is no Freigabe gate.

### `mark_missed(shift, employer_account)` — `attendance.py:168-175`

Employer-only. Sets `status = MISSED`, writes a `MISSED` event. Does **not** clear
`actual_minutes` — a shift that was checked out and then marked missed keeps its
minutes on the row, while `time_records()` reports 0 for it (`:192`).

### `time_records(account, start, end, worker=None)` — `attendance.py:178-205`

```python
qs = Shift.objects.filter(
    plan__account=account, date__gte=start, date__lte=end,
    status__in=[ShiftStatus.DONE, ShiftStatus.MISSED],
).select_related("worker", "zone__site").order_by("worker__display_name", "date")
```

Per row: `worker` (display name or `"—"`), `date`, `site`, `zone`, `planned`
(= `duration_minutes`), `actual` (= `billable_minutes` for `DONE`, else `0`),
`variance`, `status` (the Romanian display label). Also returns
`totals_minutes: {worker_id: minutes}` and
`retention_until = end + timedelta(days=365 * RETENTION_YEARS)`.

Notes: `IN_PROGRESS` shifts are excluded, so an open shift is invisible in the record
(the view lists them separately as `open_shifts`, `views.py:212-216`). `totals_minutes`
is keyed by `worker_id`, which is `None` for an unassigned shift — a `None` key can
appear in the dict. `retention_until` uses 365-day years, so it drifts across a leap
year.

---

## 4. Views, URLs, templates (Fakt)

| Route | View | Auth |
|---|---|---|
| `POST /dashboard/planificare/<pk>/publicare/` | `publish_plan_view` (`views.py:121-133`) | `get_object_or_404(ShiftPlan, pk=pk, account=request.account)`; GET redirects to the planner |
| `GET/POST /dashboard/turele-mele/` | `my_shifts_view` (`views.py:136-181`) | `request.account is None` → redirect to onboarding; queryset filtered to `worker=request.account` **and** `plan__status=PUBLISHED` (`:143-148`) |
| `GET/POST /dashboard/pontaj/` | `time_records_view` (`views.py:184-223`) | raises `PermissionDenied` unless the account has `EMPLOYER` or `PROVIDER` capability (`:188-189`) |

URL names: `dashboard:plan_publish`, `dashboard:my_shifts`, `dashboard:time_records`
(`apps/dashboard/urls.py:38-41`). Segments are Romanian; `name=` values English.

`my_shifts_view` dispatches on `request.POST["action"]` ∈ {`confirm`, `decline`,
`check_in`, `check_out`} (`views.py:157-168`), catching `ShiftError` into a Django
message and always redirecting back to the week (`:169-171`). The week total shown is
`sum(s.billable_minutes for s in shifts if s.status == DONE)` (`:173`).

`time_records_view` dispatches on `action` ∈ {`correct`, `missed`} (`views.py:197-206`)
and additionally lists shifts in the week that are neither `DONE` nor `MISSED` as
`open_shifts` (`:212-216`).

`templates/dashboard/time_records.html:5-6` prints the legal notice to the employer:
"Evidența timpului de lucru e obligatorie (BAG 1 ABR 22/21, §3 ArbSchG). Păstrare până la
{{ records.retention_until|date:"d.m.Y" }} (§16 ArbZG)."

---

## 5. What the tests lock in — `tests/test_attendance.py` (Fakt)

22 tests, 5 classes, all passing (`.venv/bin/python -m pytest -q` → 190 tests as of
2026-08-29 20:40 and still growing — count it yourself, the repo is edited concurrently).
Fixtures: `plan` builds a `Site` "Haus Nord" in Norderstedt with one `Zone`
(`minutes_per_visit=120`, `visits_per_week=2`, `allowed_weekdays="1,3"`) against a signed
40 h/month contract, then calls `generate_week_plan(employer, MONDAY)` where
`MONDAY = date(2026, 10, 5)` (`:29`, `:32-40`); `shift` publishes the plan and takes the
first shift (`:43-46`).

| Class | Test | What it pins |
|---|---|---|
| `TestPublishing` | `test_publicarea_anunta_lucratorii` | `status=PUBLISHED`, `published_at` set, **exactly one email** ("un email per lucrător, nu unul per tură"), site name in the body |
| | `test_un_plan_gol_nu_se_publica` | empty plan → `ShiftError` |
| | `test_planul_publicat_nu_se_regenereaza_accidental` | `generate_week_plan` over a published week raises |
| | `test_regenerarea_explicita_e_permisa` | `replace=True` regenerates, 2 shifts |
| | `test_ciornele_nu_apar_la_lucrator` | a draft plan renders "Nicio tur…" for the worker |
| `TestAttendance` | `test_confirmare` | `PLANNED → CONFIRMED` |
| | `test_refuz_cu_motiv` | `DECLINED` + `worker_note == "Sunt bolnavă"` |
| | `test_pontajul_calculeaza_timpul_real` | check-in, check-out +95 min → `actual_minutes == 95`, `variance_minutes == -25` against the 120-min estimate |
| | `test_check_out_fara_check_in_e_refuzat` | check-out from `PLANNED` raises |
| | `test_check_out_inainte_de_check_in_e_refuzat` | check-out 5 min **before** check-in raises |
| | `test_tura_altuia_nu_se_ponteaza` | a different account cannot check in |
| | `test_jurnalul_inregistreaza_fiecare_pas` | event kinds in order: `["PUBLISHED", "CONFIRMED", "CHECK_IN", "CHECK_OUT"]` |
| | `test_evenimentele_sunt_imutabile` | mutating a loaded `ShiftEvent` and saving raises `RuntimeError` |
| `TestCorrections` | `test_corectia_pastreaza_valoarea_veche` | 200 min corrected to 120 with reason "Pauză neînregistrată"; the `CORRECTED` event carries `from=200`, `to=120`, `reason` |
| | `test_corectia_are_nevoie_de_motiv` | empty reason raises |
| | `test_doar_angajatorul_corecteaza` | the worker cannot correct their own hours |
| `TestTimeRecords` | `test_evidenta_insumeaza_timpul_efectiv` | two shifts × 100 min → 2 rows, `totals_minutes[worker.pk] == 200` |
| | `test_tura_neefectuata_nu_se_ponteaza` | `MISSED` → row `actual == 0`, total 0 |
| | `test_retentia_e_de_doi_ani` | `(retention_until - end).days >= 730` |
| `TestShiftViews` | `test_lucratorul_ponteaza_din_dashboard` | POST `action=check_in` → `IN_PROGRESS` |
| | `test_pontajul_e_inaccesibil_lucratorului` | `GET /dashboard/pontaj/` as a worker → **403** |
| | `test_angajatorul_publica_din_dashboard` | POST to the publish URL → `PUBLISHED` |

Note the correction test's reason — "Pauză neînregistrată" — is the codebase's own
acknowledgement that break handling is missing: today a break can only enter the record
as an employer correction after the fact.

---

## 6. Downstream consumers — do not break them (Fakt)

**`apps/planning/calibration.py:99-104`** reads
`Shift.objects.filter(zone=zone, status=DONE, actual_minutes__isnull=False, date__gte=start, date__lte=today).values_list("actual_minutes", flat=True)`
and derives a median and MAD to *propose* a new `Zone.minutes_per_visit`. If
`actual_minutes` ever becomes a rounded or Soll-Zeit value, this loop converges on its
own estimate and the calibration signal dies. The model docstring already says why the
proposal is not auto-applied (`apps/planning/models.py:236-245`).

**`apps/devices/services.py:130-178`** (`find_discrepancies`) compares
`shift.actual_minutes` against summed `TelemetrySession.runtime_minutes` for `DONE`
shifts, with `SUSPICIOUS_RATIO = 0.10` (`:16`) and `MATCH_TOLERANCE = timedelta(hours=2)`
(`:14`), emitting `NO_TELEMETRY`, `LOW_ACTIVITY` or `OVER_RUNTIME` discrepancies. Its
docstring is the right posture and should be preserved: "Nu produce sancțiuni — produce
întrebări." The `apps/devices/models.py:1-15` module docstring states the governing principle
verbatim: "**timpul de funcționare al unui aspirator nu este timpul de curățenie**" —
telemetry is a source of **verification**, never of calibration, and "Telemetria nu
înlocuiește pontajul."

---

## 7. Gap list against the legal requirements

| ID | Missing | Why it matters | Reference |
|---|---|---|---|
| **G-01** | **Ruhepausen** — no break field, no break entry path | RTV § 3 Nr. 1.1 sets the 8-hour day "**ausschließlich der Ruhepausen**"; the Stundenzettel's 7th mandatory field is **Pausenzeiten**. `actual_minutes` is gross elapsed time and therefore overstates Arbeitszeit. | `stundenzettel-und-berechnung.md` §1, §3c |
| **G-02** | **Daily totals** — `actual_minutes` is per shift, never aggregated per `(worker, date)` | ArbSchG data point 3 is a **daily** duration; the 8-hour limit is a **daily** limit | `rechtsgrundlagen.md` §2a |
| **G-03** | **Freigabe** — no approval state, no approver, no immutability point | Approval is the gate between a draft record and the basis of pay; without it `correct_minutes` is unbounded in time and count | `stundenzettel-und-berechnung.md` §6 |
| **G-04** | **Wegezeit / Fahrzeit / Zwischenzeit** — nothing at all | RTV § 3 Nr. 3.2/3.3 makes much travel between sites paid working time, with the ≤3 h test, the "more than half" rule and half-hour ceiling rounding | `stundenzettel-und-berechnung.md` §4 |
| **G-05** | **Source of the entry** — no field distinguishing app clock / retro-entry / correction / import | "nachgetragene Zeiten" is a first-class Fehlerart in the competitor's approval queue; a manipulation-resistant record must say how it came about | `stundenzettel-und-berechnung.md` §6a |
| **G-06** | **Location** — no geofence, no consent type, no capture | Only relevant if location is ever added; the current absence is defensible | `geofence-und-dsgvo.md` |
| **G-07** | **Recording deadline** — nothing flags a check-out or correction that lands late | The sources state a **7-day** documentation deadline (and "idealerweise am selben Tag") | `rechtsgrundlagen.md` §3 |
| **G-08** | **ArbZG check at recording time** — the 8 h/day, 11 h rest and Sunday rules are enforced only when the planner allocates (`apps/planning/services.py:27-29`, `:88`, `:93`, `:161`), never at check-out | Actual worked time is what breaches the statute, not planned time | — |
| **G-09** | **Export** — `time_records()` renders only to HTML; no CSV/PDF, and it drops `checked_in_at` / `checked_out_at` although it has them | MiLoG documentation must be producible at an unannounced Zoll/FKS inspection | `rechtsgrundlagen.md` §6 |
| **G-10** | **Bitemporality** — re-running `time_records()` after a correction cannot reproduce the earlier figure | The events hold the history but nothing reconstructs a point-in-time view | `rechtsgrundlagen.md` §6 |
| **G-11** | **Retention is display-only** — `retention_until` is computed per query; nothing stores, enforces or blocks deletion, and 365-day years drift | 2-year retention obligation | `rechtsgrundlagen.md` §5 |
| **G-12** | **Signature / worker confirmation of the timesheet** | "sollte der Stundenzettel vom **Arbeitnehmer unterschrieben** werden" | `stundenzettel-und-berechnung.md` §1 |
| **G-13** | **Objektleiter role** — corrections are employer-account-only; there is no site-manager tier | The competitor's whole approval flow is Objektleiter-driven | `stundenzettel-und-berechnung.md` §6a |
| **G-14** | **Sollstunden / Zeitkonto / Saldo**; **Zuschläge**; **Abwesenheiten** | Needed before any payroll claim; note the repo has **no payroll entity at all** | `stundenzettel-und-berechnung.md` §3d, §5, §7 |
| **G-15** | **`ShiftEvent` can still be bypassed** by `.update()` / `.delete()` / raw SQL; `Shift` rows cascade away with their `ShiftPlan` | The immutability guarantee is a convention enforced at one layer only | `apps/planning/models.py:141`, `:217-220` |

---

## 8. Working rules for changes here (Vorschlag)

1. **Add fields, never repurpose `actual_minutes`.** It is the measurement. Rounding,
   Soll-Zeit booking, break deduction and travel time each get their own column.
2. **Every state change writes a `ShiftEvent`.** If you add a transition, add a `Kind`
   and write the event in the same `@transaction.atomic` block, as every existing
   function does.
3. **Every mutation of recorded minutes carries an actor and a reason.** Follow
   `correct_minutes`.
4. **Guard first, mutate second.** New worker actions go through `_guard`; new employer
   actions repeat the `shift.plan.account_id != account.pk` check.
5. **Do not register these models in the Django admin** without first deciding what an
   admin edit means for the append-only guarantee — the admin bypasses the service layer
   entirely.
6. **Keep the language split**: Romanian comments/docstrings and URL segments, English
   identifiers, German user-facing domain text (as `_notify_workers` already does).
7. **Test the raw value.** Any change touching minutes needs a test asserting the
   measured value survives, in the style of `test_corectia_pastreaza_valoarea_veche`.
8. **Run** `/Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python -m pytest -q`
   (Python 3.12.13, Django 5.2.17; 190 tests green as of 2026-08-29 20:40 and still
   growing — count it yourself, the repo is edited concurrently).

---

## Quellen

Repository files (read 2026-08-29, `/Users/Geronimo/Projects/Cleaning_SaaS/`):
- `apps/planning/attendance.py`
- `apps/planning/models.py`
- `apps/planning/views.py`
- `apps/planning/services.py`
- `apps/planning/calibration.py`
- `apps/devices/services.py`
- `apps/dashboard/urls.py`
- `apps/dashboard/panels.py`
- `apps/accounts/compliance.py`
- `apps/geo/models.py`
- `templates/dashboard/my_shifts.html`
- `templates/dashboard/time_records.html`
- `tests/test_attendance.py`

Environment facts verified by running the project on 2026-08-29: Python 3.12.13,
Django 5.2.17, venv at `.venv`, `manage.py check` clean, 190 tests passing as of
2026-08-29 20:40 (still growing — count it yourself), no `.git`.

Competitor behaviour referenced for contrast:
- https://pland.app/onboardings/freigabe-von-zeiterfassungen
- https://pland.app/onboardings/fahrzeiterfassung-mit-pland
- https://pland.app/arbeitslexikon/stundenzettel
- https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023
