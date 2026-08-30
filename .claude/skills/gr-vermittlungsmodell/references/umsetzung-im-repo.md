# Umsetzung im Repo — the inline model against the code that exists today

**Stand: 2026-08-29**, verified by opening the files. The repo is edited concurrently and is **not**
under version control — re-open before you rely on a line number.

Markers: **Fakt** (`file:line` given) · **Vorschlag** (design proposal, nothing depends on it) ·
**Ungeprüft**.

Rule for this file: **every existing thing carries its `file:line`; every proposal is labelled
Vorschlag.** No exceptions.

---

## 1. `apps/marketplace` exactly as coded

### 1.1 The module docstring is the design decision — read it first

**Fakt**, `apps/marketplace/models.py:1-15`. Two statements, in Romanian:

1. The request is **standardised**: „Fără tip × suprafață × frecvență, ofertele nu sunt
   comparabile, iar «bursa fără negociere» devine o licitație pe orb."
2. **„Nu există alocare automată.** Sistemul poate SUGERA prestatori, dar fiecare decide singur dacă
   ofertează și la ce preț. În Germania, un sistem care repartizează munca unei persoane fizice
   bifează criteriile §7 SGB IV (Scheinselbstständigkeit) și se apropie de Arbeitnehmerüberlassung —
   care cere licență de la Bundesagentur für Arbeit."

**These are not preferences.** Do not silently reverse either one.

### 1.2 `Frequency` and `VISITS_PER_MONTH`

**Fakt**, `apps/marketplace/models.py:25-37`.

```
Frequency = ONE_TIME | WEEKLY | BIWEEKLY | MONTHLY
VISITS_PER_MONTH = {ONE_TIME: 1, WEEKLY: 4.33, BIWEEKLY: 2.17, MONTHLY: 1}   # Decimal
```

**Known defect (Fakt).** `ONE_TIME` and `MONTHLY` both map to `Decimal("1")`, so `Offer.monthly_price`
(`models.py:157-159`) and the §35a yearly projection (`models.py:168-174`) are wrong for one-off
work — a single visit is projected as twelve. The two archetypes are conflated in one enum. In the
taxonomy of `references/auftragsarten.md` this is exactly the Ad-hoc/Dauerauftrag boundary showing
through the data model. → `gr-marktplatz-dispatch`, `references/zwei-vergabemodi.md`.

### 1.3 `RequestStatus` and `ServiceRequest`

**Fakt**, `apps/marketplace/models.py:40-112`.

`RequestStatus` = `DRAFT` / `OPEN` / `AWARDED` / `CANCELLED` / `EXPIRED` (`models.py:40-45`).
**It ends at AWARDED.** There is no ACTIVE, no term, no notice period, no Leistungsverzeichnis.

`ServiceRequest` fields, in file order:

| Field | Line | Note |
|---|---|---|
| `client` FK `accounts.Account`, CASCADE, `related_name="service_requests"` | 49-51 | |
| `category` FK `taxonomy.ServiceCategory`, **PROTECT** | 52-54 | leaf-only, enforced in `clean()` at 110-112 |
| `locality` FK `geo.Locality`, **PROTECT** | 55-57 | |
| `postal_code` CharField(5), blank | 58 | |
| `area_sqm` PositiveInteger, `MinValueValidator(1)` | 61-63 | „Suprafața de curățat" — the standardisation field |
| `rooms` PositiveSmallInteger, nullable | 64 | |
| `frequency` CharField, `Frequency.choices` | 65 | |
| `preferred_weekdays` CharField(13), blank | 66 | free-form string, no validator |
| `earliest_start` DateField | 67 | **the date every dated lookup should resolve against** |
| `title` (180) / `description` | 69-70 | |
| `has_pets` / `supplies_provided` Boolean | 71-74 | |
| `status` CharField, `db_index=True` | 76-78 | |
| `offers_close_at` DateTime | 79 | „După acest moment nu se mai ofertează" |
| `published_at` DateTime, nullable | 80 | |
| `awarded_offer` **OneToOne** to `Offer`, SET_NULL, `related_name="won_request"` | 81-83 | |
| `created_at` | 84 | |

`Meta`: ordering `-created_at`, `Index(fields=("status", "locality", "category"))` (`models.py:86-90`).

Properties: `is_open` = `status == OPEN and offers_close_at > now()` (95-97) ·
`visits_per_month` (99-101) · `is_35a_eligible` = category flag **and** client is
`EntityType.INDIVIDUAL` (103-108).

### 1.4 `Offer`

**Fakt**, `apps/marketplace/models.py:115-174`. Docstring: „O ofertă, nu o negociere. Prestatorul își
pune prețul o dată; clientul alege pe mai multe criterii, nu neapărat cel mai mic preț."
(`models.py:123-126`)

`OfferStatus` = `SUBMITTED` / `WITHDRAWN` / `WON` / `LOST` (115-119).

Fields: `request` FK CASCADE (128) · `provider` FK `Account` (129-131) · `price_per_visit` Decimal(8,2)
min 0.01 (132-134) · `estimated_minutes` PositiveSmallInteger (135) · `includes_supplies` (136) ·
`earliest_start` (137) · `message` (138) · `status` (140-142) · timestamps (143-144).

`Meta`: **ordered by `price_per_visit`** (147) and `UniqueConstraint(request, provider)` named
`uniq_offer_per_provider` (149) — one offer per provider per request, enforced in the DB.

Properties: `monthly_price` = price × visits_per_month (157-159) · **`implied_hourly`** = price × 60 /
minutes, documented as „singura bază reală de comparație între oferte" (161-166) ·
`deduction_35a` = 20 % of the yearly labour figure capped at 4.000 € per § 35a Abs. 2 EStG (168-174).

### 1.5 `Invitation` — the suggestion, and why it is not an assignment

**Fakt**, `apps/marketplace/models.py:177-200`. Docstring: „**Sugestie** către un prestator, **NU
repartizare.** Prestatorul decide singur dacă ofertează și la ce preț" (178-181).

Fields: `request` (183-185) · `provider` (186-188) · `score` Decimal(5,2) (189) ·
**`reasons` JSONField** (190) · `seen_at` nullable (191) · `created_at` (192).
`Meta`: ordering `-score`, `UniqueConstraint(request, provider)` named `uniq_invitation` (194-200).

`reasons` is the field that makes the eG model implementable: it already stores the per-criterion
breakdown as JSON, so a suggestion carries its own justification.

### 1.6 `scoring.py`

**Fakt**, `apps/marketplace/scoring.py`.

Docstring premise (1-11): „clientul nu alege cel mai mic preț, ci cea mai bună potrivire. Dar un scor
**opac e mai rău decât niciun scor** — dacă nu se vede DE CE o ofertă e prima, clientul nu are motive
să aibă încredere în ordine, iar prestatorul respins nu are ce corecta." Normalisation is **inside
one request's offer set**: „un scor nu are sens absolut, ci doar relativ la ce a primit clientul."

```
WEIGHTS = {price 0.30, verification 0.25, experience 0.20, availability 0.15, proximity 0.10}
```
(`scoring.py:22-28`) with a comment recording that `price` was lowered from 0.35 because an
unverified provider was tying with a verified one with ten years' experience.

| Function | Line | What it does |
|---|---|---|
| `ScoredOffer` dataclass with `percent` and `explain()` | 39-55 | `explain()` returns (label, %, "pondere N %") triples |
| `score_offers(request, offers=None)` | 58-91 | Loads `SUBMITTED` offers, computes min/max of `implied_hourly`, builds the five-criterion breakdown, sorts by `(-total, implied_hourly, pk)` — deterministic tie-break |
| `_price_score` | 94-98 | Cheapest 1, dearest 0; all equal → all 1 |
| `_verification_score` | 101-102 | `provider.verification_level / 3` |
| `_proximity_score` | 105-115 | Same locality 1.0 · declared `areas` 0.7 · else 0.2. Docstring says it is a placeholder until `Locality` has lat/lon |
| `_experience_score` | 118-133 | Individuals: `years_experience / 10` capped at 1. Companies: 0.4 base + 0.4 liability insurance + 0.2 HWK |
| `_availability_score` | 136-142 | Linear decay over 28 days from `request.earliest_start` |
| `_notes` | 145-157 | Signals shown but **not** scored: supplies mismatch, §35a estimate |
| `suggest_providers(request, limit=10)` | 160-190 | Candidate set = `published() ∩ providers() ∩ services__category ∩ areas__locality`, excluding the client. Ranks on verification/proximity/experience only (no price — nobody has bid yet). Docstring repeats the §7 SGB IV reasoning |

### 1.7 `services.py` — the lifecycle

**Fakt**, `apps/marketplace/services.py`.

| Service | Line | Guard / effect |
|---|---|---|
| `publish_request(request, invite=True)` | 16-33 | DRAFT only; `offers_close_at` must be future; sets OPEN + `published_at`; then `get_or_create`s an `Invitation` per suggested provider with the reasons stringified |
| `submit_offer(request, provider, **data)` | 36-49 | Requires `request.is_open`, provider ≠ client, `provider.is_provider`; `update_or_create` resets status to SUBMITTED |
| `withdraw_offer` | 52-60 | Owner only, SUBMITTED only |
| `award_warnings(request, offer)` | 63-97 | **Informs, never blocks** — deliberately: „platforma nu poate ști dacă prestatorul și-a înregistrat între timp activitatea". Warns on `LegalStatus.UNDECLARED`, on Minijob-in-a-household (client becomes the employer, Haushaltsscheck), on §35a bank-payment requirement, on `verification_level == 0` |
| `award_offer(request, offer, actor)` | 100-119 | **`request.client_id != actor.pk` → error.** The client awards; the platform does not |
| `CONTRACT_TYPE_BY_STATUS` | 125-130 | SELBSTSTAENDIG/KLEINUNTERNEHMER/COMPANY → WERKVERTRAG; MINIJOB → MINIJOB |
| `contract_type_for(offer)` | 133-145 | `UNDECLARED` raises — no contract can be generated, „orice altceva ar fi muncă nedeclarată" |
| `create_contract_from_offer` | 148-196 | Client only, AWARDED only. Derives `hours_per_month` from `estimated_minutes × visits_per_month / 60` and `hourly_wage` from `implied_hourly`. **Nobody retypes anything** |
| `cancel_request` | 199-208 | An AWARDED request cannot be cancelled |
| `expire_requests(now=None)` | 211-216 | Bulk OPEN→EXPIRED past `offers_close_at`. **No scheduler calls it** |

**Known defect (Fakt).** The idempotency key in `create_contract_from_offer` is
`(employer, worker, start_date, workplace)` with `contract_type__isnull=False`
(`services.py:172-176`) — two genuinely different requests for the same worker, same locality, same
start date collapse onto one contract. Under a Tour model (§4.1) this gets worse, not better, since
one operator legitimately serves several Objekte on one day.

### 1.8 `forms.py` and `views.py`

**Fakt**. `ServiceRequestForm` (`apps/marketplace/forms.py:10-34`) narrows `category` to
`ScopedLeaf.queryset()` and `locality` to `active_localities()`, and rejects a past
`offers_close_at`.

`OfferForm.clean` (`forms.py:51-68`) is **the pattern to copy for every dated threshold**: it
computes the implied hourly rate and resolves
`WageFloor.current(WageFloor.Kind.GEBAEUDE, earliest_start)` — **at the start date, not at "now"** —
and adds a form error naming the floor and its as-of date. Its own comment says why: „Pragul NU se
scrie în cod."

Views (`apps/marketplace/views.py`): `MyRequestsView` (26-33), `request_create_view` (36-46),
`request_detail_view` (49-…) which dispatches on a POST `action` of `publish` / `cancel` / `award` /
`contract` and renders `score_offers` output with the legal warnings attached **next to the award
button** (97-100 onward). Dashboard routes: `cereri/`, `cereri/noua/`, `cereri/<pk>/`, `bursa/`,
`bursa/<pk>/oferta/` (`apps/dashboard/urls.py:46-50`).

---

## 2. What of the inline model is already expressed

**Fakt** in every row.

| inline element | Already in the repo | Where |
|---|---|---|
| **Vermittlung, not Zuweisung** | `Invitation` is documented as a suggestion; `suggest_providers` returns a ranked list; the provider must act (`submit_offer`) and the **client** awards | `models.py:177-181` · `scoring.py:160-190` · `services.py:36-49,100-119` |
| **The scoring breakdown is visible to both sides** — inline's own weakness (an opaque „Vermittlung per Funk") already fixed here | `ScoredOffer.breakdown` + `explain()`; `Invitation.reasons` JSON | `scoring.py:39-55` · `models.py:190` |
| **A standardised order spec so offers compare** (inline's „Sendung": preset / own measurements / pick the vehicle) | `area_sqm` + `frequency` + `earliest_start`, mandatory; `implied_hourly` as the stated comparison basis | `models.py:61-67,161-166` |
| **Rate rows resolved at a date, never hardcoded** (inline injects `Stadt-TS`, `OVER-CO2` … from a rate table) | `WageFloor.current(kind, on)` / `MinijobThreshold.current(on)` | `apps/contracts/models.py:83-89,107-113` |
| **The executing legal entity decides the commercial regime** (inline's `order.firm`) | Partially: `LegalStatus` drives the contract type, which drives the engagement model and the compliance severity | `apps/accounts/enums.py:24-35` · `apps/marketplace/services.py:125-145` · `apps/contracts/models.py:37-42,197-249` |
| **Two-sided account model without a role column** | Capability **rows**, `revoke()` is a soft flag | `apps/accounts/models.py:143-160,229-243` |
| **Proof-of-performance as a record** (thin version) | `Shift.checked_in_at` / `checked_out_at` / `actual_minutes` / `worker_note`, append-only `ShiftEvent` | `apps/planning/models.py:154-160,188-220` |
| **A recurring execution engine** (inline's Festtour, but internal) | `Site` → `Zone` → `ShiftPlan` → `Shift`, hard ArbZG constraints, `unmet_demand` with reasons | `apps/planning/models.py:21-185` · `apps/planning/services.py:82-156` |
| **Capacity comes only from a signed commitment** | `build_capacities` reads **only** `DraftStatus.SIGNED` contracts | `apps/planning/services.py:51-79` |
| **An offer must not open the client's data** — stricter than inline, which discloses the courier's identity on the proof document | Relation rises to ENGAGED only on `status="WON"`, with a comment explaining that a mere bid would let anyone harvest addresses | `apps/accounts/visibility.py:106-112`, projection at `115-147` |
| **Verification as a trust asset** (inline's licence claim, without the number) | `VerificationLevel` 0–3 and `VerificationDocument` incl. `POLIZEILICHES`, private storage, `expires_at`, `delete_after` | `apps/accounts/enums.py:46-50` · `apps/accounts/compliance.py:7-41` |

---

## 3. What is missing — the gap list

**Fakt** in every row (each is verified absent).

| Missing | Evidence | Consequence |
|---|---|---|
| **Any link `marketplace` → `planning`** | `apps/marketplace` never imports `apps.planning`; nothing creates a `Site`/`Zone`/`ShiftPlan` from an awarded request | An awarded recurring request never becomes a roster. Largest structural gap |
| **A RECURRING regime at all** | `RequestStatus` ends at `AWARDED` (`models.py:40-45`) | No ACTIVE, no term, no Kündigungsfrist, no Leistungsverzeichnis |
| **A Tour across Objekte** | `Zone.site` is a single FK (`planning/models.py:48`); `Shift.zone` is a single FK (`planning/models.py:142`); the allocator has no travel time and starts every day at `DAY_START = time(7, 0)` (`planning/services.py:30,143-151`) | Verteilerrunde / Tourenreinigung is inexpressible |
| **A capability/equipment class** | `AccountService` binds an Account to a leaf category (`accounts/profiles.py:68-83`) — that is *what* it offers, not *what it can staff* | No qualification gate on bidding; a Höhenzugang job and a Büroreinigung job filter identically |
| **eG membership** | Nothing. `accounts.Membership` (`accounts/models.py:202-226`) is User↔Account with `MembershipRole` OWNER/ADMIN/MEMBER — a **different concept with a colliding name** | No shares, no voting weight, no Betrieb-only constraint |
| **A ratified dispatch policy** | `WEIGHTS` is a module constant (`scoring.py:22-28`) | A member vote cannot change the allocation rules without a deploy; an old ranking cannot be reproduced |
| **A Leistungsnachweis** | `Shift.worker_note` is a 300-char CharField (`planning/models.py:160`); no photos, no checklist, no counter-signature | The product of an unsupervised service has no evidence artefact |
| **An access-failure state** | `ShiftStatus.MISSED` exists but `mark_missed` is an **employer** action (`planning/models.py:137`, `planning/attendance.py:169`) | No worker-initiated "I was there, I could not get in", no reason code, no photo |
| **Key management** | Nothing anywhere | The largest single liability exposure in the industry is unmodelled |
| **A quality/history axis in scoring** | `WEIGHTS` has five criteria, none of them past performance (`scoring.py:22-28`) | Continuity — the cleaning tiebreaker — cannot win |
| **A scheduler for `expire_requests`** | Defined at `services.py:211-216`; no management command | OPEN requests sit past their deadline in production |
| **Geocoding** | `_proximity_score` is a 3-step locality approximation (`scoring.py:105-115`) | Zone/route work has no distance |
| **`preferred_weekdays` has no validator** | CharField(13), blank (`models.py:66`) — compare `Zone.clean()`, which validates ISO weekday indices 1–7 (`planning/models.py:82-87`) | Two weekday encodings, one validated, one not |

---

## 4. Vorschlag — the new entities, and how they attach

**Everything in §4 is a Vorschlag.** None of it exists. Names follow the repo convention: English
identifiers, German domain vocabulary in `verbose_name` and help text, Romanian docstrings and
comments, Romanian dashboard URL segments.

Before writing any of it: decide SPOT or RECURRING (`gr-marktplatz-dispatch`), and never let a
marketplace code path create an obligation for a natural person.

### 4.1 `Tour` + `TourStop` — attaches to `planning`

**Where it belongs: `apps/planning`, not `apps/marketplace`.** A Tour distributes work already
contracted; it does not broker anything.

```
Tour       — account FK (the member firm), name, date or recurrence, planned_start,
             status, notes
TourStop   — tour FK, zone FK (planning.Zone), sequence PositiveSmallInteger,
             planned_minutes, travel_minutes_from_previous
             UniqueConstraint(tour, sequence)
Shift      — + tour FK (nullable), + tour_stop FK (nullable)
```

Rules the design must hold:

1. **The ArbZG ceiling is evaluated over the whole Tour**, not per stop. `_fits()`
   (`apps/planning/services.py:82-95`) currently checks `MAX_DAILY_MINUTES` per worker per day — that
   already works for a Tour, but `travel_minutes` must count toward it.
2. **`_fits()`'s locality check must move up to the Tour.** Today a worker is rejected if the Site's
   locality is not in their `areas` (`services.py:85-86`). A Tour legitimately crosses localities;
   the check becomes "every stop's locality is served".
3. **Stop duration is an Objekt attribute, not a constant.** `Zone.minutes_per_visit` already is one
   (`planning/models.py:58`) and `ZoneCalibration` already corrects it from actuals
   (`planning/models.py:235-292`) — reuse both, do not add a second estimate.
4. **Unmet demand keeps its shape.** `ShiftPlan.unmet_demand` is a JSON list of
   `{zone, site, date, minutes, reasons}` (`planning/services.py:134-140`); a Tour that does not fit
   reports the same way, with the stop that broke it named.
5. **Do not turn this into a TSP.** It is shift packing under a working-time constraint.

### 4.2 `CapabilityClass` — attaches to `accounts` and to `planning.Zone`

```
CapabilityClass        — code (K1…K8), name_de, description,
                         required_documents (M2M to a DocumentType-like table),
                         required_device_kinds, max_height_m, flags
                         (may_hold_key, requires_vetting, hygiene_regime)
AccountCapabilityClass — account FK, capability_class FK, valid_until
                         UniqueConstraint(account, capability_class)
Zone                   — + required_class FK (nullable during migration)
ServiceRequest         — + required_class FK (nullable)
```

How it attaches without disturbing what exists:

- **Do not extend `Capability`** (`apps/accounts/enums.py:11-21`). That enum answers "what may this
  account *do* on the platform" (WORKER / PROVIDER / SUPPLIER / CLIENT / EMPLOYER). A capability
  class answers "what work may it *take*". Different question, separate table — and the house rule
  is capability **rows**, never a widening column.
- **Mirror the `AccountService` pattern** (`apps/accounts/profiles.py:68-83`): a join table with a
  `UniqueConstraint`, validated in `clean()`.
- **Join to devices where possible.** `Device.kind` already enumerates VACUUM / SCRUBBER / POLISHER /
  STEAM / OTHER and `Device.site` records where a machine sits (`apps/devices/models.py:24-29,48-51`).
  A class requiring a scrubber can be evidenced, not merely claimed.
- **Add it as a third hard filter in `suggest_providers`**, alongside the existing
  `services__category` and `areas__locality` intersections (`apps/marketplace/scoring.py:170-178`) —
  an **exclusion**, not a score term. A firm that cannot staff the class must not see the request.
- **Never hardcode the class list in Python.** Reference data in this repo is seeded by **data
  migrations only** (the pattern used for wage floors and contract templates).

### 4.3 `CooperativeMembership` + `DispatchPolicy` — the eG layer

**Name it `CooperativeMembership`, not `Membership`.** `accounts.Membership` already exists as
User↔Account (`apps/accounts/models.py:202-226`) and a collision here would be a lasting source of
bugs.

```
CooperativeMembership — account FK (OneToOne), joined_on, shares PositiveInteger,
                        voting_weight, status (APPLIED/ACTIVE/SUSPENDED/RESIGNED),
                        left_on
                        clean(): account.entity_type must be COMPANY
DispatchPolicy        — weights JSONField, valid_from, valid_to,
                        resolution_reference (Generalversammlung date + item),
                        rationale
                        classmethod current(on=None)  # copy WageFloor.current
Resolution            — (optional) title, decided_on, body, carried Boolean
```

Attachment points:

- `CooperativeMembership.account` → `accounts.Account`. The `clean()` constraint is the whole point:
  **only a Betrieb may be a member.** A `Capability.WORKER` account (a natural person,
  `apps/accounts/enums.py:17`) may be a marketplace provider and an employee of a member firm, but
  never a member in the governance sense. Enforce it in `clean()` **and** with a DB constraint.
- `DispatchPolicy.current(on)` copies `WageFloor.current` verbatim — `valid_from__lte=on` filtered by
  `valid_to__isnull=True | valid_to__gte=on` (`apps/contracts/models.py:83-89`). `score_offers`
  resolves the policy at `request.published_at` (`apps/marketplace/models.py:80`), **not** at "now",
  so an old ranking reproduces. Store the resolved policy id into `Invitation.reasons`
  (`models.py:190`) so a member can see which rulebook ranked them.
- `WEIGHTS` (`apps/marketplace/scoring.py:22-28`) becomes the **fallback default** when no policy row
  covers the date — keep it, do not delete it, and log when the fallback is used.

Two traps:

1. **Do not let a policy weight become a penalty for refusal.** A fairness-rotation term is a lawful
   suggestion weight; the same term becomes an instruction the moment declining lowers a member's
   future score. That is a §7 SGB IV Weisungsrecht indicator in algorithmic clothing.
   **Ungeprüft** where a court would draw the line — do not build it without advice.
2. **A ratified price ceiling is not a ratified wage.** `PlatformTariff` (a further Vorschlag)
   validates **against** `WageFloor`, which the vote can never lower — the branch minimum is
   allgemeinverbindlich under § 7 AEntG. → `gr-tarif-und-lohn`.

### 4.4 `Leistungsnachweis` — attaches to `planning.Shift`

```
ServiceRecord (verbose_name „Leistungsnachweis")
  shift        FK planning.Shift (or FK TourStop when a Tour exists)
  created_at, created_by (Account)
  items        → ServiceRecordItem: leistungsposition, done Boolean, note
  photos       → ServiceRecordPhoto: image, kind (VORHER/NACHHER/MANGEL),
                 taken_at, delete_after
  special_circumstances  TextField   # inline's „Besondere Umstände" — keep the name
  not_performed_reason   CharField
  confirmed_by / confirmed_at        # Objektverantwortlicher, where present
```

Design rules, each traceable:

- **Attach to `Shift`, never to `Offer` or `ServiceRequest`.** The record is about work performed by
  an employee under a signed contract; the marketplace layer must not own it.
- **Do not duplicate the clock.** `Shift.checked_in_at` / `checked_out_at` / `actual_minutes`
  (`apps/planning/models.py:157-159`) is the legal record; the Leistungsnachweis references it and
  never re-states it. → `gr-zeiterfassung`.
- **Append-only, corrections are new rows.** Follow `ShiftEvent.save()`, which raises
  `RuntimeError("Evenimentele de pontaj sunt imutabile.")` when `self.pk` is set
  (`apps/planning/models.py:217-220`), and `ConsentRecord.save()`, identical
  (`apps/accounts/compliance.py:67-70`).
- **Photos need a retention field from day one.** `VerificationDocument` already carries
  `expires_at` and `delete_after` (`apps/accounts/compliance.py:35-36`) — copy that, and default it.
- **Name the role, not the person, by default.** A daily named record of one employee at one place is
  performance monitoring: § 26 BDSG, § 87 Abs. 1 Nr. 6 BetrVG. See
  `references/zentrale-und-disposition.md` §5.2. **Ungeprüft**, verify before it ships.
- **Free, always-on, per visit** — the opposite of inline's 59,00 € premium add-on.

Two companion entities the same design needs:

- **`AccessFailure`** (Zutrittsversagen): shift/stop FK, reason code (KEY / ALARM / OCCUPIED /
  NOT_PREPARED / HAZARD), photo, timestamp, notified parties. Fills the gap named in §3 — today only
  the employer can mark `MISSED` (`apps/planning/attendance.py:169`).
- **`KeyIssue`** (Schlüsselprotokoll): key number, Schließanlagen-ID, holder Account, issued_at /
  returned_at, two signatures. Modelled on CertiChain's scanned-at-every-handover chain, with an
  entirely different risk profile — see `references/zentrale-und-disposition.md` §5.3.

### 4.5 The `order.firm` idea — which entity executes

**Fakt** (inline, from the wizard markup on https://inline-kurier.de/bestellung and its sub-forms):
the same wizard shell serves **three online lines** — Kurierfahrt (incl. `/kurierfahrt/dokumentiert`),
Overnight and Transporthilfe; **XXL is explicitly excluded** („eine Online-Bestellung nicht möglich",
/xxl/bestellung). Across those pages a single state variable `order.firm` indexes both the product
configuration (`order.products.data.products[order.firm]`) and the customer address book
(`customers[order.firm]`) — i.e. the wizard carries "which firm is this order for" as first-class
state.

**Ungeprüft.** *What* `order.firm` decides — price table, T&Cs, insurance ceiling, dispatch number,
invoice sender — is **not published**; only the variable and its two uses are visible in the markup.
Do not cite the list as sourced.

**Vorschlag.** `ServiceRequest` has no such field. It needs one — the executing member firm — because
in Gebäudereinigung **the employer of the cleaner must be unambiguous per order.** Today that is
implicit in `Offer.provider` and becomes explicit only when a contract is created
(`apps/marketplace/services.py:148-196`). Making it a field on the awarded order, not an inference,
is the precondition for per-firm T&Cs, per-firm liability sums and per-firm invoicing.

---

## 5. Before you write any of this

1. **Read the two module docstrings first** — `apps/marketplace/models.py:1-15` and
   `apps/marketplace/scoring.py:1-11`. The design decisions are stated there and must not be
   silently reversed.
2. **Decide SPOT or RECURRING.** If the answer is "both", the feature is wrong.
   → `gr-marktplatz-dispatch`, `references/zwei-vergabemodi.md`.
3. **Does it create an obligation for a natural person?** Then it needs a signed `ContractDraft` and
   it belongs in `apps.planning`.
4. **Is it a rule the members would vote on?** Then it is a dated row, not a constant.
5. **Does it touch an `Account` in a template?** Wrap it in `AccountView`
   (`apps/accounts/visibility.py:115-147`) — a raw `Account` in a template is a DSGVO defect, not a
   style issue. New fields are invisible until added to `FIELD_POLICY`.
6. **Reference data goes in a data migration**, never in Python constants.
7. **Language split:** German public/domain vocabulary, Romanian dashboard URLs and comments, English
   identifiers (`apps/dashboard/urls.py:32-50`).
8. **Run `.venv/bin/python -m pytest -q`** before and after. `manage.py check` must stay clean.

---

## Quellen

- Repo, read 2026-08-29: `apps/marketplace/models.py` · `scoring.py` · `services.py` · `forms.py` ·
  `views.py`; `apps/planning/models.py` · `services.py` · `attendance.py`;
  `apps/accounts/models.py` · `enums.py` · `profiles.py` · `compliance.py` · `visibility.py`;
  `apps/contracts/models.py`; `apps/taxonomy/models.py`; `apps/devices/models.py`;
  `apps/dashboard/urls.py`.
- https://inline-kurier.de/bestellung (and `/bestellung/overnight`, `/bestellung/transporthilfe`,
  `/bestellung/kurierfahrt/dokumentiert`) — `order.firm` as a state variable in the wizard markup.
  https://inline-kurier.de/xxl/bestellung — XXL is not orderable online.
- Sibling skills for anything this file deliberately does not restate: `gr-marktplatz-dispatch`,
  `gr-einsatzplanung`, `gr-tarif-und-lohn`, `gr-zeiterfassung`, `cleaning-saas-codebase`.
