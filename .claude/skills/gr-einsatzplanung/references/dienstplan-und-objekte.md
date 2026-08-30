# Dienstplan und Objekte — what the plan must contain, and how Objekt/Zone/Auftrag hang together

Covers: every field the sources name for an Einsatzplan/Dienstplan, the Objekt→Zone→Auftrag
structure as it exists in this repo and as pland.app describes it, Daueraufträge vs one-off
Sonderaufträge, Reinigungsintervalle, and the relationship between a **Reinigungsplan** (what is
cleaned, how often, by whom, checked how) and a **Dienstplan** (who works when).

**Stand: 2026-08-29.** Repo claims read from `/Users/Geronimo/Projects/Cleaning_SaaS`;
pland.app claims from the crawl of 2026-08-29 with the source URL on every row. Legal content is
reference material, not legal advice.

---

## 1. Reinigungsplan vs Dienstplan — the distinction that drives the data model

**Fakt (pland.app).** These are two different documents in the German trade, with different
audiences and different lifetimes.

| | **Reinigungsplan** | **Dienstplan** |
|---|---|---|
| Answers | *What is cleaned, where, how often, by whom, checked how* | *Which person works which hours on which day* |
| Definition | „Ein Reinigungsplan ist ein **schriftlich festgelegtes Konzept**, das die Art und Weise der Reinigung in einem Gebäude oder einer Einrichtung beschreibt." — https://pland.app/arbeitslexikon/reinigungsplan | „Es gilt, die Dienstpläne von Arbeitskräften in **Vollzeit, Teilzeit und Minijobbern** zu koordinieren … sodass … jederzeit die richtige Anzahl an qualifizierten Personalressourcen zum richtigen Zeitpunkt an den zu besetzenden Einsatzorten verfügbar ist." — https://pland.app/arbeitslexikon/dienstplan |
| Structured by | **room / area** — „In der Regel ist er nach Räumlichkeiten oder Bereichen aufgeteilt" (same URL) | **person × day** |
| Lifetime | months–years; „in regelmäßigen Abständen überarbeitet" (same URL) | one week / one period |
| Legal weight | „kann der Plan als **Nachweis** für die durchgeführten Reinigungsarbeiten dienen, was insbesondere im Falle von **Beschwerden oder Streitigkeiten** von Vorteil ist" — https://pland.app/arbeitslexikon/reinigungsplan | co-determination: „Laut **§ 87 Abs. 1 Nr. 2 BetrVG** haben Mitarbeiter … ein Mitspracherecht bei der Erstellung ihres Dienstplans, weswegen diese in großen Unternehmen im Regelfall **genehmigungspflichtig** sind." — https://pland.app/arbeitslexikon/dienstplan |
| In this repo | derived from `Zone` rows, exported as XLSX (`apps/planning/reinigungsplan.py`) | derived from `ShiftPlan` + `Shift` (`apps/planning/services.py:98-156`) |

**Fakt (code).** The repo models this correctly: the Reinigungsplan is *not* a table. It is a
**projection of the `Zone` rows of one `Site`** — `zone_rows(site)` at
`apps/planning/reinigungsplan.py:37-54`. The Dienstplan is a materialised weekly table
(`ShiftPlan` → `Shift`). One is the standing specification; the other is this week's execution
of it.

---

## 2. The five mandatory Reinigungsplan content blocks

**Fakt.** Source: https://pland.app/arbeitslexikon/reinigungsplan (verbatim block names).

| Block (German) | What it holds | Repo coverage |
|---|---|---|
| **Raum- oder Bereichsbezeichnung** | a clear identifier for every room/area to be cleaned | `Zone.name` (`models.py:49`) + `Site.name` (`models.py:27`); exported as `f"{site.name} · {z.name}"` (`reinigungsplan.py:45`) |
| **Reinigungsaufgaben** | per area: Staubsaugen, Wischen, Abstauben, Fensterreinigung, Desinfektion, Müllentsorgung | partially — `Zone.category` (`taxonomy.ServiceCategory`, leaf only) is the *service*, `Zone.description` (`models.py:53-56`, max 300 chars) is the free-text instruction. **There is no task list model.** |
| **Zeitrahmen** | täglich / wöchentlich / monatlich / jährlich | partially — `visits_per_week` + `allowed_weekdays` express a **weekly** rhythm only. Monthly, quarterly, semi-annual and annual intervals **cannot be expressed** today. |
| **Verantwortlichkeit** | the person or team performing it — internal cleaner or external company | **missing at plan level.** Responsibility only appears once a `Shift` is generated (`Shift.worker`, `models.py:143-146`). There is no Objektleiter field on `Site`. |
| **Kontrolle** | quality-control mechanism, e.g. periodic inspection by the Objektleiter | **missing.** No Qualitätskontrolle / Checkliste / Mangel model exists anywhere in the repo. |

**Fakt.** The four columns pland.app's downloadable template promises:
„Bereich/Ort · Leistung · Beschreibung · Reinigungsfrequenz" —
https://pland.app/blog/gebaudereinigung-reinigungsplan-hier-kostenlose-vorlage-herunterladen
(the page lists exactly these four as the columns a Vorlage „idealerweise" should have, and adds
„Je nach Bedarf können weitere Spalten hinzugefügt werden, beispielsweise für Materialien oder
spezielle Anweisungen").

**Fakt (code).** `apps/planning/reinigungsplan.py:18-26` exports those four **plus three the
empty template cannot produce**, exactly as its own docstring (`reinigungsplan.py:1-10`) claims:

```python
HEADERS = [
    ("Bereich / Ort", 34),
    ("Leistung", 30),
    ("Beschreibung", 46),
    ("Reinigungsfrequenz", 22),
    ("Dauer je Einsatz", 18),
    ("Wochentage", 18),
    ("Minuten / Woche", 16),
]
```

Row construction, `reinigungsplan.py:43-54`:

| Column | Value | Source field |
|---|---|---|
| Bereich / Ort | `f"{site.name} · {z.name}"` | `Site.name`, `Zone.name` |
| Leistung | `z.category.name_de or z.category.name` | `taxonomy.ServiceCategory` |
| Beschreibung | `z.description` | `Zone.description` |
| Reinigungsfrequenz | `frequency_label(z.visits_per_week)` | see §4 |
| Dauer je Einsatz | `f"{z.minutes_per_visit} min"` | `Zone.minutes_per_visit` |
| Wochentage | `", ".join(WEEKDAY_DE[d] for d in z.weekdays)` | `Zone.allowed_weekdays` |
| Minuten / Woche | `z.weekly_minutes` | `minutes_per_visit * visits_per_week` |

`WEEKDAY_DE = {1: "Mo", 2: "Di", 3: "Mi", 4: "Do", 5: "Fr", 6: "Sa", 7: "So"}`
(`reinigungsplan.py:16`) — **German**, because the document goes to the customer and the worker
(docstring `reinigungsplan.py:9`).

Workbook layout, `reinigungsplan.py:62-91`: title in `A1` (`f"Reinigungsplan — {site.name}"`,
14 pt bold), address in `A2` (`f"{site.street}, {site.postal_code} {site.locality.name}"`,
10 pt, colour `666666`), header row is **row 4** with fill `1F3A5F` and white bold text, data
from row 5, a bold `Summe` row at `header_row + len(rows) + 1` summing column 7, and
`freeze_panes` at row 5 column 1. Filename `f"reinigungsplan-{slugify(site.name)}.xlsx"`
(`reinigungsplan.py:99-102`).

Only **active** zones appear: `Zone.objects.filter(site=site, is_active=True)`
(`reinigungsplan.py:38-42`), asserted by `tests/test_reinigungsplan.py:52-56`.

Route + authorisation: `dashboard:site_reinigungsplan` at
`obiective/<int:pk>/reinigungsplan.xlsx` (`apps/dashboard/urls.py:34-35`); the view raises
`PermissionDenied` for an anonymous account and 404s a foreign `Site`
(`apps/planning/views.py:296-310`), asserted by `tests/test_reinigungsplan.py:94-98`.

---

## 3. Objekt / Zone / Auftrag — repo structure

### 3.1 `Site` — the Objekt (`apps/planning/models.py:21-39`, table `planning_site`)

Docstring: `"""Obiectivul de curățat: o clădire, o reședință, un sediu."""`

| Field | Definition | Note |
|---|---|---|
| `account` | `ForeignKey("accounts.Account", CASCADE, related_name="sites")` | the tenant |
| `name` | `CharField(max_length=160)` | |
| `locality` | `ForeignKey("geo.Locality", PROTECT, related_name="sites")` | **the only geographic matching key the planner uses** |
| `street` | `CharField(max_length=160, blank=True)` | |
| `postal_code` | `CharField(max_length=5, blank=True)` | German PLZ width |
| `is_active` | `BooleanField(default=True)` | soft delete; the generator filters `site__is_active=True` |

`Meta`: `ordering = ("name",)`, `verbose_name = "Obiectiv"`, `verbose_name_plural = "Obiective"`.
No constraints, no indexes, no `clean()`.

**Missing versus pland.app's Objekt** — none of these exist as fields:
`objektleiter` (https://pland.app/onboardings/kunden-objekte-in-pland), geocoded lat/lng,
`radius_meter` for a Standortkontrolle (https://pland.app/funktionen/uebersicht:
„Werden Sie automatisch informiert, wenn Mitarbeiter **außerhalb des geplanten Objekt-Radius'**
Zeiten erfassen"), `vertragsende`, `zugangscode` / Sonstiges, digitale Objektmappe,
`kunde` FK. `Site` also has **no customer** — the account owning the Site *is* the employer, and
there is no Kunde entity in the repo at all.

Reverse accessor added by another app: `site.devices` (`apps/devices/models.py:49`,
`on_delete=SET_NULL`).

### 3.2 `Zone` — the planning granularity (`apps/planning/models.py:42-87`, table `planning_zone`)

Docstring: *„O suprafață cu propriul ritm de curățenie. Granularitatea la care se face
planificarea — nu clădirea întreagă, ci „etajul 2, coridor + băi"."*

| Field | Definition | Note |
|---|---|---|
| `site` | `ForeignKey(Site, CASCADE, related_name="zones")` | |
| `name` | `CharField(max_length=160)` | the Reinigungsplan's *Bereichsbezeichnung* |
| `category` | `ForeignKey("taxonomy.ServiceCategory", PROTECT, related_name="zones")` | **leaf categories only** — `clean()` at `:82-84`; form narrows to `ScopedLeaf.queryset()` (`forms.py:35`) |
| `description` | `CharField(max_length=300, blank=True, help_text="Instrucțiuni pentru lucrător — apar în Reinigungsplan și la check-in")` | added by migration `0004_zone_description` |
| `area_sqm` | `PositiveIntegerField(null=True, blank=True)` | **stored, never used in any calculation** |
| `minutes_per_visit` | `PositiveSmallIntegerField(help_text="Durata estimată a unei vizite")` | the single input to the planner and to calibration |
| `visits_per_week` | `PositiveSmallIntegerField(default=1)` | the Reinigungsintervall, weekly only |
| `allowed_weekdays` | `CharField(max_length=13, default="1,2,3,4,5")` | **CSV of ISO weekday indices**, not JSON. `max_length=13` == `"1,2,3,4,5,6,7"` |
| `is_active` | `BooleanField(default=True)` | |

`Meta`: `ordering = ("site", "name")`, `verbose_name = "Zonă"`, `verbose_name_plural = "Zone"`.
`__str__` → `f"{self.site.name} · {self.name}"` (middle dot U+00B7).

Properties (`models.py:74-80`):

```python
@property
def weekdays(self) -> list[int]:
    return [int(x) for x in self.allowed_weekdays.split(",") if x.strip()]

@property
def weekly_minutes(self) -> int:
    return self.minutes_per_visit * self.visits_per_week
```

`clean()` (`models.py:82-87`) raises `ValidationError({"category": "Doar categoriile-frunză
sunt selectabile."})` when the category has no parent, and
`ValidationError({"allowed_weekdays": "Zilele valide sunt 1–7."})` for any index outside 1–7
(the dash is an EN DASH U+2013).

**Three layers disagree about Sunday, on purpose.** `Zone.clean()` accepts `7`;
`ZoneForm.WEEKDAYS` (`forms.py:18`) offers only 1–6 with
`help_text="Duminica nu e selectabilă (§9 ArbZG)."` (`forms.py:25`); `_visit_days`
(`services.py:161`) strips 7 regardless. Change all three or none.

**`ZoneForm` weekday trick** (`forms.py:21-44`): `weekdays` is a declared
`MultipleChoiceField`, **not** in `Meta.fields`, and `clean()` writes
`self.instance.allowed_weekdays = ",".join(sorted(data["weekdays"]))` directly. The sort is
lexicographic on strings — safe only while every value is a single digit. Adding
`allowed_weekdays` to `Meta.fields` would silently overwrite the assignment.

### 3.3 There is no `Auftrag` entity

**Fakt.** Grep confirms: no `Auftrag`, `Order`, `Contract` (commercial), `Angebot` or `Rechnung`
model exists. What the repo has instead:

* `apps/contracts.ContractDraft` is an **employment** contract (Arbeitsvertrag), not a customer
  order — `hours_per_month`, `hourly_wage`, `workplace`, `probation_months`, `vacation_days`
  (`apps/contracts/models.py:163-167`).
* `apps/marketplace.ServiceRequest` is a **customer request** that becomes `AWARDED` when an
  `Offer` wins (`apps/marketplace/services.py:100-119`) — but nothing downstream consumes it.

So the chain pland.app describes — **Angebot → Auftrag → Einsatz → Rechnung**
(https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung) — exists here only as
*Anfrage → Offer → (dead end)* on the spot side, and as *Zone → Shift* on the recurring side,
with no commercial parent joining them.

**Vorschlag.** When the Auftrag layer is added, it belongs **between** `Site` and `Zone`
conceptually but should be a sibling FK on `Zone` (`zone.auftrag`, nullable), not a
re-parenting: a single Objekt routinely carries a Dauerauftrag *and* occasional Sonderaufträge
against the same zones, and `Zone` is already the planning granularity. Keep `Zone.site` as the
authoritative tenant path (`zone.site.account`) — every isolation query in the codebase depends
on it (`services.py:113`, `calibration.py:151`, `views.py:275-277`).

### 3.4 Relationship map (verified)

```
accounts.Account ──1:N──> Site ──1:N──> Zone ──1:N──> Shift ──1:N──> ShiftEvent
       │                    │             │              ↑
       │                    │             └──1:N──> ZoneCalibration
       │                    └── FK PROTECT ─> geo.Locality
       │             Zone ── FK PROTECT ─> taxonomy.ServiceCategory (leaf only)
       ├──1:N──> ShiftPlan ──1:N──> Shift        (Shift carries BOTH plan and zone FKs)
       ├──1:N (worker, SET_NULL)──> Shift
       ├──1:N (actor, SET_NULL)──> ShiftEvent
       └──1:N (decided_by, SET_NULL)──> ZoneCalibration
```

Two independent paths lead from a `Shift` to an `Account`:

1. `shift.plan.account` — the **employer/tenant**. Used by `time_records`
   (`attendance.py:184`), `correct_minutes` (`:153`), `mark_missed` (`:170`),
   `time_records_view` (`views.py:195`).
2. `shift.worker` — the **worker**. Used by `my_shifts_view` (`views.py:154`) and `_guard`
   (`attendance.py:83`).

Zones reach the tenant only via `zone.site.account`.

---

## 4. Reinigungsintervalle

### 4.1 What the trade recognises

**Fakt.** Source: https://pland.app/arbeitslexikon/reinigungsintervall. Definition:
„Reinigungsintervalle sind **festgelegte Zeitabstände**, in denen bestimmte Reinigungsarbeiten
durchgeführt werden."

| Interval | Tasks the page assigns to it |
|---|---|
| **Tägliche Reinigung** | Reinigen von Sanitäranlagen; Staubsaugen von Teppichböden in stark frequentierten Bereichen; Leeren von Abfallbehältern |
| **Wöchentliche Reinigung** | Wischen von Hartböden; Staubwischen von Oberflächen; Reinigung von Glasflächen |
| **Monatliche Reinigung** | Grundreinigung von Teppichböden; Reinigen schwer zugänglicher Bereiche; Pflege von Holzoberflächen |
| **Vierteljährliche oder halbjährliche Reinigung** | Reinigung von Fenstern, Jalousien und Leuchten; Tiefenreinigung von Polstermöbeln |
| **Jährliche Reinigung** | umfassende Grundreinigungen: Stripping und Neuversiegeln von Bodenbelägen; Fassadenreinigung |

**Six factors that determine an interval** (same URL, the „Faktoren zur Bestimmung" list):
Gebäudenutzung (Art und Intensität, z. B. Bürogebäude, Krankenhaus, Schule) · Besucherfrequenz
(Anzahl der Personen, die das Gebäude täglich nutzen) · Hygieneanforderungen ·
Oberflächenmaterialien · Gesetzliche Vorschriften · Kundenwünsche und Budgetvorgaben.

An earlier list on the *same page* gives five determinants in different wording: Art des
Objekts/Bereichs · Nutzungsintensität · Hygieneanforderungen · Gesetzliche Vorschriften
(besonders Lebensmittelindustrie / Gesundheitswesen) · Ästhetische Ansprüche. Both lists are on
the page; neither is authoritative over the other.

**Fakt.** Intervals are expected to be **reviewed and adjusted** for saisonale Schwankungen,
Änderungen in der Gebäudenutzung and neue Hygieneanforderungen (same URL).

**Fakt (competitor capability).** „Mit PlanD legen Sie Ihre Reinigungsintervalle … digital …
fest und **Einsätze werden in Zukunft immer automatisch in den festgelegten Abständen
geplant**." — https://pland.app/arbeitslexikon/reinigungsintervall

### 4.2 What this repo can express

**Fakt.** `Zone` expresses **exactly one interval class: weekly**, as
`visits_per_week` + `allowed_weekdays`. `frequency_label` (`reinigungsplan.py:29-34`) is the
whole German vocabulary the export can emit:

```python
def frequency_label(visits_per_week: int) -> str:
    if visits_per_week >= 7:
        return "täglich"
    if visits_per_week == 1:
        return "1× wöchentlich"
    return f"{visits_per_week}× wöchentlich"
```

Asserted by `tests/test_reinigungsplan.py:58-63`:
`1 → "1× wöchentlich"`, `3 → "3× wöchentlich"`, `7 → "täglich"`.

**Monatlich, vierteljährlich, halbjährlich, jährlich and saisonal are not representable.**
A quarterly window clean must currently be faked as a separate low-`visits_per_week` zone that
is generated every week anyway — which is wrong. Say so rather than pretending otherwise.

**Vorschlag.** The minimal correct extension is an interval enum + a period anchor on `Zone`:

```python
class Interval(models.TextChoices):
    WEEKLY      = "WEEKLY",      "Săptămânal"
    MONTHLY     = "MONTHLY",     "Lunar"
    QUARTERLY   = "QUARTERLY",   "Trimestrial"
    SEMIANNUAL  = "SEMIANNUAL",  "Semestrial"
    ANNUAL      = "ANNUAL",      "Anual"
    SEASONAL    = "SEASONAL",    "Sezonier"
```

with `interval = CharField(max_length=12, choices=Interval.choices, default=Interval.WEEKLY)`
and `last_done_on = DateField(null=True, blank=True)`. `_visit_days` (`services.py:159-169`)
then becomes: for `WEEKLY` keep today's behaviour; for everything else emit **at most one** date
in the requested week and only when `week_start >= last_done_on + period`. Keep
`visits_per_week` for the weekly case rather than overloading it — `Zone.weekly_minutes`
(`models.py:78-80`) and `capacity_report` (`services.py:174-179`) both read it, and the
Reinigungsplan export prints it.

### 4.3 How `visits_per_week` is turned into dates

**Fakt.** `_visit_days` — `apps/planning/services.py:159-169`:

```python
def _visit_days(zone: Zone, week_start: date) -> list[date]:
    """Distribuie vizitele cât mai uniform peste zilele permise, fără duminică."""
    allowed = [d for d in sorted(zone.weekdays) if d != SUNDAY]
    if not allowed:
        return []
    visits = min(zone.visits_per_week, len(allowed))
    if visits == 0:
        return []
    step = len(allowed) / visits
    picked = [allowed[int(i * step)] for i in range(visits)]
    return [week_start + timedelta(days=d - 1) for d in picked]
```

Verified spread (re-run 2026-08-29 against the exact expression):

| `allowed_weekdays` | `visits_per_week` | resulting ISO weekdays |
|---|---|---|
| `1,2,3,4,5` | 1 | `[1]` |
| `1,2,3,4,5` | 2 | `[1, 3]` |
| `1,2,3,4,5` | 3 | `[1, 2, 4]` |
| `1,2,3,4,5` | 5 | `[1, 2, 3, 4, 5]` |
| `1,2,3,4,5` | 7 | `[1, 2, 3, 4, 5]` (capped) |
| `1,2,3,4,5,6,7` | 7 | `[1, 2, 3, 4, 5, 6]` (Sunday dropped, then capped at 6) |
| `1,3` | 2 | `[1, 3]` |
| `2,4` | 2 | `[2, 4]` |
| `1` | 3 | `[1]` (capped at 1) |

**Two silent behaviours you must know.**

1. `visits_per_week` is capped by `min(zone.visits_per_week, len(allowed))`, and at most **one
   visit per zone per day**. A zone with `visits_per_week=10` on 5 allowed weekdays produces 5
   shifts and **zero** `unmet_demand` entries — the lost demand is invisible.
2. `capacity_report`'s `demand_minutes` uses the **uncapped** `Zone.weekly_minutes`
   (`services.py:174-179`), so the report and the generated plan disagree for over-specified
   zones.

---

## 5. Dauerauftrag vs Sonderauftrag

**Fakt (pland.app).** The distinction is the competitor's most-repeated planning claim:
„Egal ob **regelmäßige Unterhaltsreinigung** oder **spontaner Sonderauftrag**." —
https://pland.app/funktionen/einsatzplanung-gebaeudereinigung (H1 subtitle, and repeated as
„Von der regelmäßigen Unterhaltsreinigung bis zum einmaligen Sonderauftrag").

Related trade definitions, both https://pland.app/arbeitslexikon/unterhaltsreinigung and
https://pland.app/arbeitslexikon/grundreinigung:

| Type | Definition given | Contrast the page draws |
|---|---|---|
| **Unterhaltsreinigung** | „die regelmäßige Reinigung eines Objektes in **festen Zeitabständen**"; typically Böden, Oberflächen, Möbel, Sanitäranlagen, Abfall, Staub | „zielt darauf ab, den Zustand der Räume auf einem **bereits gereinigten Niveau zu halten**" |
| **Grundreinigung** | „eine **intensive** Reinigungsmethode … tiefgreifende und umfangreiche Reinigung, die **in bestimmten Zeitintervallen** durchgeführt wird" | against „der regelmäßigen Unterhaltsreinigung, die eine **kontinuierliche Pflege** darstellt"; Grundreinigung also covers **Wände und Decken** |
| **Sichtreinigung** | „die oberflächliche Sichtreinigung" | — (https://pland.app/blog/wie-software-ihre-gebaeudereinigung-auf-das-naechste-level-hebt) |

**Fakt (pland.app, product mechanics).** A recurring Einsatz is a *series*, and editing it asks a
two-axis question: **this occurrence vs this and all following**, and (for a Teameinsatz)
**this member vs all team members**. Rules stated verbatim: changes to recurring Einsätze
„**nur … die Zukunft**"; occurrences already split out as singles are **not** affected by later
series changes. Intervals named: „jede Woche, alle zwei Wochen am Dienstag, monatlich".
Source: https://pland.app/onboardings/auftrage-und-einsatzplanung-in-pland

**Fakt (this repo).** The two regimes live in two apps and never touch:

| | Recurring (`apps/planning`) | Spot (`apps/marketplace`) |
|---|---|---|
| Recurrence | `Zone.visits_per_week` + `allowed_weekdays`, materialised **one week at a time** by `_visit_days` inside `generate_week_plan` | `Frequency` enum: `ONE_TIME`, `WEEKLY`, `BIWEEKLY`, `MONTHLY` (`apps/marketplace/models.py:25-29`) with `VISITS_PER_MONTH = {ONE_TIME: 1, WEEKLY: 4.33, BIWEEKLY: 2.17, MONTHLY: 1}` (`:32-37`) used only for pricing (`Offer.monthly_price`, `:157-159`) |
| Series object | **none** — every week is an independent `ShiftPlan` row, no RRULE, no `dateutil`, no roll-forward, no cron/Celery/management command. A human must POST to `/dashboard/planificare/?week=…` for each week. | `ServiceRequest` is the series; no Einsätze are generated from it at all |
| Preferred days | `Zone.allowed_weekdays` (CSV, ISO) | `ServiceRequest.preferred_weekdays` (`CharField(max_length=13, blank=True, default="")`, `models.py:66`) — **same CSV encoding, never read by any code** |

**Vorschlag.** If you implement the Sonderauftrag path inside planning rather than the
marketplace, do **not** add a nullable `Zone` — a one-off has no standing interval. Add a
sibling demand row (e.g. `AdHocVisit(site, category, date, minutes, description)`) and teach
`generate_week_plan` to iterate `chain(zone_visits, adhoc_visits)` through the same `_fits`
gate, so a Sonderauftrag competes for the same contracted-hours budget as everything else.
Anything that bypasses `_fits` bypasses P1 and §3 ArbZG.

---

## 6. Fields the Einsatzplan must carry — sources vs repo

**Fakt.** The pland.app page that promises a Vorlage does **not** print a field list (the file
is behind an e-mail gate). The table below assembles every element the pages *do* name.

| Element | German wording used | Source | In `Shift` today |
|---|---|---|---|
| Assigned employee | „**Mitarbeiter zuweisen**" per drag-and-drop | https://pland.app/blog/gebaudereinigung-wie-erstelle-ich-den-perfekten-einsatzplan-vorlage | `Shift.worker` (nullable, `SET_NULL`) |
| Place of work | „**Einsatzort**" | ibid. | `Shift.zone.site` (+ `site.locality`) |
| Time window | „**Zeitfenster** definieren" | ibid. | ✗ — only `start_time` + `duration_minutes`; no window, no latest-start |
| Special cleaning wishes | „**besondere Reinigungswünsche**" hinterlegen | ibid. | partially — `Zone.description`, standing not per-visit |
| Task detail / instructions | „detaillierte **Anweisungen und Anforderungen** zu jedem Auftrag" | https://pland.app/blog/welche-funktionen-sollten-alles-in-einer-gebaudereiniger-software-enthalten-sein | partially — `Zone.description` |
| Priority / urgency | „Aufträge nach **Dringlichkeit, Größe oder spezifischen Anforderungen** organisieren" | ibid. | ✗ |
| Progress / status | „Mitarbeiter können den **Fortschritt** ihrer Aufträge in Echtzeit aktualisieren" | ibid. | `Shift.status` (6 values, `models.py:131-137`) |
| Name / Adresse / Uhrzeit on the mobile plan | „Name, Adresse, Uhrzeit? Im mobilen Dienstplan sind alle einsatzrelevanten Informationen hinterlegt" | https://pland.app/funktionen/einsatzplanung-gebaeudereinigung | site name + locality + start time are rendered in `templates/dashboard/my_shifts.html:9-11`; **street is not** |
| Materials & equipment | „alle notwendigen **Arbeitsmaterialien und Geräte** vorhanden sind" | https://pland.app/blog/was-sind-eigentlich-die-aufgaben-eines-objeltleiters-in-der-gebaudereinigung | ✗ in planning; `apps/devices` tracks equipment against `Site`, not against a Shift |
| Access code / object notes | „Fotos, Dokumente und Bemerkungen wie **Zugangscodes** oder **Sonderaufträge** … für Servicekräfte **freischalten**" (digitale Objektmappe) | https://pland.app/blog/wie-software-ihre-gebaeudereinigung-auf-das-naechste-level-hebt | ✗ |
| Absences shown alongside | „Überblick über alle **Einsätze und Abwesenheiten**" | https://pland.app/funktionen/einsatzplanung-gebaeudereinigung | ✗ — no absence model |
| Travel time / routes | „Automatisierung von **Routen** und Schichtplänen"; avoid „lange Fahrwege" | https://pland.app/blog/gebaudereinigung-wie-erstelle-ich-den-perfekten-einsatzplan-vorlage | ✗ — back-to-back shifts get zero travel buffer (`services.py:143-151`) |
| Pausen & Fahrzeiten stored per Einsatz *and* per Dauerauftrag | „**Pausen- & Fahrzeiten** … Stored per Einsatz und per Dauerauftrag, auto-applied" | https://pland.app/funktionen/uebersicht | ✗ |

**Fakt (`Shift`, `apps/planning/models.py:140-185`).** What the row actually carries:
`plan`, `zone`, `worker`, `date`, `start_time`, `duration_minutes`, `status`, `checked_in_at`,
`checked_out_at`, `actual_minutes`, `worker_note`. Properties: `hours` (`:171-173`, unreferenced
anywhere), `billable_minutes` (`:175-178`), `variance_minutes` (`:180-185`).

**Fakt.** There is **no `clean()` on `Shift`** and **no DB constraint** binding `date` into
`plan.week_start … +6`. `tests/test_calibration.py:53-66` deliberately creates shifts outside
their plan's week.

---

## 7. Plan-level object: `ShiftPlan`

**Fakt.** `apps/planning/models.py:96-128`, table `planning_shiftplan`.

| Field | Definition |
|---|---|
| `account` | `ForeignKey("accounts.Account", CASCADE, related_name="shift_plans")` |
| `week_start` | `DateField(help_text="Luni")` |
| `status` | `CharField(max_length=12, choices=PlanStatus.choices, default=PlanStatus.DRAFT)` — **no `db_index`** |
| `unmet_demand` | `JSONField(default=list, blank=True)` — comment `# Ce nu a încăput: motivul, nu doar faptul.` |
| `published_at` | `DateTimeField(null=True, blank=True)` |
| `created_at` | `DateTimeField(auto_now_add=True)` |

`Meta`: `ordering = ("-week_start",)`, unique constraint `uniq_plan_per_week` on
`("account", "week_start")`, `verbose_name = "Plan săptămânal"`.
`week_end` = `week_start + timedelta(days=6)` (`:118-120`);
`planned_minutes` is a **Python-side sum** over `self.shifts.all()` (`:122-124`), not an
aggregate. `clean()` (`:126-128`) rejects a non-Monday `week_start`.

`PlanStatus` (`models.py:90-93`): `DRAFT` „Ciornă" · `PUBLISHED` „Publicat" · `ARCHIVED`
„Arhivat". **`ARCHIVED` is never assigned anywhere** — there is no archival flow.

`unmet_demand` element shape, produced at `services.py:134-140`:

```python
{"zone": <zone.name>, "site": <zone.site.name>, "date": <ISO date str>,
 "minutes": <zone.minutes_per_visit>, "reasons": {<worker display_name>: <reason str>, ...}}
```

When there are no capacities at all, `reasons` becomes
`{"—": "niciun lucrător cu contract semnat"}` — the key is an EM DASH U+2014
(`services.py:139`).

---

## 8. Objektleiter — the role the plan is written for

**Fakt.** https://pland.app/blog/was-sind-eigentlich-die-aufgaben-eines-objeltleiters-in-der-gebaudereinigung
defines the role verbatim: *„Der Objektleiter ist … die Führungskraft, die für die operative
Leitung eines oder mehrerer Reinigungsobjekte zuständig ist. Er ist das **Bindeglied zwischen
Reinigungspersonal und Auftraggebern**…"*. The page's own six-item checklist:

1. Erstellung und Überwachung der **Dienstpläne**
2. **Personalführung und Schulung**
3. Durchführung von **Qualitätskontrollen**
4. Direkter **Ansprechpartner für Kundenanfragen**
5. **Dokumentation und Verwaltung**
6. Sicherstellung von **Arbeitssicherheit und Hygienevorschriften**

Duties the same page assigns to planning specifically: erstellt Dienstpläne · teilt
Reinigungskräfte den Aufgaben zu · achtet darauf, dass **genügend Personal** zur Verfügung steht
· behält die **Anforderungen der Kunden** im Blick · stellt sicher, dass alle Bereiche
**gründlich und termingerecht** gereinigt werden · sorgt dafür, dass **Arbeitsmaterialien und
Geräte** vorhanden sind.

**Fakt (repo).** There is no Objektleiter role. Authorisation is capability-based
(`apps/accounts/enums.py:11-21`: `WORKER`, `PROVIDER`, `SUPPLIER`, `CLIENT`, `EMPLOYER`) and the
planning pages gate on `{EMPLOYER, PROVIDER}`. pland.app's own access-right enum is different
and worth knowing when comparing: **Servicekraft · Objektleiter · Innendienst · Administrator**
— exactly four values (https://pland.app/onboardings/mitarbeiter-in-pland-erstellen), with
Geschäftsführung and Lohnbuchhaltung being *training audiences*, not access rights.

**Ungeprüft.** Mapping an Objektleiter onto this repo would most naturally be a new
`Capability.SITE_MANAGER` plus a `Site.manager` FK — not a `role` column. The codebase rule is
explicit: never add a `role` column or a per-model Django permission
(`apps/accounts/permissions.py:1-7`).

---

## 9. Unterhaltsreinigung lifecycle (the five steps the plan sits inside)

**Fakt.** https://pland.app/arbeitslexikon/unterhaltsreinigung, verbatim order:

1. **Objektbesichtigung** — at the start of every new maintenance contract the Objektleiter
   inspects: size of rooms, **number of toilets**, and agrees with the customer what is cleaned
   and how. All information must be collected so step 2 has complete input.
2. **Reinigungsplan** — records on which days and how regularly cleaning happens, which services
   are needed in which rooms, and that services are documented after each clean.
3. **Reinigung** — execution; interval decided by size and type of premises.
4. **Qualitätskontrolle** — the Objektleiter checks against the agreed standard; cleaners attach
   photos and comments via app; the Objektleiter can raise **Tickets** for defects.
5. **Leistungsnachweis** — services recorded and sent to the customer.

**Fakt (repo).** Only step 2 (as `Zone` rows + the XLSX export) and step 3 (as `Shift` +
attendance) exist. Steps 1, 4 and 5 have **no model at all** — no Besichtigung record, no
Qualitätscheck, no Leistungsnachweis, no Ticket/Reklamation.

---

## Quellen

Repository (read 2026-08-29, all paths relative to `/Users/Geronimo/Projects/Cleaning_SaaS`):

* `apps/planning/models.py` — `Site` 21-39, `Zone` 42-87, `PlanStatus` 90-93,
  `ShiftPlan` 96-128, `ShiftStatus` 131-137, `Shift` 140-185
* `apps/planning/services.py` — constants 27-31, `_visit_days` 159-169,
  `capacity_report` 172-188, `generate_week_plan` 98-156
* `apps/planning/forms.py` — `SiteForm` 8-15, `WEEKDAYS` 18, `ZoneForm` 21-44
* `apps/planning/reinigungsplan.py` — whole file (102 lines)
* `apps/planning/views.py` — `reinigungsplan_view` 296-310
* `apps/planning/migrations/0004_zone_description.py`
* `apps/marketplace/models.py` — `Frequency` 25-29, `VISITS_PER_MONTH` 32-37,
  `ServiceRequest` 48-112, `Offer` 122-174, `Invitation` 177-200
* `apps/marketplace/services.py` — `award_offer` 100-119
* `apps/contracts/models.py` — `MinijobThreshold` 92-113, `ContractDraft` 151-254
* `apps/accounts/enums.py` 11-21; `apps/accounts/permissions.py` 1-7
* `apps/dashboard/urls.py` 32-42
* `apps/devices/models.py` 49, 115
* `templates/dashboard/sites.html`, `templates/dashboard/my_shifts.html`
* `tests/test_reinigungsplan.py`, `tests/test_planning.py`

pland.app (crawled 2026-08-29):

* https://pland.app/arbeitslexikon/reinigungsplan
* https://pland.app/arbeitslexikon/reinigungsintervall
* https://pland.app/arbeitslexikon/dienstplan
* https://pland.app/arbeitslexikon/unterhaltsreinigung
* https://pland.app/arbeitslexikon/grundreinigung
* https://pland.app/funktionen/einsatzplanung-gebaeudereinigung
* https://pland.app/funktionen/uebersicht
* https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung
* https://pland.app/onboardings/auftrage-und-einsatzplanung-in-pland
* https://pland.app/onboardings/kunden-objekte-in-pland
* https://pland.app/onboardings/mitarbeiter-in-pland-erstellen
* https://pland.app/blog/gebaudereinigung-reinigungsplan-hier-kostenlose-vorlage-herunterladen
* https://pland.app/blog/gebaudereinigung-wie-erstelle-ich-den-perfekten-einsatzplan-vorlage
* https://pland.app/blog/was-sind-eigentlich-die-aufgaben-eines-objeltleiters-in-der-gebaudereinigung
* https://pland.app/blog/welche-funktionen-sollten-alles-in-einer-gebaudereiniger-software-enthalten-sein
* https://pland.app/blog/wie-software-ihre-gebaeudereinigung-auf-das-naechste-level-hebt
