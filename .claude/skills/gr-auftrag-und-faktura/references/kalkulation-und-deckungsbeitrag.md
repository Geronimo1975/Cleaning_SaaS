# Kalkulation und Deckungsbeitrag — pricing a cleaning job and measuring whether it pays

**Covers:** every cost component the sources name, the published price tables verbatim, the
Grundreinigung and Angebot calculation methods, the Leistungsverzeichnis / Raumliste document
set, the Deckungsbeitrag formula and its worked example, how tender (Ausschreibung) pricing
differs — and an explicit map of the numbers that are **not** in the sources.

**Stand: 2026-08-29.** Sources are pland.app pages crawled 2026-08-29 (raw text under
`scratchpad/txt/`) and the dossiers `knowledge/blog-faktura.md`,
`knowledge/lexikon-betrieb.md`, `knowledge/product-modules.md`,
`knowledge/product-onboardings.md`. Every price row carries the URL it came from and the
page's own caveat. Reference material for building software — not pricing advice.

> **The single most important fact in this file:** the crawled sources contain **no
> Quadratmeterleistung / m²-per-hour performance table and no hourly-rate build-up formula**.
> See §3. Do not fabricate them.

---

## 1. Cost components

### 1.1 The Kalkulation cost factors

**Fakt.** Verbatim from
<https://pland.app/blog/die-kalkulation-in-der-gebaudereinigung-ein-umfassender-leitfaden-fur-eine-erfolgreiche-preisgestaltung>
(page date: September 23, 2024). The article gives the list twice — once as "Kostenfaktoren",
once as "Welche Ausgaben habe ich bei welchem Auftrag?" — with slightly different wording.

| Kostenfaktor | What the page says it covers |
|---|---|
| **Personalkosten** / *Kosten für Arbeitskräfte* | *"Die **Lohn- und Sozialversicherungskosten** für die Reinigungskräfte"*; vary by **Erfahrung** and **Qualifikation** |
| **Materialkosten** | *"Reinigungsmittel, -geräte und Verbrauchsmaterialien wie **Tücher, Wischmopps** usw."* |
| **Fahrzeug- und Transportkosten** | *"Falls ein Firmenfahrzeug benötigt wird … **Treibstoff, Wartung und Versicherung**"* |
| **Verwaltungskosten** | *"**Büromiete, Büroausstattung, Kommunikationskosten** und andere Verwaltungsausgaben"* |
| **Sonstige Kosten** | *"**Versicherungen, Schulungen, Marketing und Werbung** sowie eventuelle **Lizenz- und Genehmigungsgebühren**"* |
| **Gewinnmarge** | *"eine **angemessene Gewinnmarge** … um Rentabilität und Wachstum sicherzustellen"* |

**Fakt.** A seventh item appears only on the Angebote article:
**Mietkosten für Büro- oder Lagerräume**.
(<https://pland.app/blog/wie-schreibe-ich-als-gebaudereinigung-gute-angebote>)

### 1.2 Arbeitszeit as its own axis

**Fakt.** Verbatim, same Kalkulation page:
*"Die Reinigungszeit für jedes Objekt sollte anhand von Faktoren wie der **Größe des
Gebäudes**, der **Art der Reinigungsaufgaben** und der **Verschmutzungsintensität** geschätzt
werden. Es ist wichtig, realistische Zeitrahmen zu setzen und gegebenenfalls **Pufferzeiten**
einzuplanen."*

That is the whole method the page gives. It says *estimate*; it gives no figures, no table
and no formula.

### 1.3 Grundreinigung — the 5-step costing method

**Fakt.** Verbatim structure from <https://pland.app/arbeitslexikon/grundreinigung>:

1. **Flächenberechnung** — *"Bestimmen Sie die Gesamtfläche … indem Sie Länge und Breite der
   Räume oder Oberflächen messen."*
2. **Arbeitsstunden** — *"Schätzen Sie die benötigte Arbeitszeit … Berücksichtigen Sie dabei
   die Art der Aufgaben, den Zustand der Oberflächen und die **Erfahrung des
   Reinigungsteams**."*
3. **Materialeinsatz** — cost of Reinigungsmittel, Werkzeuge, Ausrüstung specific to the deep
   clean, *"auch den **Verbrauch und die Wiederbeschaffung**"*.
4. **Personal- und Lohnkosten** — *"die **Anzahl der Reinigungskräfte**, deren **Stundenlohn**
   sowie etwaige **Zusatzleistungen** oder **Sozialversicherungsbeiträge**."*
5. **Sonstige Kosten** — *"**Anfahrt, Parkgebühren** oder andere Ausgaben."*

Output, verbatim: *"können Sie **einen Stundensatz oder einen Pauschalpreis** für die
Grundreinigung festlegen"* — the pricing mode is an explicit choice, not an implementation
detail.

Same page: *"Es ist ratsam, **vorab eine Besichtigung vor Ort** durchzuführen, um den genauen
Umfang … zu ermitteln"* — the inspection precedes the calculation.

**Fakt (corroborating workflow).** The Unterhaltsreinigung lifecycle starts the same way:
step 1 is **Objektbesichtigung** by the Objektleiter, who records room sizes, the **number of
toilets**, and what is to be cleaned and how.
(<https://pland.app/arbeitslexikon/unterhaltsreinigung>)

---

## 2. Which unit to price on, per cleaning type

**Fakt.** <https://pland.app/blog/die-kalkulation-in-der-gebaudereinigung-ein-umfassender-leitfaden-fur-eine-erfolgreiche-preisgestaltung>

| Reinigungsart | Calculation base(s) | Price-driving factors named |
|---|---|---|
| **Büroreinigung** | Fläche (Preis pro m²) **or** Anzahl der Räume (Preis pro Raum) | Verschmutzungsintensität · Häufigkeit der Reinigung · Art der Reinigungsaufgaben |
| **Treppenhausreinigung** | Stockwerke **or** Fläche des Treppenhauses | Größe des Treppenhauses · Anzahl der Etagen · Verschmutzungsintensität |
| **Fensterreinigung** | Anzahl der Fenster **or** Quadratmeterzahl | Art der Fenster · **Zugänglichkeit** · Verschmutzungsintensität |
| **Teppichreinigung** | m² **or** pro Teppich | Größe · Verschmutzungsgrad · Reinigungsmethode; *"Eine gründliche **Inspektion** der Teppiche vor der Kalkulation ist wichtig"* |
| **Sanitärreinigung** | Anzahl der Sanitäranlagen **or** Fläche des Sanitärbereichs | Anzahl der Anlagen · Größe des Bereichs · Art der Aufgaben |

**Fakt (Glasreinigung-specific drivers).** Größe der zu reinigenden Glasflächen · Art der
Glasflächen · **Zugänglichkeit** · Häufigkeit der Reinigung · **Geografische Lage**
(*"da in manchen Regionen höhere Lohn- und Transportkosten anfallen können"*).
(<https://pland.app/blog/glasreinigung-welche-leistungen-sind-alles-enthalten-und-wie-kalkuliere-ich-sie>)

**Vorschlag.** The unit is a **field**, not a convention:
`unit ∈ {QM, RAUM, STOCKWERK, FENSTER, SANITAERANLAGE, STUNDE, LFM, PAUSCHAL, STUECK}`.
Note `LFM` (laufender Meter) is needed only by frame cleaning (§4.2) and `STUECK` by material
lines from `catalog.Product` (`apps/catalog/models.py:56`, default unit `"Stück"`).

---

## 3. The gap where the Leistungswerte should be

**Fakt (absence, verified by grep across all 237 crawled pages).** The following are **not
stated on any source page**:

| Missing | Status |
|---|---|
| **m²/h Leistungswerte / Quadratmeterleistung** per Reinigungsart and Ausstattungsgrad | *nicht belegt / not established from the sources.* The pages say cleaning time should be "estimated" from size, task type and soiling — no figures, no table, no formula |
| **Stundenverrechnungssatz build-up** (how wage + social contributions + material + vehicle + admin + other + margin combine into an hourly charge-out rate) | The **components** are listed (§1.1) but there is **no formula, no percentage and no worked example** anywhere in the cluster |
| A **worked numerical example of a full job calculation** | Does not exist in the crawl. The only numbers are the two price tables (§4) and the window-cleaning price points |
| **Leistungsverzeichnis structure** — position numbering, standard task catalogue | Named only as a document to be produced (§5). No structure given |
| **Deckungsbeitrag II / mehrstufige DB-Rechnung**, and which cleaning cost items count as variable vs. fixed | *nicht belegt* (<https://pland.app/arbeitslexikon/deckungsbeitrag>) |
| **Pufferzeit** magnitude | Named as a concept; no percentage given |

**Ungeprüft.** Performance values for the German cleaning trade are conventionally published
per Reinigungsart and Ausstattungsgrad by trade bodies and in industry calculation manuals.
Since the sources give none, **any figure the product ships must come from a licensed source
or from the tenant's own measurements.**

**Vorschlag — and this is the product's actual advantage here.** The repo already contains a
measured replacement for a bought Leistungswert table:

| Repo mechanism | Location | What it gives |
|---|---|---|
| `Zone.minutes_per_visit`, `Zone.area_sqm`, `Zone.visits_per_week`, `Zone.weekly_minutes` | `apps/planning/models.py:57-80` | A per-area, per-tenant time estimate — a Leistungswert in the only form that matters |
| `Shift.actual_minutes`, `Shift.variance_minutes`, `Shift.billable_minutes` | `apps/planning/models.py:159, 175-185` | Measured reality against the estimate |
| `ZoneCalibration` — `sample_size`, `window_start/end`, `current_minutes`, `suggested_minutes`, `median_minutes`, `dispersion_minutes` (MAD), `confidence`, and a **PROPOSED → APPLIED/REJECTED** decision | `apps/planning/models.py:235-292` | A statistically grounded correction of the estimate, **proposed not auto-applied**, with history |

The docstring at `apps/planning/models.py:236-245` states the reason it is a proposal:
`minutes_per_visit` is the planner's input and the planner produces contractual obligations,
so a self-moving value makes the plan unpredictable and hides the interesting signal.

**Do not hard-code an m²/h constant anywhere.** Derive minutes from `Zone`, calibrate from
`Shift`, and let the tenant own the number. If a licensed Leistungswert table is ever bought,
model it as `LeistungswertProfile(account, category, ausstattungsgrad, qm_per_hour,
valid_from, source_note)` — a seed for a new Zone, never an override of a measured one.

---

## 4. The published price tables

Both tables are **Richtwerte only**, per the pages' own words. They contradict each other —
see §4.3. Ship them, if at all, as **editable tenant defaults**, never as constants.

### 4.1 Average prices by cleaning type

**Fakt.** Verbatim table from
<https://pland.app/blog/die-kalkulation-in-der-gebaudereinigung-ein-umfassender-leitfaden-fur-eine-erfolgreiche-preisgestaltung>
(page date: September 23, 2024).

| Reinigungsart | Durchschnittlicher Preis pro Einheit |
|---|---|
| Fensterreinigung | **3–7 Euro pro Fenster** oder **10–20 Euro pro Quadratmeter** |
| Büroreinigung | **8–12 Euro pro Quadratmeter pro Monat** |
| Treppenhausreinigung | **50–100 Euro pro Stockwerk pro Monat** |
| Teppichreinigung | **2–5 Euro pro Quadratmeter** |
| Sanitärreinigung | **15–30 Euro pro Sanitäranlage** oder **10–20 Euro pro Quadratmeter** |
| Sonderreinigungen | *"Je nach Aufwand und Art der Spezialreinigung. Preise können individuell vereinbart werden"* |

Page's own caveat, verbatim: *"Die genannten Preise dienen **nur als Orientierung** und können
je nach individuellen Umständen variieren … je nach **Region, Objektgröße, Reinigungsaufwand
und individuellen Vereinbarungen**."*

Note the units differ per row: Büroreinigung and Treppenhausreinigung are **per month**;
the others are per clean. Do not aggregate these into one column without carrying the period.

### 4.2 Glasreinigung price bands

**Fakt.** Verbatim table from
<https://pland.app/blog/glasreinigung-welche-leistungen-sind-alles-enthalten-und-wie-kalkuliere-ich-sie>
(page date: April 24, 2024).

| Art der Glasreinigung | Preis pro m² |
|---|---|
| Fensterreinigung | 2,00 € – 4,00 € |
| Glasdachreinigung (Unterseite) | 2,50 € – 5,50 € |
| Glasdachreinigung (Oberseite) | 5,00 € – 8,00 € |
| Wintergartenreinigung | 3,00 € – 6,00 € |
| Fassadenreinigung (inkl. Glas) | 2,00 € – 6,00 € |
| spezielle Reinigungsmittel (bei z. B. Fassadenreinigung) | 5,00 € – 10,00 € |
| Gerüst (bei Fassadenreinigung) | 5,00 € – 10,00 € |
| Glasfrontreinigung | 1,50 € – 4,50 € |
| Imprägnierung / Versiegelung | 5,00 € – 20,00 € |

**Fakt.** Other price points on the same page:

| Fact | Value |
|---|---|
| Standard window incl. frame, per unit | **2,50 € – 4,00 €** ("im Schnitt") |
| Sides | *"die angegebenen Preise gelten oftmals **nur für eine Seite**"* — inside **and** outside **"werden die Preise dementsprechend verdoppelt"** |
| Package example | *"bis zu **10 Fenster zum Preis von 28 €**"* |
| Heavy soiling | surcharge possible, *"da die Reinigung dann unter die **Grundreinigung** fällt"* |
| Hourly alternative | Grundreinigung **20–30 Euro pro angefangene Stunde** — *angefangene* = each **started** hour ⇒ `ceil()` |
| Extra costs | **Anfahrt**, Reinigungsmittel, **Spezialequipment** for hard-to-reach surfaces |
| Access caveat | *"**Hebebühnen, Kräne oder Gerüste** werden von den Fensterreinigern in der Regel **nicht gestellt**"* — must be clarified in advance |

**Fakt.** A **third** Glasreinigung price set, from the lexicon entry
<https://pland.app/arbeitslexikon/glasreinigung>:

| Item | Price | Worked example given on the page |
|---|---|---|
| Standard-Fensterreinigung | **3–7 EUR per m² of window glass** ("je nach Region und Dienstleister") | **200 m² Fensterfläche, einmalige Reinigung ⇒ 600–1.400 EUR** |
| Spezialreinigungen (hard-to-reach glass, stubborn soiling) | **5–15 EUR per m²** | — |
| **Rahmenreinigung** (frame surcharge) | **0,50–2 EUR pro laufendem Meter** | — |
| Frequency effect | *"Je öfter die Glasflächen gereinigt werden, desto **niedriger** können die Kosten pro Reinigung ausfallen"* — contract-based discount for recurring cleans | — |

Page's caveat, verbatim: *"die genannten Preise nur als **Richtwerte** dienen und je nach
Dienstleister und Region variieren können."*

### 4.3 The contradiction — do not average it away

**Fakt.** For the **same service in the same unit**, the three pages disagree:

| Service | `/blog/die-kalkulation-…` | `/blog/glasreinigung-…` | `/arbeitslexikon/glasreinigung` |
|---|---|---|---|
| Fensterreinigung **per m²** | **10–20 €** | **2,00–4,00 €** | **3–7 €** |
| Standard window **per unit** | **3–7 €** | **2,50–4,00 €** (with frame) | — |

The per-m² spread is a **3–5× discrepancy**. All three are recorded; **do not average them,
do not pick one silently.** If a default must ship, ship the range as `min`/`max` with the
source URL attached to the row so a user can see where it came from, and make it editable.

### 4.4 The two named quoting failure modes

**Fakt.** <https://pland.app/blog/wie-schreibe-ich-als-gebaudereinigung-gute-angebote>

| Failure | Verbatim |
|---|---|
| **Preisorientierung an Mitbewerbern** | *"Viele Reinigungsunternehmen schauen auf die Preise ihrer Wettbewerber und setzen einfach einen niedrigeren Preis an. Dies kann zu **unrealistisch niedrigen Angeboten** führen, die letztendlich **nicht rentabel** sind."* |
| **Fehlende Kostenanalyse** | *"Oftmals werden Angebote auf Basis **früherer Aufträge** erstellt, ohne eine genaue Analyse der aktuellen Leistungen und Kosten … wichtige Kosten übersehen oder falsch eingeschätzt."* |

Remedy prescribed on the same page: clarify Kundenanforderungen (Größe der Räume,
Verschmutzungsgrad, gewünschter **Reinigungsturnus**) → determine costs → use a **feste
Angebotsstruktur**.

**Vorschlag.** These two failure modes are the strongest argument for making the quote
calculator show a **computed floor price** (cost + margin) next to the entered offer price,
and warning when the offer falls below it. The repo already has the comparison primitive:
`Offer.implied_hourly` (`apps/marketplace/models.py:161-166`), described in its own docstring
as *"singura bază reală de comparație între oferte"*.

---

## 5. The Angebot document set

**Fakt.** Four documents make a convincing quote.
<https://pland.app/blog/wie-schreibe-ich-als-gebaudereinigung-gute-angebote>

| Document | Content prescribed, verbatim sense |
|---|---|
| **Angebotsschreiben** | *"die angebotenen Leistungen, den Preis, den **Reinigungsturnus** und andere relevante Informationen"* |
| **Leistungsverzeichnis** | *"eine detaillierte Liste der geplanten Reinigungsleistungen **für jeden Raum oder Bereich**. Geben Sie an, **welche Aufgaben in welchem Umfang** durchgeführt werden sollen."* |
| **Raumlisten** | *"eine Liste aller zu reinigenden Räume … einschließlich ihrer **Größe** und des **geschätzten Zeitaufwands** für die Reinigung."* |
| **Sonderaufgaben** | special customer requirements, documented so *"sowohl der Kunde als auch Ihre Mitarbeiter über diese Vereinbarungen informiert sind."* |

**Fakt.** Additional Angebot content from
<https://pland.app/blog/gebaudereinigung-so-schreiben-sie-angebote>:
- Detaillierte Beschreibung der Reinigungsleistungen incl. **Art der Reinigung**
  (Büroreinigung, Fensterreinigung, Teppichreinigung) and **Häufigkeit** (täglich,
  wöchentlich, monatlich).
- Liste der verwendeten Reinigungsmittel und -geräte, **einschließlich Marke und Modell**,
  falls erforderlich.
- Preis + Zahlungsbedingungen (Fälligkeit, Zahlungsmodalitäten).
- Erklärung der **Garantie- und Haftungsbedingungen** sowie der **Versicherungspolice**.
- Clear prices per service incl. **Stundensätze**, **Arbeitszeit** and **Material**;
  transparency about additional fees.
- The quote must be sent **in writing**.
- Optional: Referenzen und Empfehlungen; personalisation to the customer's needs.

**Fakt.** The later invoice must match the quote: *"genau den im Angebot vereinbarten Preis
und Leistungsumfang widerspiegeln"*
(<https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen>).

**Fakt (repo).** The Raumliste already exists as `planning.Zone` — `name`, `area_sqm`,
`minutes_per_visit`, `visits_per_week`, `category` FK, `description`
(*"Instrucțiuni pentru lucrător — apar în Reinigungsplan și la check-in"*).
`apps/planning/models.py:42-87`. And a Reinigungsplan renderer exists at
`apps/planning/reinigungsplan.py`, routed as
`/dashboard/obiective/<int:pk>/reinigungsplan.xlsx` (`apps/dashboard/urls.py`).

**Vorschlag.** Generate the Leistungsverzeichnis from `Zone` rows, not from a parallel
structure: one LV position per Zone × task, carrying `frequency` (from `visits_per_week`),
`area_sqm`, and `estimated_minutes` (from `minutes_per_visit`). A `Sonderaufgabe` is an LV
position with `is_recurring = False`.

**Ungeprüft.** **Raumbuch** (the underlying area register with area type, m², floor covering
and cleaning group) is the third FM/tender entity that neither the sources nor the repo model
explicitly. `Zone` is closer to a Raumbuch row than to an LV position; a serious tender needs
both levels. Verify against a real tender document before building it.

---

## 6. The competitor's quote calculation engine

**Fakt.** <https://pland.app/blog/wie-schreibe-ich-als-gebaudereinigung-gute-angebote>

1. **Eingabe der grundlegenden Stammdaten** — *"betriebliche Stammdaten wie **Stundenlöhne
   und Materialkosten**"*.
2. **Erfassung der Auftragsdetails** — *"die **Quadratmeter** und den **Verschmutzungsgrad**
   jedes zu reinigenden Raums … gegebenenfalls **Sonderaufgaben** oder **periodische
   Leistungen**"*.
3. **Automatische Kalkulation** — *"PlanD berechnet anhand der eingegebenen Daten den
   **voraussichtlichen Zeitaufwand und die Kosten**"*.
4. **Preisanpassung** — *"Sie können den Angebotspreis entsprechend anpassen, um Ihren
   **gewünschten Gewinn** zu erzielen."*
5. **Automatische Generierung** — one click produces **Angebotsschreiben,
   Leistungsverzeichnis und Raumlisten**.

**Fakt.** Quote → order conversion: an accepted Angebot converts to an **Auftrag** in one
click; Objekt and Auftragsart are prefilled from the quote; Start- und Enddatum are set on
the Auftrag. *"Angenommene Angebote werden automatisch abgerechnet."*
(<https://pland.app/onboardings/wiederholende-rechnungen-mit-pland-erstellen>,
<https://pland.app/funktionen/uebersicht>)

**The shape of the engine, restated (Vorschlag):**

```
per room/zone:  estimated_minutes = f(area_sqm, soiling_level, task_set)
                # f is NOT given by the sources — see §3
job_minutes    = Σ estimated_minutes + Sonderaufgaben + Pufferzeit
labour_cost    = job_minutes/60 × (hourly_wage × (1 + social_contribution_rate))
job_cost       = labour_cost + material + transport + admin + other
offer_price    = job_cost × (1 + margin_pct)      # user-adjustable
```

Every symbol above is a **configured value**, not a constant. The sources supply the
*component list* and nothing else.

### 6.1 Dynamische Positionen — billing basis, with the source's own worked example

**Fakt.** <https://pland.app/onboardings/dynamische-positionen-in-rechnungen-mit-pland>

Definition, verbatim: *"Dynamische Positionen sind Positionen, die **nicht pauschal**, sondern
erst im Nachhinein … **nach Termin oder geleisteter Arbeitszeit im Objekt** abgerechnet werden
sollen."*

| Billing basis | Meaning |
|---|---|
| **Soll-Zeit** | the Einsätze **planned** in the month |
| **Lohnzeit** | the hours the employees are **paid** for that Auftrag |
| **nach Termin** | **per appointment** — used in the example for **Anfahrt** |

**Worked example, verbatim:** 2 planned hours, **1 hour approved** ⇒ the customer is billed
**1 Stunde Glasreinigung** plus **2× Anfahrtskosten**, because the Auftrag was scheduled twice
and Anfahrt is billed per Termin.

On manual invoice creation, all Einsätze of that Auftrag inside the chosen
**Leistungszeitraum** are pulled in and the dates on which they took place are shown.

**Fakt (repo).** The distinction already exists in code:
`Shift.billable_minutes` returns *"Timpul real dacă a fost pontat, altfel cel planificat"*
(`apps/planning/models.py:175-178`) — that is Lohnzeit-with-Soll-Zeit-fallback in one
property. `Shift.duration_minutes` is the Soll-Zeit; `Shift.actual_minutes` the measured one.

---

## 7. Deckungsbeitrag (contribution margin)

**Fakt.** <https://pland.app/arbeitslexikon/deckungsbeitrag>

| Item | Verbatim |
|---|---|
| Formula | **`Deckungsbeitrag = Erlöse − variable Kosten`** |
| Erlöse | *"der Umsatz oder Verkaufserlös, der durch den Verkauf des Produkts erzielt wird"* |
| Variable Kosten | *"Kosten, die **direkt** mit der Produktion oder dem Verkauf des Produkts zusammenhängen, z. B. Materialkosten oder Produktionskosten, die **bei jeder zusätzlich produzierten Einheit** anfallen"* |
| **Worked example** | Verkaufspreis **100 €**, variable Kosten **60 €** ⇒ `100 € − 60 € = **40 €**` |
| Positive DB | contributes to covering fixed costs |
| **Negative DB** | *"das Produkt ist **nicht kostendeckend** und **gefährdet möglicherweise die Rentabilität** des Unternehmens"* |
| Gesamtdeckungsbeitrag | Σ of all contribution margins; shows whether total fixed costs are covered and how much profit remains |

**Fakt.** DB is computed **per Auftrag**, not just per product: *"PlanD zeigt Ihnen den
Deckungsbeitrag für **all Ihre Aufträge** ganz automatisch an."* (vendor claim as to the
automation; the *level* is the fact.) — same page

**Fakt.** The mechanics the competitor states: *"PlanD **vergleicht in Echtzeit Ausgaben wie
Lohn und Material mit den Einnahmen**, die ein Kunde generiert."*
⇒ `DB_Auftrag = Einnahmen − (Lohnkosten + Materialkosten)`.
(<https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>)

**Fakt.** Reported at three levels: *"welche **Aufträge, Objekte oder Leistungen** den größten
Beitrag leisten"*. (<https://pland.app/funktionen/umsatzuebersicht>)

**Fakt (gap).** The pages do **not** give a Deckungsbeitrag II / mehrstufige
Deckungsbeitragsrechnung formula, and do **not** say which cost items count as variable for a
cleaning contract. *Nicht belegt.*

**Fakt (gap).** The term **Deckungsbeitrag does not appear on any of the 18 Faktura blog
pages** — only in the lexicon and the module pages.

**Vorschlag.**

```
DB1(auftrag, period) = Σ invoiced_net(auftrag, period)
                     − Σ labour_cost(shifts in period)
                     − Σ material_cost(consumed in period)
```

- `labour_cost` = `Shift.billable_minutes` × the wage rate **in force on the shift date** —
  use the `WageFloor.current(kind, on)` dated-lookup pattern
  (`apps/contracts/models.py:83-89`), and take the actual contracted wage from
  `ContractDraft.hourly_wage` (`apps/contracts/models.py:164`), not the floor.
- `material_cost` from `catalog.Product.price_net` (`apps/catalog/models.py:52`).
- **Snapshot the variable-cost figures onto the Order period record** so historical margins do
  not silently shift when a wage rate or a product price changes. The repo already uses
  freeze-at-generation for exactly this reason
  (`ContractDraft.rendered_body`, `apps/contracts/models.py:116-121`).
- Surface `DB < 0` prominently. The source calls a negative DB a threat to company
  profitability; it is the single most actionable number this layer can produce.
- Do **not** invent a DB II tier. If one is added later, make the variable/fixed split
  explicit per cost type and configurable — the sources give no allocation rule.

---

## 8. Ausschreibungen — how tender pricing differs

**Fakt.** All from
<https://pland.app/blog/ausschreibungen-in-der-gebaudereinigung-ein-leitfaden-fur-unternehmen>
(page date: May 5, 2025).

**Definition.** A formal procedure by which Auftraggeber — *"öffentliche Institutionen,
Unternehmen oder **Wohnungsbaugesellschaften**"* — award services through a structured
application process, to compare providers and pick *"das **wirtschaftlichste und qualitativ
beste** Angebot"*. Public authorities are legally obliged to tender publicly *"**ab einer
bestimmten Wertgrenze**"* — **the threshold value is never named.** *Nicht belegt.*

### 8.1 Components of a cleaning tender

| Component | Content |
|---|---|
| **Leistungsbeschreibung** | which cleaning services, which surfaces, which standards must be met |
| **Vergabebedingungen** | legal/organisational framework: **Teilnahmevoraussetzungen, Fristen** |
| **Preisblatt / Kalkulationsschema** | *"Die Bieter müssen ihre Preise **transparent darlegen** und häufig eine **detaillierte Kalkulation** abgeben."* |
| **Bewertungskriterien** | *"Neben dem Preis spielen oft auch **Qualität, Nachhaltigkeit und Referenzen** eine Rolle."* |
| **Vertragsbedingungen** | **Laufzeit**, Kündigungsbedingungen, mögliche **Vertragsstrafen** |

### 8.2 What changes versus an ordinary Angebot

| Ordinary Angebot | Ausschreibung |
|---|---|
| Free-form document set (§5) | Prices must go into the client's **Preisblatt / Kalkulationsschema** — an externally imposed structure the calculation must be exportable into |
| Price is the main lever | Award is multi-criteria: **Preis + Qualität + Nachhaltigkeit + Referenzen** |
| No eligibility paperwork | **Handelsregisterauszüge**, **Unbedenklichkeitsbescheinigungen der Sozialversicherungsträger**, **Referenzen** must be obtained **in time** |
| Losing means a lost customer | *"Viele Unternehmen scheitern **nicht am Preis, sondern an Formfehlern**."* |
| No contractual penalty regime by default | **Vertragsstrafen** are an explicit tender component — a risk input to the calculation |

**Fakt — platforms named:** **Deutsches Vergabeportal (DTVP)**, **TED (Tenders Electronic
Daily)**, plus sector-specific Ausschreibungsportale.

**Fakt — participation procedure (7 steps, verbatim order):**
1. Find suitable tenders on DTVP / TED / industry portals; check the job **fits your company
   size and capacity**.
2. Obtain documents in time (Handelsregisterauszug, Unbedenklichkeitsbescheinigungen,
   Referenzen).
3. Calculate realistically — competitive **but profitable**.
4. Write an individual, non-standardised offer; highlight **Alleinstellungsmerkmale**.
5. Emphasise Qualität and Nachhaltigkeit where the Bewertungskriterien allow it.
6. Follow every formality exactly.
7. If you lose, **request feedback** and improve the next offer.

**Fakt — disadvantages named:** hoher bürokratischer Aufwand · **Preiswettbewerb/Preisdruck** ·
Ungewissheit.

**Fakt (adjacent).** DIN norms are voluntary *"es sei denn, sie wird **durch Verträge oder
Gesetze verbindlich** gemacht"* — and clients frequently make a named DIN norm contractually
binding in tenders, which turns compliance into an audit obligation and a tender advantage.
(<https://pland.app/arbeitslexikon/din-normen>)

**Vorschlag.** A tender is a pipeline object, not a quote variant:
`Tender(source_platform ∈ {DTVP, TED, SONSTIGE}, submission_deadline,
award_criteria (weighted), contract_penalties, required_documents M2M with per-document
validity dates)`. The required-documents checklist with expiry dates is the direct answer to
"most losses are Formfehler". Note `apps/accounts/compliance.py:7-37` already has
`VerificationDocument` with `doc_type` (incl. `HRB`, `GEWERBE`, `INSURANCE`), `expires_at`
and `status` — reuse it rather than building a second document store.

---

## 9. Repo calculation surface that already exists

**Fakt (repo), read 2026-08-29.**

| Primitive | Location | Note |
|---|---|---|
| `Zone.area_sqm`, `minutes_per_visit`, `visits_per_week`, `weekly_minutes` | `apps/planning/models.py:57-80` | The Raumliste and the time estimate |
| `Shift.hours`, `billable_minutes`, `variance_minutes` | `apps/planning/models.py:171-185` | Realised time; Soll/Lohnzeit split |
| `ZoneCalibration` (median, MAD, confidence, proposed) | `apps/planning/models.py:235-292` | Empirical Leistungswert correction |
| `Offer.price_per_visit`, `estimated_minutes`, `monthly_price`, `implied_hourly` | `apps/marketplace/models.py:132-166` | Per-visit → per-month → per-hour conversion, already written |
| `VISITS_PER_MONTH` = ONE_TIME 1 · WEEKLY **4.33** · BIWEEKLY **2.17** · MONTHLY 1 (`Decimal`) | `apps/marketplace/models.py:32-37` | **Reuse verbatim.** Do not invent a second frequency→visits map |
| `Offer.deduction_35a` — 20 % of yearly labour, capped **4.000 €** (§ 35a Abs. 2 EStG) | `apps/marketplace/models.py:168-174` | Only for `ServiceCategory.is_35a_eligible` **and** `EntityType.INDIVIDUAL` (`apps/marketplace/models.py:103-108`) |
| `Product.price_net`, `vat_rate` (default `19.00`), `price_gross` | `apps/catalog/models.py:52-55, 89-91` | Material lines; the net/gross convention |
| `WageFloor.current()`, `MinijobThreshold.current()` | `apps/contracts/models.py:83-113` | The dated-value lookup every price band should copy |
| `ContractDraft.monthly_gross = hours × wage` | `apps/contracts/models.py:189-191` | The cost side of DB, per worker |

**Fakt (repo, absent).** No `PriceBand`, no `TaxRate` table, no cost-settings model, no margin
field, no Deckungsbeitrag computation, no Angebot document. All of that is to be built.

---

## Quellen

pland.app pages (crawled 2026-08-29):
- <https://pland.app/blog/die-kalkulation-in-der-gebaudereinigung-ein-umfassender-leitfaden-fur-eine-erfolgreiche-preisgestaltung> (September 23, 2024)
- <https://pland.app/blog/glasreinigung-welche-leistungen-sind-alles-enthalten-und-wie-kalkuliere-ich-sie> (April 24, 2024)
- <https://pland.app/arbeitslexikon/glasreinigung>
- <https://pland.app/arbeitslexikon/grundreinigung>
- <https://pland.app/arbeitslexikon/unterhaltsreinigung>
- <https://pland.app/arbeitslexikon/deckungsbeitrag>
- <https://pland.app/arbeitslexikon/din-normen>
- <https://pland.app/blog/wie-schreibe-ich-als-gebaudereinigung-gute-angebote> (May 6, 2025)
- <https://pland.app/blog/gebaudereinigung-so-schreiben-sie-angebote> (May 5, 2025)
- <https://pland.app/blog/ausschreibungen-in-der-gebaudereinigung-ein-leitfaden-fur-unternehmen> (May 5, 2025)
- <https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen> (May 5, 2025)
- <https://pland.app/onboardings/dynamische-positionen-in-rechnungen-mit-pland>
- <https://pland.app/onboardings/wiederholende-rechnungen-mit-pland-erstellen>
- <https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>
- <https://pland.app/funktionen/umsatzuebersicht>
- <https://pland.app/funktionen/uebersicht>

Repository files read for this document (2026-08-29):
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/marketplace/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/catalog/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/compliance.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/dashboard/urls.py`
