---
name: gr-marktplatz-dispatch
description: >
  Use for any work on the marketplace and dispatch layer of /Users/Geronimo/Projects/Cleaning_SaaS —
  `apps/marketplace` (ServiceRequest, Offer, Invitation, scoring.py, suggest_providers), the
  `/dashboard/cereri/` and `/dashboard/bursa/` routes, and every task phrased as "bursă de servicii",
  "cerere de serviciu", "ofertă", "atribuire", "matching", "auto-allocation", "auto-assign a cleaner",
  "Auftrag", "Dauerauftrag", "Angebot", "Ausschreibung", "Vergabe", "split payment", "escrow",
  "Lieferando for cleaning", or "courier-agency dispatch". Also use before touching the seam between
  `apps.marketplace` and `apps.planning` / `apps.contracts`. It overrides the generic gig-marketplace
  instinct: in the German Gebäudereinigung the platform allocates EMPLOYEES, not gig workers, so
  §7 SGB IV Scheinselbstständigkeit, the AÜG licence requirement and the allgemeinverbindlicher
  Mindestlohntarifvertrag decide the data model. Skipping this skill produces an auto-dispatcher that
  is illegal to ship, a single Request model that cannot serve both spot and recurring work, and
  payment code written before the legal payer is known.
metadata:
  author: Geronimo
  target: Cleaning_SaaS (Django 5.2, German Gebäudereinigung market)
  repo_root: /Users/Geronimo/Projects/Cleaning_SaaS
  sources: pland.app (crawled 2026-08-29, 237 pages) + repository code
---

# Marktplatz & Dispatch

**Stand: 2026-08-29, re-verified ~20:30 after a concurrent edit round.** Verified against the live
repository (`manage.py check` clean, **190 tests passing**) and against the pland.app crawl. Legal
content here is **reference material for building software, not legal advice**; a Steuerberater /
Fachanwalt decides the real cases.

> The repo is under active concurrent editing and is **not** under version control. Re-read any file
> before citing it; line numbers in this skill were correct at the Stand above.

Three kinds of statement are marked throughout this skill and its references:

| Marker | Meaning |
|---|---|
| **Fakt** | Sourced from pland.app (URL cited) or from repository code (`file:line` cited) |
| **Vorschlag** | Design proposal for code that does not exist yet |
| **Ungeprüft** | Domain knowledge added here that the crawled sources do **not** establish |

---

## 1. The one thing to get right

The owner's mental model is "Lieferando/courier agency + PlanD". **That analogy holds only for the
spot segment, and even there only partly.**

Lieferando dispatches a courier who is (or is treated as) an independent contractor or an employed
rider of a delivery company. In the German Gebäudereinigung, the same move — the platform picking a
person and pushing work at them — is what German law reads as either
**Scheinselbstständigkeit (§7 SGB IV)** or **Arbeitnehmerüberlassung (AÜG)**. The repository already
encodes this refusal in a module docstring:

> „**Nu există alocare automată.** Sistemul poate SUGERA prestatori, dar fiecare decide singur dacă
> ofertează și la ce preț. În Germania, un sistem care repartizează munca unei persoane fizice
> bifează criteriile §7 SGB IV (Scheinselbstständigkeit) și se apropie de Arbeitnehmerüberlassung —
> care cere licență de la Bundesagentur für Arbeit."
> — `apps/marketplace/models.py:10-14` (**Fakt**, code)

**Consequence for the data model, and it is the load-bearing consequence of this whole skill:**
the dispatch layer that actually schedules a named human onto a named site allocates **employees**,
under a **signed contract**, inside `apps.planning`. Contracts + planning are therefore a *legal
precondition* of the marketplace, not a later phase. `apps/planning/services.py:51-79` already
enforces exactly this — capacity comes **only** from `ContractDraft` rows with `status=SIGNED`.

---

## 2. Rules that must never be broken in this layer

1. **Never write auto-assignment of an individual.** `Invitation` is a suggestion
   (`apps/marketplace/models.py:177-181`), `suggest_providers` returns a ranked list
   (`apps/marketplace/scoring.py:160-190`). No code path may create an obligation for a
   `Capability.WORKER` account without a signed `ContractDraft`. If a task asks for "automatic
   allocation", build it inside `apps.planning` against contracted employees, never in
   `apps.marketplace` against marketplace providers.
2. **Never merge SPOT and RECURRING into one lifecycle.** They differ in state machine, matching
   inputs, SLA and settlement. See `references/zwei-vergabemodi.md`.
3. **Never hard-code a euro amount, a wage floor or a threshold.** Rows in
   `contracts.WageFloor` / `contracts.MinijobThreshold` with `valid_from`
   (`apps/contracts/models.py:57-113`), resolved **at the date the work starts**, never at "now".
   `apps/marketplace/forms.py:51-68` is the pattern to copy: it resolves
   `WageFloor.current(WageFloor.Kind.GEBAEUDE, earliest_start)` at the offer's `earliest_start` and
   **rejects** the offer with a field error when the implied hourly falls below it
   (`forms.py:62-67`, `self.add_error`), printing the as-of date. Only the contract-side wage-floor
   check is severity-graded (blocking for employment, warning for `WERKVERTRAG`,
   `apps/contracts/models.py:211`/`:221`).
4. **Never let an `Offer` unlock the client's address.** Only `status="WON"` raises the relation to
   `ENGAGED` (`apps/accounts/visibility.py:106-112`). Rendering an `Account` directly in a template
   instead of an `AccountView` is a DSGVO defect, not a style issue.
5. **Never widen the taxonomy.** `ServiceCategory` is max two levels, only leaves are selectable
   (`apps/taxonomy/models.py:39-42`, `apps/marketplace/models.py:110-112`). Slugs are German and
   SEO-load-bearing.
6. **Never write payment code before the legal-payer question is answered.** See
   `references/implementierung-django.md` §7. `LegalStatus` (`apps/accounts/enums.py:24-35`) exists
   precisely to hold that answer and is still `UNDECLARED` by default.
7. **Preserve the language convention.** Public URL segments German, dashboard URL segments
   Romanian (`/dashboard/cereri/`, `/dashboard/bursa/`), docstrings and comments Romanian, Python
   identifiers and `name=` values English, domain data German.

---

## 3. What exists vs. what does not — verified 2026-08-29

The repo moved during the dossier work. **`apps.marketplace` now exists.** Any older note claiming
"there is no ServiceRequest/Offer entity" is stale.

### Built (Fakt — code)

| Thing | Where | Notes |
|---|---|---|
| `ServiceRequest` (standardised spec) | `apps/marketplace/models.py:48-112` | category × locality × `area_sqm` × `frequency` × `earliest_start`; leaf-only category |
| `Offer` | `apps/marketplace/models.py:122-174` | one per (request, provider); `implied_hourly` is the comparison basis |
| `Invitation` (suggestion, not assignment) | `apps/marketplace/models.py:177-200` | carries `score` + `reasons` JSON |
| Multi-criteria scoring with visible breakdown | `apps/marketplace/scoring.py:22-91` | price 0.30 / verification 0.25 / experience 0.20 / availability 0.15 / proximity 0.10 |
| Request lifecycle services | `apps/marketplace/services.py:16-119`, `199-216` | publish / submit / withdraw / award / cancel / expire |
| Legal warnings shown next to the award button | `apps/marketplace/services.py:63-97` | Minijob-Haushaltsscheck, undeclared status, §35a payment-by-bank |
| **Award → contract seam** | `apps/marketplace/services.py:125-196`, `views.py:74-81` | `create_contract_from_offer`; contract type derived from `LegalStatus`, never chosen by the user |
| Typed compliance findings with explicit severity | `apps/contracts/models.py:44-54`, `196-254` | `ComplianceIssue(code, message, blocking)`; wage floor blocks employment contracts, only warns on a Werkvertrag |
| Two-sided account model | `apps/accounts/enums.py:11-21`, `models.py:229-243` | capability **rows**, not a `role` column |
| Orthogonal legal status | `apps/accounts/enums.py:24-35` | UNDECLARED / MINIJOB / SELBSTSTAENDIG / KLEINUNTERNEHMER / COMPANY |
| Contracts + e-signature | `apps/contracts/` | simple electronic signature over a frozen SHA-256 body |
| Recurring execution engine | `apps/planning/` | `Site` → `Zone` → `ShiftPlan` → `Shift`, hard ArbZG constraints |
| Dashboard routes | `apps/dashboard/urls.py:46-50` | `cereri/`, `cereri/noua/`, `cereri/<pk>/`, `bursa/`, `bursa/<pk>/oferta/` |

### Not built (the real gaps)

| Missing | Why it matters | Detail |
|---|---|---|
| **Any link `marketplace` → `planning`** | An AWARDED recurring request never becomes a `Site`/`Zone`/roster. `grep -rn "planning\|Site\|Zone\|Shift" apps/marketplace/` returns **nothing** (re-checked after the contract seam landed). This is now the single largest gap. | `references/zwei-vergabemodi.md` §5 |
| A RECURRING regime at all | `RequestStatus` ends at `AWARDED` (`apps/marketplace/models.py:40-45`); there is no ACTIVE, no term, no notice period, no Leistungsverzeichnis | `references/zwei-vergabemodi.md` §3 |
| `Kunde` / `Objekt` (customer-facing), `Angebot` document, `Rechnung`, `Review`, `Payment` | Nothing to bill, nothing to rate, nothing to settle. §35a is promised (`services.py:87-91`) but no invoice entity can back it. | `references/implementierung-django.md` §5–§7 |
| Scheduler for `expire_requests` | Defined at `apps/marketplace/services.py:211-216`, called only from `tests/test_marketplace.py:139`. No management command, nothing runs it in production. | — |
| Geocoding | `Locality.latitude/longitude` exist and are nullable; `_proximity_score` is a 3-step locality approximation (`apps/marketplace/scoring.py:105-115`) | — |
| A quality/rating axis in scoring | `WEIGHTS` has five criteria, none of them past performance (`apps/marketplace/scoring.py:22-28`) | `references/implementierung-django.md` §5.1 |

### Recently fixed — do not "re-fix", and copy the pattern

Four defects flagged earlier in this skill were closed by a concurrent edit round on 2026-08-29.
They are listed because the *patterns* are now the house style:

| Was | Now |
|---|---|
| branch wage floor hard-coded as `14` in the offer form | resolves `WageFloor.current(Kind.GEBAEUDE, earliest_start)` and prints the as-of date (`apps/marketplace/forms.py:51-68`) |
| `WageFloor` GEBAEUDE had no 2026 row (14,25 € with `valid_to=None`) | `apps/contracts/migrations/0005_wage_floor_2026.py` closes 2025 at 31.12.2025 and adds **15,00 € ab 01.01.2026**, `source_note` „Lohntarifvertrag LG 1, ab 01.01.2026, allgemeinverbindlich (§ 7 AEntG)" |
| `send_for_signature` decided severity by substring `"Verifică" not in i` | typed `ComplianceIssue(code, message, blocking)` (`apps/contracts/models.py:44-54`); `send_for_signature` filters on `i.blocking` (`apps/contracts/services.py:25-32`) |
| a won `Offer` produced no contract | `create_contract_from_offer` (`apps/marketplace/services.py:148-196`) |

### Still open defects

| Defect | Location | Fix |
|---|---|---|
| `Frequency.ONE_TIME` and `Frequency.MONTHLY` both map to `VISITS_PER_MONTH = 1`, so `monthly_price` and the §35a yearly projection are wrong for one-off work | `apps/marketplace/models.py:32-37`, `157-174` | the two regimes are conflated in one enum — see `references/zwei-vergabemodi.md` §4 |
| `jobs.EmploymentType.MINIJOB` is emitted into schema.org JSON-LD but is not a valid `employmentType` | `apps/jobs/models.py:9` | map MINIJOB → `PART_TIME` in the JSON-LD builder only; keep „Minijob" in the UI |
| `create_contract_from_offer` idempotency key is `(employer, worker, start_date, workplace)` with `contract_type__isnull=False` — two genuinely different requests for the same worker, same locality, same start date collapse onto one contract | `apps/marketplace/services.py:172-177` | key it on the `Offer` / a future `Assignment` instead |

---

## 4. Reference routing

| If the task is about … | Read |
|---|---|
| Which regime a feature belongs to; lifecycle states; matching inputs; SLA; what each regime needs in the data model; why one model cannot serve both | `references/zwei-vergabemodi.md` |
| Whether a design is legal; Mindestlohntarifvertrag / AVE; Scheinselbstständigkeit criteria; AÜG + BAG Konzernprivileg; Handwerksrolle; §16 ArbZG; what the sources actually establish vs. what is Ungeprüft | `references/rechtliche-grenzen.md` |
| Concrete Django work: what `apps/jobs` is and is not; how capabilities carry the two-sided model; proposed entities and their relation to `planning.Shift`; scoring inputs; settlement and split-payment questions | `references/implementierung-django.md` |
| **Who the counterparty actually is** — the Genossenschaft/eG operating model taken from inline-kurier.de: members co-decide the *rules* of dispatch (price list, allocation policy, budget) while a Disponent executes them, and the operators are **Betriebe, not natural persons**. That distinction is what keeps allocation on the right side of §7 SGB IV, and it is the premise behind the "never auto-assign an individual" rule in §2 above. | skill **`gr-vermittlungsmodell`** |

## 5. Before you write code in this layer

1. Read the module docstring of `apps/marketplace/models.py` and `apps/marketplace/scoring.py` — the
   design decisions are stated there and must not be silently reversed.
2. Decide SPOT or RECURRING first. If the answer is "both", the feature is wrong.
3. Ask: does this create an obligation for a natural person? If yes, it needs a signed contract and
   belongs in `apps.planning`.
4. Ask: does this move money? If yes, stop and answer the legal-payer questions in
   `references/implementierung-django.md` §7 first.
5. Run `.venv/bin/python -m pytest -q` — 190 tests pass repo-wide, 38 of them the
   marketplace invariants in `tests/test_marketplace.py`, including „sugestia nu este repartizare",
   „o ofertă nu deschide datele clientului" and the whole `TestContractSeam` class.
