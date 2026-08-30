# Kalibrierung — the zone-estimate calibration engine, verbatim

Covers: the whole of `apps/planning/calibration.py` — every formula, weight, threshold and
minimum-sample rule quoted with `file:line`, why each constant exists, how a calibrated
minutes-per-zone value flows back into planning, what the tests assert, and how to tune it
without breaking the suite.

**Stand: 2026-08-29.** Every line number below was read from
`/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/calibration.py` (237 lines) and
`apps/planning/models.py` on that date. Numeric results were re-derived by executing the exact
expressions with `.venv/bin/python`. This module contains no legal content.

---

## 1. Why the engine exists

**Fakt.** `Zone.minutes_per_visit` (`apps/planning/models.py:58-60`) is a hand-entered guess
about how long one visit takes. It is also the **single input** that drives the weekly
generator: it is read at `services.py:127` (the `_fits` test), `:138` (the `unmet` record),
`:147` (`Shift.duration_minutes`), `:149-151` (budget + day bookkeeping) and `:115` (zone
ordering). If it is wrong, every week's plan is wrong in the same direction, forever.

**Fakt.** The engine reads the **actual clocked minutes** (`Shift.actual_minutes`, produced by
`check_out` at `attendance.py:133-135` and by `correct_minutes` at `:158`), decides whether a
zone's estimate is *systematically* wrong, and — if so — writes a `ZoneCalibration` **proposal**.
A human with `EMPLOYER` or `PROVIDER` capability applies or rejects it on `/dashboard/calibrare/`.

**Fakt.** Rationale for never self-applying, `apps/planning/models.py:236-245` (verbatim
docstring of `ZoneCalibration`):

```
Propunere de corectare a estimării unei zone, calculată din pontaj.

Se PROPUNE, nu se aplică. Motivul nu e prudență tehnică: `minutes_per_visit`
e intrarea planificatorului, iar planificatorul produce obligații
contractuale. O valoare care se mișcă singură face planul imprevizibil și
ascunde exact semnalul interesant — că o zonă a început să dureze altfel.

Istoricul rămâne: se vede cum a evoluat estimarea și pe ce date.
```

**Fakt.** Module docstring, `calibration.py:1-19`, states the four design decisions verbatim:

```
Calibrarea estimărilor din pontaj.

Fiecare tură încheiată produce o abatere față de estimare. Adunate, abaterile
spun dacă `minutes_per_visit` e greșit — dar numai dacă se citesc cu grijă:

  * Mediana, nu media. O singură tură de 300 de minute (o inundație, o
    predare de locuință) ar trage media în sus și ar strica estimarea pentru
    toate săptămânile următoare.

  * Prag dublu: abaterea trebuie să fie și relativă (≥ 15 %), și absolută
    (≥ 10 min). 8 minute peste o estimare de 45 nu merită un plan schimbat.

  * Eșantion minim și fereastră care începe la ULTIMA calibrare aplicată.
    Altfel se măsoară eroarea unei estimări care nu mai există, iar sistemul
    oscilează la infinit între două valori.

  * Perioadă de liniște după o aplicare, din același motiv.
```

**Fakt.** There is **no management command, no cron, no Celery task and no signal** that runs
calibration. The only callers of `propose_calibrations` / `analyze_zone` are
`apps/planning/views.py` and `tests/test_calibration.py`. The scan is 100 % human-triggered by
a POST button (`templates/dashboard/calibration.html:7-8`).

---

## 2. Every constant

**Fakt.** `apps/planning/calibration.py:36-40`, verbatim:

```python
MIN_SAMPLE = 5
MIN_RELATIVE_DEVIATION = 0.15
MIN_ABSOLUTE_DEVIATION = 10
COOLDOWN_DAYS = 28
MAX_LOOKBACK_DAYS = 180
```

| Constant | Line | Value | Why it exists |
|---|---|---|---|
| `MIN_SAMPLE` | 36 | `5` | Below five clocked shifts the median is noise, not a statement about the zone. Docstring `:14-16`: *„Eșantion minim și fereastră care începe la ULTIMA calibrare aplicată. Altfel se măsoară eroarea unei estimări care nu mai există, iar sistemul oscilează la infinit între două valori."* |
| `MIN_RELATIVE_DEVIATION` | 37 | `0.15` (15 %) | Half of the double threshold. Protects **large** estimates: 15 min over a 200-min zone is 7.5 % and not worth churning a plan for. |
| `MIN_ABSOLUTE_DEVIATION` | 38 | `10` minutes | The other half. Protects **small** estimates. Docstring `:11-12`: *„8 minute peste o estimare de 45 nu merită un plan schimbat."* |
| `COOLDOWN_DAYS` | 39 | `28` | Quiet period after an apply — four weeks ≈ four fresh cycles of a weekly plan, so the next verdict rests on data produced **under the new estimate**. Docstring `:18`. |
| `MAX_LOOKBACK_DAYS` | 40 | `180` | Hard floor on the analysis window (~6 months). Older data describes a building, a team and a contract that may no longer exist. |

**There is no smoothing factor, no EWMA, no learning rate and no weighting.** The suggested
value is the raw median. `median_minutes` and `suggested_minutes` are kept as **separate
columns** (`models.py:253-254`) precisely so a damped suggestion can be introduced later without
losing the observation. Today the two are computed from the identical expression
(`calibration.py:112` vs `:125`).

---

## 3. The algorithm, step by step

### Step 0 — window start

**Fakt.** `calibration.py:74-80`, verbatim:

```python
def _window_start(zone: Zone, today: date) -> date:
    """Fereastra începe după ultima calibrare aplicată, ca să nu măsurăm trecutul."""
    last_applied = zone.calibrations.filter(status=CalibrationStatus.APPLIED).first()
    floor = today - timedelta(days=MAX_LOOKBACK_DAYS)
    if last_applied and last_applied.decided_at:
        return max(floor, last_applied.decided_at.date())
    return floor
```

* `.first()` respects `ZoneCalibration.Meta.ordering = ("-created_at",)` (`models.py:272`) → the
  **most recently created** APPLIED row, not the most recently *decided* one.
* Result = `max(today - 180d, decided_at.date())`. The window can never reach back past the last
  applied calibration, and never past 180 days.

### Step 1 — cooldown gate

**Fakt.** `calibration.py:91-97`:

```python
last_applied = zone.calibrations.filter(status=CalibrationStatus.APPLIED).first()
if last_applied and last_applied.decided_at:
    if (today - last_applied.decided_at.date()).days < COOLDOWN_DAYS:
        analysis.verdict = (
            f"Calibrat recent; se așteaptă {COOLDOWN_DAYS} de zile de date noi."
        )
        return analysis
```

Strictly `< 28`, so **day 28 exactly is allowed**. Returns an `Analysis` with `sample_size=0`,
`median_minutes=None`, `suggested_minutes=None` → `actionable` is `False`. **No shift query is
issued at all.**

Note this is the *same* query as `_window_start`'s, issued a second time — see §8, G12.

### Step 2 — sample collection

**Fakt.** `calibration.py:99-105`:

```python
durations = list(
    Shift.objects.filter(
        zone=zone, status=ShiftStatus.DONE, actual_minutes__isnull=False,
        date__gte=start, date__lte=today,
    ).values_list("actual_minutes", flat=True)
)
analysis.sample_size = len(durations)
```

Four filters, all mandatory:

1. `zone=zone` — per zone, never per site, never per worker.
2. `status=ShiftStatus.DONE` — `MISSED` / `DECLINED` / `IN_PROGRESS` never count. Asserted by
   `test_turele_neefectuate_nu_intra_in_calcul` (`tests/test_calibration.py:120-127`).
3. `actual_minutes__isnull=False` — belt and braces; a `DONE` shift always has it after
   `check_out`, but `correct_minutes` and manual DB edits could produce `DONE`-with-NULL.
4. `date__gte=start, date__lte=today` — inclusive both ends, on **`Shift.date`** (the scheduled
   day), **not** on `checked_out_at`.

Notably **absent**: no filter on `plan__status`, no filter on `worker`, no per-worker
normalisation. A shift on a `DRAFT` plan counts if someone set `actual_minutes` on it. No test
covers the DRAFT-plan case — the `log_shifts` fixture creates a `PUBLISHED` plan
(`tests/test_calibration.py:58`).

### Step 3 — minimum sample

**Fakt.** `calibration.py:107-109`:

```python
if len(durations) < MIN_SAMPLE:
    analysis.verdict = f"Prea puține ture pontate ({len(durations)}/{MIN_SAMPLE})."
    return analysis
```

Needs **≥ 5**. The verdict embeds the count, and `tests/test_calibration.py:73-77` asserts the
literal `"5"` appears in it.

### Step 4 — robust centre and spread

**Fakt.** `calibration.py:61-71`:

```python
def _median(values: list[int]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


def _mad(values: list[int], center: float) -> float:
    """Abaterea mediană absolută — dispersie rezistentă la valori extreme."""
    return _median([int(abs(v - center)) for v in values]) if values else 0.0
```

and `calibration.py:111-113`:

```python
median = _median(durations)
analysis.median_minutes = round(median)
analysis.dispersion_minutes = round(_mad(durations, median))
```

Three properties you must not "clean up":

* **Median, not mean.** This is the *entire* outlier strategy — there is no trimming, no
  winsorising, no z-score filter, no IQR fence. Extremes stay in the sample; the median ignores
  them.
* **MAD, not standard deviation.** `_mad` truncates each absolute deviation with `int(...)`
  *before* taking their median, so on an even-length list it can lose up to 0.5 min per element.
  Verified: `_mad([85,90,88,92,87,90], 89.0)` → `1.5`.
* **`round()` is Python 3 banker's rounding.** Verified: `round(120.5) == 120`,
  `round(127.5) == 128`, `round(2.5) == 2`. `test_media_ar_fi_gresit_aici`
  (`tests/test_calibration.py:104-108`) **depends on the first one**: the median of
  `[118,122,120,119,121,400]` is `120.5` and the assertion is `median_minutes == 120`.
  Switching to `int(median + 0.5)` or `Decimal.quantize(ROUND_HALF_UP)` breaks that test and
  shifts every even-length median by a minute.

### Step 5 — the double threshold

**Fakt.** `calibration.py:115-123`:

```python
deviation = median - zone.minutes_per_visit
relative = abs(deviation) / zone.minutes_per_visit if zone.minutes_per_visit else 0

if abs(deviation) < MIN_ABSOLUTE_DEVIATION or relative < MIN_RELATIVE_DEVIATION:
    analysis.verdict = (
        f"Estimarea e corectă: mediana {round(median)} min față de "
        f"{zone.minutes_per_visit} min planificate."
    )
    return analysis
```

**Read the boolean carefully.** The `if` is the **bail-out**, and it is an `or`. To be actionable
a zone must satisfy **both**:

```
abs(median - minutes_per_visit) >= 10                        AND
abs(median - minutes_per_visit) / minutes_per_visit >= 0.15
```

Changing the `or` to `and` would make a zone actionable on *either* half and defeat
`test_abatere_mica_nu_declanseaza_nimic` (`tests/test_calibration.py:92-96`) entirely.

`deviation` is **signed** and drives the wording only. The baseline is
`zone.minutes_per_visit` **as it is right now**, never `Shift.duration_minutes` (what the shift
was actually planned for) — `Shift.variance_minutes` (`models.py:180-185`) is *not used by the
engine* despite its docstring pointing at exactly this use. That is intentional given the window
rule: after an apply, the window resets, so old-baseline shifts are excluded anyway.

**Division guard.** If `minutes_per_visit == 0`, `relative` is forced to `0`, so
`relative < 0.15` is true and the zone is **permanently non-actionable**. The column is
`PositiveSmallIntegerField`, which permits 0.

### Step 6 — suggestion, confidence, verdict

**Fakt.** `calibration.py:125-131`:

```python
analysis.suggested_minutes = round(median)
analysis.confidence = _confidence(len(durations), analysis.dispersion_minutes, median)
direction = "mai mult" if deviation > 0 else "mai puțin"
analysis.verdict = (
    f"Durează sistematic {direction}: mediana {round(median)} min "
    f"pe {len(durations)} ture, față de {zone.minutes_per_visit} min planificate."
)
```

**Fakt.** `calibration.py:135-142`:

```python
def _confidence(sample: int, dispersion: float, median: float) -> str:
    """Un eșantion mare cu ture consistente e o dovadă; unul mic și împrăștiat, nu."""
    spread = dispersion / median if median else 1
    if sample >= 12 and spread <= 0.15:
        return Confidence.HIGH
    if sample >= 8 and spread <= 0.30:
        return Confidence.MEDIUM
    return Confidence.LOW
```

| Result | Condition |
|---|---|
| `HIGH` | `sample >= 12` **and** `MAD/median <= 0.15` |
| `MEDIUM` | `sample >= 8` **and** `MAD/median <= 0.30` |
| `LOW` | everything else |

Consequences worth internalising:

* Samples of 5, 6 or 7 are **always `LOW`**, however tight. Verified against the test fixture
  `[180,185,175,182,178,180]` (n=6, MAD=2) → `LOW`.
* The `dispersion` argument passed at `:126` is the **already-rounded int**
  `analysis.dispersion_minutes`, not the raw float MAD. For a MAD of 1.5 the value used is `2`.
* `median` is the raw float, so `spread` mixes a rounded numerator with an unrounded
  denominator. Harmless at these magnitudes, but `_confidence` is therefore not a pure function
  of the raw statistics.
* Guard `if median else 1`: median 0 ⇒ `spread = 1` ⇒ `LOW`.
* **Confidence is advisory only.** Nothing in `apply_calibration` reads it — a `LOW`-confidence,
  5-sample proposal applies exactly as easily as a 14-sample `HIGH` one.

### Worked examples (re-derived 2026-08-29 against the exact helpers)

Zone `minutes_per_visit = 120`, as in the test fixture (`tests/test_calibration.py:40-46`).

| Sample | median | round | MAD | round | deviation | relative | ≥10? | ≥15%? | actionable | confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| `[175,180,185,178,182,180]` | 180.0 | 180 | 2.0 | 2 | +60 | 0.5000 | ✔ | ✔ | **yes** | LOW |
| `[85,90,88,92,87,90]` | 89.0 | 89 | 1.5 | 2 | −31 | 0.2583 | ✔ | ✔ | **yes** | LOW |
| `[125,130,128,126,129,127]` | 127.5 | 128 | 1.0 | 1 | +7.5 | 0.0625 | ✘ | ✘ | no | — |
| `[118,122,120,119,121,400]` | 120.5 | **120** | 1.0 | 1 | +0.5 | 0.0042 | ✘ | ✘ | no | — |
| `[120,240,90,260,100,230]` | 175.0 | 175 | 70.0 | 70 | +55 | 0.4583 | ✔ | ✔ | **yes** | LOW (spread 0.40) |
| `[180] * 14` | 180.0 | 180 | 0.0 | 0 | +60 | 0.5000 | ✔ | ✔ | **yes** | **HIGH** |

Row 4 is the anti-outlier proof: the mean would be ≈ 166.7 and would have proposed a 39 %
increase; the median moves the estimate by half a minute and the double threshold kills it.

### `Analysis`

**Fakt.** `calibration.py:43-58`:

```python
@dataclass
class Analysis:
    zone: Zone
    sample_size: int
    window_start: date
    window_end: date
    current_minutes: int
    median_minutes: int | None = None
    dispersion_minutes: int = 0
    suggested_minutes: int | None = None
    confidence: str | None = None
    verdict: str = ""

    @property
    def actionable(self) -> bool:
        return self.suggested_minutes is not None
```

Every early return leaves `suggested_minutes` at `None`, i.e. not actionable.
`analyze_zone` builds it at `:86-89` with `sample_size=0`, `window_start=start`,
`window_end=today`, `current_minutes=zone.minutes_per_visit`.

**The four verdicts, in the order they can fire** (`analyze_zone`, `:83-132`):

1. cooldown — `f"Calibrat recent; se așteaptă {COOLDOWN_DAYS} de zile de date noi."`
2. sample — `f"Prea puține ture pontate ({len(durations)}/{MIN_SAMPLE})."`
3. below thresholds — `f"Estimarea e corectă: mediana {round(median)} min față de {zone.minutes_per_visit} min planificate."`
4. actionable — `f"Durează sistematic {direction}: mediana {round(median)} min pe {len(durations)} ture, față de {zone.minutes_per_visit} min planificate."`

`analyze_zone` is a **pure read**: no writes, no side effects, no permission check (the caller is
responsible). Cost is **3 queries per zone** worst case — two of them the same
`zone.calibrations.filter(status=APPLIED).first()` issued twice (lines 76 and 91), plus the
`Shift` fetch.

---

## 4. Proposal lifecycle

**Fakt.** `propose_calibrations` — `calibration.py:145-186`, `@transaction.atomic`. Zone scope:
`Zone.objects.filter(site__account=account, is_active=True, site__is_active=True)
.select_related("site")` (`:150-152`) — **both** `is_active` flags.

The state machine per zone, per scan (`:154-185`):

| Analysis | Existing open proposal | Action |
|---|---|---|
| not actionable | none | nothing |
| not actionable | yes | existing → `REJECTED`, `decision_note = "Retrasă automat: datele noi nu o mai susțin."`, `decided_at = now()`, **`decided_by` left NULL** |
| actionable | none | create a new `PROPOSED` |
| actionable | yes, **same** `suggested_minutes` | nothing — **idempotent**; this is what makes a second scan return `[]` |
| actionable | yes, **different** `suggested_minutes` | existing → `REJECTED`, note `"Înlocuită de o propunere mai recentă."`; then create the new `PROPOSED` |

Verbatim, `calibration.py:158-173`:

```python
if not analysis.actionable:
    # O propunere care nu mai e susținută de date se retrage singură.
    if existing:
        existing.status = CalibrationStatus.REJECTED
        existing.decision_note = "Retrasă automat: datele noi nu o mai susțin."
        existing.decided_at = timezone.now()
        existing.save(update_fields=["status", "decision_note", "decided_at"])
    continue

if existing:
    if existing.suggested_minutes == analysis.suggested_minutes:
        continue
    existing.status = CalibrationStatus.REJECTED
    existing.decision_note = "Înlocuită de o propunere mai recentă."
    existing.decided_at = timezone.now()
    existing.save(update_fields=["status", "decision_note", "decided_at"])
```

The new row copies, in this order (`:175-185`): `zone`, `sample_size`, `window_start`,
`window_end`, `current_minutes`, `suggested_minutes`, `median_minutes`, `dispersion_minutes`,
`confidence`.

**The reject-then-create order is load-bearing.** The partial unique index
`uniq_open_calibration_per_zone` (`models.py:275-280`) means the `UPDATE` must land before the
`INSERT`, or the DB refuses the second open proposal. Django emits statements in source order
inside the transaction, which is why the code rejects first and creates last.

The whole scan is one `@transaction.atomic` block: a failure on zone 9 rolls back the proposals
for zones 1-8.

`propose_calibrations` returns only the **newly created** rows, not the withdrawn ones.

---

## 5. `ZoneCalibration` — the persisted proposal

**Fakt.** `apps/planning/models.py:235-292`, table `planning_zonecalibration`.

| Field | Definition (`models.py` line) | Note |
|---|---|---|
| `zone` | `ForeignKey(Zone, CASCADE, related_name="calibrations")` (`:247`) | used throughout as `zone.calibrations.filter(...)` (`calibration.py:76, 91, 156`). CASCADE: deleting a zone deletes its calibration history. |
| `sample_size` | `PositiveSmallIntegerField()` (`:248`) | snapshot; never recomputed |
| `window_start` | `DateField()` (`:249`) | snapshot of the window's lower bound |
| `window_end` | `DateField()` (`:250`) | always `today` at scan time |
| `current_minutes` | `PositiveSmallIntegerField()` (`:252`) | snapshot of `zone.minutes_per_visit` at scan time — **not** re-read later, so history stays truthful about what was replaced |
| `suggested_minutes` | `PositiveSmallIntegerField()` (`:253`) | `round(median)` |
| `median_minutes` | `PositiveSmallIntegerField()` (`:254`) | identical to `suggested_minutes` today; separate column so a damped suggestion can be added later |
| `dispersion_minutes` | `PositiveSmallIntegerField(help_text="Abaterea mediană absolută (MAD)")` (`:255-257`) | MAD, rounded |
| `confidence` | `CharField(max_length=8, choices=Confidence.choices)` (`:258`) | **NOT NULL, no default** — creating a row without it raises |
| `status` | `CharField(max_length=10, choices=CalibrationStatus.choices, default=PROPOSED)` (`:260-262`) | |
| `decided_by` | `ForeignKey("accounts.Account", null=True, blank=True, SET_NULL, related_name="calibration_decisions")` (`:263-266`) | stays NULL for auto-withdrawn rows |
| `decided_at` | `DateTimeField(null=True, blank=True)` (`:267`) | written with `timezone.now()` → **UTC-aware** |
| `decision_note` | `CharField(max_length=300, blank=True)` (`:268`) | always `note[:300]` in the services |
| `created_at` | `DateTimeField(auto_now_add=True)` (`:269`) | the ordering key |

`Meta` (`:271-280`): `ordering = ("-created_at",)`, `verbose_name = "Calibrare zonă"`,
`verbose_name_plural = "Calibrări zone"`, and:

```python
constraints = [
    models.UniqueConstraint(
        fields=("zone",), condition=models.Q(status="PROPOSED"),
        name="uniq_open_calibration_per_zone",
    )
]
```

The condition uses the **raw string** `"PROPOSED"`, matching what the migration serialised
(`0003_zonecalibration.py:38`). Resulting sqlite DDL:

```sql
CREATE UNIQUE INDEX "uniq_open_calibration_per_zone"
  ON "planning_zonecalibration" ("zone_id") WHERE "status" = 'PROPOSED'
```

**There is no index on `status` alone**, and no composite index for the
`zone__site__account=…, status=PROPOSED` queries the view and `pending_impact` run.

`__str__` (`:282-283`): `f"{self.zone} · {self.current_minutes} → {self.suggested_minutes} min"`
— RIGHTWARDS ARROW U+2192, which is why `tests/test_calibration.py:211` asserts defensively on
`b"120 &rarr; 180 min" in response.content or b"180 min" in response.content`.

Properties:

* `delta_minutes` (`:285-287`) → `suggested_minutes - current_minutes`; signed, positive = the
  zone takes longer than planned.
* `weekly_impact_minutes` (`:289-292`) → `delta_minutes * self.zone.visits_per_week`.
  Docstring: *„Cât se schimbă cererea săptămânală dacă propunerea e aplicată."*
  **Touches `self.zone` → N+1 unless the queryset uses `select_related("zone")`.**

Enums (`models.py:223-232`):

```python
class CalibrationStatus(models.TextChoices):
    PROPOSED = "PROPOSED", "Propusă"
    APPLIED = "APPLIED", "Aplicată"
    REJECTED = "REJECTED", "Respinsă"

class Confidence(models.TextChoices):
    LOW = "LOW", "Scăzută"
    MEDIUM = "MEDIUM", "Medie"
    HIGH = "HIGH", "Ridicată"
```

Terminal states are `APPLIED` and `REJECTED`. There is **no `WITHDRAWN` / `SUPERSEDED`** —
auto-withdrawal and supersession both reuse `REJECTED` and are distinguishable **only** by the
Romanian `decision_note` text, which makes them impossible to query reliably.

Migrations: exactly one touched this model, `apps/planning/migrations/0003_zonecalibration.py`
(`CreateModel`, dependencies `('accounts', '0001_initial')` and
`('planning', '0002_shift_actual_minutes_shift_checked_in_at_and_more')`). No `AlterField`, no
data migration, no backfill.

---

## 6. Decisions — and how a calibrated value flows back into planning

**Fakt.** `apply_calibration` — `calibration.py:189-205`, verbatim:

```python
@transaction.atomic
def apply_calibration(calibration: ZoneCalibration, actor, note: str = "") -> ZoneCalibration:
    if calibration.status != CalibrationStatus.PROPOSED:
        raise ValueError("Propunerea a fost deja decisă.")
    if calibration.zone.site.account_id != actor.pk:
        raise ValueError("Zona nu aparține contului.")

    zone = calibration.zone
    zone.minutes_per_visit = calibration.suggested_minutes
    zone.save(update_fields=["minutes_per_visit"])

    calibration.status = CalibrationStatus.APPLIED
    calibration.decided_by = actor
    calibration.decided_at = timezone.now()
    calibration.decision_note = note[:300]
    calibration.save(update_fields=["status", "decided_by", "decided_at", "decision_note"])
    return calibration
```

**This one field assignment is the entire "apply back to planning" mechanism.** There is no
signal, no cache invalidation, no plan regeneration, and **no touch of existing
`Shift.duration_minutes`** — those were snapshotted at generation time (`services.py:147`).

The new value takes effect the *next* time someone runs:

* `generate_week_plan` (`services.py:98-156`) — reads `zone.minutes_per_visit` at `:115`
  (zone ordering), `:127` (`_fits`), `:138` (unmet record), `:147-151` (`duration_minutes`,
  budget, `day_end`).
* `capacity_report` (`services.py:172-188`) — via `Zone.weekly_minutes`
  (`minutes_per_visit * visits_per_week`).
* `apps/planning/reinigungsplan.py:49,51` — the exported "Dauer je Einsatz" and
  "Minuten / Woche" columns.

The view says this out loud (`views.py:262-267`):
*„{zone}: estimare actualizată la {n} min. **Regenerează planul ca să se aplice.**"*

Two consequences you must state when asked:

1. `zone.save(update_fields=["minutes_per_visit"])` **bypasses `Zone.clean()`**
   (`models.py:82-87`) — Django's `save()` never calls `full_clean()`. Fine here (the only rules
   are about `category` and `allowed_weekdays`), but nothing validates a suggested value before
   it becomes the planner's input.
2. Following the advice on a **published** week is currently a crash: `planning_view` calls
   `generate_week_plan(request.account, week_start)` with the default `replace=False` and
   **without a `try/except`** (`views.py:74`), so `generate_week_plan` raises
   `ValueError("Planul e publicat. Regenerarea cere confirmare explicită.")`
   (`services.py:107-108`) → HTTP 500. See `references/implementierung-django.md`, Recipe 5.

**Fakt.** `reject_calibration` — `calibration.py:208-219`. Identical guards, no zone mutation,
sets `status = REJECTED`, `decided_by`, `decided_at`, `decision_note = note[:300]`.

**Fakt.** Both raise plain **`ValueError`**, not `ShiftError` and not `PermissionDenied`. Keep it
that way: the view catches `ValueError` (`views.py:271-272`) and turns it into a flash message;
a `PermissionDenied` would become an unhandled 403 on a POST.

**Fakt.** `pending_impact` — `calibration.py:222-237`:

```python
proposals = ZoneCalibration.objects.filter(
    zone__site__account=account, status=CalibrationStatus.PROPOSED
).select_related("zone")
delta = sum(p.weekly_impact_minutes for p in proposals)
return {
    "count": len(proposals),
    "weekly_delta_minutes": delta,
    "increases": sum(1 for p in proposals if p.delta_minutes > 0),
    "decreases": sum(1 for p in proposals if p.delta_minutes < 0),
}
```

Keys verbatim: `"count"`, `"weekly_delta_minutes"`, `"increases"`, `"decreases"`.
`weekly_delta_minutes` is a **signed net sum** — an increase of +120 and a decrease of −120 net
to 0 while `increases` and `decreases` both read 1. Never present it alone as "how much work
changed".

Docstring `:223-227` names the real stake: the hours budget in `generate_week_plan` is a legal
ceiling, so **raising an estimate can silently turn a satisfiable week into one with unmet
demand**.

---

## 7. The view and the page

**Fakt.** `calibration_view` — `apps/planning/views.py:238-287`. Plain function view, no
decorators. URL `/dashboard/calibrare/`, name `dashboard:calibration`
(`apps/dashboard/urls.py:42`). Template `dashboard/calibration.html`.

Guards (`:240-243`): `request.account is None` → `redirect("accounts:onboarding")` (this also
covers anonymous users, because `ActiveAccountMiddleware` sets `request.account = None` for
them, `apps/accounts/middleware.py:19-25`); then
`if not ({Capability.EMPLOYER, Capability.PROVIDER} & request.account.capability_set()):
raise PermissionDenied` → 403.

POST branches (`:245-273`), dispatched on `request.POST["action"]`:

* `"scan"` → `propose_calibrations(request.account)` with **no `today` argument**, so it uses
  `timezone.localdate()`. `messages.success(f"{len(created)} propuneri noi.")` if any, else
  `messages.info("Nicio abatere sistematică peste prag.")`.
* anything else → `get_object_or_404(ZoneCalibration, pk=request.POST.get("calibration"),
  zone__site__account=request.account)`, `note = request.POST.get("note", "")`, then
  `"apply"` → `apply_calibration(...)`, `"reject"` → `reject_calibration(...)` with
  `messages.info("Propunere respinsă.")`; `ValueError` → `messages.error(str(exc))`.
  **Any other `action` value silently does nothing** but still 404s on a missing/foreign pk.
* Every POST redirects with `redirect("dashboard:calibration")` (`:273`) — POST-redirect-GET, no
  query string. This is the *only* planning view that uses a named redirect; the others hard-code
  `"/dashboard/…/"` strings. Copy this one.

GET context (`:275-287`):

| key | value |
|---|---|
| `proposals` | `ZoneCalibration.objects.filter(zone__site__account=…, status=PROPOSED).select_related("zone__site")` |
| `history` | same filter `.exclude(status=PROPOSED).select_related("zone")[:20]` — newest first via `Meta.ordering`, hard-capped at 20, no pagination |
| `analyses` | `[analyze_zone(z) for z in zones]` where `zones = Zone.objects.filter(site__account=…, is_active=True).select_related("site")` |
| `impact` | `pending_impact(request.account)` |

**Filter mismatch worth knowing:** `analyses` does **not** filter `site__is_active=True`, while
`propose_calibrations` does (`calibration.py:151`). Zones on a deactivated site therefore appear
in the "Situația zonelor" table with a live verdict but can never receive a proposal.

**Template**, `templates/dashboard/calibration.html` (51 lines, extends `base.html`, no htmx, no
CSS): heading + a paragraph restating the never-auto-apply rule including the literal
`<code>minutes_per_visit</code> (`:2-5`); the scan form (`:7-8`); the impact banner shown only
`{% if impact.count %}` (`:10-14`); one `<article>` per proposal rendering
`{{ p.current_minutes }} → {{ p.suggested_minutes }} min`, `delta_minutes`,
`weekly_impact_minutes`, `median_minutes`, `sample_size`, `dispersion_minutes`,
`{{ p.get_confidence_display }}` and the window as
`{{ p.window_start|date:"d.m.Y" }} – {{ p.window_end|date:"d.m.Y" }}` (**German date format**),
with a per-article form carrying a hidden `calibration` pk, a free-text `note` and two submit
buttons `value="apply"` / `value="reject"` (`:16-32`); the "Situația zonelor" table over
`analyses` showing the full Romanian `a.verdict` — the only place a non-actionable verdict is
ever shown (`:34-40`); and the `Istoric` list (`:42-50`).

Flash messages **are** rendered — by `templates/base.html:9-13`, not by
`calibration.html`. Any new calibration page must extend `base.html` to inherit them.

Dashboard tile: `Panel("calibration", "Calibrare estimări", "Ce spune pontajul despre duratele
planificate", "dashboard:calibration", Capability.EMPLOYER, order=37)`
(`apps/dashboard/panels.py:74-75`) — `EMPLOYER` only, so a pure `PROVIDER` can reach the URL but
sees no tile.

---

## 8. What the tests assert

**Fakt.** `tests/test_calibration.py` — 21 tests in 4 classes; the whole suite is
**190 passed** (verified 2026-08-29 with `.venv/bin/python -m pytest`).

Anchor: `TODAY = timezone.localdate()` (`:37`) with the comment
*„Ancorat în ziua reală: `decided_at` folosește ceasul, iar perioada de liniște se calculează
față de el — o dată fictivă ar face testele să treacă degeaba."* The thresholds are imported
**symbolically** (`COOLDOWN_DAYS`, `MIN_SAMPLE` at `:14-22`) precisely so tuning a constant does
not break the assertions that reference it.

Fixtures: `zone` (`:40-46`) creates a `Site` "Haus Nord" and a `Zone` "Etaj 1" with
`minutes_per_visit=120, visits_per_week=2`; `log_shifts` (`:49-68`) creates `DONE` shifts with
given `actual_minutes`, defaulting to `start = TODAY - timedelta(days=60)`, one per consecutive
day, on a `PUBLISHED` plan whose `week_start` is derived from `start`.

| Test | Line | What it defends |
|---|---|---|
| `test_esantion_prea_mic_nu_produce_propunere` | 73-77 | n=3 → not actionable; the literal `MIN_SAMPLE` appears in the verdict |
| `test_abatere_sistematica_e_detectata` | 79-84 | `[175,180,185,178,182,180]` → actionable, `suggested_minutes == 180`, verdict contains `"mai mult"` |
| `test_scadere_sistematica_e_detectata` | 86-90 | `[85,90,88,92,87,90]` → `suggested_minutes == 89`, verdict contains `"mai puțin"` |
| `test_abatere_mica_nu_declanseaza_nimic` | 92-96 | `[125,130,128,126,129,127]` → not actionable; message *„8 min peste 120 nu justifică un plan schimbat"*; verdict contains `"corectă"` |
| `test_o_singura_tura_extrema_nu_muta_estimarea` | 98-102 | `[118,122,120,119,121,400]` → not actionable; *„mediana rezistă la valori extreme"* |
| `test_media_ar_fi_gresit_aici` | 104-108 | same sample: asserts the mean **would** exceed 165, and `median_minutes == 120` — **this is the banker's-rounding test** |
| `test_increderea_creste_cu_esantionul_si_consistenta` | 110-112 | `[180]*14` → `Confidence.HIGH` |
| `test_ture_imprastiate_dau_incredere_scazuta` | 114-118 | scattered sample → `LOW` **only if actionable** (a conditional assertion, i.e. a no-op if not) |
| `test_turele_neefectuate_nu_intra_in_calcul` | 120-127 | a `MISSED` shift does not change `sample_size` (stays 6) |
| `test_propunerea_se_creeaza_o_singura_data` | 132-136 | first scan → 1, second scan → 0, exactly one open row |
| `test_propunerea_nesustinuta_se_retrage_singura` | 138-145 | after `Shift.objects.filter(zone=zone).update(actual_minutes=120)` a rescan flips it to `REJECTED` with `"Retrasă automat"` in the note |
| `test_impactul_saptamanal_e_calculat` | 147-153 | `impact["count"] == 1`, `increases == 1`, `weekly_delta_minutes == 120` — hard-coded as `+60 min × 2 vizite` |
| `test_aplicarea_schimba_estimarea` | 158-164 | `zone.minutes_per_visit == 180`; `decided_by == employer` |
| `test_respingerea_lasa_estimarea_neatinsa` | 166-171 | estimate stays 120 |
| `test_o_propunere_decisa_nu_se_redecide` | 173-178 | `ValueError` on re-deciding |
| `test_alt_cont_nu_decide` | 180-184 | `ValueError` when the actor is not the owning account |
| `test_perioada_de_liniste_previne_oscilatia` | 186-192 | probing at `TODAY + COOLDOWN_DAYS - 1` → not actionable, `"recent"` in verdict |
| `test_dupa_liniste_fereastra_ignora_datele_vechi` | 194-201 | at `TODAY + COOLDOWN_DAYS + 1`: `sample_size == 0` *(„turele dinainte de calibrare nu se recontează")* and `window_start >= proposal.decided_at.date()` |
| `test_pagina_listeaza_propunerile` | 206-211 | POST `action=scan`, then GET renders the arrow line |
| `test_aplicarea_din_dashboard` | 213-220 | POST `action=apply` with the pk changes the zone to 180 |
| `test_lucratorul_nu_are_acces` | 222-224 | a `WORKER` gets 403 |

**Not covered by any test:** `MAX_LOOKBACK_DAYS` (the 180-day floor), the `MEDIUM` confidence
tier, the scan skipping zones on an inactive site, and **every flash-message string** in
`calibration_view` — you can silently break or delete any of that wording.

---

## 9. Gotchas

**G1 — The `if` at `calibration.py:118` reads like an OR of two triggers; it is the opposite.**
It is the *bail-out*. Actionable requires **both** halves.

**G2 — `round()` is banker's rounding.** `round(120.5) == 120`, `round(127.5) == 128`.
`test_media_ar_fi_gresit_aici` depends on the first.

**G3 — Confidence is capped by sample size before it is capped by consistency.** Fourteen
identical shifts give `HIGH`; six identical shifts give `LOW`. Someone "fixing" the `LOW` label
on a perfectly consistent 6-shift zone will be tempted to lower the `sample >= 12` gate — that
gate is the point.

**G4 — `decided_at.date()` is the UTC date, not the Berlin date.** `timezone.now()` returns a
UTC-aware datetime; `today` comes from `timezone.localdate()` with
`TIME_ZONE = "Europe/Berlin"` (`config/settings.py:108`). Between midnight and 01:00/02:00
Berlin time the two disagree by one day, so both the cooldown arithmetic (`:93`) and the window
floor (`:79`) can be off by a day. The correct form is
`timezone.localtime(last_applied.decided_at).date()`. Do **not** "clean up" the existing calls
without adding a boundary test.

**G5 — `.first()` on `zone.calibrations` orders by `-created_at`, not `-decided_at`.** If a
proposal created in March is applied in May while one created in April was applied in April,
`_window_start` picks the April row — the window can start *earlier* than the most recent apply.

**G6 — A zone with `minutes_per_visit = 0` is permanently non-actionable.** `:116` forces
`relative = 0`, which always fails the 15 % gate. The column permits 0.

**G7 — Applying does not change any existing `Shift`,** and following the "regenerate" advice on
a published week is a 500 today (`views.py:74`, `services.py:107-108`).

**G8 — Nothing asserts on the flash messages.** `"Nicio abatere sistematică peste prag."`,
`"{n} propuneri noi."`, `"Propunere respinsă."` and the apply message (`views.py:263-267`) are
completely unguarded by the suite.

**G9 — The scan's zone filter and the page's zone filter differ** (`site__is_active`), §7 above.

**G10 — `pending_impact` returns a signed net delta.** Never present `weekly_delta_minutes`
alone.

**G11 — `weekly_impact_minutes` and `delta_minutes` touch `self.zone`.** Any queryset feeding
them must `select_related("zone")`, as `pending_impact` does (`:230`).

**G12 — `analyze_zone` is called once per zone in the view's list comprehension**
(`views.py:285`), each costing up to 3 queries, and `_window_start` + the cooldown check issue
the *same* `zone.calibrations.filter(status=APPLIED)` query twice (lines 76 and 91). The page is
O(zones) queries with a constant of ~3, no caching.

**G13 — No index supports the view's main filters.** Only `zone_id`, `decided_by_id` and the
partial unique index exist; `status` and `zone__site__account` scans are unindexed.

**G14 — `zone.save(update_fields=["minutes_per_visit"])` skips `Zone.clean()`.**

**G15 — Import placement.** The calibration imports live mid-file at `views.py:228-235` under a
Romanian banner comment, each marked `# noqa: E402`. The file has three such sectioned blocks
(attendance at 101-118, calibration at 228-235, Reinigungsplan at 291-293). Moving them to the
top changes a deliberate layout; ruff is configured `line-length = 100`,
`target-version = "py312"` (`pyproject.toml`).

---

## 10. How to tune it safely

### Rule set

1. **Every threshold is a module-level `UPPER_SNAKE` constant at `calibration.py:36-40`.** Never
   inline a magic number in a comparison — the tests import constants by name, so a named
   constant is the contract.
2. **Never widen the double threshold into an `and`.** If you add a third gate, add it as another
   `or` clause in the same `if`, or as a separate early return with its own Romanian verdict.
3. **Every early return must set `analysis.verdict` to a Romanian sentence containing the
   numbers.** The template surfaces `verdict` raw (`calibration.html:39`) and tests assert on
   substrings (`"corectă"`, `"recent"`, `"mai mult"`, `"mai puțin"`, the `MIN_SAMPLE` literal).
4. **New statistics go on the `Analysis` dataclass first** (`:43-54`) with a default, then get
   copied into the `ZoneCalibration.objects.create(...)` call at `:175-185`. Keep both in the
   same field order.
5. **Any new `ZoneCalibration` column needs a migration**, and — because `confidence` is the
   precedent (NOT NULL, no default) — a `null=True` or a default if `propose_calibrations` might
   not always set it.
6. **Status transitions only ever move `PROPOSED → APPLIED|REJECTED`.** Guard every new
   transition with the same
   `if calibration.status != CalibrationStatus.PROPOSED: raise ValueError("Propunerea a fost deja decisă.")`
   and keep the Romanian message identical — the view surfaces `str(exc)` to the user.
7. **Ownership check is `calibration.zone.site.account_id != actor.pk`, raising `ValueError`**,
   not `PermissionDenied`.
8. **Every mutating service is `@transaction.atomic` and saves with explicit
   `update_fields=[...]`.** Both are non-negotiable in this module.
9. **Truncate free text with `[:300]`** before assigning to `decision_note`.
10. **Docstrings are Romanian and explain *why*, not *what*** — see `:70, 75, 136, 147, 223-227`.

### Recipe A — change a threshold (e.g. require 8 samples)

1. Edit the constant only, `calibration.py:36`: `MIN_SAMPLE = 8`. Nothing else in the engine
   changes — `:107` and the verdict at `:108` both interpolate it.
2. Fix the fixtures: every `TestProposals` / `TestDecisions` test logs exactly **6** durations
   (`tests/test_calibration.py:133, 139, 148, 159, 167, 174, 181, 187, 195`). All would start
   failing. Extend each list, e.g. `log_shifts([180, 185, 175, 182, 178, 180, 179, 181])`.
3. Re-check `_confidence` (`:138-141`): if `MIN_SAMPLE` climbs past 8, the `MEDIUM` tier stops
   being reachable-but-distinct. Adjust the tiers in the same commit.
4. Update the module docstring at `:1-19`, which spells the thresholds out in prose.
5. `.venv/bin/python -m pytest tests/test_calibration.py -q`.

Note `test_abatere_mica_nu_declanseaza_nimic` (`:92-96`) and `test_abatere_sistematica_e_detectata`
(`:79-84`) hard-code durations tuned to the current 120-minute estimate and the 15 % / 10 min
thresholds — re-tune those fixtures if you move `MIN_RELATIVE_DEVIATION` or
`MIN_ABSOLUTE_DEVIATION`.

### Recipe B — add damping so the estimate moves gradually

The seam already exists: `median_minutes` and `suggested_minutes` are separate columns
(`models.py:253-254`).

1. Add the constant next to the others, `calibration.py:41`:

```python
SMOOTHING = 0.5   # cât din diferență se aplică dintr-o dată; restul, la calibrarea următoare
```

2. Replace `:125`:

```python
analysis.suggested_minutes = round(
    zone.minutes_per_visit + SMOOTHING * (median - zone.minutes_per_visit)
)
```

Leave `:112` (`analysis.median_minutes = round(median)`) untouched — the observation and the
recommendation are deliberately different columns.

3. **Re-verify the double threshold at `:118` still gates on the raw deviation**
   (`median - zone.minutes_per_visit`), not the damped one; otherwise a damped suggestion could
   fall below `MIN_ABSOLUTE_DEVIATION` and never fire.
4. New test in `TestAnalysis`:

```python
def test_ajustarea_e_treptata(self, zone, log_shifts):
    log_shifts([180, 185, 175, 182, 178, 180])
    analysis = analyze_zone(zone, TODAY)
    assert analysis.median_minutes == 180
    assert analysis.suggested_minutes == 150, "jumătate din drum, nu tot"
```

5. Update `test_aplicarea_schimba_estimarea` (`:158-164`) and
   `test_impactul_saptamanal_e_calculat` (`:147-153`, which hard-codes
   `weekly_delta_minutes == 120  # +60 min × 2 vizite`).

### Recipe C — block low-confidence proposals from being applied

1. In `calibration.py:189-194`, after the status guard:

```python
if calibration.confidence == Confidence.LOW:
    raise ValueError("Încredere prea scăzută; mai adună date.")
```

`Confidence` is already imported at `:29`.

2. The view already renders `str(exc)` as `messages.error` (`views.py:271-272`) — no view change.
3. Hide the button in `templates/dashboard/calibration.html:29`:

```django
{% if p.confidence != "LOW" %}<button name="action" value="apply">Aplică</button>{% endif %}
```

4. **This breaks most of `TestDecisions`**, because a 6-shift sample is always `LOW` (see the
   worked-examples table). Raise the fixture samples to 12 identical durations
   (`log_shifts([180] * 12)` → `HIGH`) or add explicit `LOW` tests.

### Recipe D — run the scan automatically (management command)

The only existing management package is `apps/jobs/management/` (`commands/flush_indexing.py`) — copy its layout; `apps/planning` has none yet.

1. `apps/planning/management/__init__.py` and
   `apps/planning/management/commands/__init__.py` (both empty).
2. `apps/planning/management/commands/calibrare.py`:

```python
"""Rulează scanarea de calibrare pentru toate conturile cu zone active."""

from django.core.management.base import BaseCommand

from apps.accounts.models import Account
from apps.planning.calibration import propose_calibrations


class Command(BaseCommand):
    help = "Propune calibrări din pontaj pentru toate conturile."

    def handle(self, *args, **options):
        for account in Account.objects.filter(sites__zones__is_active=True).distinct():
            created = propose_calibrations(account)
            if created:
                self.stdout.write(f"{account}: {len(created)} propuneri noi.")
```

`related_name="sites"` comes from `apps/planning/models.py:24-26`, `related_name="zones"` from
`:48`.

3. **Do not add an auto-apply step.** That is the one rule this module exists to protect.

### Recipe E — add a per-worker breakdown

1. Extend the dataclass (`:43-54`) with `per_worker: dict[int, int] = field(default_factory=dict)`
   (add `field` to the `dataclasses` import on `:21`).
2. Change the query at `:99-104` to `.values_list("worker_id", "actual_minutes")` and split the
   tuples; keep `durations` a plain `list[int]` so `_median` / `_mad` stay unchanged.
3. Populate `analysis.per_worker` with `{worker_id: _median([...])}`.
4. **Do not persist it on `ZoneCalibration`** unless you add a migration; render it from
   `analyses` in the "Situația zonelor" table instead.
5. Watch the query count — `analyses` already costs ~3 queries per zone (G12); resolving worker
   names adds one more per row unless you prefetch.

### What is deliberately not here

* **No smoothing / damping** (Recipe B is the seam).
* **No automatic scheduling** — a zone can be 40 % wrong for a year and nobody is told.
* **No notification** — new proposals produce no email, no dashboard badge, no metric.
  `apps/dashboard/panels.py` registers a tile but `METRICS` (`panels.py:92-99`) has no
  calibration entry.
* **No confidence gate** (Recipe C).
* **No per-worker signal** — a zone that is slow only because one worker is slow looks identical
  to a genuinely under-estimated zone.
* **No seasonality, no day-of-week, no m²-per-minute normalisation.** `Zone.area_sqm`
  (`models.py:57`) exists and is used by nothing.
* **No trend detection** — the engine answers "is the estimate wrong *now*", never "is this zone
  getting slower". `window_start`/`window_end` are stored but never compared across rows.
* **No `WITHDRAWN` / `SUPERSEDED` status**, and `decided_by` is NULL for auto-withdrawn rows
  while `decided_at` is set — the history list (`calibration.html:44-49`) renders them as if a
  human decided.
* **No admin registration** — there is no `apps/planning/admin.py`, so `ZoneCalibration` is
  invisible in the Django admin. Support cannot inspect a row without a shell.
* **Telemetry must not be wired in.** `apps/devices/models.py:1-15` states the boundary
  explicitly: *„telemetria e sursă de VERIFICARE, nu sursă de calibrare"*. Do **not** feed
  `TelemetrySession.runtime_minutes` into this module; calibration reads `Shift.actual_minutes`
  only.

---

## Quellen

Repository (read 2026-08-29, paths relative to `/Users/Geronimo/Projects/Cleaning_SaaS`):

* `apps/planning/calibration.py` — whole file, 237 lines: docstring 1-19, constants 36-40,
  `Analysis` 43-58, `_median` 61-66, `_mad` 69-71, `_window_start` 74-80, `analyze_zone` 83-132,
  `_confidence` 135-142, `propose_calibrations` 145-186, `apply_calibration` 189-205,
  `reject_calibration` 208-219, `pending_impact` 222-237
* `apps/planning/models.py` — `Zone` 42-87, `Shift` 140-185, `CalibrationStatus` 223-226,
  `Confidence` 229-232, `ZoneCalibration` 235-292
* `apps/planning/services.py` — `generate_week_plan` 98-156, `capacity_report` 172-188
* `apps/planning/attendance.py` — `check_out` 127-144, `correct_minutes` 147-165
* `apps/planning/views.py` — `planning_view` 60-96, calibration imports 228-235,
  `calibration_view` 238-287
* `apps/planning/reinigungsplan.py` 49, 51
* `apps/planning/migrations/0003_zonecalibration.py`
* `apps/dashboard/urls.py:42`; `apps/dashboard/panels.py:74-75`, `METRICS` 92-99
* `apps/accounts/middleware.py:19-25`
* `apps/devices/models.py:1-15`
* `config/settings.py:107-110`
* `templates/dashboard/calibration.html` (51 lines); `templates/base.html:9-13`
* `tests/test_calibration.py` (224 lines, 21 tests)
* `pyproject.toml` (`[tool.ruff]` line-length 100, target-version py312)

No pland.app page describes an estimate-calibration engine; this module has **no competitor
counterpart** in the crawl. The closest published concept is the Soll/Ist-Vergleich
(https://pland.app/funktionen/zeiterfassung-gebaeudereinigung), which compares one recorded time
against one planned time and flags a deviation — it does not feed the planning estimate back.
