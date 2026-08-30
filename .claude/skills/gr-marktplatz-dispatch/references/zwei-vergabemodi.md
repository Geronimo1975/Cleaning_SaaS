# Zwei Vergabemodi — SPOT vs. RECURRING

**What this covers:** the two allocation regimes the platform must serve, their lifecycles, matching
inputs, timing expectations, and what each needs in the data model — plus why a single model cannot
serve both.
**Stand: 2026-08-29, re-verified ~20:30 after a concurrent edit round.** The repo is under active
concurrent editing and is not under version control — re-read any file before citing it.
**Material from:** the live repository at `/Users/Geronimo/Projects/Cleaning_SaaS` (every code claim
carries `file:line`, re-read on 2026-08-29); the pland.app crawl
(`scratchpad/knowledge/lexikon-betrieb.md`, `blog-fachwissen.md`, `product-modules.md`,
`tutorials-gruendung.md`, each row carrying the page URL); `PLAN-FAZA-0.md`.
Statements are marked **Fakt** / **Vorschlag** / **Ungeprüft**.

---

## 1. The split, in one table

| | **SPOT** | **RECURRING** |
|---|---|---|
| German name for the work | Sonderauftrag / einmaliger Auftrag | Unterhaltsreinigung / Dauerauftrag |
| Seeded leaf categories that land here | `bauendreinigung`, `umzugsreinigung`, `grundreinigung`, `fensterreinigung-privat`, `entruempelung`, `polsterreinigung`, `teppichreinigung`, `fassadenreinigung`, `glasreinigung-hoehe`, `schaedlingsbekaempfung`, `lueftungsreinigung`, `fahrzeugaufbereitung`, `winterdienst` (seasonal, hybrid) | `unterhaltsreinigung-privat`, `haushaltshilfe`, `bueroreinigung`, `treppenhausreinigung`, `ladenreinigung`, `gastronomiereinigung`, `praxisreinigung`, `industriereinigung`, `waeschepflege`, `gartenpflege` |
| Unit of value | one visit, one price | a month of visits at a fixed interval, a monthly price |
| Buyer | mostly private household or small business | mostly Hausverwaltung, office, retail, care home |
| What the buyer chooses | a provider, once | a *relationship* — and, in practice, a crew |
| The Lieferando analogy | holds, partly | **does not hold at all** |
| Who executes | the winning provider, in person or with own staff | a named, stable crew under signed contracts, rostered weekly |
| Where it lives in code today | `apps.marketplace` (built) | `apps.marketplace` for the request, `apps.planning` for execution — **the two are still not connected** |

**Fakt (code):** the seeded taxonomy has 4 top-level and 24 leaf categories, 15 of them flagged
`is_35a_eligible` — confirmed by querying the dev DB on 2026-08-29 against
`apps/taxonomy/migrations/0003_seed_categories.py`. Leaf slugs are German
(`apps/taxonomy/models.py:5-42`).

**Fakt (pland.app):** the two types are defined against each other in the source. Unterhaltsreinigung
is „die regelmäßige Reinigung eines Objektes in **festen Zeitabständen**" and „zielt darauf ab, den
Zustand der Räume auf einem **bereits gereinigten Niveau zu halten**"; Grundreinigung is „eine
**intensive** Reinigungsmethode … die **in bestimmten Zeitintervallen** durchgeführt wird".
Sources: <https://pland.app/arbeitslexikon/unterhaltsreinigung>,
<https://pland.app/arbeitslexikon/grundreinigung>.

---

## 2. SPOT — lifecycle, inputs, timing

### 2.1 Lifecycle states as implemented

**Fakt (code):** `apps/marketplace/models.py:40-45` and `apps/marketplace/services.py:16-119, 199-216`.

```
DRAFT ──publish_request()──▶ OPEN ──award_offer()──▶ AWARDED
  │                            │                        │
  │                            │                        └─ create_contract_from_offer()
  │                            │                             ──▶ contracts.ContractDraft (DRAFT)
  │                            ├──cancel_request()──▶ CANCELLED
  │                            └──expire_requests()─▶ EXPIRED   (offers_close_at passed)
  └──cancel_request()───────▶ CANCELLED
```

`AWARDED` is terminal on the request. Contract generation is a **separate, explicit action** by the
client (`action="contract"`, `apps/marketplace/views.py:74-81`) and does not change
`RequestStatus` — the request stays AWARDED whether or not paper was produced.

Offer side (`apps/marketplace/models.py:115-119`):

```
SUBMITTED ──withdraw_offer()──▶ WITHDRAWN
    │
    ├──award_offer(this one)──▶ WON
    └──award_offer(another)───▶ LOST     (bulk update, services.py:113-115)
```

Guards actually enforced (**Fakt**, code):

| Guard | Where |
|---|---|
| only a DRAFT can be published | `services.py:18-19` |
| `offers_close_at` must be in the future at publish time | `services.py:20-21` |
| request must be `is_open` to receive an offer | `services.py:38-39` |
| a client cannot bid on their own request | `services.py:40-41` |
| bidder must hold WORKER or PROVIDER capability | `services.py:42-43` (`Account.is_provider`, `apps/accounts/models.py:158-160`) |
| one offer per (request, provider) | `UniqueConstraint`, `models.py:148-150` |
| only the client awards | `services.py:102-103` |
| an AWARDED request cannot be cancelled | `services.py:203-204` |
| only the client generates the contract | `services.py:166-167` |
| a provider with `LegalStatus.UNDECLARED` gets **no contract at all** | `services.py:133-146` |

**Gap (Fakt):** `expire_requests()` exists (`services.py:211-216`) but is called only from
`tests/test_marketplace.py:139`. There is no management command and no scheduler — verified by
`find apps -path "*management/commands*"`, which returns only `apps/jobs/management/commands/flush_indexing.py`.
Without a runner, OPEN requests never move to EXPIRED in production.

### 2.2 The standardised request — why the fields are mandatory

**Fakt (code, `apps/marketplace/models.py:6-8`):** „Cererea e standardizată. Fără tip × suprafață ×
frecvență, ofertele nu sunt comparabile, iar «bursa fără negociere» devine o licitație pe orb."

This restates `PLAN-FAZA-0.md:200-202`, which called a standardised request spec a precondition for
a no-negotiation exchange.

| Field | Type | Required | `file:line` |
|---|---|---|---|
| `category` | FK leaf `ServiceCategory` | yes, leaf enforced in `clean()` | `models.py:52-54`, `110-112` |
| `locality` | FK `geo.Locality` (closed list) | yes | `models.py:55-57` |
| `postal_code` | CharField(5) | no | `models.py:58` |
| `area_sqm` | PositiveInteger, `MinValueValidator(1)` | **yes** | `models.py:61-63` |
| `rooms` | PositiveSmallInteger | no | `models.py:64` |
| `frequency` | `Frequency` choices | yes | `models.py:65` |
| `preferred_weekdays` | CharField(13) | no | `models.py:66` |
| `earliest_start` | DateField | yes | `models.py:67` |
| `has_pets`, `supplies_provided` | Boolean | default False | `models.py:71-74` |
| `offers_close_at` | DateTime | **yes** | `models.py:79` |

### 2.3 Matching inputs — what actually drives the ranking

**Fakt (code, `apps/marketplace/scoring.py:22-28`):**

| Criterion | Weight | How it is computed | `file:line` |
|---|---|---|---|
| `price` | 0.30 | min–max normalisation of `implied_hourly` **within this request's offer set**; cheapest 1, dearest 0; all-equal → all 1 | `scoring.py:94-98` |
| `verification` | 0.25 | `Account.verification_level / 3` (0 NONE … 3 DOCUMENTS) | `scoring.py:101-102`, `apps/accounts/enums.py:46-50` |
| `experience` | 0.20 | individual: `years_experience / 10` capped at 1; company: 0.4 base + 0.4 if `has_liability_insurance` + 0.2 if `hwk_registered` | `scoring.py:118-133`, `apps/accounts/profiles.py:19`, `50-54` |
| `availability` | 0.15 | days of delay vs. `request.earliest_start`; ≤0 → 1, ≥28 → 0, linear between | `scoring.py:136-142` |
| `proximity` | 0.10 | same locality 1.0; declared `ServiceArea` for that locality 0.7; otherwise 0.2 | `scoring.py:105-115` |

Comparison basis: `Offer.implied_hourly = price_per_visit × 60 / estimated_minutes`
(`models.py:161-166`), described in the code as „singura bază reală de comparație între oferte".
Tie-break is deterministic: higher score, then lower implied hourly, then lower pk (`scoring.py:91`).

The weight comment records a deliberate earlier correction (**Fakt**, `scoring.py:18-21`): at
`price = 0.35` an unverified, inexperienced provider tied with a verified one holding documents and
10 years' experience — the exact outcome the "not a price auction" premise must exclude.

Non-scored signals surfaced as notes (`scoring.py:145-157`): a supplies mismatch in either
direction, and the estimated §35a deduction.

### 2.4 Timing / SLA expectations

**Vorschlag** — nothing in the code sets these today; `offers_close_at` is free-form client input.

| Segment | Suggested `offers_close_at` default | Rationale |
|---|---|---|
| Umzugs-/Endreinigung with a handover date | 48 h, hard-capped at `earliest_start − 3 days` | key handover dates do not move |
| Bauendreinigung | 5 days | needs site inspection before pricing |
| Fenster-/Glasreinigung, private | 72 h | low urgency, price-shoppable |
| Grundreinigung, private | 72 h | |
| Winterdienst | ≤ 24 h in season | weather-driven |

**Ungeprüft:** these windows are proposed from market intuition, not from any crawled page. The
sources give no SLA figures at all.

**Fakt (pland.app), the only price anchors in the entire crawl** — usable as sanity bounds on
`implied_hourly`, not as platform prices:

| Item | Value | Source |
|---|---|---|
| Standard-Fensterreinigung | 3–7 € per m² of glass; worked example 200 m² one-off → 600–1.400 € | <https://pland.app/arbeitslexikon/glasreinigung> |
| Spezialreinigung of glass | 5–15 € per m² | same |
| Rahmenreinigung surcharge | 0,50–2 € per laufendem Meter | same |
| Regular Unterhaltsreinigung, office buildings | 0,15 € per m² (from a page's own *example* business plan) | <https://pland.app/tutorials/beispiel-geschaftsplan> |

The glass page explicitly labels its figures „nur als **Richtwerte**", varying by provider and
region, and states that more frequent cleaning lowers the per-clean cost — i.e. a recurring contract
is expected to price below a spot visit.

---

## 3. RECURRING — lifecycle, inputs, timing

### 3.1 The real lifecycle, and where the code stops

**Fakt (pland.app):** the Unterhaltsreinigung lifecycle is five ordered steps
(<https://pland.app/arbeitslexikon/unterhaltsreinigung>):

1. **Objektbesichtigung** — the Objektleiter inspects the object at the start of every new
   maintenance-cleaning contract: room sizes, **number of toilets**, and what exactly is to be
   cleaned. All information collected here is the input to step 2.
2. **Reinigungsplan** — because the work repeats at fixed intervals, a written plan records on which
   days and how regularly cleaning happens, which services are required in which rooms, and that
   services are documented after each clean.
3. **Reinigung** — execution; scope varies per contract (office rooms vs. a supermarket).
4. **Qualitätskontrolle** — the Objektleiter checks against the agreed scope; cleaners attach photos
   and comments; defects become Tickets.
5. **Leistungsnachweis** — proof of service recorded and sent to the customer.

**Fakt (code):** steps 2–3 exist. `apps/planning/models.py:21-87` models `Site` → `Zone`
(`minutes_per_visit`, `visits_per_week`, `allowed_weekdays`, `description` shown to the worker at
check-in); `apps/planning/reinigungsplan.py` renders a Reinigungsplan; `apps/planning/services.py:98-156`
generates the weekly roster. Step 1 (Objektbesichtigung as a recorded event) and step 5
(Leistungsnachweis document) **do not exist**.

The proposed request-side state machine (**Vorschlag**) is therefore longer than SPOT's:

```
DRAFT ─▶ OPEN ─▶ (offers) ─▶ SHORTLISTED ─▶ SITE_VISIT ─▶ AWARDED ─▶ ACTIVE ─▶ ENDED
                                  │                          │
                                  └──▶ LOST/EXPIRED          └──▶ SUSPENDED (Kündigung, seasonal stop)
```

`SITE_VISIT` is not decoration: the source makes the Objektbesichtigung the first step of every new
maintenance contract, and a price quoted without it is a guess. `ACTIVE` is the state the current
model has no room for at all — `RequestStatus` ends at `AWARDED` (`apps/marketplace/models.py:40-45`).

### 3.2 Reinigungsintervalle — the recurrence vocabulary

**Fakt (pland.app), whole table from <https://pland.app/arbeitslexikon/reinigungsintervall>:**

| Interval | Tasks named on the page |
|---|---|
| **Tägliche Reinigung** | Reinigen von Sanitäranlagen; Staubsaugen von Teppichböden in stark frequentierten Bereichen; Leeren von Abfallbehältern |
| **Wöchentliche Reinigung** | Wischen von Hartböden; Staubwischen von Oberflächen; Reinigung von Glasflächen |
| **Monatliche Reinigung** | Grundreinigung von Teppichböden; Reinigen schwer zugänglicher Bereiche; Pflege von Holzoberflächen |
| **Vierteljährliche oder halbjährliche Reinigung** | Reinigung von Fenstern, Jalousien und Leuchten; Tiefenreinigung von Polstermöbeln |
| **Jährliche Reinigung** | umfassende Grundreinigungen: Stripping und Neuversiegeln von Bodenbelägen; Fassadenreinigung |

Six factors that set an interval (same page): Gebäudenutzung, Besucherfrequenz,
Hygieneanforderungen, Oberflächenmaterialien, Gesetzliche Vorschriften, Kundenwünsche und
Budgetvorgaben. Intervals are explicitly stated to be **reviewed and adjusted** for saisonale
Schwankungen, Änderungen in der Gebäudenutzung and neue Hygieneanforderungen.

**Comparison with the code's two frequency vocabularies (Fakt):**

| Source | Values | `file:line` |
|---|---|---|
| pland.app | täglich, wöchentlich, monatlich, vierteljährlich/halbjährlich, jährlich | URL above |
| `marketplace.Frequency` | ONE_TIME, WEEKLY, BIWEEKLY, MONTHLY | `apps/marketplace/models.py:25-29` |
| `planning.Zone` | `visits_per_week` (int) + `allowed_weekdays` (ISO 1–7 CSV) | `apps/planning/models.py:61-63` |

Three vocabularies, none convertible into the others without loss. `marketplace.Frequency` cannot
express "täglich" or "vierteljährlich"; `Zone.visits_per_week` cannot express anything longer than a
week. This is the concrete shape of the "one model cannot serve both" problem.

### 3.3 B2B recurring arrives as a tender, not as a form

**Fakt (pland.app), <https://pland.app/blog/ausschreibungen-in-der-gebaudereinigung-ein-leitfaden-fur-unternehmen>:**
an Ausschreibung for cleaning services normally comprises five components —

| Component | What it holds |
|---|---|
| **Leistungsbeschreibung** | which cleaning services, which surfaces, which standards |
| **Vergabebedingungen** | legal/organisational frame, participation conditions, deadlines |
| **Preisblatt / Kalkulationsschema** | bidders must disclose prices transparently, often with a detailed calculation |
| **Bewertungskriterien** | how the best offer is chosen — beside price, often quality, sustainability, references |
| **Vertragsbedingungen** | term, termination conditions, contractual penalties |

The same page states that public bodies are legally obliged to tender above a value threshold (no
figure given), names DTVP and TED as sources, lists Handelsregisterauszüge,
**Unbedenklichkeitsbescheinigungen der Sozialversicherungsträger** and references as documents to
obtain in advance, and warns that many companies fail on **Formfehler**, not on price.

**Implication (Vorschlag):** the RECURRING request must be able to carry a document set and an
explicit criteria weighting supplied by the *buyer*, because in a tender the buyer defines the
Bewertungskriterien. The current `WEIGHTS` dict is platform-global and immutable
(`apps/marketplace/scoring.py:22-28`) — correct for a private household, wrong for a Hausverwaltung.

### 3.4 Timing / SLA expectations

**Vorschlag.** Recurring is slow and relationship-shaped:

| Phase | Expected duration | Why |
|---|---|---|
| OPEN (offers) | 7–14 days | providers must schedule a site visit before pricing |
| SITE_VISIT | within the OPEN window | source makes it step 1 of the contract |
| AWARDED → ACTIVE | 2–4 weeks | the winner must hire or reallocate staff, sign contracts, and only then can `generate_week_plan` produce a roster |
| substitution on sickness | same day | the crew is contractual; a missed Objekt is a Reklamation |

**Ungeprüft:** these durations are proposed, not sourced.

---

## 4. Why one model cannot serve both

Six independent reasons, each traceable.

**R1 — The frequency enum already collapses.**
`VISITS_PER_MONTH[ONE_TIME] = 1` and `VISITS_PER_MONTH[MONTHLY] = 1`
(`apps/marketplace/models.py:32-37`). `Offer.monthly_price` (`models.py:157-159`) therefore returns
the same number for a single Bauendreinigung and for a monthly maintenance visit — and
`deduction_35a` (`models.py:168-174`) then multiplies that by 12, projecting a yearly deduction for
work that happens once. The collapse is not a bug in arithmetic; it is the model being asked to mean
two things.

**R2 — The buyer's decision is a different decision.**
SPOT: pick a provider for one job; a bad choice costs one visit. RECURRING: pick a counterparty for
a year; a bad choice costs a Kündigungsfrist. That is why the Ausschreibung page lists references,
sustainability and personnel qualification as criteria alongside price, and why the same page warns
that price-led tenders create „starken Preisdruck"
(<https://pland.app/blog/ausschreibungen-in-der-gebaudereinigung-ein-leitfaden-fur-unternehmen>).

**R3 — RECURRING has an execution phase; SPOT does not.**
`RequestStatus` terminates at `AWARDED` (`apps/marketplace/models.py:40-45`). For recurring work,
`AWARDED` is the *beginning*: the object must become a `Site` with `Zone`s
(`apps/planning/models.py:21-87`), and a weekly plan must be regenerated for every week of the term
(`apps/planning/services.py:98-156`). Modelling that as a status on the same row means a request that
never closes.

**R4 — The pricing unit is different, and the unit is contractual.**
SPOT: `price_per_visit` (`apps/marketplace/models.py:132-134`). RECURRING: a monthly price against
a Leistungsverzeichnis, whose consumption is measured in `minutes_per_visit × visits_per_week` per
zone (`apps/planning/models.py:78-80`). The recurring price also has to survive an annual tariff step
— per pland.app the Lohntarifvertrag 2025/2026 raises LG 1 from 14,25 € to 15,00 € on 01.01.2026
(<https://pland.app/blog/tariflohn-2026-in-der-gebaudereinigung-das-sind-die-neuen-stundenlohne-ab-1-januar-2026>),
which is exactly the „Überprüfung bestehender Kundenverträge" step that source names for a tariff
rollover. A `price_per_visit` field has nowhere to record a price escalation clause.

**R5 — Substitution semantics differ.**
SPOT: if the provider cannot come, the job is cancelled and re-published. RECURRING: the object must
still be cleaned, so a *different* worker under the *same* contract covers it — which is a planning
operation (`Shift.worker`, `apps/planning/models.py:143-146`), not a marketplace operation. Trying to
express "same buyer, same object, different human" inside `Offer` breaks the
`UniqueConstraint(request, provider)` (`apps/marketplace/models.py:148-150`) immediately.

**R6 — The legal exposure differs.**
A one-off Umzugsreinigung by a `SELBSTSTAENDIG` provider with their own price is defensible
independence. The same person cleaning the same office every Tuesday at 06:00 for a year, on the
platform's schedule, is the textbook Scheinselbstständigkeit fact pattern. See
`rechtliche-grenzen.md` §3. The regime therefore changes which `LegalStatus` values
(`apps/accounts/enums.py:24-35`) may even appear on the provider side.

---

## 5. What each regime needs in the data model

### 5.1 SPOT — mostly present, five things missing (the contract seam landed 2026-08-29)

**Vorschlag:**

| Need | Status | Proposal |
|---|---|---|
| Expiry actually running | missing | `apps/marketplace/management/commands/expire_requests.py` calling `expire_requests()`; schedule it. Mirror `apps/jobs/management/commands/flush_indexing.py`. |
| A record that the job happened | missing | A contract is now generated from the won offer (`apps/marketplace/services.py:148-196`), but nothing records *execution*. `Assignment` — see `implementierung-django.md` §4.2 |
| An invoice / receipt | missing | §35a requires „Rechnung + Zahlung per Überweisung" (`apps/marketplace/services.py:87-91`), so a §35a-eligible award with no invoice entity is an unfulfillable promise |
| A review | missing | scoring has no quality axis at all today; `WEIGHTS` has five criteria, none of them past performance (`apps/marketplace/scoring.py:22-28`) |
| Real distance | missing | `geo.Locality.latitude/longitude` exist and are nullable (`apps/geo/models.py:30-31`); `_proximity_score` says verbatim it should be replaced „când `Locality` are lat/lon" (`apps/marketplace/scoring.py:106-110`) |

### 5.2 RECURRING — the whole spine is missing

**Vorschlag.** Minimum shape, expressed against what already exists:

| Entity | Purpose | Anchors to |
|---|---|---|
| `RecurringRequest` (or `ServiceRequest.regime = RECURRING`) | carries interval class, term, notice period, buyer-supplied criteria weights, tender documents | `taxonomy.ServiceCategory`, `geo.Locality` |
| `SiteVisit` | records the Objektbesichtigung: date, who attended, measured areas, room/toilet counts, photos | request + provider |
| `Leistungsverzeichnis` line items | area name, m², surface type, tasks, interval, quality level — the thing that becomes contractual | becomes `planning.Zone` rows on award |
| `Dauerauftrag` | the awarded standing order: term, monthly price, escalation clause, notice period, status ACTIVE/SUSPENDED/ENDED | `accounts.Account` (client) ↔ `accounts.Account` (provider), and `planning.Site` |
| `Leistungsnachweis` | per-visit proof of service sent to the customer (step 5 of the pland.app lifecycle) | `planning.Shift` |

**The award transition is where the two apps must meet.** On award of a recurring request the system
should, in one transaction: create `planning.Site` from the request's locality/address, create one
`planning.Zone` per Leistungsverzeichnis line (mapping interval → `visits_per_week` +
`allowed_weekdays`), create the `Dauerauftrag`, and leave the roster to
`planning.services.generate_week_plan` — which will refuse to schedule anyone without a signed
contract (`apps/planning/services.py:51-79`). That refusal is the feature, not an obstacle.

**Fakt:** none of this exists. `grep -rn "planning\|Site\|Zone\|Shift" apps/marketplace/` returns no
matches (verified 2026-08-29).

### 5.3 Interval → weekday mapping is lossy in one direction

**Fakt:** `planning.Zone` can only express "n visits per week on these weekdays"
(`apps/planning/models.py:61-63`), and `planning.services._visit_days` spreads them evenly across
allowed weekdays while dropping Sunday (`apps/planning/services.py:159-169`, `SUNDAY = 7`,
`services.py:29`).

**Vorschlag** — a mapping table for the award transition, with the two lossy cases marked:

| pland.app interval | `visits_per_week` | Note |
|---|---|---|
| täglich | 5 (Mo–Fr) or 6 (Mo–Sa) | Sunday needs §9 ArbZG treatment — see `rechtliche-grenzen.md` §6 |
| wöchentlich | 1 | |
| monatlich | — | **lossy**: needs a monthly recurrence `Zone` cannot express |
| vierteljährlich / halbjährlich | — | **lossy** |
| jährlich | — | **lossy** |

The long intervals are exactly where Grundreinigung, Fensterreinigung and Fassadenreinigung sit —
i.e. the profitable add-ons on a maintenance contract. Extending `Zone` with an interval unit
(`WEEK` / `MONTH` / `QUARTER` / `YEAR`) plus an anchor date is the smaller change; introducing a
separate `PeriodicTask` model is the cleaner one.

---

## 6. Decision procedure for an agent

1. **Which regime?** If the buyer is buying a *relationship* over time → RECURRING. If they are
   buying *one outcome* → SPOT. `Frequency.ONE_TIME` is not a reliable discriminator, because a
   `MONTHLY` request is also `VISITS_PER_MONTH = 1` (`apps/marketplace/models.py:32-37`).
2. **Does the feature create an obligation for a named natural person?** If yes → it belongs in
   `apps.planning`, behind a signed contract. Never in `apps.marketplace`.
3. **Does the feature move money?** → stop, read `implementierung-django.md` §7.
4. **Does it touch scoring?** → keep the breakdown visible. The module's stated premise is that „un
   scor opac e mai rău decât niciun scor" (`apps/marketplace/scoring.py:5-7`), and both the client
   and the rejected provider must be able to see why.
5. **Does it add a frequency or interval value?** → check all three vocabularies in §3.2 before
   adding a fourth.

---

## Quellen

Repository (read 2026-08-29, `/Users/Geronimo/Projects/Cleaning_SaaS`):

- `apps/marketplace/models.py`, `scoring.py`, `services.py`, `views.py`, `forms.py`
- `apps/planning/models.py`, `services.py`
- `apps/contracts/models.py`, `services.py`, `views.py`, `migrations/0002_seed_wage_floors.py`
- `apps/accounts/enums.py`, `models.py`, `profiles.py`, `visibility.py`
- `apps/taxonomy/models.py`, `migrations/0003_seed_categories.py`
- `apps/geo/models.py`
- `apps/dashboard/urls.py`, `apps/jobs/management/commands/flush_indexing.py`
- `tests/test_marketplace.py`
- `PLAN-FAZA-0.md`

pland.app (crawled 2026-08-29):

- <https://pland.app/arbeitslexikon/unterhaltsreinigung>
- <https://pland.app/arbeitslexikon/grundreinigung>
- <https://pland.app/arbeitslexikon/reinigungsintervall>
- <https://pland.app/arbeitslexikon/reinigungsplan>
- <https://pland.app/arbeitslexikon/glasreinigung>
- <https://pland.app/blog/ausschreibungen-in-der-gebaudereinigung-ein-leitfaden-fur-unternehmen>
- <https://pland.app/blog/unterhaltsreinigung-die-ultimative-checkliste>
- <https://pland.app/blog/tariflohn-2026-in-der-gebaudereinigung-das-sind-die-neuen-stundenlohne-ab-1-januar-2026>
- <https://pland.app/tutorials/beispiel-geschaftsplan>

Dossiers used as the index into the above:
`scratchpad/knowledge/lexikon-betrieb.md`, `blog-fachwissen.md`, `product-modules.md`,
`blog-tarif-arbeitsrecht.md`, `scratchpad/dossier/_verified-ground-truth.md`.
