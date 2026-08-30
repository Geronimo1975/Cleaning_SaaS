---
name: gr-vermittlungsmodell
description: >
  Governs the OPERATING MODEL of /Users/Geronimo/Projects/Cleaning_SaaS: a Genossenschaft (eG) of
  independent Betriebe plus a central Vermittlung, modelled on inline-kurier.de. Load it for
  Genossenschaft, eG, Mitglied, Mitgliedschaft, Selbstständigkeit, Scheinselbstständigkeit,
  §7 SGB IV, AÜG, Vermittlung, Disposition, Disponent, Zentrale, Auftragsannahme, Festtour, Tour,
  Verteilerrunde, Vorbestellung, Ad-hoc-Einsatz, Sofortreinigung, Kapazitätsklasse,
  Leistungsnachweis, dokumentierte Leistung, Wartezeit, Auslage — and for plain phrasings like
  "how do we organise the cleaners", "employees or contractors", "who sets the price", "one
  cleaner several buildings", "route for the morning", "can we auto-assign". It OVERRIDES the
  default employee-vs-gig assumption: the operators are member firms who co-decide prices and
  dispatch rules, so allocation is brokerage between businesses, never instruction to a person.
metadata:
  author: Geronimo
  target: Cleaning_SaaS (Django 5.2, German Gebäudereinigung market)
  repo_root: /Users/Geronimo/Projects/Cleaning_SaaS
  sources: inline-kurier.de (crawled 2026-08-29, 36 pages) + repository code
---

# gr-vermittlungsmodell — the operating model

**Stand: 2026-08-29.** Every inline claim carries a source URL; every repo claim carries a
`file:line` that was correct at that date. The repo is edited concurrently and is **not** under
version control — re-open a file before you rely on a line number.

Legal reasoning in this skill and its references is **reference material for building software,
not legal advice.** A Fachanwalt / Steuerberater decides the real case. Stated once, here.

| Marker | Meaning |
|---|---|
| **Fakt** | Sourced from inline-kurier.de (URL given) or from repo code (`file:line` given) |
| **Vorschlag** | A design proposal for code that does not exist yet |
| **Ungeprüft** | Domain knowledge the crawled sources do not establish — verify before it reaches code or customer copy |

An unmarked speculation in this area is a defect, not a shortcut.

---

## 1. The operating thesis

The business is run like **inline-kurier.de** — a Hamburg courier cooperative — except the work
is cleaning, not delivery.

**Fakt**, https://inline-kurier.de/uber-uns:

> „Unser Leitspruch lautet ‚Von Fahrern für Fahrer!'. Wir sind als selbstständige Kuriere in einer
> Genossenschaft organisiert. Das bedeutet echte Mitbestimmung, wie zum Beispiel bei der
> **Preisgestaltung**, der **Funk- und Tourenvermittlung** sowie der **jährlichen Budgetplanung**."

and

> „In der inline Kurier eG sind **wirtschaftlich unabhängig arbeitende Kurierunternehmer**
> zusammengeschlossen"

Two layers (**Fakt**, /uber-uns): a **membership layer** (inline Kurier eG, GnR 1186, AG Hamburg),
which „übernimmt **schrittweise** die Funktionen der bisherigen inline Kurierdienst GmbH", and an
**operating layer** (inline Kurierdienst GmbH, HRB 65662, „eine 100%ige Tochtergesellschaft der eG
…, die weiterhin als **Beteiligungsgesellschaft** bestehen wird"). **Ungeprüft:** which entity
actually signs the customer contract and carries the risk is **nowhere published**. The Impressum
names the **eG** as Diensteanbieter, the Datenschutzerklärung names **all four entities** as one
Verantwortlicher block, and the corpus contains no Vertragspartner clause at all (the „AAB inline
Kurier" is a download link only; the PDF was not crawled). Treat "eG governs / GmbH contracts" as a
design proposal (§2, last row), not as inline's documented split.

**Why this resolves the blocker.** Centrally dispatching work to nominally self-employed
individuals meets the §7 SGB IV Scheinselbstständigkeit criteria and approaches
Arbeitnehmerüberlassung — the repo already says so in code, `apps/marketplace/models.py:10-14`
(**Fakt**). The cooperative answer is that the operators are not instructed subordinates: they
**co-author the rules** (price list, allocation logic, annual budget) and then a Disponent executes
those rules fast. Note the exact wording of the second quote — members decide *„Details in der
Funk- und Tourenvermittlung"*, i.e. the **rules of dispatch, not the individual allocations**
(**Fakt**, /uber-uns). That split is the whole mechanism.

**The transplant is not free.** inline's independence story is credible because a courier owns the
vehicle, serves many principals, and the job **ends**. A cleaner returns weekly for years, holds a
key, and works alone inside a customer's building. Read §4 before assuming otherwise.

### The three consequences for the data model

| # | Consequence | Today | What it needs |
|---|---|---|---|
| 1 | **Membership is an entity, and its holder is a Betrieb — never a natural person with a mop.** | No `Mitgliedschaft` model exists. `Account` + `AccountCapability` rows (`apps/accounts/models.py:229-243`) are the closest thing (**Fakt**). | **Vorschlag** `Membership`-in-the-eG-sense: share, join date, voting weight, Betrieb-only constraint. Do **not** reuse `accounts.Membership` (`models.py:202-226`) — that is User↔Account, a different concept with an unfortunate name. |
| 2 | **The dispatch rules must be data, versioned, dated and ratified — not constants in code.** | `WEIGHTS` is a module-level dict, `apps/marketplace/scoring.py:22-28` (**Fakt**). A member vote cannot change it without a deploy. | **Vorschlag** `DispatchPolicy` rows with `valid_from` + the resolution that adopted them, resolved at request-publication time; `scoring.py` reads the row. Same shape as `contracts.WageFloor.current()` (`apps/contracts/models.py:83-89`). |
| 3 | **Price is member-ratified ABOVE a statutory floor; the floor itself is never votable.** | `WageFloor` / `MinijobThreshold` already are effective-dated rows (`apps/contracts/models.py:57-113`) and `OfferForm.clean` resolves the floor at `earliest_start` (`apps/marketplace/forms.py:51-68`) (**Fakt**). | **Vorschlag** a `PlatformTariff` that members vote, validated against `WageFloor` at the shift date. The allgemeinverbindlicher Mindestlohntarifvertrag (§ 7 AEntG) binds non-tarifgebundene firms too — a vote cannot lower it. |

---

## 2. What this changes versus the employee model

The default assumption a coding agent brings — "the platform employs cleaners and rosters them" —
is wrong for the marketplace half and right for the planning half. This table is the dividing line.

| Question | Default employee model | eG / Vermittlungsmodell | Repo consequence |
|---|---|---|---|
| **Who sets the price?** | The platform sets a rate card; the worker takes it. | Members **ratify** the tariff (**Fakt**, /uber-uns "Preisgestaltung"); the individual member firm still quotes its own `Offer`. | `Offer.price_per_visit` stays provider-set (`apps/marketplace/models.py:132-134`). A platform rate card is a **Vorschlag** ceiling/floor band, never an imposed price. |
| **Who bears the Mindestlohn duty?** | The platform, as employer. | The **member Betrieb**, as employer of its own staff. The platform only checks and warns. | `ContractDraft.compliance_report()` blocks employment contracts below the floor, only warns on a Werkvertrag (`apps/contracts/models.py:197-249`) — that asymmetry is correct and must survive. |
| **Who owes Zeiterfassung?** | The platform. | The **member Betrieb** for its employees. The platform stores the record on the Betrieb's behalf (Art. 28 DSGVO Auftragsverarbeitung — **Vorschlag**). | `Shift.checked_in_at/checked_out_at` + append-only `ShiftEvent` (`apps/planning/models.py:154-220`) already model this per `account`. See `gr-zeiterfassung`. |
| **Who may be auto-assigned?** | Anyone on the roster. | **Nobody** across the membership boundary. A member firm's own employee may be auto-assigned *inside* that firm, under a signed contract. | Two allocation regimes, no shared code path: `Invitation` is a suggestion (`apps/marketplace/models.py:177-181`); `generate_week_plan` assigns, but capacity comes **only** from `DraftStatus.SIGNED` contracts (`apps/planning/services.py:51-79`). |
| **What is a "shift"?** | A slot the platform owns. | A slot **inside a member firm's plan**, scoped by `ShiftPlan.account`. The eG never owns a shift. | `ShiftPlan.account` FK + `uniq_plan_per_week` (`apps/planning/models.py:96-111`). Nothing in `apps/marketplace` may create a `Shift`. |
| **Who holds the customer contract?** | The platform. | The operating GmbH (or the member firm). The eG governs; it does not sign the Reinigungsvertrag. **Vorschlag** — inline's ownership split is sourced (**Fakt**, /uber-uns) but *who signs* is not published there. | The order must carry the executing legal entity. inline's order wizard does carry a `order.firm` state variable (**Fakt**, markup on https://inline-kurier.de/bestellung); what it decides is **Ungeprüft**. `ServiceRequest` has no such field today. |
| **Who bears liability and insurance?** | The platform. | The member Betrieb: Betriebshaftpflicht, Schlüsselversicherung, Bearbeitungsschäden. | `CompanyProfile.has_liability_insurance` / `insurance_valid_until` / `hwk_registered` (`apps/accounts/profiles.py:50-54`) — thin, but the right place. |
| **What does "Vergabe" mean?** | Assignment. | **Vermittlung** — brokerage between two businesses. inline's own vocabulary is consistently *Vermittlung*, never *Zuweisung* (**Fakt**, https://inline-kurier.de/kurierfahrten, process step 2). | `award_offer` is the client's act (`apps/marketplace/services.py:100-119`). Never rename it to something that reads as assignment. |

---

## 3. The order taxonomy

**Fakt.** inline runs four order archetypes on the Kurier line, all described on one page,
https://inline-kurier.de/kurierfahrten. The cleaning names are **Vorschlag** unless marked.

| inline | Cleaning name | Timing promise | How it is planned | Repo home today |
|---|---|---|---|---|
| **Kurierfahrt** — „Wir fahren sofort nach Auftragseingang los" | **Ad-hoc-Einsatz / Sofortreinigung** (Wasserschaden, Bauendreinigung, Glasbruch, Krankheits-Vertretung) | inline: „oft in weniger als 60 Minuten", „im Schnitt 45 Minuten nach Vermittlung". Cleaning: a **day-part window**, never a minute SLA — the operator must bring material and often a key. | Dispatched on receipt | `marketplace.ServiceRequest` with `Frequency.ONE_TIME` (`apps/marketplace/models.py:25-37`) |
| **Vorbestellung** — „wir kommen genau zur vereinbarten Zeit"; „einmalig, regelmäßig oder im Rahmen einer laufenden Tour" | **Termingebundener Einsatz** (Fensterreinigung 2×/Jahr, Grundreinigung zum Quartalsende) | A committed date/window | Same engine as ad-hoc, plus a fixed slot | `ServiceRequest.earliest_start` only — no committed-window field exists |
| **Festtour** — „fest in Ihre Abläufe eingebunden", „Feste Tourenpläne und definierte Zeitfenster", „Tag für Tag" | **Dauerauftrag / Unterhaltsreinigung** on a Leistungsverzeichnis | Recurring, indefinite term, notice period | Roster, not dispatch | `planning.Site` → `Zone` → `ShiftPlan` → `Shift` (`apps/planning/models.py:21-185`). `RequestStatus` has no ACTIVE state (`models.py:40-45`) |
| **Verteilerrunde** — „Eine Tour für mehrere Zustellungen", „Abholung und Zustellung in geplanter Reihenfolge", „täglich, wöchentlich oder nach Bedarf" | **Tourenreinigung** — one operator, several Objekte in sequence, e.g. Treppenhausreinigung | Per round, on a cadence | Route + shift packing under ArbZG | **Nothing.** `Zone` belongs to exactly one `Site` (`apps/planning/models.py:48`); a `Shift` points at one `Zone` (`models.py:142`). A tour across Objekte cannot be expressed. |

Add-on services (**Fakt**, /kurierfahrten and /bestellung), with their cleaning counterparts:

| inline add-on | Cleaning counterpart | Note |
|---|---|---|
| **Dokumentierte Zustellung** — 59,00 € netto surcharge, photos + protocol, names the „beauftragten selbständigen Kurier" | **Leistungsnachweis** per Einsatz | Same data structure, **opposite commercial position**: free and always-on, because the Hausverwaltung expects it and the work is unsupervised |
| **Ladehilfen** — „Helfer (Personen)" × „ca. Dauer (Minuten)", „Abgerechnet wird in **15-Minuten-Schritten**" | **Helferstunden / Zusatzkräfte** | The closest 1:1 element on the whole site. Copy the two form fields and the quarter-hour rule verbatim |
| **Geldauslage** — banded fee, frei / 4 / 8 / 15 € up to 300 € | **Materialauslage** (Seife, Papier, Streusalz) | Same mechanism, wrong ceiling: consumables recur monthly and run higher |
| **Zeit für Service / Wartezeit** — free allowance per stop, then per started 5 or 15 min | **Mehraufwand / Wartezeit** | Needs approval-in-the-loop: unlike a courier, nobody is standing there watching |
| **2. Anfahrt / Adressklärung** — a price line, never a described process | **Vergebliche Anfahrt**: Objekt verschlossen, Schlüssel passt nicht, Alarm scharf | Must be a first-class order **state**, not just a fee. See `references/zentrale-und-disposition.md` |

Detail, sourcing and lifecycle states: `references/auftragsarten.md`.

---

## 4. Where the courier analogy breaks — say this out loud

**A cleaner holds a key and works unsupervised inside a customer's building for months. A courier
does not.** That single asymmetry drives four things the courier model has no field for:

1. **Trust and vetting.** Führungszeugnis for sensitive Objekte, identity, insurance. The repo has
   `DocumentType.POLIZEILICHES` (`apps/accounts/compliance.py:9`) — **Fakt** — and nothing that
   requires it per Objektklasse.
2. **Liability.** Loss of a Generalschlüssel can cost a whole Schließanlage. inline's analogue —
   insurance up to 5.000 € Warenwert on the Kurier line (**Fakt**, /kurierfahrten) — is the wrong
   shape entirely: cover belongs to the Betrieb and the Objekt, not to the order.
3. **Access control.** Schlüsselnummer, Ausgabe/Rückgabe, Alarmcode, Zutrittsprotokoll. inline's
   CertiChain SafeBag chain-of-custody (**Fakt**, /dokumentierte-zustellung-overnight) is the
   mechanism to steal; the risk model and retention period are different.
4. **Continuity beats proximity.** For a courier the optimum is the nearest free unit; for cleaning
   it is *the same crew as last week*. The customer will ask for a named person — and the more the
   customer names the person, the more the arrangement reads as Arbeitnehmerüberlassung. Both
   pressures are real and they pull against each other.

A fifth break, economic: inline peaked at 250 Kuriere and **bis zu 2500 Aufträgen pro Tag**
(**Fakt**, /uber-uns). A cleaning crew does 1–4 Objekte a day. Any throughput assumption copied
from inline is wrong by roughly two orders of magnitude.

---

## 5. Reference routing

| If the task is about … | Read |
|---|---|
| The cooperative itself: what members co-decide, Verein→eG transition, the corporate tree with register numbers, headcount and fleet, „Von Fahrern für Fahrer", and what a Reinigungs-eG must replicate for the model to hold | `references/inline-prinzip-genossenschaft.md` |
| The four order archetypes + add-ons: sourced definitions, cleaning equivalents, timing promises, planning mode, lifecycle states, and why the per-Objekt shift model cannot express a Tour | `references/auftragsarten.md` |
| Capacity and eligibility: inline's seven vehicle classes verbatim, and the cleaning capability/equipment class model (qualification, machines, height access, DDD, Glas, key authorisation) | `references/kapazitaets-und-klassenmodell.md` |
| The central office: intake channels and hours, Disponenten, reachability, tracking, documented proof, failed access and escalation, Reklamation intake, what must be logged | `references/zentrale-und-disposition.md` |
| Concrete Django work: `ServiceRequest` / `Offer` / `Invitation` / `scoring.py` as coded, what already expresses the model, and the proposed `Tour`, `CapabilityClass`, `CooperativeMembership`, `Leistungsnachweis` entities and how they attach | `references/umsetzung-im-repo.md` |

### Sibling skills — use them, do not restate them

| Skill | Owns |
|---|---|
| `gr-marktplatz-dispatch` | The `apps/marketplace` layer itself: two Vergabemodi, scoring internals, the award→contract seam, the legal boundary of the marketplace |
| `gr-einsatzplanung` | `apps/planning`: Site/Zone/ShiftPlan/Shift, the greedy allocator, ArbZG constraints, calibration, Vertretung |
| `gr-tarif-und-lohn` | Every euro amount: Lohngruppen, Mindestlohn, AVE, Zuschläge, Minijob thresholds, payroll export |
| `gebaeudereinigung-domain` | Vocabulary, roles, service types, norms, the app map |
| `cleaning-saas-codebase` | The eight house rules: no `role` column, `AccountView` projection, slug claiming, 410-not-delete, language split |

---

## 6. Was hier NICHT steht

- **Löhne, Tariflohn, Zuschläge, Minijob-Grenzen, Lohnabrechnung.** Nothing in this skill sets or
  quotes a wage. → **`gr-tarif-und-lohn`**. If you need a floor in code, resolve
  `WageFloor.current(kind, on=<shift date>)` (`apps/contracts/models.py:83-89`), never a literal.
- **Zeiterfassung.** Check-in/check-out, corrections, breaks, rounding, geofencing, retention,
  Zoll/FKS export. → **`gr-zeiterfassung`**. This skill only says *who owes* the duty (the member
  Betrieb), not how the record is built.
- **Rechnungen, Angebotsdokumente, Mahnwesen, E-Rechnung.** → `gr-auftrag-und-faktura`.
- **The Satzung, the share amount, the Eintrittsgeld, the take rate, the Provisionsmodell.**
  inline publishes **none** of these (**Fakt**, verified absent across the 36-page corpus). Do not
  invent a figure; the gap list is in `references/inline-prinzip-genossenschaft.md`.

## 7. Before you write code in this layer

1. Ask **which regime**: Vermittlung between businesses (marketplace) or roster inside one business
   (planning). If the answer is "both", the feature is wrong.
2. Ask **does this create an obligation for a natural person?** If yes it needs a signed
   `ContractDraft` and belongs in `apps.planning`, never in `apps.marketplace`.
3. Ask **is this a rule the members would vote on?** If yes it is a dated row, not a constant.
4. Preserve the language split: German public/domain vocabulary, Romanian dashboard URL segments and
   comments, English identifiers (`/dashboard/cereri/`, `/dashboard/bursa/`,
   `apps/dashboard/urls.py:46-50`).
5. Run `.venv/bin/python -m pytest -q` before and after.
