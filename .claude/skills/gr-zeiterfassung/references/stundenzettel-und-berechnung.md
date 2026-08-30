# Stundenzettel und Arbeitszeitberechnung

Covers: the columns a Stundenzettel must carry, Sollarbeitszeit vs. Ist-Zeit, the
computation rules (break exclusion, Wegezeit per RTV § 3 Nr. 3 with the three-hour
Zwischenzeit test and the started-half-hour rounding, Mehrarbeit), and the Freigabe
workflow with the reason an approved record must become immutable.

**Stand:** 2026-08-29. Material from the pland.app crawl of 2026-08-29 (Arbeitslexikon
`stundenzettel`, `stempeluhr`, `sollarbeitszeit`, `fahrzeiten`,
`rahmentarifvertrag-gebaeudereinigung-2023`; the Zeiterfassung blog cluster; the
onboarding lessons) plus the repository code. The RTV wording quoted here is the RTV
text as reproduced on the competitor's Arbeitslexikon page — **verify against the
current Rahmentarifvertrag before it drives payroll.** Reference material, not legal
advice.

Labels: **Fakt** · **Vorschlag** · **Ungeprüft**.

---

## 1. The seven mandatory Stundenzettel fields

**Fakt.** "Ein Stundenzettel ist nur als rechtlich bindendes Dokument gültig, wenn
folgende Informationen darauf vorhanden sind:"
(https://pland.app/arbeitslexikon/stundenzettel)

| # | German field | Present in this repo? | Where |
|---|---|---|---|
| 1 | **Name des Mitarbeiters** | yes | `Shift.worker` → `Account.display_name`; rendered as `row["worker"]` (`apps/planning/attendance.py:194`) |
| 2 | **Datum des Arbeitstages** | yes | `Shift.date` (`apps/planning/models.py:147`) |
| 3 | **Ort der Arbeit** | yes | `Shift.zone.site.name` + `zone.name` (`attendance.py:196-197`) |
| 4 | **Arbeitsbeginn** | yes | `Shift.checked_in_at` (`models.py:157`) — **note:** `time_records()` does not output it |
| 5 | **Arbeitsende** | yes | `Shift.checked_out_at` (`models.py:158`) — likewise not output |
| 6 | **Gesamtarbeitszeit** | yes, per shift | `Shift.actual_minutes` (`models.py:159`) |
| 7 | **Pausenzeiten** | **NO — nothing in the repo records breaks** | — |

Same page, two further requirements (**Fakt**):
- "sollte der Stundenzettel vom **Arbeitnehmer unterschrieben** werden" — no signature
  or worker confirmation step exists in the repo.
- kept "zur Überprüfung der Einhaltung des **Arbeitszeitgesetzes** sowie zu
  **Beweiszwecken**".

**Consequence:** `time_records()` (`attendance.py:178-205`) currently emits
worker/date/site/zone/planned/actual/variance/status — i.e. it satisfies fields 1, 2, 3
and 6 but **drops the timestamps it already has** and has no field 7. Before calling the
export "Stundenzettel", add `checked_in_at`, `checked_out_at` and a break column.

**Ungeprüft** — a realistic full column set for this trade (the sources never print one):
Mitarbeitername + Personalnummer; Monat/Jahr; per row → Datum, Wochentag,
Objekt/Kostenstelle, Tätigkeit/Leistungsart, Beginn hh:mm, Ende hh:mm, Pause (min),
Arbeitszeit netto (h), Wegezeit (h), Zuschlagskennzeichen (Nacht/So/Feiertag),
Bemerkung; footer → Summe Stunden, Summe Wegezeit, Soll-Stunden, Saldo, Unterschrift
Mitarbeiter, Unterschrift Objektleiter/Freigabe, Datum der Freigabe.

---

## 2. Stempeluhr — how the timestamps are meant to be produced

**Fakt** (https://pland.app/arbeitslexikon/stempeluhr):
- Workers "**ein- und ausstempeln**" at start and end of work via **mobile Geräte oder
  Terminals**; specifically "über **mobile Apps oder QR-Codes** beim **Betreten und
  Verlassen eines Objekts**".
- The central software consolidates not only Arbeitszeit but **Pausen, Schichtpläne und
  Anwesenheiten**, used for **Abrechnung, Anwesenheitskontrolle und Personalplanung**.
- Claimed properties, usable as requirements: **Echtzeit-Erfassung**,
  **Automatisierte Auswertung**, **Revisionssicherheit** ("Die Daten werden sicher
  gespeichert und **können nicht nachträglich manipuliert werden**"),
  **Ortsbasierte Erfassung** via GPS.

**Fakt** (https://pland.app/blog/zeiterfassung-in-gebaeudereinigung-einfuehren) — why
fixed terminals fail in this trade: not practical for "weitläufige Standorte und
unterschiedliche Arbeitszeiten"; failure modes named are **Internetunterbrechung** and
"die Reinigungskraft versehentlich das **Terminal ausschaltete, um den Staubsauger
einzuschalten**". Economics: "Für **kleinere Objekte, in denen nur 1-2 Mal pro Woche
gereinigt wird**, ist die Anschaffung eines Terminals **nicht sinnvoll**."

**Fakt (code):** this repo has no app, no QR code and no terminal. Clocking happens by
POSTing `action=check_in` / `action=check_out` to `/dashboard/turele-mele/`
(`apps/planning/views.py:153-171`, `templates/dashboard/my_shifts.html:16-33`).

---

## 3. Sollarbeitszeit vs. Ist-Zeit

### 3a. Definitions (Fakt)

| Term | Verbatim | Source |
|---|---|---|
| **Sollarbeitszeit** | "die **vertraglich vereinbarte Arbeitszeit**, die ein Mitarbeiter in der Gebäudereinigung zu leisten hat. Sie bildet die Grundlage für die Berechnung des **Gehalts** und die **Planung der Arbeitsabläufe**." | https://pland.app/arbeitslexikon/sollarbeitszeit |
| **Sollstunden** | "die **vertraglich vereinbarten Arbeitsstunden**, die ein Mitarbeiter in einem bestimmten Zeitraum, in der Regel **pro Monat oder pro Woche**, leisten muss." | https://pland.app/blog/gebaudereinigung-sollstunden-richtig-berechnen |
| **Soll-Zeit** (per Objekt) | the target time booked for a site; the app books it in full even when the cleaner finishes early ("automatische **Aufrundungsfunktion**") | https://pland.app/blog/zeiterfassung-in-gebaeudereinigung-einfuehren |

### 3b. Statutory limits as listed on the Sollarbeitszeit page (Fakt; the page names no statute sections)

| Limit | Value | Enforced in this repo? |
|---|---|---|
| Maximale tägliche Arbeitszeit | **8 Stunden** (kann auf **bis zu 10 Stunden** verlängert werden) | at **planning** time only: `MAX_DAILY_MINUTES = 480` (`apps/planning/services.py:27`, comment cites §3 ArbZG). **Not** checked at check-out. |
| Wöchentliche Höchstarbeitszeit | **48 Stunden** | no |
| Ruhezeit zwischen zwei Arbeitstagen | **mindestens 11 Stunden** | at planning time: `MIN_REST_MINUTES = 11 * 60` (`services.py:28`, §5 ArbZG) |
| Pausenzeiten | **30 Minuten bei mehr als 6 Stunden** Arbeitszeit | **no** |
| (§9 ArbZG, not on this page) Sonn- und Feiertagsruhe | — | at planning time: `SUNDAY = 7` excluded (`services.py:29`, whose comment cites §9 ArbZG, and `:161`) |

**The Sunday exclusion is statutory, not tariff.** The RTV does **not** forbid Sunday
work — Nr. 4.3 defines Sonn- und Feiertagsarbeit ("Die an Sonn- und Feiertagen in der
Zeit von 0.00 Uhr bis 24.00 Uhr geleistete Arbeit gilt als Sonn- und Feiertagsarbeit")
and Nr. 4.7 b) surcharges it at **80 v.H.** (see §5 below). The planner's blanket
Sunday skip implements §9 ArbZG, and it is stricter than the tariff.

### 3c. RTV § 3 Nr. 1 and Nr. 4 — the tariff working-time frame (Fakt)

Source: https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023

**RTV § 3 Nr. 1 (Allgemeine Regelungen / Arbeitszeit):**

| RTV ref | Rule |
|---|---|
| 1.1 | regelmäßige **wöchentliche** Arbeitszeit **39 Stunden** |
| 1.1 | regelmäßige **werktägliche** Arbeitszeit **8 Stunden**, **ausschließlich der Ruhepausen** |
| 1.2 | deviation by the employer **im Einvernehmen mit dem Betriebsrat**, for operational reasons |
| 1.3 | Ausgleich von Mehrarbeit / ausfallender Arbeitszeit by shortening or lengthening weekly hours on other working days **innerhalb von einem Monat** |
| 1.4 | Beginn/Ende der täglichen Arbeitszeit **und Ruhepausen** are fixed by the employer with the Betriebsrat and **durch Aushang bekannt gegeben** |

**RTV § 3 Nr. 4 (Nacht-, Sonn- und Feiertagsarbeit)** — these rows sit under Nr. 4 on the
source page, **not** under Nr. 1; cite them as Nr. 4.x:

| RTV ref | Rule |
|---|---|
| 4.1 | **Mehrarbeit (Überstunden)** = working time beyond the regular **weekly or daily** working time per Nr. 1 |
| 4.5 | further extension of working time only under the **Arbeitszeitgesetz** |
| 4.6 | 4.1–4.5 **gelten nicht für Jugendliche** |

**"Ausschließlich der Ruhepausen" is the load-bearing phrase**: the 8-hour day is net of
breaks, therefore **breaks must be excluded from Arbeitszeit**, therefore they must be
recorded. The current `actual_minutes` (`apps/planning/attendance.py:133`) is gross
elapsed time from check-in to check-out and includes any break the worker took. The only
way a break currently reaches the record is an employer correction — which is exactly
what the existing test does: `correct_minutes(shift, employer, 120, "Pauză
neînregistrată")` (`tests/test_attendance.py:141`).

### 3d. Sollstunden formulas (Fakt, with their contradictions)

All from https://pland.app/blog/gebaudereinigung-sollstunden-richtig-berechnen

```
Monatliche Sollstunden = Wöchentliche Arbeitszeit × 4,33
  39 × 4,33 = 168,87  →  "Aufgerundet ergibt das etwa 169 Sollstunden pro Monat"

Jahres-Sollstunden     = Wöchentliche Arbeitszeit × 52
  39 × 52 = 2.028
```

Rationale printed for 4,33: the number of working days varies month to month, so "zur
Vereinfachung oft ein **Durchschnittswert von 4,33 Wochen pro Monat**".

Also on the page (Fakt): a **Feiertag falling on a regular working day reduces the
Sollstundenanzahl**; **Jahresarbeitszeitkonten** fix the annual Sollstunden and settle
**Über- und Unterstunden** in a **Zeitkonto**; everything can be overridden by
"besondere Regelungen im Betrieb oder im Tarifvertrag".

Contradictions to preserve, not resolve:
- **4,33 × 12 = 51,96 ≠ 52.** The two worked examples on the same page therefore give
  different annual totals (2.026,44 vs. 2.028).
- **168,87 → "etwa 169"** is ordinary rounding described as "aufgerundet"; whether
  payroll uses 168,87 or 169 is not stated.
- The Arbeitslexikon `sollarbeitszeit` page gives **no formula at all** — only four
  input factors: Vereinbarte Wochenstunden, Arbeitstage pro Woche, Berücksichtigung von
  Feiertagen und Urlaubstagen, Ausgleich von Mehrarbeit oder Minderarbeit.

**Fakt (code):** this repo derives weekly capacity from the signed contract, not from a
tariff week: `weekly = int(Decimal(contract.hours_per_month) * 60 / WEEKS_PER_MONTH)`
with `WEEKS_PER_MONTH = Decimal("52") / Decimal("12")` = 4,3333…
(`apps/planning/services.py:67`, `:31`). That is the 52-week convention, **not** the
4,33 convention — a deliberate-looking choice that is nowhere documented. If you ever
surface "Sollstunden" in the UI, say which factor produced it.

**Vorschlag** — if a `SollstundenPeriod` / Zeitkonto is added: fields
`account`, `worker`, `period_type` (`MONAT` | `JAHR`), `period_start`, `period_end`,
`soll_minutes`, `ist_minutes`, `saldo_minutes`, `holiday_adjustment_minutes`,
`week_factor` (stored per row, never a module constant), `model`
(`STANDARD` | `JAHRESARBEITSZEITKONTO`). Store the factor **with the row** so a past
period stays reproducible after the tenant changes it.

---

## 4. Wegezeit / Fahrzeit — RTV § 3 Nr. 3

### 4a. The tariff text (Fakt, verbatim from the source page)

Source: https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023
(the raw crawl renders the "3.2" marker as "32" — an extraction artefact, not a
different clause number).

| RTV ref | Rule |
|---|---|
| **3.1** | "Die Arbeitszeit **beginnt und endet an der Arbeitsstelle**. Haben Beschäftigte vor oder nach Aufsuchen der Arbeitsstelle eine **betriebliche Sammelstelle (Aufenthalts-, Umkleide- oder Putzraum)** aufzusuchen, **beginnt oder endet die Arbeitszeit dort**." |
| **3.2** | "Die **direkte Wegezeit zwischen mehreren aufzusuchenden Arbeitsstellen** ist **wie Arbeitszeit zu vergüten**, wenn die Zeit zwischen dem Ende der ersten und dem Beginn der nächsten Arbeitsstelle (**Zwischenzeit**) **bis zu drei Stunden** beträgt." |
| **3.2** | "Wird für die direkte Wegezeit **mehr als die Hälfte dieser Zwischenzeit** benötigt, so ist die **gesamte Zwischenzeit** wie Arbeitszeit zu vergüten." |
| **3.2** | "Wird die Zwischenzeit **ausschließlich** zur Bewältigung des Weges zwischen den Arbeitsstellen benötigt, so ist diese Wegezeit **auch über drei Stunden hinaus** wie Arbeitszeit zu vergüten." |
| **3.3** | "Übersteigt der Zeitaufwand für den Weg **vom Wohnsitz zur nichtregelmäßigen Arbeitsstelle** den üblichen Zeitaufwand für den Weg zum **Betriebssitz**, so gilt diese Zeit als Arbeitszeit." |
| **3.3** | "**Jede angefangene halbe Stunde wird als halbe Stunde berechnet.**" |

Corroborating (Fakt): "**Jede angebrochene halbe Stunde Wegezeit wird dabei auch als
halbe Stunde berechnet.**" (https://pland.app/arbeitslexikon/fahrzeiten)

### 4b. Travel time outside the RTV clauses (Fakt)

Source: https://pland.app/arbeitslexikon/fahrzeiten and
https://pland.app/blog/gebaeudereinigung-arbeitszeiten-korrekt-berechnen

| Situation | Treatment |
|---|---|
| Fixed workplace, home → work | "gilt die Fahrt dorthin **nicht als Arbeitszeit** und wird auch **nicht vergütet**" — regardless of distance |
| **No fixed workplace**, Einsatzort → Einsatzort | "zählt die Fahrzeit **laut einem Urteil des EuGH** als **zu vergütende Arbeitszeit**" |
| First trip of the day home → first Einsatz, and last Einsatz → home | "gelten als **zu vergütende Arbeitswege**"; the blog page adds "von der ersten bis zur letzten Fahrt" |
| Occupations named | **Außendienst, Reinigungskräfte, Handwerker, Bauarbeiter** (Fahrzeiten page); Gebäudereinigungen, Baumontagen, Handwerker (blog page) |
| Pay rate | employers may pay travel time "**geringer … als die normale Arbeitszeit**"; "allerdings gilt auch bei der Fahrzeit der **Mindestlohn als erlaubte Untergrenze**" |
| Counts toward the 8-hour day | "da die Wegezeiten zur normalen 8-stündigen Arbeitszeit gezählt wird" |
| ArbZG constraint flagged | "Der **tägliche Durchschnitt von 8 Arbeitsstunden** darf im Zeitraum von **24 Wochen** nicht überschritten werden." |
| EuGH case number | **not given on any page** |

**Ungeprüft:** the travel-time ruling for workers without a fixed workplace is Tyco,
**EuGH C-266/14, 10 September 2015**. Confirm before citing.

### 4c. What the competitor's product actually implements (Fakt)

Source: https://pland.app/onboardings/fahrzeiterfassung-mit-pland

1. Global toggle: Einstellungen → … → **Fahrzeit**, activate **Fahrzeiterfassung**.
2. Travel counts as such only if "zwischen dem Ende eines Einsatzes und dem Beginn eines
   neuen Einsatzes eine **maximale Zeit von 3 Stunden** verstrichen ist"; the
   **maximale Zwischenzeit** is adjustable.
3. Must also be permitted **per employee**: Mitarbeiter → tab **Vertrag** →
   Fahrzeiterfassung erlauben.
4. In the app the worker finishes one Einsatz, starts a new Zeiterfassung and enters the
   Fahrzeit; "Die angegebene Fahrzeit **darf die maximale Zwischenzeit nicht
   überschreiten**".
5. It appears in Mitarbeiter → **Lohnzeit** and "auch beim **Export der Arbeitszeiten**".

Note the competitor implements only the **first** limb of RTV 3.2 (the ≤ 3 h gate) and
appears to implement it as a *cap on the entered travel time* rather than the tariff's
"more than half the Zwischenzeit ⇒ the whole Zwischenzeit is paid" and "exclusive use ⇒
paid even beyond three hours" limbs. Do not copy the competitor's simplification and
call it RTV-compliant.

### 4d. Reference algorithm (Vorschlag)

Not implemented anywhere in this repo. If you build it, implement all three limbs:

```python
# Vorschlag — not present in the codebase.
CEIL_UNIT_MIN = 30          # RTV 3.3: jede angefangene halbe Stunde
MAX_ZWISCHENZEIT_MIN = 180  # RTV 3.2: "bis zu drei Stunden"; tenant-configurable

def wegezeit_als_arbeitszeit(zwischenzeit_min: int,
                             direkte_wegezeit_min: int,
                             exklusiv_fuer_den_weg: bool) -> int:
    """RTV § 3 Nr. 3.2. Returns the minutes to be paid as Arbeitszeit (unrounded)."""
    if exklusiv_fuer_den_weg:
        return direkte_wegezeit_min          # paid auch über drei Stunden hinaus
    if zwischenzeit_min > MAX_ZWISCHENZEIT_MIN:
        return 0
    if direkte_wegezeit_min > zwischenzeit_min / 2:
        return zwischenzeit_min              # die GESAMTE Zwischenzeit
    return direkte_wegezeit_min

def abgerechnete_minuten(minuten: int) -> int:
    """RTV § 3 Nr. 3.3: every started half-hour counts as a half-hour."""
    return -(-minuten // CEIL_UNIT_MIN) * CEIL_UNIT_MIN
```

Store **both** `raw_minutes` and `billed_minutes`; the rounding is a pay rule, not a
measurement, and the recording duty is about the measurement.

**Vorschlag — `Wegezeit` model:** `worker`, `date`, `from_site` (nullable),
`to_site` (nullable), `leg_type` ∈ {`WOHNORT_ZU_ERSTEM_EINSATZ`,
`ZWISCHEN_EINSATZORTEN`, `LETZTER_EINSATZ_ZU_WOHNORT`,
`WOHNORT_ZU_NICHTREGELMAESSIGER_STELLE`, `SAMMELSTELLE`,
`NICHT_VERGUETET_FESTER_ARBEITSORT`}, `zwischenzeit_minutes`, `raw_minutes`,
`billed_minutes`, `exclusive_use` (bool), `pay_rate` (validated ≥ the applicable
Mindestlohn — the repo already has a date-effective wage floor check pattern in the
`WAGE_FLOOR` branch of `ContractDraft.compliance_report()`,
`apps/contracts/models.py:207-222`: the lookup is
`WageFloor.current(kind, self.start_date)` at `:207-209`, the comparison
`if floor and self.hourly_wage < floor:` at `:213`). Wegezeit **must** be included in the daily 8-hour
and averaging-window computations.

---

## 5. Mehrarbeit and the surcharge interaction

**Fakt (RTV, via https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023):**
- 4.1 **Mehrarbeit (Überstunden)** = time beyond the regular weekly *or* daily working
  time per Nr. 1 — i.e. beyond 39 h/week **or** beyond 8 h/day.
- 1.3 it can be balanced by shortening/lengthening weekly hours on other working days
  **within one month**; the blog page adds this happens "**ohne Mehrarbeitszuschlag**"
  (https://pland.app/blog/gebaeudereinigung-arbeitszeiten-korrekt-berechnen).
- 4.7/4.8 surcharge rates and the combination rule live in the tariff, **not here** —
  see the `gr-tarif-und-lohn` skill. Two facts matter for time computation:
  the surcharges are computed "**aus dem Stundenlohn**" (RTV 4.8), and
  "**Treffen mehrere der vorgenannten Zuschläge zusammen, ist nur der jeweils höchste zu
  zahlen**" (RTV 4.8) — **highest-only, never cumulative**. The competitor's product
  confirms it implements exactly that: "Sollten Nacht, Feiertag und Sonntagszuschlag
  gleichzeitig anfallen, nimmt PlanD automatisch immer nur den höchsten Zuschlag (siehe
  Lohntarifvertrag)."
  (https://pland.app/onboardings/lohnarten-und-zuschlage-in-pland).

**Note the source conflict on rates.** The Arbeitslexikon RTV page prints night 30 %,
Sunday/holiday 80 %, big holidays 200 %; the blog page
`gebaeudereinigung-arbeitszeiten-korrekt-berechnen` prints night 25 v.H., Sunday 100
v.H., other holidays 150 v.H., big holidays 200 %, plus a 25 % Belastungszuschlag beyond
the 8th daily hour and a 75 v.H. rate for recurring contractual Sunday/holiday work at
the same site. **These two sets are incompatible.** Do not hard-code either; rates are
data with a `valid_from` and a Tarifvertrag FK. Resolve against the current RTV.

**Fakt (code):** no surcharge logic exists in this repo. `Shift` has no night/Sunday/
holiday classification and `time_records()` returns plain minutes.

---

## 6. Freigabe — the approval workflow

### 6a. What the competitor does (Fakt)

Source: https://pland.app/onboardings/freigabe-von-zeiterfassungen (lesson
"Freigabe von Zeiterfassungen", 6 Minuten; audience Innendienst, Lohnbuchhaltung,
Objektleiter).

**Fehlerarten** — configurable triggers that force a record into manual approval:

| Fehlerart | Trigger as stated |
|---|---|
| **Standortfehler** | "jedes Mal, wenn eine Reinigungskraft sich **über 800 Meter** vom Objekt entfernt ein- oder ausstempelt" |
| **deaktivierte Standortfreigabe** | "alle Zeiten …, bei denen Mitarbeiter die **GPS-Ortung deaktiviert** haben" |
| **Einfache Zeiterfassung** | "Einsätze, die **nicht geplant** wurden und bei denen sich der Mitarbeiter z.B. mittels **QR-Code** einstempelt" |
| **nachgetragene Zeiten** | "die mithilfe des **Stundenzettels** von der App **nachträglich** erfasst wurden" |

**Unter- und Überschreitungen** (tab): tolerated deviation set "**prozentual oder
minütig**"; anything inside it is auto-approved. Worked example verbatim: "bei zum
Beispiel einer Stunde Arbeit und einer erlaubten **10 prozentigen Unterschreitung**,
dass alle Zeiten **unter 54 Minuten** Ihnen noch einmal zur Kontrolle vorgelegt werden."

**Ist-/Soll-Regler:** "kann hier … bestimmt werden, ob die Mitarbeiter nach **Ist- oder
Soll-Zeit** abgerechnet werden sollen. Ist der Regler aktiviert, werden die Zeiten
**automatisch auf die Soll-Zeit aufgerundet**."

**GPS-Erfassung:** a single on/off switch.

**The queue:** each faulty record shows its **Fehlerart** and "die **zeitliche Abweichung
von der Soll-Zeit**". Green button approves Soll- or Ist-Zeit in one click; red button
rejects. Clicking the **Zeitstempel** opens the detail: **Vorgabe** vs. **Erfassung**,
plus the **Check-In** and **Check-Out Standort**; the **Freigabe** dropdown then offers
**Vorgabe / Erfassung / Custom**. **Quick Actions** bulk-select and bulk-approve.

**After approval:** "erscheint diese nun automatisch in der **Lohnliste** des jeweiligen
Mitarbeiters", showing **Plan-Zeit / erfasste Zeit / Lohn-Zeit**; unapproved times can
also be added retroactively there.

Corroborating on the blog side (Fakt,
https://pland.app/blog/zeiterfassung-in-gebaeudereinigung-einfuehren): hours are
"**automatisch durch Algorithmen auf Fehler überprüft**"; on a **falscher Zeitstempel**
the Objektleiter is alerted, consults the employee, then grants **Freigabe**; if the
worker forgot to clock in or out the hours are entered directly on the digital
Stundenzettel; and the **Aufrundungsfunktion** books the full Soll-Zeit when the cleaner
finished the Objekt early.

**The plausibility rules themselves are never specified** on any source page — what
exactly counts as a wrong Zeitstempel beyond the four Fehlerarten is unknown.

### 6b. The Aufrundung problem — read before implementing a Soll/Ist toggle

The same page that sells the Aufrundungsfunktion as a motivation feature also claims it
lets the employer see "der **tatsächliche Arbeitsaufwand** auf einem Objekt … kann
erstmals erfasst werden". Both can only be true if **raw and booked minutes are stored
separately**. If a Soll/Ist toggle overwrote the measured value, the record would no
longer be the *tatsächlich geleistete Arbeitszeit* the ArbSchG/EuGH system exists to
capture. The sources never address this tension.

**Rule for this codebase:** `Shift.actual_minutes` is the measurement. A Soll-Zeit or
rounding policy must land in a **separate** field (`Vorschlag`: `payroll_minutes` plus
`rounding_rule_applied`), never on top of it. `apps/planning/calibration.py:99-104`
reads `actual_minutes` to propose corrections to `Zone.minutes_per_visit`; feeding it
rounded-up Soll-Zeit would make the planner converge on its own estimate and destroy the
feedback loop.

### 6c. Why an approved record must become immutable

The reasoning chain, stated in the sources and already half-built in the repo:

1. The record is **evidence** — kept "zu **Beweiszwecken**" and for checking ArbZG
   compliance (https://pland.app/arbeitslexikon/stundenzettel), and producible at an
   unannounced Zoll inspection
   (https://pland.app/blog/zeiterfassung-in-gebaeudereinigung-einfuehren).
2. Evidence that can be edited after the fact is worth nothing — hence
   **Revisionssicherheit**: "Die Daten … **können nicht nachträglich manipuliert
   werden**" (https://pland.app/arbeitslexikon/stempeluhr), and the shelved draft law's
   "**manipulationssicher**" requirement.
3. Approval (**Freigabe**) is the gate at which the record stops being a draft and
   becomes the basis of pay. After that point a change is a **correction with a reason
   and an author**, not an edit.
4. Therefore: freeze the approved values, and record every subsequent change as a new,
   immutable event that carries `from`, `to`, `reason`, `actor`, `timestamp`.

**Fakt (code):** the repo already implements step 4 without having step 3.
`ShiftEvent.save()` raises `RuntimeError("Evenimentele de pontaj sunt imutabile.")` on
re-save (`apps/planning/models.py:217-220`, locked by
`tests/test_attendance.py:127-132`), and `correct_minutes` writes
`payload={"from": previous, "to": minutes, "reason": reason[:300]}`
(`apps/planning/attendance.py:161-164`, locked by `tests/test_attendance.py:137-146`).
What is missing is the Freigabe state itself: today `correct_minutes` can be called any
number of times, on any `DONE` shift, forever.

### 6d. Freigabe design for this repo (Vorschlag)

Not implemented. If added, keep it inside the existing shapes:

- extend `ShiftEvent.Kind` with `APPROVED` and `REJECTED` — the enum currently holds
  exactly `PUBLISHED, CONFIRMED, DECLINED, CHECK_IN, CHECK_OUT, CORRECTED, MISSED`
  (`apps/planning/models.py:195-202`);
- add `Shift.approval_status` ∈ {`OFFEN`, `ZUR_PRUEFUNG`, `FREIGEGEBEN`, `ABGELEHNT`}
  and `approved_at`, `approved_by`, `approval_basis` ∈ {`VORGABE`, `ERFASSUNG`,
  `CUSTOM`} — mirroring the competitor's Freigabe dropdown;
- add `Shift.flags` (JSON or M2M) for the Fehlerart set: `STANDORTFEHLER`,
  `GPS_DEAKTIVIERT`, `UNGEPLANT`, `NACHGETRAGEN`, `UNTERSCHREITUNG`, `UEBERSCHREITUNG`;
- gate corrections: once `approval_status == FREIGEGEBEN`, `correct_minutes` must refuse
  unless it also writes a `REOPENED` event; never mutate silently;
- tolerance settings (`percent` or `minutes`, under- and overrun separately) belong to a
  tenant settings row **with a `valid_from`**, so a past approval stays explainable.

---

## 7. Absence pay — three methods (Fakt, for completeness)

Source: https://pland.app/blog/gebaeudereinigung-arbeitszeiten-korrekt-berechnen. These
determine how many hours are paid for a day nobody worked, so they consume time data.

| # | German label | Rule | Page's recommendation |
|---|---|---|---|
| 1 | "Alle Stunden, die geplant wurden, werden auch bezahlt" | pay every hour originally **planned** | "die einfachste … gerade bei **kurzfristigen und nicht so langen Ausfällen**" |
| 2 | "Vertragsstunden auszahlen" | a fixed number of hours **per weekday** stored per employee | "bei Reinigungskräften, die **immer wiederkehrende Einsätze an festen Tagen** haben" |
| 3 | "Durchschnittliche Arbeitszeit berechnen" | average of the **last three months**; printed example: "im Durchschnitt **6 Stunden am Tag**" | "insbesondere bei **längeren Ausfällen oder Urlauben** … oder für Reinigungskräfte, die sehr **unregelmäßige Arbeitszeiten** haben oder nur **Teilzeit** arbeiten" |

No absence entity exists in this repo. Method 1 would be computable today
(`Shift.duration_minutes` over a range); methods 2 and 3 would need
`contract_hours_per_weekday` and a three-month history query respectively.

---

## 8. Computation summary — what to implement, in order

Ordered by how much of the legal requirement each step closes. All **Vorschlag**.

1. **Pausen.** Add `break_minutes` to `Shift` and a break entry path; make
   `net_minutes = actual_minutes - break_minutes` the value that flows to
   payroll and to the daily 8-hour check. Without it the record overstates Arbeitszeit
   and understates compliance risk (RTV 1.1 "ausschließlich der Ruhepausen").
2. **Daily totals.** Aggregate per `(worker, date)`, not per shift — ArbSchG data point
   3 is a **daily** duration and the 8-hour limit is a **daily** limit.
3. **Freigabe.** §6d above.
4. **Wegezeit.** §4d above.
5. **Recording deadline.** Flag a record whose `checked_out_at`/correction lands more
   than N days after `Shift.date` (default 7, configurable).
6. **Sollstunden / Zeitkonto.** §3d above.
7. **Zuschläge.** Rates as data; highest-only resolution; out of scope for this skill —
   see `gr-tarif-und-lohn`.

---

## Quellen

Source pages (pland.app, crawled 2026-08-29):
- https://pland.app/arbeitslexikon/stundenzettel
- https://pland.app/arbeitslexikon/stempeluhr
- https://pland.app/arbeitslexikon/sollarbeitszeit
- https://pland.app/arbeitslexikon/fahrzeiten
- https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023
- https://pland.app/onboardings/freigabe-von-zeiterfassungen
- https://pland.app/onboardings/fahrzeiterfassung-mit-pland
- https://pland.app/onboardings/lohnarten-und-zuschlage-in-pland
- https://pland.app/blog/gebaudereinigung-sollstunden-richtig-berechnen
- https://pland.app/blog/gebaeudereinigung-arbeitszeiten-korrekt-berechnen
- https://pland.app/blog/zeiterfassung-in-gebaeudereinigung-einfuehren
- https://pland.app/blog/zeiterfassung-2-0-mit-dem-digitalen-stundenzettel

Repository (read 2026-08-29):
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/attendance.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/services.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/calibration.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/views.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/templates/dashboard/my_shifts.html`
- `/Users/Geronimo/Projects/Cleaning_SaaS/tests/test_attendance.py`
