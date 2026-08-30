# Zuteilung und Vertretung — allocation constraints, substitution, absence, notification

Covers: every constraint an allocation must respect (qualification, capacity/remaining hours,
proximity, working-time law, Ruhezeit, absence), the substitution (Vertretung) flow when someone
calls in sick, absence management (Urlaubsantrag, Urlaubsanspruch, Krankheit) and how it should
feed planning, and the notification duties on a plan change.

**Stand: 2026-08-29.** Repo claims read from `/Users/Geronimo/Projects/Cleaning_SaaS` with
`file:line`; pland.app claims from the crawl of 2026-08-29 with the source URL. Legal content is
reference material, not legal advice; the statutory values below are the ones the code itself
cites, and Tarif/statutory values change — re-check them against the cited source.

---

## 1. The allocator: what it is and what it is not

**Fakt.** Module docstring, `apps/planning/services.py:1-15` (verbatim):

```
Generatorul de plan săptămânal.

Nu e un optimizator matematic — e un repartizor lacom cu constrângeri tari.
Diferența contează: un optimizator care „aproape" respectă plafonul de ore
produce o încălcare legală. Aici, dacă o vizită nu încape fără să spargă o
regulă, rămâne NEALOCATĂ și apare în raport cu motivul.

Constrângeri tari:
  1. Bugetul de ore din contractul semnat (plafon legal, nu preferință)
  2. Max. 8 h pe zi de lucrător           — §3 ArbZG
  3. Min. 11 h odihnă între ture          — §5 ArbZG
  4. Duminica liberă                      — §9 ArbZG
  5. Lucrătorul deservește localitatea obiectivului
```

**Fakt.** The allocation loop, `services.py:121-151`. Zones are iterated
`order_by("-minutes_per_visit")` — heaviest first, comment: *„sarcinile grele întâi: încap mai
greu"* (`:115`). For each zone × visit day, capacities are tried
`sorted(capacities, key=lambda c: -c.remaining)` — most remaining budget first (`:126`). The
**first** capacity for which `_fits` returns `None` wins; every refusal is collected into
`reasons[cap.name]`.

**Fakt.** Start times are packed **back-to-back from 07:00 with no breaks and no travel buffer**
(`services.py:143-151`):

```python
start_minutes = candidate.per_day.get(day, 0)
start = (datetime.combine(day, DAY_START) + timedelta(minutes=start_minutes))
```

Asserted by `tests/test_planning.py:139-146` (first shift at `07:00`, second not at `07:00`).

---

## 2. The constraint set, exactly as implemented

**Fakt.** `_fits` — `apps/planning/services.py:82-95`, verbatim:

```python
def _fits(cap: WorkerCapacity, day: date, minutes: int, locality_id: int) -> str | None:
    """Returnează motivul refuzului, sau None dacă tura încape."""
    if locality_id not in cap.localities:
        return "nu deservește localitatea"
    if cap.remaining < minutes:
        return f"buget săptămânal epuizat ({cap.weekly_minutes} min contractate)"
    if cap.per_day.get(day, 0) + minutes > MAX_DAILY_MINUTES:
        return "ar depăși 8 h într-o zi (§3 ArbZG)"
    previous_end = cap.day_end.get(day - timedelta(days=1))
    if previous_end:
        start = datetime.combine(day, DAY_START)
        if (start - previous_end).total_seconds() / 60 < MIN_REST_MINUTES:
            return "sub 11 h de odihnă față de tura anterioară (§5 ArbZG)"
    return None
```

**Order matters.** The first failing check wins, so a worker who fails on locality never reports
a budget reason. Keep the cheapest / most-informative refusal first when you add a check.

### 2.1 Proximity

**Fakt.** Proximity is **exact set membership on `Locality` ids**, nothing more —
`services.py:84-85`, against `zone.site.locality_id` (`services.py:127`).
`cap.localities` is built at `services.py:68-70`:

```python
localities = set(
    contract.worker.areas.values_list("locality_id", flat=True)
) or {contract.workplace_id}
```

i.e. the worker's declared `ServiceArea` rows (`apps/accounts/profiles.py:86-97`), **falling
back to the contract's `workplace` locality** when the worker declared none. Asserted by
`tests/test_planning.py:111-119`.

**Fakt.** Unused geographic data that exists in the repo:
`WorkerProfile.willing_to_travel_km` (`apps/accounts/profiles.py:26`) and
`Locality.latitude` / `longitude` (`apps/geo/models.py:30-31`). Neither is read by planning.
`Site` has no coordinates. There is **no distance calculation and no travel-time buffer**
anywhere.

**Fakt (pland.app).** The competitor claims proximity as a *suggestion* feature, not a hard
constraint: **Planungsassistent** — „Wer hat noch Zeit? Wer ist in der Nähe?"
(https://pland.app/funktionen/uebersicht). Blog wording is qualitative only: „**Lange Fahrwege**
oder Überschneidungen werden so vermieden"; „auf Basis der Verfügbarkeit und des
**Einsatzortes** passende Mitarbeiter"
(https://pland.app/blog/gebaudereinigung-wie-erstelle-ich-den-perfekten-einsatzplan-vorlage).
**No distance figure, no radius, no travel-time value is stated on any planning page.**

The only radius figure anywhere in the crawl is a *time-recording* threshold, not a planning
one: check-in/check-out **more than 800 Meter** from the Objekt flags the record for manual
review (https://pland.app/onboardings/freigabe-von-zeiterfassungen). Do not reuse it as a
planning radius — it is a Zeiterfassung tolerance.

### 2.2 Capacity / remaining hours

**Fakt.** `build_capacities` — `services.py:51-79`. One `WorkerCapacity` **per signed
contract**:

```python
contracts = (
    ContractDraft.objects.filter(
        employer=account, status=DraftStatus.SIGNED, start_date__lte=week_end
    )
    .exclude(end_date__lt=week_start)
    .select_related("worker")
)
```

Weekly budget: `weekly = int(Decimal(contract.hours_per_month) * 60 / WEEKS_PER_MONTH)` with
`WEEKS_PER_MONTH = Decimal("52") / Decimal("12")` (`services.py:31,67`). Verified:
40 h/month → **553** min/week; 200 h/month → **2769** min/week. Asserted by
`tests/test_planning.py:58-63` (`550 <= supply <= 555`).

The contract window is inclusive on both sides: it must start on/before Sunday and must not end
before Monday. `end_date=None` (open-ended) survives `.exclude(end_date__lt=…)` because SQL
`NULL < x` is unknown.

`WorkerCapacity` (`services.py:34-48`): `account_id`, `name`, `weekly_minutes`, `localities`,
`used_minutes=0`, `per_day: dict[date, int]`, `day_end: dict[date, datetime]`, and
`remaining = weekly_minutes - used_minutes`.

**Known modelling hole.** One capacity **per contract, not per person**. Two concurrent signed
contracts for the same worker under the same employer produce **two independent weekly budgets
and two independent `per_day`/`day_end` dicts** — so the §3 and §5 limits are computed *per
contract*, which is wrong: ArbZG limits are per person. Untested. If you touch
`build_capacities`, this is the fix worth doing: group by `contract.worker_id` and sum
`weekly_minutes`, keeping a single `per_day`/`day_end` per person.

**Second hole.** The ceiling is enforced **weekly, never monthly**. The Geringfügigkeitsgrenze
is a *monthly* limit (`apps/contracts/models.py:92-97`); the planner converts it to a weekly
average and never checks a calendar-month total across plans. Four heavy weeks inside a 5-week
month can exceed the monthly cap while every individual week passes.

**Fakt (pland.app).** The competitor's equivalent: a capacity bar under each employee name;
hovering shows **geplante** and **noch verfügbare Arbeitsstunden** for the rest of the week and
the rest of the month; the bar turns **red** when exceeded
(https://pland.app/onboardings/auftrage-und-einsatzplanung-in-pland). And:
„erkennt die Software sofort wieviele Stunden Ihre Mitarbeiter arbeiten und **informiert Sie im
Falle einer möglichen Überbelastung**"
(https://pland.app/arbeitslexikon/personaleinsatzplanung). Note their capacity check is a
**warning**, ours is a **hard refusal** — that is a deliberate difference and the stronger
position: see `apps/planning/models.py:4-8`.

### 2.3 Working-time law

**Fakt (code).** Constants, `apps/planning/services.py:27-31`:

```python
MAX_DAILY_MINUTES = 480          # §3 ArbZG: 8 h; 10 h doar cu compensare în 6 luni
MIN_REST_MINUTES = 11 * 60       # §5 ArbZG
SUNDAY = 7                       # §9 ArbZG
DAY_START = time(7, 0)
WEEKS_PER_MONTH = Decimal("52") / Decimal("12")
```

| Rule | Status | Evidence |
|---|---|---|
| §3 ArbZG — 8 h/day | **live** | `services.py:88-89`; test `tests/test_planning.py:86-97` |
| §5 ArbZG — 11 h rest | **encoded but unreachable** | see below |
| §9 ArbZG — Sunday free | **live**, applied by day-stripping | `services.py:161`; test `tests/test_planning.py:99-103` |
| §4 ArbZG — breaks | **not implemented** | no `break_minutes`; `check_out` bills the whole elapsed span (`attendance.py:133`) |
| §11 ArbZG — one rest day per week / max 6 consecutive days | **not implemented** | no constant, no check |
| §16 Abs. 2 ArbZG — 2-year retention | **displayed, not enforced** | `RETENTION_YEARS = 2` (`attendance.py:22`), surfaced at `attendance.py:205`; nothing deletes or archives |

**Why §5 is dead.** Every day starts at `DAY_START = time(7, 0)` and holds at most
`MAX_DAILY_MINUTES = 480`, so the latest possible `cap.day_end` is 15:00. 15:00 → next day 07:00
is 16 h, always ≥ 11 h. Verified arithmetically. The branch becomes reachable only if
`DAY_START` becomes per-zone/configurable or `MAX_DAILY_MINUTES` rises past 720. **There is no
test for it.** Do not describe §5 as implemented.

**Fakt (pland.app).** The break rules the competitor states, with no statute cited on their page:
„**Ab einer Arbeitszeit von 6 Stunden ist mindestens eine halbe Stunde Pause Pflicht.**" and
„**Bei der täglichen Maximalarbeitszeit von 8 Stunden müssen mindestens 45 Minuten Pause
eingehalten werden.**" — https://pland.app/arbeitslexikon/dienstplan. The page names an 8-hour
„tägliche Maximalarbeitszeit" but never cites ArbZG.

**Ungeprüft.** The 30/45-minute figures correspond to the ArbZG break schedule that this repo's
own recipe comment already names (`§4 ArbZG: 30 min pauză după 6 h, 45 min după 9 h`) — note
the *45-minute* trigger differs between the two statements (pland.app ties 45 min to the 8 h
maximum; the ArbZG threshold commonly cited is > 9 h). Do not hard-code either without checking
the statute text; if you implement breaks, make the thresholds named constants with the
paragraph in the comment, per repo rule P10.

**Fakt (pland.app, co-determination).** „Laut **§ 87 Abs. 1 Nr. 2 BetrVG** haben Mitarbeiter
zudem ein **Mitspracherecht** bei der Erstellung ihres Dienstplans, weswegen diese in großen
Unternehmen im Regelfall **genehmigungspflichtig** sind."
— https://pland.app/arbeitslexikon/dienstplan. **Nothing in this repo models a Betriebsrat, an
approval step, or a plan-approval status.** `PlanStatus` has only DRAFT/PUBLISHED/ARCHIVED
(`models.py:90-93`).

### 2.4 Qualification — the one constraint the sources demand and the repo lacks

**Fakt (pland.app).** Qualification is the competitor's single most-repeated planning claim:

| Wording | Source |
|---|---|
| „Filtern Sie Mitarbeiter nach **Qualifikationen und Kapazitäten**" | https://pland.app/funktionen/einsatzplanung-gebaeudereinigung |
| „Einsätze an Mitarbeiter basierend auf deren **Qualifikationen und Verfügbarkeiten** in Echtzeit zugewiesen" | https://pland.app/arbeitslexikon/personaleinsatzplanung |
| „Mitarbeitende werden basierend auf **Qualifikationen** und Verfügbarkeiten optimal eingeplant" | https://pland.app/blog/digitaler-dienstplan-5-vorteile-von-denen-ihr-unternehmen-profitiert |
| „die Mitarbeiterqualifikationen mit ihren Aufgabenbereichen abgeglichen … Ziel ist es, **Unter-, oder Überforderung** frühzeitig zu erkennen" | https://pland.app/arbeitslexikon/personaleinsatzplanung |
| Planner filters: **Objekterfahrung** (has worked at this object before) and **Auftragsarten** (has performed e.g. an Unterhaltsreinigung before) | https://pland.app/onboardings/auftrage-und-einsatzplanung-in-pland |

**Fakt (repo).** `Zone.category` is stored and **never read by the planner**. There is no
skill/qualification matching between the zone's `ServiceCategory` and the worker's
`AccountService` rows. `services.py:112-116` selects zones with
`.select_related("site", "category")` but `category` is only used by the Reinigungsplan export
and the templates.

**Vorschlag — the smallest correct qualification check.** The account already declares services
(`account.services` → `AccountService.category`, used by `suggest_providers` at
`apps/marketplace/scoring.py:174`). Add to `build_capacities` (`services.py:66-78`):

```python
categories = set(contract.worker.services.values_list("category_id", flat=True))
```

carry it on `WorkerCapacity` as `categories: set[int]`, and add the check **first** in `_fits`
(before locality, because it is the cheapest and the most informative):

```python
if category_id not in cap.categories:
    return "nu are calificarea pentru acest serviciu"
```

passing `zone.category_id` from `services.py:127`. Two cautions:

1. An **empty** `categories` set must mean "no restriction", not "qualified for nothing" —
   otherwise every existing tenant's plan empties on deploy. Mirror the locality fallback at
   `services.py:68-70`: `... or None`, and skip the check when it is `None`.
2. `tests/test_planning.py` fixtures give the worker no `AccountService` rows, so the
   empty-set-means-unrestricted rule is what keeps the suite green. Add a positive test that a
   worker *with* declared services is refused a zone outside them.

---

## 3. Absence — Urlaub, Krankheit, Urlaubsanspruch

### 3.1 What exists in the repo: nothing

**Fakt.** There is **no absence model anywhere**. `ContractDraft.vacation_days`
(`apps/contracts/models.py:167`, `PositiveSmallIntegerField(default=20)`) is the only
holiday-shaped field, and **nothing in planning reads it**. A worker on holiday is fully
allocatable today: `build_capacities` looks only at the signed contract, and `_fits` has no
availability check.

### 3.2 What the sources say the absence layer must do

**Fakt (pland.app).** Base types are **Urlaub** and **Krankheit**; further types are
tenant-defined via **Abwesenheitsart erstellen**, each carrying three settings: a
**Lohnnummer**, whether employees may request it themselves, and whether it **reduces the
Urlaubsanspruch** (example given: unbezahlter Urlaub).
— https://pland.app/onboardings/abwesenheiten-in-pland

**Entgeltfortzahlung basis.** The single most concrete configuration fact in the whole crawl,
and it appears in **two variants** that must be reconciled before coding:

| Source | Options given |
|---|---|
| https://pland.app/funktionen/lohnabrechnung-gebaeudereinigung | „Wählen Sie zwischen **unbezahlt**, **Vertragsstunden**, **geplanten Stunden** oder dem **Stundendurchschnitt**." (4 values) |
| https://pland.app/onboardings/abwesenheiten-in-pland | „Hier kann man zum Beispiel die **Vertragsstunden**, **Planstunden** oder den **Stundendurchschnitt** angeben." (3 values; „geplante Stunden" appears as „Planstunden") |

Definitions, verbatim from the onboarding page: *„Bei **Vertragsstunden** nimmt PlanD automatisch
die Stunden, die im Vertrag hinterlegt sind, bei **Planstunden**, die Stunden, die der
Mitarbeiter in dem Zeitraum geplant ist und beim **Stundendurchschnitt** berechnet PlanD den
Durchschnitt an gearbeiteten Stunden in den **letzten drei Monaten**."*

**Urlaubsanspruch.**

| Fact | Value | Source |
|---|---|---|
| Branch default annual entitlement | **30 Tage** „laut Rahmentarifvertrag" | https://pland.app/onboardings/einstellungen-fur-die-urlaubstageberechnung |
| Global settings offered | annual days · whether new hires have a **Wartezeit** · how **Übernahme der Urlaubstage in einen neuen Zyklus** (carry-over) works | ibid. |
| Per-employee derivation | „Die effektiven Urlaubstage werden auf der Basis der **Anzahl der Arbeitstage in der Woche** berechnet" | https://pland.app/onboardings/urlaubsanspruch-von-mitarbeitern |
| Individual adjustments | possible, explicitly including carrying **Überstunden** into the next year as extra holiday days; **every deletion of an adjustment triggers an automatic recalculation** | ibid. |
| Consumption rule | a 3-day working week ⇒ a full week of absence deducts only **3 Urlaubstage** | https://pland.app/onboardings/urlaubstage-im-urlaubsantrag |
| Visibility | remaining entitlement updates automatically, is shown to the employee in the app, and is displayed while requesting leave | ibid. |

**Caution on the 30 days.** The page attributes it to „Rahmentarifvertrag" and names **no
paragraph and no year**. `ContractDraft.vacation_days` in this repo defaults to **20**
(`apps/contracts/models.py:167`) — the two numbers disagree, and neither is sourced to a statute
in the material available. Treat 30 as *a competitor's stated branch default with a
Stand-unknown*, not as a value to hard-code. Repo rule P10 applies: annually-changing values
belong in DB rows with `valid_from`/`valid_to`.

**Approval.** „Die **Genehmigung durch Vorgesetzte** erfolgt mit nur einem Klick"
(https://pland.app/gebaeudereinigung-app); employees are auto-notified of Freigabe/Änderung
(„Digitaler Urlaubsantrag", https://pland.app/funktionen/uebersicht). Sick notes:
„Mitarbeiter erstellen Krankheits- und Urlaubsanträge ganz einfach über die PlanD App und können
**Krankheitsscheine und Dokumente** sofort hinterlegen"
(https://pland.app/funktionen/einsatzplanung-gebaeudereinigung).

**Shared calendar.** One **Abwesenheitskalender in Echtzeit** for Objektleitung, Innendienst,
Geschäftsführung, covering past and upcoming absences, with Urlaubsanträge planned in the same
view (https://pland.app/funktionen/abwesenheitsverwaltung,
https://pland.app/funktionen/einsatzplanung-gebaeudereinigung).

### 3.3 How absence must feed planning

**Vorschlag.** Absence belongs in a new `apps/absences` (or in `apps/planning` if you keep the
app count down), with three models and exactly one integration point:

```python
class AbsenceKind(models.TextChoices):
    URLAUB     = "URLAUB",     "Concediu"
    KRANKHEIT  = "KRANKHEIT",  "Boală"
    UNPAID     = "UNPAID",     "Concediu fără plată"

class ContinuedPayBasis(models.TextChoices):
    UNPAID          = "UNPAID",     "Neplătit"
    CONTRACT_HOURS  = "CONTRACT",   "Ore contractuale"
    PLANNED_HOURS   = "PLANNED",    "Ore planificate"
    AVERAGE_HOURS   = "AVERAGE",    "Media ultimelor 3 luni"
```

`Absence(worker, employer, kind, starts_on, ends_on, status, continued_pay_basis,
requested_at, decided_by, decided_at, note)` plus an append-only `AbsenceEvent` mirroring
`ShiftEvent` (`models.py:188-220`) — a sick note is evidence, so the same immutability argument
applies.

**The integration point is `build_capacities`, not `_fits`.** Two reasons:

1. A whole-day absence removes a *day*, not a *minute budget*; putting it in `_fits` would make
   every refusal message say "absent" instead of the real binding constraint.
2. `WorkerCapacity` already carries `per_day` — an absent day is naturally expressed by
   pre-seeding `cap.per_day[day] = MAX_DAILY_MINUTES`, which makes the existing §3 check refuse
   it with a message you can then specialise.

The clean version: add `blocked_days: set[date]` to `WorkerCapacity` (`services.py:34-48`),
populate it in `build_capacities` from approved absences overlapping the week, and add as the
**first** check in `_fits`:

```python
if day in cap.blocked_days:
    return "absent în ziua respectivă"
```

Then the existing machinery does the rest: the visit lands in `plan.unmet_demand` with a
per-worker reason (`services.py:133-141`) and the planner sees it. **Do not** silently drop the
visit.

**Do not** deduct absence from `weekly_minutes`. The contracted budget is a legal ceiling on
*worked* hours (P1); Entgeltfortzahlung is a payroll concept, not a planning one. Keep them
separate — the calculation `PLANNED_HOURS` needs the plan, so the dependency runs
planning → payroll, never back.

---

## 4. Vertretung — the substitution flow

### 4.1 The gap in the repo, precisely

**Fakt.** The shift lifecycle, from `apps/planning/attendance.py:82-175`:

```
                       (plan must be PUBLISHED for every transition below)
   PLANNED ──confirm_shift──> CONFIRMED
      │  └──decline_shift──> DECLINED  ◄──decline_shift── CONFIRMED
      │
      ├──check_in──────────> IN_PROGRESS ──check_out──> DONE
   CONFIRMED ──check_in────>              (actual_minutes computed)
      │
   any state ──mark_missed (employer)──> MISSED
   any state ──correct_minutes (employer)──> DONE
```

| Function | file:line | allowed source states (`_guard`) | writes | event |
|---|---|---|---|---|
| `confirm_shift(shift, account)` | `attendance.py:91-97` | `{PLANNED}` | `status` | `CONFIRMED` |
| `decline_shift(shift, account, reason="")` | `:100-110` | `{PLANNED, CONFIRMED}` | `status`, `worker_note = reason[:300]` | `DECLINED`, payload `{"reason": …}` |
| `check_in(shift, account, now=None)` | `:113-124` | `{PLANNED, CONFIRMED}` | `checked_in_at`, `status=IN_PROGRESS` | `CHECK_IN`, payload `{"at": …}` |
| `check_out(shift, account, now=None, note="")` | `:127-144` | `{IN_PROGRESS}` | `checked_out_at`, `actual_minutes`, `status=DONE`, `worker_note` if note | `CHECK_OUT`, payload `{"at": …, "minutes": …}` |
| `correct_minutes(shift, employer_account, minutes, reason)` | `:147-165` | **no `_guard`** — employer-ownership check only | `actual_minutes`, `status=DONE` | `CORRECTED`, payload `{"from", "to", "reason"}` |
| `mark_missed(shift, employer_account)` | `:168-175` | **no `_guard`** — employer-ownership check only | `status=MISSED` | `MISSED` |

**Fakt.** **`DECLINED` is terminal.** There is no transition out of it, no re-assignment
function, and — critically — a declined visit is **not** added to `plan.unmet_demand`. The work
silently disappears from the schedule. That is the single largest correctness gap in the
planning subsystem.

**Fakt.** `my_shifts_view` flashes *„Tură refuzată. Angajatorul a fost informat."*
(`apps/planning/views.py:162`) — **no notification is sent**. The employer only discovers it in
`time_records_view`'s "Ture neîncheiate" list (`views.py:212-216`), and only if they look.

**Fakt.** `_guard` — `attendance.py:82-88`, the three checks every worker action passes:

```python
def _guard(shift: Shift, account, allowed: set[str]):
    if shift.worker_id != account.pk:
        raise ShiftError("Tura nu îți aparține.")
    if shift.plan.status != PlanStatus.PUBLISHED:
        raise ShiftError("Planul nu este publicat.")
    if shift.status not in allowed:
        raise ShiftError(f"Tura este în starea {shift.get_status_display()}.")
```

`ShiftError` subclasses `ValueError` (`attendance.py:25-26`) and is caught in the views to
become a flash message.

### 4.2 The flow the sources describe

**Fakt (pland.app), W3 Krankmeldung → Vertretung**, assembled from
https://pland.app/funktionen/abwesenheitsverwaltung,
https://pland.app/funktionen/einsatzplanung-gebaeudereinigung and
https://pland.app/onboardings/abwesenheiten-in-pland:

1. Mitarbeiter meldet Krankheit/Urlaub **in der App**, hängt Krankheitsschein/Dokumente an.
2. Erscheint im gemeinsamen **Abwesenheitskalender** (Objektleitung, Innendienst,
   Geschäftsführung).
3. Das System listet die **Betroffenen Einsätze** und schlägt **Vertretungen basierend auf
   Kapazitäten und Qualifikationen** vor: „Fällt eine Reinigungskraft kurzfristig aus, werden
   Ihnen automatisch die am besten geeignete Vertretungen, **basierend auf Kapazitäten und
   Qualifikationen**, vorgeschlagen" (https://pland.app/arbeitslexikon/reinigungsplan).
4. Each affected Einsatz is either **reassigned immediately** — the new employee gets a
   **Push-Benachrichtigung** — or turned into an **Offene Schicht**; confirm with **Zuweisen**.
5. **Kunde wird per E-Mail automatisch über die Vertretung informiert** — customer notification
   is an explicit part of the flow
   (https://pland.app/funktionen/einsatzplanung-gebaeudereinigung), configurable under
   Einstellungen → Abwesenheiten → **E-Mail Benachrichtigung**
   (https://pland.app/onboardings/abwesenheiten-in-pland).

**Fakt (visual vocabulary, worth stealing for the UI).**
https://pland.app/onboardings/auftrage-und-einsatzplanung-in-pland and
https://pland.app/onboardings/abwesenheiten-in-pland:

| Signal | Meaning |
|---|---|
| Grün | abgeschlossener Einsatz |
| Rot (Einsatz) | nicht abgeschlossener Einsatz |
| Blau | Einsatz in der Zukunft |
| Graue Flächen | Tage, an denen Mitarbeiter nicht zur Verfügung stehen |
| **Oranger Balken** | Mitarbeiter im Urlaub (Abwesenheit) |
| **Grau gesetzte Einsätze** | Einsätze im Abwesenheitszeitraum, die nicht angetreten werden können |
| **Kleines Flugzeug am Einsatz** | Vertretungseinsatz |
| Roter Kapazitätsbalken | geplante Zeiten überzogen |
| Kleine Symbole oben rechts | Teameinsatz / wiederkehrender Einsatz |
| **Lupe** in der Leiste | list all **unbesetzte Einsätze**, assignable by drag-and-drop |

**Fakt (organisational practice).** A standby pool is named as a manual practice, not an
algorithm: „Bestimmen Sie Mitarbeiter, die **auf Abruf** da sind, um **Krankheitsfälle**
auszugleichen und Einsätze übernehmen können, die sonst auszufallen drohen."
— https://pland.app/blog/was-muss-ich-bei-einer-effizienten-personaleinsatzplanung-beachten

### 4.3 Vorschlag — the substitution flow for this repo

Three states are missing from `ShiftStatus` (`models.py:131-137`). **Watch the column width:
`max_length=12`, and `"IN_PROGRESS"` is already 11 characters** — any new value must be ≤ 12
characters or the field needs an `AlterField` migration.

```python
OPEN = "OPEN", "Neatribuită"      #  4 chars — the "offene Schicht"
```

Then one service in `attendance.py`, shaped exactly like `mark_missed` (`:168-175`):

```python
@transaction.atomic
def release_shift(shift: Shift, employer_account, reason: str = "") -> Shift:
    """
    Tura rămâne, dar fără lucrător: e o schimbare de acoperire, nu o anulare.
    Munca nu dispare din plan — devine vizibilă ca neatribuită.
    """
    if shift.plan.account_id != employer_account.pk:
        raise ShiftError("Doar angajatorul poate elibera o tură.")
    if shift.status in {ShiftStatus.DONE, ShiftStatus.IN_PROGRESS}:
        raise ShiftError(f"Tura este în starea {shift.get_status_display()}.")
    previous = shift.worker_id
    shift.worker = None
    shift.status = ShiftStatus.OPEN
    shift.save(update_fields=["worker", "status"])
    ShiftEvent.objects.create(
        shift=shift, kind=ShiftEvent.Kind.RELEASED, actor=employer_account,
        payload={"from_worker": previous, "reason": reason[:300]},
    )
    return shift


@transaction.atomic
def reassign_shift(shift: Shift, employer_account, worker, notify: bool = True) -> Shift:
    """Vertretung. Cine a preluat și când rămâne în jurnal — e o dovadă, nu o notă."""
    if shift.plan.account_id != employer_account.pk:
        raise ShiftError("Doar angajatorul poate reatribui o tură.")
    if shift.status in {ShiftStatus.DONE, ShiftStatus.IN_PROGRESS}:
        raise ShiftError(f"Tura este în starea {shift.get_status_display()}.")
    previous = shift.worker_id
    shift.worker = worker
    shift.status = ShiftStatus.PLANNED
    shift.save(update_fields=["worker", "status"])
    ShiftEvent.objects.create(
        shift=shift, kind=ShiftEvent.Kind.REASSIGNED, actor=employer_account,
        payload={"from_worker": previous, "to_worker": worker.pk},
    )
    if notify:
        _notify_single_shift(shift)      # German, like _notify_workers
    return shift
```

Add `RELEASED = "RELEASED", "Tură eliberată"` (8 chars) and
`REASSIGNED = "REASSIGNED", "Tură reatribuită"` (10 chars) to `ShiftEvent.Kind`
(`models.py:195-202`) — both fit `max_length=12`.

**A substitute candidate list must reuse the existing constraint code, not reimplement it.**
The correct shape (`Vorschlag`):

```python
def substitution_candidates(shift: Shift) -> list[tuple[object, str | None]]:
    """
    Cine ar putea prelua tura, cu motivul refuzului acolo unde nu se poate.
    Aceleași constrângeri ca la generare — altfel Vertretung ocolește §3 ArbZG.
    """
    week_start = shift.plan.week_start
    capacities = build_capacities(shift.plan.account, week_start)
    _replay_week(capacities, shift.plan, exclude=shift)   # rebuild used_minutes/per_day
    return [
        (cap, _fits(cap, shift.date, shift.duration_minutes, shift.zone.site.locality_id))
        for cap in capacities
        if cap.account_id != shift.worker_id
    ]
```

`_replay_week` is the piece you must write: `WorkerCapacity` starts empty, so you have to walk
the plan's existing shifts and re-apply `used_minutes` / `per_day` / `day_end` exactly as
`generate_week_plan` does at `services.py:149-151`, otherwise every candidate looks free and the
Vertretung quietly blows the weekly budget. **This is the trap.** Extract that three-line
bookkeeping into a helper used by both call sites rather than duplicating it.

**Then update all four places that enumerate statuses** whenever you add one:

* `attendance.py:185` — `status__in=[ShiftStatus.DONE, ShiftStatus.MISSED]` (the register)
* `views.py:214` — `.exclude(status__in=[ShiftStatus.DONE, ShiftStatus.MISSED])` ("Ture neîncheiate")
* `calibration.py:101` — `status=ShiftStatus.DONE` (calibration sample)
* `views.py:173` — `if s.status == ShiftStatus.DONE` (worker's weekly total)

And grep `apps/devices` — `find_discrepancies` filters `status=ShiftStatus.DONE`
(`apps/devices/services.py:130-177`) and `match_shift` reads `Shift.date`/`start_time`/
`duration_minutes` (`:89-117`).

**Templates compare raw status strings**: `{% if s.status == 'PLANNED' %}`
(`templates/dashboard/my_shifts.html:16`), `{% elif s.status == 'IN_PROGRESS' %}` (`:28`),
`{% if plan.status == 'DRAFT' %}` (`templates/dashboard/planning.html:24`). Renaming a
`TextChoices` **value** breaks the UI with no Python error. Rename labels freely; never rename
values without grepping the templates.

---

## 5. Notification on plan changes

### 5.1 What the repo sends

**Fakt.** Exactly one notification exists: `_notify_workers` — `apps/planning/attendance.py:48-74`,
called only from `publish_plan` (`:43-44`).

* **One email per worker, not per shift** (docstring `:49`); shifts are grouped by
  `worker_id`, unassigned shifts are skipped (`:50-53`).
* Recipient: `worker.contact_email or _login_email(worker)` where `_login_email` is
  `account.memberships.select_related("user").first().user.email` (`:77-79`). Workers with no
  address are **silently skipped** (`:59-60`).
* The mail is the one **German** artefact in the subsystem (`:66-72`):

```python
send_mail(
    subject=f"Dein Einsatzplan ab {plan.week_start.strftime('%d.%m.%Y')}",
    message="Deine Einsätze:\n\n" + "\n".join(lines),
    from_email=None,
    recipient_list=[email],
    fail_silently=True,
)
```

with each line `f"{s.date.strftime('%d.%m.%Y')} {s.start_time.strftime('%H:%M')} — "
f"{s.zone.site.name} / {s.zone.name} ({s.duration_minutes} min)"` (`:62-64`).

* Sent **synchronously inside the publish transaction** with `fail_silently=True`, so a slow
  SMTP server blocks the request and a failure is invisible.
  `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` (`config/settings.py:122`)
  — nothing is actually delivered in this environment.
* Asserted by `tests/test_attendance.py:51-58`: exactly one message in `mail.outbox`, containing
  `"Haus Nord"`.

### 5.2 What is not notified

**Fakt.** No notification on: a plan **regeneration** (`generate_week_plan(replace=True)` saves
only `unmet_demand` at `services.py:154-155` — status stays `PUBLISHED`, `published_at` is not
touched, **no new `PUBLISHED` events, no email**); a **decline**; a `mark_missed`; a
`correct_minutes`; an applied calibration. There is no notification model, no in-app inbox, no
push channel, no customer-facing message of any kind.

### 5.3 What the sources require

**Fakt (pland.app).**

| Requirement | Wording | Source |
|---|---|---|
| Real-time push on every roster change | „Mitarbeiter werden automatisch über **neue Einsätze oder Änderungen** im Dienstplan per **Push-Benachrichtigung** auf ihrem Smartphone informiert." | https://pland.app/funktionen/einsatzplanung-gebaeudereinigung |
| Same, restated | „Änderungen im Dienstplan werden **in Echtzeit** per Push-Benachrichtigung an die Mitarbeiter geschickt" | https://pland.app/funktionen/uebersicht |
| Substitute gets pushed | the reassigned employee „bekommt direkt eine **Push-Benachrichtigung** über ihren Einsatz" | https://pland.app/onboardings/abwesenheiten-in-pland |
| **Customer** informed about substitutions | „informieren Sie **Kunden per E-Mail automatisch** über die Vertretung" | https://pland.app/funktionen/einsatzplanung-gebaeudereinigung |
| Customer notification is a setting | Einstellungen → Abwesenheiten → **E-Mail Benachrichtigung**: whether customers are informed about absences and substitutions | https://pland.app/onboardings/abwesenheiten-in-pland |
| Employee auto-notified on leave approval/change | „Digitaler Urlaubsantrag" — auto-notification on Freigabe/Änderung | https://pland.app/funktionen/uebersicht |

**Vorschlag.** Before adding channels, fix the correctness bug: **`generate_week_plan(replace=True)`
on a published week silently swaps every worker's schedule with no journal entry and no
message.** The minimal correct behaviour is to diff old vs new shifts inside the regeneration,
emit a fresh `ShiftEvent` per changed shift, and re-notify only the affected workers — the
`by_worker` grouping in `_notify_workers` (`attendance.py:50-53`) is already the right shape for
"notify only who is affected". Only then add a `Notification` model or a push channel.

**Ungeprüft.** A German employer changing a published Dienstplan at short notice touches
Ankündigungsfristen and, where a Betriebsrat exists, §87 Abs. 1 Nr. 2 BetrVG (which pland.app
does cite, see §2.3). Neither a notice period nor an approval step is modelled here, and no
source in the crawl gives a number of days. Do not invent one.

---

## 6. Constraint checklist for any new allocation code

Use this as the review gate. Every item is either enforced today or explicitly not.

| # | Constraint | Enforced? | Where / what to do |
|---|---|---|---|
| 1 | Signed contract exists and covers the week | ✅ | `services.py:58-64` |
| 2 | Weekly contracted budget | ✅ | `services.py:86-87` — a **hard refusal**, never a warning |
| 3 | Monthly Geringfügigkeitsgrenze | ❌ | weekly average only; see §2.2 |
| 4 | §3 ArbZG 8 h/day | ✅ | `services.py:88-89` |
| 5 | §5 ArbZG 11 h rest | ⚠️ encoded, unreachable | `services.py:90-94`; becomes live if `DAY_START` or `MAX_DAILY_MINUTES` changes |
| 6 | §9 ArbZG Sunday | ✅ | `services.py:161` (day-stripping, not refusal) |
| 7 | §4 ArbZG breaks | ❌ | no `break_minutes`; `check_out` bills the whole span |
| 8 | §11 ArbZG max 6 consecutive days | ❌ | add as a `_fits` check with a Romanian reason naming the paragraph |
| 9 | Locality served | ✅ | `services.py:84-85` |
| 10 | Real distance / travel buffer | ❌ | lat/lng and `willing_to_travel_km` exist and are unused |
| 11 | Qualification / Auftragsart | ❌ | `Zone.category` never read by the planner; see §2.4 |
| 12 | Absence (Urlaub/Krankheit) | ❌ | no model; see §3.3 |
| 13 | Double-booking of one worker | ✅ implicitly | shifts are packed sequentially from `per_day`, so overlap is impossible **within** a plan; nothing prevents it across two plans of the same week (blocked by `uniq_plan_per_week`) or against a manually created shift |
| 14 | Per-person (not per-contract) limits | ❌ | one `WorkerCapacity` per contract; see §2.2 |
| 15 | Tenant isolation | ✅ | `services.py:113`, and every queryset in §P9 of SKILL.md |
| 16 | Unallocatable work reported with reason | ✅ | `services.py:133-141`; **preserve the dict shape** |

---

## Quellen

Repository (read 2026-08-29, paths relative to `/Users/Geronimo/Projects/Cleaning_SaaS`):

* `apps/planning/services.py` — docstring 1-15, constants 27-31, `WorkerCapacity` 34-48,
  `build_capacities` 51-79, `_fits` 82-95, `generate_week_plan` 98-156, `_visit_days` 159-169
* `apps/planning/attendance.py` — `RETENTION_YEARS` 22, `ShiftError` 25-26,
  `publish_plan` 29-45, `_notify_workers` 48-74, `_login_email` 77-79, `_guard` 82-88,
  lifecycle services 91-175, `time_records` 178-205
* `apps/planning/models.py` — `Zone` 42-87, `PlanStatus` 90-93, `ShiftStatus` 131-137,
  `Shift` 140-185, `ShiftEvent` 188-220
* `apps/planning/views.py` — `planning_view` 60-96, `my_shifts_view` 136-181,
  `time_records_view` 184-223
* `apps/contracts/models.py` — `MinijobThreshold` 92-113, `ContractDraft.vacation_days` 167
* `apps/accounts/profiles.py` — `WorkerProfile.willing_to_travel_km` 26, `ServiceArea` 86-97
* `apps/geo/models.py` 30-31
* `apps/devices/services.py` — `MATCH_TOLERANCE` 14, `match_shift` 89-106, `_overlaps` 109-117,
  `find_discrepancies` 130-177
* `apps/marketplace/scoring.py` — `suggest_providers` 160-190
* `config/settings.py` 105-122
* `templates/dashboard/my_shifts.html`, `templates/dashboard/planning.html`
* `tests/test_planning.py`, `tests/test_attendance.py`

pland.app (crawled 2026-08-29):

* https://pland.app/arbeitslexikon/dienstplan
* https://pland.app/arbeitslexikon/personaleinsatzplanung
* https://pland.app/arbeitslexikon/reinigungsplan
* https://pland.app/funktionen/einsatzplanung-gebaeudereinigung
* https://pland.app/funktionen/abwesenheitsverwaltung
* https://pland.app/funktionen/lohnabrechnung-gebaeudereinigung
* https://pland.app/funktionen/uebersicht
* https://pland.app/gebaeudereinigung-app
* https://pland.app/onboardings/abwesenheiten-in-pland
* https://pland.app/onboardings/auftrage-und-einsatzplanung-in-pland
* https://pland.app/onboardings/einstellungen-fur-die-urlaubstageberechnung
* https://pland.app/onboardings/urlaubsanspruch-von-mitarbeitern
* https://pland.app/onboardings/urlaubstage-im-urlaubsantrag
* https://pland.app/onboardings/freigabe-von-zeiterfassungen
* https://pland.app/blog/was-muss-ich-bei-einer-effizienten-personaleinsatzplanung-beachten
* https://pland.app/blog/digitaler-dienstplan-5-vorteile-von-denen-ihr-unternehmen-profitiert
* https://pland.app/blog/gebaudereinigung-wie-erstelle-ich-den-perfekten-einsatzplan-vorlage
