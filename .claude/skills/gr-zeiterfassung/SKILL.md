---
name: gr-zeiterfassung
description: >
  Use for any work on time recording in /Users/Geronimo/Projects/Cleaning_SaaS —
  Zeiterfassung, Arbeitszeiterfassung, Pontaj, Stundenzettel, Stempeluhr, Zeitstempel,
  Check-in/Check-out, Zeitenfreigabe/Freigabe, Sollarbeitszeit/Sollstunden, Ist-Zeit,
  Mehrarbeit, Ruhepausen, Wegezeit/Fahrzeit/Zwischenzeit, Geofence, GPS-Ortung,
  Standortkontrolle, nachgetragene Zeiten, Zoll/FKS-Export, Aufbewahrung. Fires on any
  change to apps/planning/attendance.py, apps/planning/models.py (Shift, ShiftEvent,
  ShiftStatus), the /dashboard/pontaj/ and /dashboard/turele-mele/ views,
  templates/dashboard/time_records.html, templates/dashboard/my_shifts.html,
  tests/test_attendance.py, and apps/devices/services.py, where telemetry is
  cross-checked against pontaj. Also fires on "add breaks to the timesheet", "round the
  hours", "record GPS at check-in", "let the employer edit hours", "export hours for
  payroll". OVERRIDES generic time-tracking advice: in Germany the record is evidence,
  so an approved entry stays immutable, a correction is a new append-only event, raw and
  derived minutes must both survive, and a worker position may not be stored without a
  documented legal basis. Skipping it produces code that silently overwrites legal
  records or collects location data with no consent trail.
metadata:
  author: Geronimo
  target: Cleaning_SaaS (Django 5.2, German Gebäudereinigung market)
  repo_root: /Users/Geronimo/Projects/Cleaning_SaaS
  sources: pland.app (crawled 2026-08-29, 237 pages) + repository code
---

# gr-zeiterfassung — Zeiterfassung in Cleaning_SaaS

Stand: 2026-08-29. Legal content here is **reference material, not legal advice**;
Tarif and statutory values change yearly, so every table in `references/` carries its
own Stand and source URL.

Three kinds of statement are labelled throughout:
**Fakt** (sourced from pland.app with a URL, or from repo code with file:line) ·
**Vorschlag** (design proposal for code that does not exist) ·
**Ungeprüft** (domain knowledge the crawled sources do not cover).

---

## 1. Rules that must hold for every change in this area

1. **The journal is append-only.** `ShiftEvent.save()` raises
   `RuntimeError("Evenimentele de pontaj sunt imutabile.")` when `self.pk` is set
   (`apps/planning/models.py:217-220`). Never add an `update()`, `bulk_update()` or
   admin edit path over `ShiftEvent`. A correction is a **new** event, never an
   overwrite — see `correct_minutes` (`apps/planning/attendance.py:147-165`), which
   writes `payload={"from": previous, "to": minutes, "reason": ...}`.
2. **A correction needs a reason.** `correct_minutes` raises `ShiftError` on an empty
   reason (`attendance.py:155-156`). Do not add a code path that changes
   `Shift.actual_minutes` without an actor and a reason.
3. **Only the employer corrects; only the assigned worker clocks.** `_guard`
   (`attendance.py:82-88`) rejects a shift that is not `shift.worker_id == account.pk`;
   `correct_minutes` and `mark_missed` reject anyone but `shift.plan.account`
   (`attendance.py:153-154`, `:170-171`).
4. **Nothing is workable before the plan is published.** `_guard` requires
   `shift.plan.status == PlanStatus.PUBLISHED`. Worker-facing querysets must keep
   filtering on it (`apps/planning/views.py:143-148`).
5. **Store the raw value next to any derived value.** `actual_minutes` is today the raw
   check-out minus check-in figure (`attendance.py:133`). If you introduce rounding,
   Soll-Zeit booking, break deduction or travel time, add **new** fields; do not
   overwrite `actual_minutes` with a rounded number — the tatsächliche Arbeitszeit is
   what the recording duty is about, and the calibration engine reads it
   (`apps/planning/calibration.py:99-104`).
6. **Never store a worker position without a consent trail.** There is currently no
   location field anywhere in the repo (verified by grep for lat/lng/geo/distance across
   `apps/`). If you add one, gate it on a `ConsentRecord`-style record
   (`apps/accounts/compliance.py:51-70` — already append-only, already versioned via
   `POLICY_VERSION` at `apps/accounts/services.py:15`) and read
   `references/geofence-und-dsgvo.md` first.
7. **Retention is data, not a magic number.** `RETENTION_YEARS = 2`
   (`attendance.py:22`) and the derived `retention_until`
   (`attendance.py:205`) are the only retention logic. Do not shorten it; do not add a
   deletion job without reading `references/rechtsgrundlagen.md`.
8. **`time_records()` is the audit artefact.** Its docstring is explicit: "ce trebuie să
   poți arăta la un control (Zoll / FKS)" (`attendance.py:178-181`). Any change must
   keep it reproducible for a past date range; do not make it depend on mutable
   settings that are not themselves versioned.
9. **Preserve the language convention.** Dashboard URL segments stay Romanian
   (`/dashboard/pontaj/`, `/dashboard/turele-mele/` — `apps/dashboard/urls.py:40-41`),
   comments and docstrings Romanian, Python identifiers and `name=` values English,
   user-facing domain vocabulary German. Do not "translate" one side.
10. **Do not silently pick a value where the sources disagree.** The reference period
    for the 8-hour daily average is printed as both *24 Wochen* and *6 Monate* on the
    same competitor page; the month factor 4,33 and the 52-week year are mutually
    inconsistent. Make such values configurable and record which one was chosen.

---

## 2. What exists in the code today

| Concern | State | Where |
|---|---|---|
| Shift state machine (6 states) | exists | `apps/planning/models.py:131-137` |
| Check-in / check-out with guards | exists | `apps/planning/attendance.py:113-144` |
| `actual_minutes` = floor((out − in)/60 s) | exists | `attendance.py:133` |
| Check-out before check-in rejected | exists | `attendance.py:131-132` |
| Employer correction with reason, old value kept | exists | `attendance.py:147-165` |
| Append-only event journal | exists | `models.py:188-220` |
| Plan publishing freezes the week + emails workers | exists | `attendance.py:29-74` |
| Audit export for a date range (`time_records`) | exists | `attendance.py:178-205` |
| Retention constant (2 years) | exists | `attendance.py:22` |
| Telemetry cross-check against pontaj | exists | `apps/devices/services.py:130-178` |
| Planner hard limits 8 h/day, 11 h rest, no Sunday | exists | `apps/planning/services.py:27-29` |
| **Ruhepausen / break recording** | **missing** | — |
| **Wegezeit / Fahrzeit / Zwischenzeit** | **missing** | — |
| **Geofence, GPS, Standortkontrolle** | **missing** | — |
| **Approval (Freigabe) gate before payroll** | **missing** | — |
| **Rounding / Soll-Zeit booking / tolerance windows** | **missing** | — |
| **Sollstunden / Zeitkonto / Saldo** | **missing** | — |
| **Zuschläge (night, Sunday, holiday)** | **missing** | — |
| **Retro-entry ("nachgetragene Zeiten") as a typed source** | **missing** | — |
| **`Site` geo coordinates** (only `Locality` has lat/lng) | **missing** | `apps/geo/models.py:30-31` vs `apps/planning/models.py:21-39` |
| **Admin registration for these models** | **missing** | no `apps/planning/admin.py` |

`Shift.actual_minutes` is a `PositiveSmallIntegerField` (`models.py:159`) — max 32767
minutes ≈ 22 days; adequate for a shift, not for a monthly aggregate.

---

## 3. Where to read the detail

| File | Use it when |
|---|---|
| `references/rechtsgrundlagen.md` | You need the legal basis for the duty, what exactly must be recorded, the deadlines (7 days / same day), retention periods, and which claims are sourced vs. unsourced. Read before changing `RETENTION_YEARS`, `time_records()`, or arguing that a feature is "required by law". |
| `references/stundenzettel-und-berechnung.md` | You are computing hours: Stundenzettel columns, Soll vs. Ist, break exclusion, Wegezeit per RTV § 3 Nr. 3 with the three-hour Zwischenzeit rule and the started-half-hour rounding, Mehrarbeit, and the Freigabe workflow with its immutability consequence. |
| `references/geofence-und-dsgvo.md` | You are about to touch location: geofence radius, Standortfehler, GPS toggle, BYOD, consent declaration, Betriebsrat/Mitbestimmung, data minimisation. |
| `references/implementierung-django.md` | You are editing the code: exact behaviour of every attendance function with file:line, what the 22 tests lock in, and the gap list against the legal requirements. |

---

## 4. Vocabulary map (German domain term → this codebase)

| German | Code |
|---|---|
| Zeiterfassung / Arbeitszeiterfassung | the `apps/planning/attendance.py` module ("pontaj") |
| Zeitstempel | `Shift.checked_in_at`, `Shift.checked_out_at` |
| Ist-Zeit | `Shift.actual_minutes` |
| Soll-Zeit (per Einsatz) | `Shift.duration_minutes`, seeded from `Zone.minutes_per_visit` |
| Abweichung Soll/Ist | `Shift.variance_minutes` (`models.py:180-185`) |
| Einsatz | `Shift` |
| Dienstplan / Einsatzplanung | `ShiftPlan` + `apps/planning/services.py` |
| Objekt | `Site` (`apps/planning/models.py:21`) |
| Objektleiter | **no role exists**; corrections are done by the employer `Account` |
| Stundenzettel | `templates/dashboard/time_records.html` + `time_records()` |
| Freigabe / Zeitenfreigabe | **does not exist** — see `references/stundenzettel-und-berechnung.md` §6 |
| Wegezeit / Fahrzeit | **does not exist** |
| Ruhepause | **does not exist** |
| Aufbewahrung | `RETENTION_YEARS`, `records["retention_until"]` |
| Zoll / FKS-Nachweis | `time_records(account, start, end, worker=None)` |

There is **no Customer, Auftrag, Angebot, Rechnung or Lohnabrechnung entity** in this
repo. Do not write code that assumes a payroll run exists; the furthest downstream
consumer of pontaj today is `apps/planning/calibration.py` and
`apps/devices/services.py`.

---

## 5. Before you write code

1. Open the file and confirm the current state — this repo is edited concurrently and a
   line number in these references may already have shifted.
2. Run the suite: `/Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python -m pytest -q`
   (190 tests as of 2026-08-29 20:40 and still growing — count it yourself, the repo is
   edited concurrently; 22 of them in `tests/test_attendance.py`).
3. If your change touches minutes, add a test that asserts the **raw** value survives.
4. If your change touches location, stop and read `references/geofence-und-dsgvo.md`.
