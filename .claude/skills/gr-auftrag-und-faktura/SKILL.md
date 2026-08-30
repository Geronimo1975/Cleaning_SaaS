---
name: gr-auftrag-und-faktura
description: >
  Use for ANY commercial-layer work in /Users/Geronimo/Projects/Cleaning_SaaS — the customer,
  order, quoting and invoicing layer that does not exist in the repo yet. Trigger on Kunde,
  Auftrag, Angebot, Rechnung, Rechnungsposition, Faktura, Rechnungsnummer, Abschlagsrechnung,
  Akontorechnung, Teilrechnung, Schlussrechnung, Abschlussrechnung, Dauerrechnung,
  Stornorechnung, Gutschrift, Leistungsempfänger, Rechnungsempfänger, Leitweg-ID, E-Rechnung,
  XRechnung, ZUGFeRD, EN 16931, GoBD, Zahlungsziel, Mahnung, Mahnstufe, Verzugszinsen,
  Basiszinssatz, Kalkulation, Stundenverrechnungssatz, Leistungsverzeichnis, Raumliste,
  Deckungsbeitrag, Ausschreibung, Preisblatt — and on phrasings like "add invoicing", "bill
  the customer", "create an offer", "price a cleaning job", "margin per contract", "dunning".
  Also applies to a proposed apps/billing, and to any dashboard route for clients, offers,
  invoices or payments. Skipping it produces code that edits issued invoices, merges
  Rechnungs- and Leistungsempfänger into one field, hard-codes an unsupported e-invoicing
  date, duplicates planning.Site or marketplace.Offer, or breaks the repo's language split.
metadata:
  author: Geronimo
  target: Cleaning_SaaS (Django 5.2, German Gebäudereinigung market)
  repo_root: /Users/Geronimo/Projects/Cleaning_SaaS
  sources: pland.app (crawled 2026-08-29, 237 pages) + repository code
---

# Auftrag und Faktura — the commercial layer

**Stand: 2026-08-29.** Legal and tariff values in this skill are reference material for
building software, not legal or tax advice. Every one carries a date and a source; re-check
before shipping.

## 0. The one thing to know first

**Fakt (repo).** There is no commercial layer in this codebase. Verified 2026-08-29 by
reading every `models.py` under `apps/`:

```
apps/accounts   apps/geo   apps/taxonomy   apps/jobs   apps/catalog
apps/contracts  apps/planning  apps/devices  apps/marketplace  apps/dashboard
```
(`config/settings.py:13-37`)

`grep -rniE "invoice|rechnung|faktura|angebot|auftrag|mahnung|dunning"` over `*.py` and
`*.html` returns **only** template prose inside
`apps/contracts/migrations/0003_seed_templates.py:89-104` (a Werkvertrag body containing
"Die Abrechnung erfolgt monatlich per Rechnung"). No `Customer`, no `Invoice`, no
`Payment`, no number sequence, no VAT logic, no PDF or XML renderer exists.

So: everything in `references/implementierung-django.md` is a **Vorschlag**. Everything in
the other four reference files is either a **Fakt** with a source URL, or marked
**Ungeprüft**.

## 1. Statement types — always visible

| Marker | Meaning |
|---|---|
| **Fakt** | Sourced from pland.app (URL given) or from repo code (`file:line` given) |
| **Vorschlag** | Design proposal for code that does not exist |
| **Ungeprüft** | Domain knowledge added here that the crawled sources do not cover — verify against the statute or the BMF before it reaches code or customer-facing copy |

Never silently promote an **Ungeprüft** row to a **Fakt**. Never invent a euro amount, a
percentage, a date or a paragraph reference.

## 2. Rules that must never be broken

1. **An issued invoice is immutable.** Corrections are a *new linked document* with its own
   number and negative amounts (Stornorechnung / Gutschrift), never an `UPDATE` and never a
   `DELETE`. Source for the mechanism: <https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen>.
   The "you may not edit it" framing itself is **Ungeprüft** (GoBD practice) — see
   `references/rechnungsarten.md` §7.
2. **Rechnungsempfänger ≠ Leistungsempfänger.** Two separate FKs, never one. The
   Leistungsempfänger *must* be printed on the invoice whenever the customer wants to deduct
   Vorsteuer; the Rechnungsempfänger may live on the envelope only — but not for an invoice
   sent electronically. Source:
   <https://pland.app/blog/rechnungsempfanger-und-leistungsempfanger-definition-und-unterschiede>.
3. **Invoice numbers are gapless, sequential and per-sequence.** Allocate under
   `select_for_update()` inside the same transaction that finalises the document. Never
   derive a number from `pk`, never renumber, never reuse a number from a deleted draft.
4. **Never hard-code a tax rate, a Zahlungsziel, a Basiszinssatz, an m²/h performance value
   or a price band.** All of them are dated, tenant-editable rows — the repo already does
   this for wage floors (`apps/contracts/models.py:57-89`, `WageFloor.current()`); follow
   that exact pattern.
5. **Do not encode an e-invoicing obligation date from these sources.** The crawled pages
   contradict each other and are demonstrably behind (see §4 below and
   `references/e-rechnung-pflicht.md`). Model the obligation as configuration, not as a
   constant.
6. **Reuse the existing vocabulary. Do not build a second one.** See §3.
7. **Preserve the repo's language split** (`_verified-ground-truth.md`, confirmed against
   `apps/dashboard/urls.py` and `apps/marketplace/models.py`):
   public URL segments German · dashboard URL segments Romanian · comments and docstrings
   Romanian · Python identifiers, model and field names, URL `name=` English · seeded domain
   data and user-facing domain vocabulary German.
   Consequence for this layer: the model is `Invoice`, the German term `Rechnung` lives in
   `verbose_name`, the route is `/dashboard/facturi/` with `name="invoices"`.
8. **Line amounts must be allowed to be negative.** No `MinValueValidator(0)` on
   `InvoiceLine.quantity`, `unit_price`, `line_net`, `line_tax` or `line_gross` — a Storno
   line is negative by construction.
9. **Money is `DecimalField`.** The repo is consistent about this
   (`apps/catalog/models.py:52-55`, `apps/marketplace/models.py:132-134`). Never float.

## 3. What already exists — attach to it, do not duplicate

**Fakt (repo), all read 2026-08-29.**

| Existing thing | Where | What the commercial layer must do with it |
|---|---|---|
| `Account` (the central economic entity; `entity_type`, `legal_status`, `vat_id`, `tax_number`, `legal_name`, `registration_number`, address, `locality` FK) | `apps/accounts/models.py:79-177` | This **is** the tenant *and* the counterparty. A `Customer` is a relationship between two Accounts, not a fresh party table. `vat_id`/`tax_number` (`:96-97`) already hold USt-IdNr. and Steuernummer. |
| `EntityType` = INDIVIDUAL \| COMPANY | `apps/accounts/enums.py:4-8` | Drives B2C vs B2B default interest (5 pp vs 9 pp) and the B2C duty to state consequences explicitly. Do **not** add a second `kunde_typ` field. |
| `LegalStatus` incl. `KLEINUNTERNEHMER` (§19 UStG) and `COMPANY` | `apps/accounts/enums.py:24-35` | Already carries the Kleinunternehmer flag the e-invoicing exemption needs. Reuse it. |
| `Capability` = WORKER / PROVIDER / SUPPLIER / CLIENT / EMPLOYER, as rows in `AccountCapability`, never a `role` column | `apps/accounts/enums.py:11-22`, `apps/accounts/models.py:229-243` | Invoicing permissions and dashboard panels key off capabilities, not off a new role field. |
| `Membership` (User↔Account, roles OWNER/ADMIN/MEMBER, `can_manage`) | `apps/accounts/models.py:202-226` | The authorisation gate for issuing/cancelling a document. |
| `Locality` / `Region` (30 seeded SH/HH localities) | `apps/geo/models.py:4-44` | Invoice and site addresses; also the regional axis of price bands. |
| `ServiceCategory`, max depth 2, leaves only, `is_35a_eligible` | `apps/taxonomy/models.py:5-42` | The Leistungsart on a quote/invoice line. `clean()` at `:40-42` enforces the two-level rule; `Zone.clean()` (`apps/planning/models.py:82-87`) and `ServiceRequest.clean()` (`apps/marketplace/models.py:110-112`) both enforce leaf-only — an invoice line must do the same. |
| **`planning.Site`** — "Obiectivul de curățat: o clădire, o reședință, un sediu" | `apps/planning/models.py:21-39` | **This is the `Objekt`.** Do not create a second one. |
| **`planning.Zone`** — area with `area_sqm`, `minutes_per_visit`, `visits_per_week`, `allowed_weekdays`, `category` FK | `apps/planning/models.py:42-87` | This is the Raumliste / Leistungsverzeichnis row already. A quote calculation reads `area_sqm` + `minutes_per_visit`; an invoice line can reference a Zone. |
| `Shift` with `billable_minutes` (actual if clocked, else planned) and `variance_minutes` | `apps/planning/models.py:140-185` | The billing basis for a *dynamic* invoice position. `billable_minutes` (`:175-178`) is exactly the "Lohnzeit vs. Soll-Zeit" distinction PlanD documents. |
| `ShiftEvent`, append-only, `save()` raises on re-save | `apps/planning/models.py:188-220` | The immutability pattern to copy for issued invoices and payments. |
| `ContractSignature`, immutable, `document_sha256` | `apps/contracts/models.py:256-281` | The freeze-the-rendered-document pattern to copy for invoice PDFs/XML. |
| `ContractTemplate` + `ContractDraft.rendered_body` / `body_sha256` — template text is copied at generation so later template edits cannot rewrite signed documents | `apps/contracts/models.py:116-171` | Do exactly this for invoice header/footer texts and dunning texts. |
| `WageFloor.current(kind, on)` / `MinijobThreshold.current(on)` — dated, editable statutory values, not constants | `apps/contracts/models.py:57-113` | The template for `TaxRate`, `Basiszinssatz`, `PaymentTerm`, `PriceBand`. |
| `marketplace.Offer` — `price_per_visit`, `estimated_minutes`, `implied_hourly`, `monthly_price`, `deduction_35a` (20 % capped 4.000 €, §35a Abs. 2 EStG) | `apps/marketplace/models.py:122-174` | **A marketplace Offer is not an Angebot.** It is a bid on a standardised `ServiceRequest`. A won Offer is the *input* to an `Order`; the Angebot document is a separate, richer artefact. |
| `marketplace.Frequency` + `VISITS_PER_MONTH` = 1 / 4.33 / 2.17 / 1 | `apps/marketplace/models.py:25-37` | Reuse verbatim for recurring billing arithmetic. Do not invent a second frequency enum. |
| `catalog.Product` with `price_net`, `vat_rate` (default 19.00), `unit`, `price_gross` | `apps/catalog/models.py:35-91` | Material lines on an invoice. `price_gross` at `:89-91` is the existing net→gross convention. |
| `devices.Device` + telemetry ingest at `POST /api/telemetry/` | `apps/devices/models.py`, `config/urls.py:28` | Telemetry is a source of VERIFICATION and discrepancy detection, explicitly **not** a calibration source and not a replacement for Zeiterfassung (module docstring, `apps/devices/models.py:1-15`); treating it as a billing basis is therefore a **Vorschlag**-level decision this skill rejects. |
| `dashboard.PANELS` — dashboard defined as data keyed by `Capability` | `apps/dashboard/panels.py:14-34` (the `Panel` dataclass) and `:45-90` (the `PANELS` list) | Add invoicing panels as rows here; never as `if` branches in a template. |

**Fakt (repo).** No commercial dashboard route exists.
`apps/dashboard/urls.py` currently routes: `anunturi`, `candidaturi`, `contracte`,
`obiective`, `planificare`, `turele-mele`, `pontaj`, `calibrare`, `echipamente`, `cereri`,
`bursa`. Romanian segments, English `name=`.

## 4. The legal constraints that shape the design

Each row is a **Fakt** from the source named. Precision matters: what is *not* on the pages
is marked as such, and `references/` says so at length.

| Constraint | What it forces in code | Source |
|---|---|---|
| Fälligkeit arises on **Abnahme der Arbeit** (§ 641 Abs. 1 S. 1 BGB) | The due-date anchor is an acceptance event, not `created_at` | <https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-wie-und-wann-schreibe-ich-am-besten-zahlungserinnerungen-und-mahnungen> |
| **30 days** for the customer to pay or object; § 286 BGB makes the 30-day period binding; "Mahnungen dienen nicht mehr der Fristsetzung" | Default → dunning is date-driven, not reminder-driven. A Mahnung is a communication, not a precondition | same |
| Verzugszinsen **9 pp over Basiszinssatz** (Geschäftskunden) / **5 pp over Basissatz** (Privatkunden) | Rate depends on `Account.entity_type`; Basiszinssatz is a dated table | same |
| Privatkunden **must be expressly informed** of deadlines and consequences of default | A B2C-only mandatory text block on the document | same |
| Gerichtliches Mahnverfahren may start **immediately** at Zahlungsverzug | Terminal state reachable without traversing Mahnstufen | same |
| Mahnkosten are borne by the Schuldner | `dunning_fee` per stage, tenant-configured | same |
| A **Gutschrift is legally equated with an invoice** → same Pflichtangaben; § 14 UStG treats it as an "umgekehrte Rechnung" | Same validator runs on a credit note | <https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden> |
| The **Leistungsempfänger must be named on the invoice** for the customer's Vorsteuerabzug | Non-null FK, always rendered | <https://pland.app/blog/rechnungsempfanger-und-leistungsempfanger-definition-und-unterschiede> |
| Abschlag: warranty starts only at **Abnahme der Gesamtleistung**. Teil: warranty starts **immediately** on part-payment | Document type drives a warranty clock, not just a label | <https://pland.app/arbeitslexikon/abschlagsrechnung> · <https://pland.app/arbeitslexikon/teilrechnung> |
| Schlussrechnung must **list and offset** every Abschlags-/Teilzahlung and show the Restbetrag | M2M to settled predecessors + derived residual | <https://pland.app/arbeitslexikon/schlussrechnung> |
| E-Rechnung is **structured data**, not a PDF | XML generation path, not a PDF renderer | <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen> |
| Public-sector e-invoicing applies to invoices to **öffentliche Auftraggeber über 1.000 Euro**; **Leitweg-ID** is required | Per-customer `leitweg_id`, `is_public_authority` flag | same |
| **XRechnung** = KoSIT/IT-Planungsrat standard implementing **EN 16931** and **Richtlinie 2014/55/EU**; for the Bundesverwaltung its current version is in principle mandatory; **ZUGFeRD 2.2.0 Profil XRECHNUNG** is an accepted alternative if it meets EN 16931, the **E-RechV** and the platform's Nutzungsbedingungen | `format` + `profile` + `standard_version` fields; validation before send | <https://pland.app/blog/gebaudereinigung-xrechnung-pflicht-ab-2025> |
| E-Rechnungen must be archived **digital und revisionssicher für mindestens zehn Jahre** (GoBD) | `retention_until = issue_date + 10 years`, write-once storage | <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen> |
| **The B2B timetable in the sources is unreliable.** Two pages dated 2025 say "spätestens ab 2025" / "ab dem 1. Januar 2025 … alle Unternehmen"; neither gives receipt-vs-issue phases, transition periods or turnover thresholds | Do not hard-code a date. Ship a dated, editable obligation table | <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen> · <https://pland.app/arbeitslexikon/e-rechnung> |
| **§ 13b UStG reverse charge is not mentioned anywhere in 237 crawled pages** yet applies to Gebäudereinigungsleistungen supplied to a business that itself supplies cleaning | A `reverse_charge` flag that suppresses the tax amount and forces the "Steuerschuldnerschaft des Leistungsempfängers" note. **Ungeprüft — verify against § 13b UStG before implementing** | absence, verified by grep across `scratchpad/txt/` |

## 5. Route to the references

| File | Use it when | Contains |
|---|---|---|
| `references/rechnungsarten.md` | Choosing or validating a document type; writing the Pflichtangaben validator | Abschlags-, Teil-, Schluss-, Abschluss-, Dauer-, Storno-, Gutschrift: definition, timing vs. performance, warranty effect, verbatim field lists per type, the Rechnungs-/Leistungsempfänger split, the § 14 UStG list (marked **Ungeprüft**) and the three contradictions in the sources |
| `references/e-rechnung-pflicht.md` | Anything touching XRechnung, ZUGFeRD, EN 16931, Leitweg-ID, archiving | Every date the sources give and why each is unreliable; format matrix; what is *not* an e-invoice; GoBD retention; a dated-configuration design instead of constants |
| `references/kalkulation-und-deckungsbeitrag.md` | Pricing a job, building a quote calculator, per-Auftrag margin | Every cost component named by the sources; both published price tables verbatim (including the 3–5× contradiction between them); the Grundreinigung 5-step method; the Deckungsbeitrag formula and worked example; Angebot/LV/Raumliste document set; Ausschreibung components and platforms; the explicit gap where m²/h Leistungswerte would be |
| `references/mahnwesen.md` | Overdue invoices, reminders, interest | Stage ladder, § 286 BGB 30-day rule, § 641 BGB due-date anchor, 9 pp / 5 pp interest, mandatory Mahnung content, what the software must track and what the sources leave open (stage intervals, day-count convention) |
| `references/implementierung-django.md` | Writing the actual app | **Whole file is Vorschlag.** Models, enums, state machines, gapless numbering under lock, immutability guards, attachment points to the existing apps, dashboard routes in the repo's language convention, test list |

## 6. Working method for this layer

1. Read the relevant reference file before writing code. They carry the verbatim field lists;
   paraphrasing them is how Pflichtangaben get lost.
2. Before asserting anything about the repo, open the file. Two apps (`apps/marketplace`,
   `apps/devices`) landed *after* the dossiers were written; more may follow.
3. Run `/Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python manage.py check` and
   `.venv/bin/python -m pytest -q` after every model change. Baseline: 190 tests passing
   (re-run `pytest` to confirm the current count before trusting this number — the repo is
   edited concurrently).
4. When a value is not in the sources, write "nicht belegt / not established from the
   sources" and make it configuration. Do not fill the gap with a plausible number.
5. Every table you add anywhere must carry its Stand and its source URL.
