---
name: gr-einsatzplanung
description: >
  Einsatzplanung / Dienstplan for the Cleaning_SaaS repo at /Users/Geronimo/Projects/Cleaning_SaaS.
  Load it for any work touching apps/planning (Site/Obiectiv, Zone/Zonă, ShiftPlan, Shift,
  ShiftEvent, ZoneCalibration, reinigungsplan.py), the allocation side of apps/marketplace
  (ServiceRequest, Offer, Invitation, suggest_providers), the dashboard routes
  /dashboard/obiective/, /dashboard/planificare/, /dashboard/turele-mele/, /dashboard/pontaj/,
  /dashboard/calibrare/, or the XLSX Reinigungsplan export. Triggers on Einsatzplan, Dienstplan,
  Personaleinsatzplanung, Reinigungsintervall, Reinigungsplan, Dauerauftrag, Sonderauftrag,
  Objekt, Zone, Vertretung, Abwesenheit, Urlaubsantrag, Krankmeldung, Ruhezeit, offene Schicht,
  roster generation, allocation constraints, shift publication, unmet demand, minutes_per_visit,
  calibration thresholds. Skipping it produces code that breaks the contracted-hours ceiling
  (Geringfügigkeitsgrenze), the ArbZG constraints, the append-only ShiftEvent journal, the
  Romanian/German/English language split, or the deliberate no-auto-allocation rule that keeps
  the marketplace layer clear of §7 SGB IV and the AÜG.
metadata:
  author: Geronimo
  target: Cleaning_SaaS (Django 5.2, German Gebäudereinigung market)
  repo_root: /Users/Geronimo/Projects/Cleaning_SaaS
  sources: pland.app (crawled 2026-08-29, 237 pages) + repository code
---

# Einsatzplanung

**Stand: 2026-08-29.** Repo state verified by reading the files; every code claim carries a
`file:line`. Every pland.app claim carries its source URL. Legal paragraphs below are reference
material copied from the code and from the sources — not legal advice.

Statement types used throughout this skill and its references:

* **Fakt** — sourced from the repo (`file:line`) or from pland.app (URL).
* **Vorschlag** — a design proposal for code that does not exist yet.
* **Ungeprüft** — domain knowledge added here that the sources do not cover.

---

## Why planning is the seam of the product

Planning is where the courier-dispatch layer meets the PlanD roster layer. The owner's framing —
"Lieferando/courier agency + PlanD" — collapses into **two allocation regimes that must never
share a code path**:

| | **Spot regime** (Einzelauftrag / Sonderauftrag) | **Recurring regime** (Dauerauftrag / Unterhaltsreinigung) |
|---|---|---|
| Demand object | `marketplace.ServiceRequest` — `apps/marketplace/models.py:48-112` | `planning.Zone` — `apps/planning/models.py:42-87` |
| Recurrence expressed as | `Frequency` + `VISITS_PER_MONTH` — `models.py:25-37` | `visits_per_week` + `allowed_weekdays` — `models.py:61,63` |
| Who decides the assignment | **The provider decides to bid; the client awards.** `award_offer` — `apps/marketplace/services.py:100-119` | **The generator assigns.** `generate_week_plan` — `apps/planning/services.py:98-156` |
| Automatic allocation | **Forbidden.** `Invitation` is a suggestion only — `apps/marketplace/models.py:177-181`, rationale `apps/marketplace/models.py:10-14` | **Required.** Greedy allocator with hard constraints — `apps/planning/services.py:1-15` |
| Legal reason for the difference | Allocating work to a natural person meets the §7 SGB IV criteria and approaches Arbeitnehmerüberlassung, which needs a Bundesagentur-für-Arbeit licence (`apps/marketplace/models.py:11-14`) | The worker is already an employee under a **signed** `ContractDraft`; the plan only distributes hours already contracted (`apps/planning/services.py:52-56`) |
| Output | `Offer` → `RequestStatus.AWARDED` | `ShiftPlan` → `Shift` rows → published + emailed |

**Fakt.** The two regimes are today two separate apps with **no shared code and no bridge**.
Nothing converts an awarded `Offer` into a `Site`/`Zone`/`ShiftPlan`. Grep confirms
`apps/marketplace` never imports `apps.planning` and vice versa.

**Vorschlag.** If you are asked to "turn an awarded request into a recurring plan", the bridge is
a new service that creates a `Site` + `Zone` from the `ServiceRequest` (area, category, locality,
preferred_weekdays, frequency → `visits_per_week`) and leaves `minutes_per_visit` seeded from
`Offer.estimated_minutes`. Do **not** put that logic in either app's `services.py`; put it in a
new module and keep the §7 SGB IV boundary visible in its docstring.

---

## Rules that must never be broken

**P1 — Contracted hours are a legal ceiling, not a preference.**
`apps/planning/models.py:4-8`, enforced at `apps/planning/services.py:86-87`. Weekly budget =
`int(Decimal(contract.hours_per_month) * 60 / WEEKS_PER_MONTH)` with
`WEEKS_PER_MONTH = Decimal("52") / Decimal("12")` (`services.py:31,67`). 40 h/month → **553**
weekly minutes (verified by running the expression). Overshooting a Minijob's
Geringfügigkeitsgrenze converts the employment into a compulsorily-insured one
(`apps/contracts/models.py:92-97`).

**P2 — No signed contract, no capacity.** `apps/planning/services.py:58-64` filters
`ContractDraft.objects.filter(employer=account, status=DraftStatus.SIGNED, …)`. Planning is not
where employment relationships are created (docstring `services.py:52-56`).

**P3 — Work that does not fit stays unallocated and is reported with a reason.**
`services.py:133-141`. The dict shape is fixed:
`{"zone", "site", "date", "minutes", "reasons"}` where `reasons` is `{worker_name: reason_str}`.
Never silently over-allocate; never drop the reason.

**P4 — Refusals return a reason string, not a boolean.** `_fits` returns `str | None`
(`services.py:82-95`). Keep that contract when you add a constraint.

**P5 — A published plan is not silently regenerated.** `services.py:104-109` raises
`ValueError("Planul e publicat. Regenerarea cere confirmare explicită.")` unless `replace=True`.

**P6 — Workers only ever see published plans.** `views.py:143-151` and `_guard`
(`attendance.py:82-88`).

**P7 — `ShiftEvent` is append-only.** `models.py:217-220` raises `RuntimeError` on re-save. A
correction is a new `CORRECTED` event carrying `{"from", "to", "reason"}`
(`attendance.py:161-164`), never an overwrite. Rationale: BAG 13.09.2022 (1 ABR 22/21) on
§3 Abs. 2 Nr. 1 ArbSchG; retention ≥ 2 years per §16 Abs. 2 ArbZG (`models.py:154-156`,
`attendance.py:8-11,22`).

**P8 — Calibration is proposed, never auto-applied.** `apps/planning/models.py:236-245`;
the only writer of `Zone.minutes_per_visit` outside the form is `apply_calibration`
(`calibration.py:196-198`), reachable only from a human POST.

**P9 — Every planning queryset is tenant-scoped.** `account=`, `site__account=`,
`plan__account=` or `zone__site__account=`. See `views.py:71, 95, 122, 154, 195, 212-213, 256,
275-284`; `services.py:113, 176-178`; `calibration.py:150-152, 228-230`; `attendance.py:184`.

**P10 — Legal constants get a named module constant with the paragraph in the comment.**
`MAX_DAILY_MINUTES = 480  # §3 ArbZG…` (`services.py:27-29`). Amounts that change annually
(wage floors, Minijob threshold) belong in DB rows with `valid_from`/`valid_to`, like
`apps/contracts/models.py:57-113` — never in code.

**P11 — Business logic in `services.py` / `attendance.py` / `calibration.py`, never in views.**
Views parse the request, call one function, set one message, redirect. Every mutating service is
`@transaction.atomic`.

**P12 — Language split (see the repo convention).** Romanian for anything an operator reads
(`verbose_name`, `TextChoices` labels, docstrings, comments, `messages.*`, template copy,
dashboard URL segments). German for anything a German user or authority reads (the worker
notification email `attendance.py:66-72`, the XLSX Reinigungsplan `reinigungsplan.py`,
`ServiceCategory.name_de`, legal citations). English for Python identifiers, field names and URL
`name=`.

---

## Constraints the generator enforces today

| # | Constraint | Constant | Enforced at | Refusal string (verbatim) | Test |
|---|---|---|---|---|---|
| 1 | Locality served | `cap.localities` (`services.py:68-70`) | `services.py:84-85` | `"nu deservește localitatea"` | `tests/test_planning.py:111-119` |
| 2 | Weekly contracted budget | `WEEKS_PER_MONTH` `services.py:31` | `services.py:86-87` | `f"buget săptămânal epuizat ({cap.weekly_minutes} min contractate)"` | `tests/test_planning.py:78-84` |
| 3 | Max 8 h/day, §3 ArbZG | `MAX_DAILY_MINUTES = 480` | `services.py:88-89` | `"ar depăși 8 h într-o zi (§3 ArbZG)"` | `tests/test_planning.py:86-97` |
| 4 | Min 11 h rest, §5 ArbZG | `MIN_REST_MINUTES = 11 * 60` | `services.py:90-94` | `"sub 11 h de odihnă față de tura anterioară (§5 ArbZG)"` | **none** |
| 5 | Sunday free, §9 ArbZG | `SUNDAY = 7` | `services.py:161` (`_visit_days`) | — (day is stripped, not refused) | `tests/test_planning.py:99-103` |

**Constraint 4 is dead code today.** With `DAY_START = time(7, 0)` (`services.py:30`) and a
480-minute daily cap, the latest possible `day_end` is 15:00; 15:00 → next day 07:00 is 16 h,
always ≥ 11 h. It becomes reachable only if `DAY_START` becomes configurable or
`MAX_DAILY_MINUTES` rises past 720. Do not cite §5 as "implemented".

Not implemented at all: **§4 ArbZG breaks**, **§11 ArbZG (max 6 consecutive days)**,
**qualification matching**, **travel time / proximity beyond exact locality membership**,
**absence**, **monthly (as opposed to weekly) hour ceilings**. See
`references/zuteilung-und-vertretung.md`.

---

## What exists vs what does not

| Capability | Status | Where |
|---|---|---|
| Objekt (`Site`) + Zone with interval | **exists** | `apps/planning/models.py:21-87` |
| Weekly plan generation, greedy, hard constraints | **exists** | `services.py:98-156` |
| Capacity report (demand vs supply) | **exists** | `services.py:172-188` |
| Plan publication + one German email per worker | **exists** | `attendance.py:29-74` |
| Shift lifecycle + append-only journal | **exists** | `attendance.py:82-175` |
| Working-time register for an FKS/Zoll audit | **exists** | `attendance.py:178-205`, `views.py:184-223` |
| Estimate calibration from clocked time | **exists** | `apps/planning/calibration.py` |
| Reinigungsplan XLSX export per Objekt | **exists** | `apps/planning/reinigungsplan.py`, route `dashboard:site_reinigungsplan` |
| Telemetry cross-check against clocked time | **exists (other app)** | `apps/devices/services.py:130-177` |
| Marketplace request → offer → award | **exists** | `apps/marketplace/` |
| **Absence / Urlaub / Krankheit model** | **missing** | `ContractDraft.vacation_days` exists (`apps/contracts/models.py:167`) but nothing in planning reads it |
| **Vertretung / substitution flow** | **missing** | `DECLINED` is terminal; the work vanishes from the plan and is *not* added to `unmet_demand` |
| **Manual shift editing / drag-and-drop** | **missing** | the only writer of `Shift.date/start_time/worker` is `generate_week_plan` |
| **Site/Zone edit or delete UI** | **missing** | only Create + List; `ZoneForm.__init__:37-38` has dead edit-path code |
| **Qualification matching** | **missing** | `Zone.category` is stored and never read by the planner |
| **Recurrence engine / roll-forward** | **missing** | no RRULE, no cron, no Celery, no management command; a human must POST per week |
| **Notification on plan change / decline** | **missing** | `views.py:162` claims "Angajatorul a fost informat" — nothing is sent |
| **Django admin for planning** | **missing** | there is no `admin.py` anywhere in the project |
| **Customer-facing plan visibility** | **missing** | no customer portal, no Leistungsnachweis |

---

## Routing table

| If the task is about… | Read |
|---|---|
| What an Einsatzplan/Dienstplan must contain; Objekt/Zone/Auftrag structure; Daueraufträge vs one-off; Reinigungsintervalle; how a Reinigungsplan relates to a Dienstplan; the XLSX export | `references/dienstplan-und-objekte.md` |
| Allocation constraints (qualification, capacity, proximity, ArbZG, Ruhezeit, absence); the Vertretung flow when someone calls in sick; Urlaubsantrag / Urlaubsanspruch / Krankheit; notification duties on plan change | `references/zuteilung-und-vertretung.md` |
| `apps/planning/calibration.py` — every formula, weight, threshold, minimum-sample rule; how a calibrated value flows back into planning; what the tests assert; how to tune safely | `references/kalibrierung.md` |
| Exact model fields, the publication flow, timezone handling under `Europe/Berlin` + `USE_TZ`, and step-by-step recipes for the likely changes | `references/implementierung-django.md` |

---

## Fast facts you will need constantly

* Dashboard routes (`apps/dashboard/urls.py:32-42`): `obiective/` → `dashboard:sites`;
  `obiective/nou/` → `site_create`; `obiective/<pk>/reinigungsplan.xlsx` →
  `site_reinigungsplan`; `obiective/zona-noua/` → `zone_create`; `planificare/` → `planning`;
  `planificare/<pk>/publicare/` → `plan_publish`; `turele-mele/` → `my_shifts`;
  `pontaj/` → `time_records`; `calibrare/` → `calibration`.
* `apps/planning` has **no `urls.py`** — every route is registered in `apps/dashboard/urls.py`.
* Views gate on `{Capability.EMPLOYER, Capability.PROVIDER}` except three (below); dashboard tiles for
  sites/planning/time_records/calibration are registered under `Capability.EMPLOYER` only
  (`apps/dashboard/panels.py:68-79`), so a PROVIDER-only account can reach the URL but sees no
  tile. Three views have **no** capability gate: `my_shifts_view` (on purpose — workers hold
  `WORKER`), `publish_plan_view` (`views.py:121-133`, ownership only) and `reinigungsplan_view`
  (`views.py:296-310`, `account is None` → `PermissionDenied`, then ownership).
* `templates/base.html` **does** render flash messages (`base.html:9-13`). Any dossier or note
  claiming otherwise is stale.
* Migration chain: `0001_initial` → `0002_shift_actual_minutes_shift_checked_in_at_and_more` →
  `0003_zonecalibration` → `0004_zone_description`. `apps/devices/migrations/0001_initial.py:13`
  depends on `planning.0003_zonecalibration` — do not insert a planning migration before it.
* Test suite: `.venv/bin/python -m pytest` → **190 passed** (verified 2026-08-29 — re-run and record the count yourself, the suite grows). Planning-side
  files: `tests/test_planning.py`, `tests/test_attendance.py`, `tests/test_calibration.py`,
  `tests/test_reinigungsplan.py`.
* Run Python as `/Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python`.
* `openpyxl 3.1.5` **is** installed in the venv, although `pyproject.toml` lists it only under
  the optional `export` extra. `apps/planning/reinigungsplan.py:58-60` imports it lazily inside
  `build_workbook`, so the module import never fails.

---

## Before you change anything

1. Open the file and confirm the line you are about to cite. The repo is edited concurrently.
2. If the change touches `ShiftStatus`, `Shift.actual_minutes`, `Shift.date/start_time/
   duration_minutes` or `Site`, grep `apps/devices` too — it is the one out-of-app consumer
   (`apps/devices/models.py:49,115`; `apps/devices/services.py:9`; `apps/devices/forms.py:3`).
3. Run `.venv/bin/python manage.py check` and `.venv/bin/python -m pytest -q` before reporting
   done. Do not run `makemigrations` unless asked.
