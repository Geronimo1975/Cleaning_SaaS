---
name: gebaeudereinigung-domain
description: >
  Foundation skill for every task in /Users/Geronimo/Projects/Cleaning_SaaS, the Django 5.2 SaaS
  for the German Gebäudereinigung market (Hamburg / Schleswig-Holstein belt). Load it before
  naming anything, before adding a model or a URL, and before answering "what does X mean".
  It carries the product thesis (Marktplatz / Dispatch / Betrieb), the German-Romanian-English
  naming rules this repo already follows, the industry vocabulary (Objekt, Objektleiter, Einsatz,
  Unterhaltsreinigung, Grundreinigung, Reinigungsplan, Leistungsnachweis, DIN EN 13549, Innung,
  BG BAU), the five operating roles, and the map of which apps exist (accounts, geo, taxonomy,
  jobs, catalog, contracts, planning, devices, marketplace, dashboard) versus which do not
  (Kunde, Auftrag, Angebot, Rechnung, Abwesenheit, Ticket, Material). Skipping it produces English
  or Romanian names in German-facing data, invented DIN numbers and euro figures, and code
  assuming modules the repo lacks.
  It routes to gr-tarif-und-lohn, gr-zeiterfassung, gr-einsatzplanung, gr-auftrag-und-faktura,
  gr-marktplatz-dispatch and cleaning-saas-codebase.
metadata:
  author: Geronimo
  target: Cleaning_SaaS (Django 5.2, German Gebäudereinigung market)
  repo_root: /Users/Geronimo/Projects/Cleaning_SaaS
  sources: pland.app (crawled 2026-08-29, 237 pages) + repository code
---

# Gebäudereinigung — Domänen-Fundament

Stand: 2026-08-29. Repo verified that day against a live `.venv/bin/python manage.py check` (clean)
and `.venv/bin/python -m pytest -q` (190 tests, all passing). The repo is edited concurrently — the
test count drifted from 178 to 190 during a single writing session, so re-run rather than trusting
any count, and open the file before restating anything about the code.

Three kinds of statement appear in this skill and in every reference file. Never blur them:

| Marker | Meaning |
|---|---|
| **Fakt** | Traceable to a pland.app source URL or to a `file:line` in this repo. |
| **Vorschlag** | A design proposal for code that does not exist. Nothing depends on it yet. |
| **Ungeprüft** | Domain knowledge added because a builder needs it; the crawled sources do not cover it. Verify before it reaches code or customer-facing copy. |

Legal material here is reference, not legal advice. Tarif and statutory values change every year —
every table carries a Stand and a source.

---

## 1. The product thesis

The owner's own framing: **"Lieferando/courier agency + PlanD"**. Three layers:

| # | Layer | What it does | Repo status |
|---|---|---|---|
| 1 | **Marktplatz** | A customer posts a cleaning need; the platform intermediates. | `apps/marketplace` exists — `ServiceRequest` → `Offer` → award. |
| 2 | **Dispatch** | The platform allocates the work, partly automatically. | Partial. `apps/marketplace/scoring.py` ranks offers; `apps/planning/services.py` allocates shifts inside one company. |
| 3 | **Betrieb** | The full back office: Einsatzplanung, Zeiterfassung, Lohnabrechnung, Faktura, Qualität, Material, Geräte. | Mostly missing. Only Einsatzplanung + a thin Zeiterfassung + a contract layer exist. |

**Hard constraint written into the code, not a preference** — `apps/marketplace/models.py:10-14`:
there is **no automatic allocation** of work to a person. The system may only *suggest*
(`Invitation`, "Sugestie, NU repartizare", `apps/marketplace/models.py:177-181`). Auto-assigning
work to an individual meets the §7 SGB IV Scheinselbstständigkeit criteria and approaches
Arbeitnehmerüberlassung, which needs a licence from the Bundesagentur für Arbeit. Do not build a
feature that assigns a marketplace job to a provider without that provider's own act.

The same line is drawn in `apps/contracts/models.py:24-27`: `EngagementModel.TEMP_AGENCY` ("AUEG")
exists as a choice but `compliance_report()` (`apps/contracts/models.py:197`) always appends a
blocking issue for it (`apps/contracts/models.py:234-239`), surfaced through `compliance_issues()`
(`apps/contracts/models.py:193-195`).

---

## 2. Vocabulary discipline — preserve it exactly, never "fix" it

This repo mixes three languages on purpose. Verified against the live code:

| Surface | Language | Evidence |
|---|---|---|
| Public / indexable URL segments | **German** | `/jobs/`, `/job/<slug>/bewerben/` (`apps/jobs/urls.py:8-11`); `/reinigungskraft/`, `/profil/<slug>/` (`apps/accounts/public_urls.py:10-14`) |
| Dashboard URL segments | **Romanian** | `anunturi/`, `candidaturi/`, `contracte/`, `obiective/`, `planificare/`, `turele-mele/`, `pontaj/`, `calibrare/`, `echipamente/`, `cereri/`, `bursa/` (`apps/dashboard/urls.py:16-50`) |
| Code comments and docstrings | **Romanian** | e.g. `apps/planning/models.py:1-12`, `apps/marketplace/models.py:1-15` |
| Python identifiers, model/field names, URL `name=` | **English** | `ServiceRequest`, `hourly_wage`, `name="site_reinigungsplan"` |
| `verbose_name`, `TextChoices` labels, admin strings | **Romanian** | `verbose_name = "Obiectiv"` (`apps/planning/models.py:35`) |
| Seeded domain data and user-facing domain vocabulary | **German** | `ServiceCategory.name_de` (`apps/taxonomy/migrations/0003_seed_categories.py:15-70`); `Locality` seed; `ContractTemplate.language` default `"de"` (`apps/contracts/models.py:125`) |
| Documents produced for customer or worker | **German** | Reinigungsplan XLSX headers `Bereich / Ort · Leistung · Beschreibung · Reinigungsfrequenz …` (`apps/planning/reinigungsplan.py:18-26`) |

Rules that follow:

1. **Never translate one side into the other** unless explicitly asked.
2. A new dashboard route gets a **Romanian** segment and an **English** `name=`.
3. A new public route gets a **German** segment.
4. A new model gets **English** identifiers, a **Romanian** docstring, **Romanian** `verbose_name`,
   and any German label goes in a dedicated `*_de` field (the pattern of
   `ServiceCategory.name_de`, `apps/taxonomy/models.py:15`).
5. Domain nouns in seed data, exports and anything the German customer or worker reads are
   **German** and use the exact spelling in `references/glossar.md`. That file is the naming
   authority for the whole project — check it before inventing a term.
6. **Fakt, known defect:** the rendered public UI today mixes German and Romanian strings
   (`14,25–15,00 EUR / oră`, `<h2>Candidatură</h2>` next to `E-Mail-Adresse:`). `USE_I18N=True`
   but no catalogue is used and `templates/base.html` is bare. Do not describe the UI as
   consistently German; do not silently "fix" it either — it is a scoped task of its own.

---

## 3. What exists in code today, and what does not

Verified 2026-08-29 by reading the files. `INSTALLED_APPS` (`config/settings.py:27-36`):
`accounts, geo, taxonomy, jobs, catalog, contracts, planning, devices, marketplace, dashboard`.

### Exists

| App | Core models (file) | Notes |
|---|---|---|
| `apps/accounts` | `User`, `Account`, `ReservedSlug`, `Membership`, `AccountCapability`, `WorkerProfile`, `CompanyProfile`, `AccountService`, `ServiceArea`, `VerificationDocument`, `ConsentRecord` | Capability rows, never a `role` column (`apps/accounts/enums.py:11-21`). `LegalStatus` carries the German legal dimension (MINIJOB / SELBSTSTAENDIG / KLEINUNTERNEHMER / COMPANY, `enums.py:24-35`). **Never render an `Account` straight into a template** — go through the `AccountView` projection, which gates each field by a `Relation` level for DSGVO reasons (`apps/accounts/visibility.py:1-30`). Details: `cleaning-saas-codebase`. |
| `apps/geo` | `Region` (Bundesland), `Locality` | 30 seeded localities, Hamburg/SH belt. Free-text city is forbidden (`apps/geo/models.py:21-23`). |
| `apps/taxonomy` | `ServiceCategory` | 2 levels, 4 parents + 24 German leaves; `is_35a_eligible` per leaf (`models.py:23-26`). |
| `apps/jobs` | `JobPosting`, `Application`, `IndexingTask` | **Recruitment** job board (Stellenanzeige / Bewerbung) — a SUPPLY funnel, **not** the customer-order marketplace. |
| `apps/catalog` | `ProductCategory`, `Product`, `ProductImage` | Dealer catalogue for cleaning consumables, `is_published` defaults False. **Not** a Materialschrank. |
| `apps/contracts` | `WageFloor`, `MinijobThreshold`, `ContractTemplate`, `ContractDraft`, `ContractSignature` | Wage floors are time-versioned rows, never constants (`models.py:57-90`). Signature immutable (`models.py:278-281`). |
| `apps/planning` | `Site`, `Zone`, `ShiftPlan`, `Shift`, `ShiftEvent`, `ZoneCalibration` | `Site` = Objekt, `Zone` = Bereich. Greedy allocator with hard ArbZG constraints (`services.py:9-31`). `ShiftEvent` append-only (`models.py:217-220`). Reinigungsplan XLSX export (`reinigungsplan.py`). |
| `apps/devices` | `Device`, `TelemetrySession` | Telemetry is verification, **not** Zeiterfassung and **not** calibration input (`models.py:1-15`). Ingest at `POST /api/telemetry/`. |
| `apps/marketplace` | `ServiceRequest`, `Offer`, `Invitation` | Standardised request (type × area × frequency) so offers compare; multi-criteria scoring in `scoring.py`. |
| `apps/dashboard` | no models — `PANELS` data table | Panels are data keyed by `Capability` (`panels.py:1-7`). |

Also wired: `sitemap.xml` + `sitemap-<section>.xml` and `robots.txt` (`config/urls.py:15-26`,
`config/sitemaps.py`, `templates/robots.txt`).

### Does NOT exist — never assume it does

`Kunde`/`Customer` as an entity (a client is an `Account` with `Capability.CLIENT`) ·
`Auftrag` (order/contract as a commercial parent) · `Angebot` · `Auftragsbestätigung` ·
`Rechnung` and every invoice subtype (Abschlag, Teil, Schluss, Dauer, Storno, Gutschrift) ·
`Mahnwesen` · `Zahlung` · `Lieferschein` · `Arbeitsschein` · `Leistungsnachweis` ·
`Leistungsverzeichnis` · `Reinigungsplan` as a stored plan (only an XLSX export of `Zone` rows) ·
`Abwesenheit` / `Urlaubsantrag` / `Krankmeldung` / `Urlaubsanspruch` ·
`Vertretung` (substitution) · `Ticket` / `Reklamation` / `Qualitätscheck` ·
`Material` / `Materialschrank` / `Materialbestellung` / `Lieferant` ·
`Lohnart` / `Zuschlag` / `Lohngruppe` / payroll export ·
`Deckungsbeitrag` / `Umsatz-Übersicht` / `Kostenstelle` ·
Kunden-Portal · Chat · push notifications · GPS / geofence on time records ·
Wartungs- and Prüfintervalle on `Device` (no DGUV V3 field) ·
`Team` / Teameinsatz · recurring `Einsatz` series (`Zone.visits_per_week` is a weekly count,
not a recurrence rule) · mobile app of any kind.

If a task needs one of these, it is **new work**. Say so, and design it under the naming rules
above and the vocabulary in `references/glossar.md`.

---

## 4. Known gaps and traps to check before you touch adjacent code

| Trap | Where | What to do |
|---|---|---|
| `employmentType: "MINIJOB"` is emitted in JSON-LD but is **not** a schema.org value (valid: FULL_TIME, PART_TIME, CONTRACTOR, TEMPORARY, INTERN, VOLUNTEER, PER_DIEM, OTHER) | job detail JSON-LD, `apps/jobs` | Map `MINIJOB` → `PART_TIME` in the structured data while keeping the German label in the UI. |
| Wage-floor seed rows are explicitly marked `DE CONFIRMAT` (to be confirmed) | `apps/contracts/migrations/0002_seed_wage_floors.py:17,20,24` | Never quote those figures as fact. Route wage questions to `gr-tarif-und-lohn`. |
| Unknown city slug returns 200, not 404 | `/jobs/<city>/` | Known behaviour; fix only when asked. |
| `psycopg` / `dj-database-url` are imported when `DATABASE_URL` is set but are **not installed** | `config/settings.py:78-79` | Setting `DATABASE_URL` today raises ImportError. |
| No `.git` in the repo | repo root | Do not assume version control exists. |
| `Zone.category` must be a leaf; `ServiceRequest.category` too | `apps/planning/models.py:82-84`, `apps/marketplace/models.py:110-112` | Any new category FK needs the same `clean()`. |

---

## 5. Routing — which skill to load for which task

Load this skill first, then exactly the one that owns the task.

| Load | When the task touches |
|---|---|
| **gr-tarif-und-lohn** | Any euro amount paid to a worker: Lohngruppe 1–9, Tariflohn, Mindestlohn, Mindestlohntarifvertrag, Rahmentarifvertrag, Allgemeinverbindlichkeit, Zuschläge (Nacht/Sonntag/Feiertag/Erschwernis), non-cumulation of surcharges, Urlaubsanspruch and Urlaubsgeld, Entgeltfortzahlung, Minijob-/Midijob-Grenze, `WageFloor`, `MinijobThreshold`, `hourly_wage`, `salary_min/max`, payroll export. **Never quote a wage number from this skill.** |
| **gr-zeiterfassung** | Recording, correcting and releasing worked time: Zeiterfassung, Pontaj, Stundenzettel, Stempeluhr, check-in/check-out, Zeitenfreigabe, Soll/Ist, nachgetragene Zeiten, Pausen, Fahrzeiten, Geofence/GPS/Standortkontrolle, retention and Zoll/FKS export. Files: `apps/planning/attendance.py`, `Shift`/`ShiftEvent`, `/dashboard/pontaj/`, `/dashboard/turele-mele/`. |
| **gr-einsatzplanung** | Building the roster: Einsatzplanung, Dienstplan, Einsatzplaner, Schicht, Tour, Vertretung, offene Schicht, Teameinsatz, wiederkehrender Einsatz, Kapazität und Qualifikation, Reinigungsintervall as a recurrence, ArbZG constraints in the allocator, Zone calibration. Files: `apps/planning/services.py`, `calibration.py`, `/dashboard/planificare/`, `/dashboard/calibrare/`. |
| **gr-auftrag-und-faktura** | The commercial layer that does not exist yet: Kunde, Auftrag, Angebot, Auftragsbestätigung, Arbeitsschein, Leistungsnachweis, Rechnung and all subtypes, Mahnwesen, Zahlung, E-Rechnung/XRechnung/ZUGFeRD/EN 16931, GoBD, Kalkulation, Stundenverrechnungssatz, Leistungsverzeichnis, Deckungsbeitrag, Ausschreibung. |
| **gr-marktplatz-dispatch** | `apps/marketplace`: ServiceRequest, Offer, Invitation, scoring weights, award flow, §35a EStG deduction, the Scheinselbstständigkeit / AÜG boundary, provider matching and ranking. |
| **gr-vermittlungsmodell** | The operating model itself, modelled on inline-kurier.de: Genossenschaft/eG membership, who co-decides prices and dispatch rules, Betrieb vs natural person, Zentrale und Disposition, the four order archetypes (Ad-hoc-Einsatz, Festtour, Vorbestellung, Tourenreinigung), Kapazitätsklassen, Leistungsnachweis, Wartezeit, Auslage. Load it before answering "employees or contractors", "who sets the price", "can we auto-assign" or "one cleaner, several buildings". |
| **cleaning-saas-codebase** | How this repo is built rather than what the domain means: app layout, settings, migrations, `AccountRequiredMixin` / `CapabilityRequiredMixin`, `ActiveAccountMiddleware`, dashboard `PANELS`, templates, pytest layout and fixtures, seeding, running the dev server. |
| **this skill** | Naming a thing · translating a German industry term · deciding which app a new concept belongs to · describing an operating role · answering "what does the market expect here" · anything about cleaning types, intervals, norms, hygiene, safety, material, equipment · founding, Handwerksrolle, Innung, insurance, company account fields. |

When two skills overlap (e.g. a Zuschlag computed from a shift), load both: the domain skill for
the vocabulary, the specialist for the rule.

---

## 6. Reference files

| File | What it holds |
|---|---|
| `references/glossar.md` | The complete German glossary: Begriff · Bedeutung · why the software needs it · source. The naming authority for the project. |
| `references/reinigungsarten-normen-qualitaet.md` | Unterhalts-/Grund-/Glas-/Bauend-/Sonderreinigung; Reinigungsintervalle; Reinigungsplan and Arbeitsschein template columns; the Vier-Farben-System; every DIN/EN norm named and what it governs; hygiene standards; the 7 Arbeitssicherheit rules; health hazards; material and equipment lists; the surface → method → agent → caution table. |
| `references/rollen-und-prozesse.md` | The five operating roles (Geschäftsführung, Innendienst, Lohnbuchhaltung, Objektleiter, Servicekraft) — duties, what each sees, what each does daily — the full Objektleiter duty list, and the end-to-end operational workflows. |
| `references/marktreferenz-pland.md` | Competitor feature matrix: the 11 `/funktionen/` pages and the ~33 further Übersicht capabilities, each with German name, function, owning role and a Have/Partial/Missing column against this repo — plus a build order derived from adoption frequency in the (vendor-published) case studies. |
| `references/branche-und-gruendung.md` | Regulatory and market context of running a German cleaning company: Handwerksrolle and Anlage A vs B, Gewerbeanmeldung, HWK/IHK, BG BAU, Bundesinnungsverband, legal forms — and what of it the platform must capture on a company account. |

---

## 7. Five rules that must never be broken

1. **Never invent a number, date, euro amount, percentage, paragraph reference or German term.**
   If it is not in a reference file with a source, write "nicht belegt / not established from the
   sources" and stop.
2. **Never assume a missing module exists.** Check §3 above, then the file.
3. **Never translate the repo's language mix.** German public URLs, Romanian dashboard URLs and
   comments, English identifiers, German data.
4. **Never hard-code a legal or tarif value.** It becomes a time-versioned row with a
   `valid_from`, following `WageFloor` (`apps/contracts/models.py:57-90`).
5. **Never let the platform assign work to a person automatically.** Suggest only —
   `apps/marketplace/models.py:10-14`.
