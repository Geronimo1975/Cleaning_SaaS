# Reinigungsarten, Normen, Qualität, Sicherheit, Material

Covers: what the cleaning types actually are and how they differ, cleaning intervals, the
Reinigungsplan and Arbeitsschein templates, the Vier-Farben-System, every DIN/EN/ISO norm the
sources name, hygiene standards, the seven safety rules, health hazards, the equipment and agent
catalogue, and the surface → method → agent → caution matrix.
**Stand: 2026-08-29.**
Material: pland.app Arbeitslexikon and blog clusters, crawled 2026-08-29; every factual row
carries its URL. Repo rows carry `file:line` (read 2026-08-29). Rows marked **Ungeprüft** are
added domain knowledge that the crawled sources do not cover.

This is reference material, not legal advice. DIN numbers, norm titles and safety duties below are
reproduced as the source states them — several are demonstrably questionable and are flagged in §K.

---

## A. The cleaning types

### A1. The four service **standards** (Reinigungsstandards)

Source for the whole block: https://pland.app/blog/reinigungsstandards-und-din-normen---was-muss-man-als-gebaudereinigung-einhalten

| Standard | Definition as printed | What it means for the model |
|---|---|---|
| **Sichtreinigung** | "eine oberflächliche Reinigung, bei der grober Schmutz und sichtbare Verschmutzungen entfernt werden. Sie wird häufig in Büros durchgeführt und dient dazu, ein gepflegtes Erscheinungsbild zu gewährleisten." | A *lower* service level that must be nameable and separately priced in a contract |
| **Unterhaltsreinigung** | "erfolgt in regelmäßigen Intervallen und umfasst wiederkehrende Reinigungsaufgaben wie das Staubsaugen, Wischen von Böden und die Reinigung von Sanitäranlagen." | The recurring product |
| **Grundreinigung** | "eine intensivere Reinigung, bei der auch schwer zugängliche Bereiche und hartnäckige Verschmutzungen behandelt werden. Sie wird in größeren Zeitabständen durchgeführt und ist oft mit einer Pflege der Oberflächen verbunden." | Episodic, includes surface care |
| **Sonderreinigung** | "spezielle Reinigungsleistungen, die nicht zum regulären Leistungsumfang gehören, wie etwa die Reinigung nach Bauarbeiten, Fassadenreinigungen oder die Entfernung von Graffiti." | One-off job type |

### A2. The type definitions and how they contrast

| Type | Definition as given | Explicit contrast | Quelle |
|---|---|---|---|
| **Unterhaltsreinigung** | "die regelmäßige Reinigung eines Objektes in **festen Zeitabständen**" — Böden, Oberflächen, Möbel, Sanitäranlagen; removal of Abfall and Staub | "zielt darauf ab, den Zustand der Räume auf einem **bereits gereinigten Niveau zu halten**" | https://pland.app/arbeitslexikon/unterhaltsreinigung |
| **Grundreinigung** | "eine **intensive** Reinigungsmethode … um hartnäckige Verschmutzungen, Ablagerungen und Rückstände zu entfernen"; "tiefgreifende und umfangreiche Reinigung, die **in bestimmten Zeitintervallen** durchgeführt wird" | Covers **Böden, Wände und Decken**, against Unterhaltsreinigung's "kontinuierliche Pflege" | https://pland.app/arbeitslexikon/grundreinigung |
| **Glasreinigung** | "die professionelle Reinigung von Glasflächen wie Fenstern, Türen oder Fassadenelementen"; removes Schmutz, Staub, Wasserflecken | Its own service line with m²-based pricing and its own method taxonomy | https://pland.app/arbeitslexikon/glasreinigung |
| **Bauendreinigung** | Final clean after building works | The crawled sources cover it **only** as an example of Sonderreinigung ("Reinigung nach Bauarbeiten"). No checklist, no method list, no pricing anywhere in the corpus — *nicht belegt*. It is nevertheless a seeded leaf in this repo: `bauendreinigung` / "Bauendreinigung", §35a-eligible | https://pland.app/blog/reinigungsstandards-und-din-normen-…; repo:`apps/taxonomy/migrations/0003_seed_categories.py:43-44` |

**Grundreinigung sub-types (4, exactly as named):** Teppichgrundreinigung (Shampoonieren,
Extrahieren, Dampfreinigen) · Bodengrundreinigung (Schrubben, Strippen, neues Wachsen/Versiegeln) ·
Fenstergrundreinigung (incl. Fensterrahmen, Fensterbänke) · Sanitärgrundreinigung (WCs, Waschbecken,
Duschen, Armaturen — Kalkablagerungen).
Source: https://pland.app/arbeitslexikon/grundreinigung

**Glasreinigung — 12 glass object classes named:** Glastüren · Glasfassaden · Glastische · Vitrinen ·
Glaskunstwerke · Beleuchtungsanlagen und Industrieverglasung · Leuchtreklame · Autoscheiben ·
Gewächshäuser/Wintergärten · Schaufenster · Lichtkuppeln · Lampen.
**Glasreinigung — 5 methods named:** Nassreinigung (spray + Mikrofasertuch) · Trockenreinigung
(dry microfibre, light soiling only) · Hochdruckreinigung (e.g. façade glass) ·
Ultraschallreinigung (ultrasonic bath, sensitive glass such as Glaskuppeln/Wintergärten) ·
Spezialreinigung (e.g. Graffitientfernung).
Source: https://pland.app/arbeitslexikon/glasreinigung

### A3. Glasreinigung price bands — the only euro figures in the whole cleaning corpus

Source for all four rows: https://pland.app/arbeitslexikon/glasreinigung
The page itself calls these "**Richtwerte**" — guide values that vary by provider and region.
**Store them as configurable defaults, never as constants.**

| Item | Price | Worked example on the page |
|---|---|---|
| Standard-Fensterreinigung | **3–7 EUR / m²** Glasfläche | 200 m² window area, one-off → **600–1.400 EUR** |
| Spezialreinigung (hard-to-reach glass, stubborn soiling) | **5–15 EUR / m²** | — |
| Rahmenreinigung (frame surcharge) | **0,50–2 EUR / laufendem Meter** | — |
| Frequency effect | "Je öfter die Glasflächen gereinigt werden, desto **niedriger** können die Kosten pro Reinigung ausfallen" | contract-based discount for recurring cleans |

The other pricing figure in the corpus: **0,15 EUR/m²** as the average price for regular office
Unterhaltsreinigung — but it appears inside a *fictitious example* business plan that the page
itself labels "lediglich Beispiel-Texte … nur zur Orientierung".
Source: https://pland.app/tutorials/beispiel-geschaftsplan. **Do not use it as a market rate.**

### A4. Grundreinigung pricing — the 5 cost components

Source: https://pland.app/arbeitslexikon/grundreinigung

1. **Flächenberechnung** — total area from length × width of rooms/surfaces.
2. **Arbeitsstunden** — labour time, considering task type, surface condition, team experience.
3. **Materialeinsatz** — agents, tools, equipment specific to the deep clean, incl. consumption and replacement.
4. **Personal- und Lohnkosten** — headcount × hourly wage, plus Zusatzleistungen and Sozialversicherungsbeiträge.
5. **Sonstige Kosten** — Anfahrt, Parkgebühren, other job-related expenses.

Output is either a **Stundensatz** or a **Pauschalpreis**. The page requires an on-site inspection
before quoting.

---

## B. Reinigungsintervalle

Source for the interval table: https://pland.app/arbeitslexikon/reinigungsintervall

| Intervall | Tasks named on the page |
|---|---|
| **Tägliche Reinigung** | Reinigen von Sanitäranlagen; Staubsaugen von Teppichböden in stark frequentierten Bereichen; Leeren von Abfallbehältern |
| **Wöchentliche Reinigung** | Wischen von Hartböden; Staubwischen von Oberflächen; Reinigung von Glasflächen |
| **Monatliche Reinigung** | Grundreinigung von Teppichböden; Reinigen schwer zugänglicher Bereiche; Pflege von Holzoberflächen |
| **Vierteljährliche oder halbjährliche Reinigung** | Reinigung von Fenstern, Jalousien und Leuchten; Tiefenreinigung von Polstermöbeln |
| **Jährliche Reinigung** | umfassende Grundreinigungen: Stripping und Neuversiegeln von Bodenbelägen; Fassadenreinigung |

A fourth plan type — **Saisonaler Reinigungsplan** — appears only on
https://pland.app/arbeitslexikon/reinigungsplan (leaves in autumn, A/C filters in summer, snow
clearing in winter). **The enum must be the union of both pages**: `TAEGLICH, WOECHENTLICH,
MONATLICH, VIERTELJAEHRLICH, HALBJAEHRLICH, JAEHRLICH, SAISONAL`.

**Six factors that determine an interval** (same source): Gebäudenutzung (Bürogebäude / Krankenhaus /
Schule) · Besucherfrequenz (persons per day) · Hygieneanforderungen · Oberflächenmaterialien ·
Gesetzliche Vorschriften · Kundenwünsche und Budgetvorgaben.

An earlier list on the same page names five, worded differently: Art des Objekts/Bereichs ·
Nutzungsintensität · Hygieneanforderungen · Gesetzliche Vorschriften (especially Lebensmittel­industrie
and Gesundheitswesen) · Ästhetische Ansprüche.

**Intervals must be reviewed and adjusted** for saisonale Schwankungen, Änderungen in der
Gebäudenutzung, and neue Hygieneanforderungen (same source). Store the derivation inputs so an
interval can be re-justified, and keep a revision history.

Qualitative frequency rule, worked example: "Eine Toilette, die von **100** Menschen benutzt wird,
benötigt … eine regelmäßigere Reinigung als eine für nur **5** Personen."
Source: https://pland.app/blog/unterhaltsreinigung-die-ultimative-checkliste. No coefficient or
formula is given anywhere — keep any recommendation coefficients configurable.

**Conflicts to be aware of:**
- Grundreinigung sits at *monthly* (carpets) and *annual* (stripping/resealing) on the interval
  page, and at "alle 6 Monate oder einmal im Jahr" vs "etwa einmal jährlich" on two blog pages.
  → Grundreinigung frequency is **per surface**, never global.
- Glass is *weekly* ("Reinigung von Glasflächen") and *quarterly/semi-annual* ("Reinigung von
  Fenstern") in the same list. → glass frequency is **per glass class**, not per building.

---

## C. Reinigungsplan — definition and template columns

**Definition:** "Ein Reinigungsplan ist ein **schriftlich festgelegtes Konzept**, das die Art und
Weise der Reinigung in einem Gebäude oder einer Einrichtung beschreibt."
Sources: https://pland.app/arbeitslexikon/reinigungsplan ·
https://pland.app/blog/gebaudereinigung-reinigungsplan-hier-kostenlose-vorlage-herunterladen

### C1. The template columns (the canonical export schema)

Source: https://pland.app/blog/gebaudereinigung-reinigungsplan-hier-kostenlose-vorlage-herunterladen

| # | Spalte | What goes in it |
|---|---|---|
| 1 | **Bereich/Ort** | "der Name des Bereichs oder Objekts …, das gereinigt werden soll" |
| 2 | **Leistung** | "die Leistungen …, die durchgeführt werden müssen, wie zum Beispiel Staubwischen, Staubsaugen, Wischen usw." |
| 3 | **Beschreibung** | "die Leistungen genauer beschrieben …, sodass die Reinigungskräfte genau wissen, was sie zu tun haben" |
| 4 | **Reinigungsfrequenz** | "wie oft die jeweilige Reinigungsaufgabe durchgeführt werden muss, zum Beispiel täglich, wöchentlich, monatlich usw." |
| + | optional | "beispielsweise für **Materialien** oder **spezielle Anweisungen**" |

**This repo already exports exactly these four columns plus three the empty template cannot
produce** — `apps/planning/reinigungsplan.py:18-26`:

```python
HEADERS = [
    ("Bereich / Ort", 34),
    ("Leistung", 30),
    ("Beschreibung", 46),
    ("Reinigungsfrequenz", 22),
    ("Dauer je Einsatz", 18),
    ("Wochentage", 18),
    ("Minuten / Woche", 16),
]
```

Frequency is rendered from `Zone.visits_per_week` as "täglich" (≥7), "1× wöchentlich" (=1) or
"N× wöchentlich" (`reinigungsplan.py:29-34`). Weekdays are rendered
`Mo Di Mi Do Fr Sa So` (`reinigungsplan.py:16`). The sheet is titled "Reinigungsplan" with a
`Summe` row over Minuten/Woche (`reinigungsplan.py:64-89`).

### C2. The five mandatory content blocks

Source: https://pland.app/arbeitslexikon/reinigungsplan

| Block | What it holds |
|---|---|
| Raum- oder Bereichsbezeichnung | a clear identifier for every room/area to be cleaned |
| Reinigungsaufgaben | per room/area: Staubsaugen, Wischen, Abstauben, Fensterreinigung, Desinfektion, Müllentsorgung |
| Zeitrahmen | täglich, wöchentlich, monatlich or jährlich |
| Verantwortlichkeit | the person or team — **internal cleaner or external cleaning company** |
| Kontrolle | the quality-control mechanism, e.g. regular inspection by the Objektleiter |

The plan is normally structured **by room or area**, and additionally records "die Art der
Reinigungsmittel und Werkzeuge" and "Verantwortlichkeiten und Zeitpläne".

**Four plan types:** Täglicher · Wöchentlicher · Monatlicher · **Saisonaler** Reinigungsplan.

**Three beneficiary roles** (effectively a permission model): **Reinigungspersonal** (structure and
completeness) · **Objektleitung** (assurance nothing is forgotten; the plan is the "**Nachweis** für
die durchgeführten Reinigungsarbeiten … insbesondere im Falle von Beschwerden oder Streitigkeiten")
· **Geschäftsführung** (transparency, control, budgeting).

**Consequence for the model:** because the plan is used as evidence in disputes, plan versions must
be **immutable and timestamped**, and distribution is per cleaner ("Die Reinigungspläne können dann
an die jeweils zuständigen Reinigungskräfte verteilt [werden]").

---

## D. Arbeitsschein — template contents

Source: https://pland.app/blog/hier-kostenlose-arbeitsschein-vorlage-herunterladen
The page enumerates the contents in prose; it never prints a column table, and the downloadable
template itself is behind an e-mail gate, so **the printed template's exact column headings and
order are not established from the sources**.

| Feld (German, as worded on the page) | Note |
|---|---|
| **Standort** | the site |
| **Art der Reinigungsdienstleistung** | service type |
| **die durchgeführten Aufgaben** | tasks performed |
| **die Arbeitszeit** | working time |
| "und andere relevante Informationen" | unspecified on the page |
| **Unterschrift des Kunden** | "dem Kunden direkt vor Ort vorgelegt …, so dass dieser Sie auf dem Smartphone unterschreiben kann" |
| **Fotos** of problem areas or completed tasks — Zustand **vor und nach** der Reinigung | |
| **Zeitstempel** | |
| **zusätzliche Kommentare** | |
| per-line **Stundenanzahl** | "alle durchgeführten Leistungen und die jeweilige Stundenanzahl" |

**Stated lifecycle** (vendor's own product, but structurally informative): Auftrag exists →
"Neuen Arbeitsschein erstellen" auto-fills from the Auftrag → cleaner opens it in the app →
performs work, adds photos/timestamps/comments → customer signs on the phone on site → the docket
is filed behind the Einsatz → one click converts it into a Rechnung.

**Design consequence:** once signed, freeze the record and version any change. It is the
customer-facing proof of performance. See `gr-auftrag-und-faktura` for the invoice half.

---

## E. Vier-Farben-System

Source: https://pland.app/arbeitslexikon/vier-farben-system

| Farbe | Reserved area / objects (verbatim scope) |
|---|---|
| **Rot** | Toilette und Urinale sowie die umliegenden Fliesenbereiche |
| **Gelb** | restliches Badezimmer: Fliesen, Waschbecken und Ablagen, Armaturen, Spiegel, Duschkabinen, Badewannen |
| **Grün** | Küchenbereiche und Krankenzimmer |
| **Blau** | Oberflächen, Möbel, Gegenstände in Wohnzimmern, Kinderzimmern und Büroräumen |

Purpose: "Das System soll bewirken, dass die **Übertragung von Keimen und Bakterien** zwischen den
verschiedenen Oberflächen verhindert wird" / "hilft, **Keimverschleppungen** zu vermeiden".

**Wechseltuchmethode** (same page): "für **jeden neuen Raum oder Reinigungsbereich** ein **frisches
Tuch**"; used cloths are washed "in der dafür vorgesehenen Temperatur" before reuse. **The
temperature is not stated on the source page.** The Wechseltuchmethode paragraph appears twice
verbatim on that page — a CMS duplication artefact, not two rules.

Cross-reference: the DIN page independently describes colour coding as the DIN 13063 practice
example — "spezielle **Farbcode-Systeme** für Reinigungstextilien … Zum Beispiel würden Tücher für
Toiletten nie in Patientenzimmern eingesetzt" (https://pland.app/arbeitslexikon/din-normen). The
2025 hygiene blog names only "**farbkodierte Reinigungstücher** zur Vermeidung von
Kreuzkontamination" with **no colour list at all**
(https://pland.app/blog/hygienestandards-in-der-gebaudereinigung-2025).

**Four caveats before you hard-code this:**
1. The page cites **no DIN, no RKI, no BGR** — it presents the mapping as established practice.
2. Only **four** colours are given; outdoor and waste areas are unassigned — *nicht belegt*.
3. **Ungeprüft:** conventions vary between operators (red is sometimes "high-risk sanitary" in
   general; some operations add white for food-prep/high-hygiene).
4. → Model it as a configurable `Farbcode(farbe, bereich, beschreibung)` table per tenant, with the
   mapping above as the seeded default. Attach the colour both to the **Bereich** (which colour
   applies here) and to the **cloth/material** (which colour this item is), so a mismatch is
   detectable. The Wechseltuchmethode then makes cloth demand a computable function of the plan:
   one fresh cloth per distinct room/area per visit, split by colour.

---

## F. DIN / EN / ISO norms named by the sources

Two pages name norms. They agree on five and disagree on one; both are reproduced.

### F1. From the Arbeitslexikon (6 norms)

Source: https://pland.app/arbeitslexikon/din-normen

| Norm | Title/subject as given | What the page says it governs |
|---|---|---|
| **DIN EN 13549** | "Qualität in der Gebäudedienstleistung" | Requirements for QM systems specific to cleaning services. Covers Planung, Ausführung, Evaluierung, incl. defining cleaning standards, methods and **Frequenzen**. Sets **Qualitätsindikatoren**, distinguishing **optische** (visible dirt) from **hygienische Defizite** (Keimbelastung). Basis for regular internal audits. |
| **DIN 77400** | "Reinigung von Schulen und Bildungseinrichtungen" | Schools, universities, kindergartens. Sets **how often** each area type (Klassenräume, Flure, Toiletten, Gemeinschaftsräume) must be cleaned; heavily used zones such as Toiletten or Kantinen may need **daily** cleaning. Prescribes agents and techniques per surface. |
| **DIN 13063** | "Reinigung in Krankenhäusern und medizinischen Einrichtungen" (later on the same page: „Krankenhaushygiene – Anforderungen an die Reinigung") | Only **desinfektionsmittelgeeignete**, germ-killing, material-compatible products. Sensitive areas — Operationssäle, Intensivstationen, Isolierzimmer — cleaned/disinfected more often, "teilweise **mehrmals täglich**". Quality verified by **mikrobiologische Tests**. Practice example: colour-coded textiles. |
| **DIN EN ISO 14001** | "Umweltmanagement in der Reinigung" | Environmental management system: efficient use of Wasser, Energie und Reinigungsmittel; **biologisch abbaubare** agents; Schadstoffreduzierung. Practice example: dosierte Spendersysteme. |
| **DIN 18379** | "Reinigung von raumlufttechnischen Anlagen" | Cleaning of ventilation and A/C systems to preserve **Luftqualität**; mechanical methods (Absaugen, Bürsten von Lüftungsschächten) and chemical methods. **See §K1 — this attribution is doubtful.** |
| **DIN EN 1822** | "Filter für die Raumluftreinigung" | Filters in ventilation systems. Defines **Filterklassen** up to **HEPA**, and how effectively a filter must retain Staub, Pollen, Krankheitserreger. Target areas: Labore, Krankenhäuser, industrial Reinräume. |

### F2. Additionally from the blog (1 more)

Source: https://pland.app/blog/reinigungsstandards-und-din-normen---was-muss-man-als-gebaudereinigung-einhalten

| Norm | Title/subject as given | What the page says it governs |
|---|---|---|
| **DIN 18065** | "Reinigung von Treppenhäusern" | "betrifft die Pflege und Reinigung von Treppenhäusern, um deren Sicherheit und Sauberkeit zu gewährleisten. Sie legt fest, welche Reinigungsmethoden anzuwenden sind und wie häufig eine Reinigung erfolgen sollte." **See §K1 — this attribution is doubtful.** |

### F3. Legal status of a DIN norm — as stated

- "Normen wie diese sind **nicht gesetzlich vorgeschrieben**."
- "Die Einhaltung von DIN-Normen ist **freiwillig**, es sei denn, sie wird **durch Verträge oder
  Gesetze verbindlich** gemacht."
- Four operating mechanics: **Definition eines Standards → Freiwillige Anwendung → Zertifizierung →
  Kontinuierliche Überarbeitung**.
- Five uses in a cleaning business: 1. Qualitätssicherung · 2. Arbeitsanweisungen und Schulung ·
  3. **Angebots- und Vertragsgestaltung** (clients frequently require a named DIN norm; compliance
  is a tender advantage) · 4. Sicherheit und Gesundheitsschutz · 5. Umweltschutz.
- Four benefits: Verbesserte Qualität · Vertrauen und Transparenz · Rechts- und Vertragssicherheit ·
  Effizienzsteigerung.

Sources: both pages above.

**Design consequence:** a norm is not a global setting. Model `Norm(nummer, titel, geltungsbereich,
ist_zertifizierbar)` and attach it **per contract** (`vereinbarte_normen`), because a voluntary norm
becomes a binding obligation with audit consequences the moment a customer writes it into the
contract. Key on the **number**, never the title — DIN 13063 carries two different titles on the
same page.

---

## G. Hygienestandards

Source for the whole section: https://pland.app/blog/hygienestandards-in-der-gebaudereinigung-2025

**Definition:** "Hygienestandards sind feste Richtlinien und Verfahren, die sicherstellen, dass eine
Reinigung nicht nur **sichtbar, sondern auch mikrobiologisch wirksam** ist. Sie betreffen sowohl die
Auswahl der Reinigungsmittel als auch die **Reinigungsfrequenz, -technik und Schulung der
Mitarbeitenden**."

**Three stated foundations:** DIN-Normen (DIN EN 13549) · **RKI-Richtlinien** (Robert Koch-Institut)
for sensitive areas such as hospitals · **Desinfektionspläne und Reinigungsprotokolle**.

**Named practices:** disinfectants per the **VAH-Liste**; **Wischdesinfektion** with VAH-listed
products on Kontaktflächen, **Einwirkzeit beachten** (also
https://pland.app/blog/reinigungsmethoden-fur-verschiedene-oberflachen-so-reinigen-profis-richtig);
**farbkodierte Reinigungstücher** against Kreuzkontamination; regular Mitarbeiterschulungen;
transparent Qualitätskontrollen through **Checklisten und Inspektionen**.

**Four sectors with especially strict requirements:**

| Sektor | Named venues |
|---|---|
| **Gesundheitswesen** | Kliniken, Arztpraxen, Pflegeeinrichtungen |
| **Lebensmittelindustrie** | Produktionsräume, Küchen, Lagerflächen |
| **Bildungseinrichtungen** | Schulen, Kindergärten |
| **Büros und öffentliche Einrichtungen** | Sanitäranlagen, Gemeinschaftsräume |

**Stated benefits:** Schutz vor Infektionskrankheiten · Erfüllung gesetzlicher Auflagen · Erhöhung
der Mitarbeitersicherheit · Verbesserung des Unternehmensimages · Reduzierung krankheitsbedingter
Ausfälle.

**Design consequence:** a `Hygienezone` on the Bereich with those four levels gates which agents are
permitted (`vah_gelistet`), whether a Desinfektionsplan is required, and the minimum frequency.
A disinfection task must carry a started/confirmed **Einwirkzeit** as liability evidence.

---

## H. Material, Geräte, Verbrauchsmittel

Source unless marked: https://pland.app/blog/gebaudereinigung-was-fur-material-brauche-ich

### H1. Reinigungsmittel

| Mittel | Purpose as stated |
|---|---|
| **Allzweckreiniger** | "darf in keinem Reinigungswagen fehlen"; from floors to worktops |
| **Glasreiniger** | glass and mirrors, "um Schlieren und Streifen zu vermeiden" |
| **Sanitärreiniger** | WCs, showers, changing rooms; dissolves **Kalkablagerungen und Seifenreste** |
| **Neutralreiniger** | mild, "schonend für empfindliche Materialien wie **Naturstein**" |
| **Desinfektionsmittel** | high-traffic buildings, "insbesondere in **Krankenhäusern oder Schulen**" |
| **Edelstahlreiniger (ölhaltig)** | stainless steel — https://pland.app/blog/reinigungsmethoden-…-profis-richtig |
| **Alkalische Reiniger** | grease and soap residue — same source |
| **Säurehaltige Reiniger** | limescale — same source; **never on Zementfugen** |
| **Spezialreiniger für Naturstein** | natural stone — same source |
| **Glasreiniger auf Alkoholbasis** | professional glass method — same source |
| **Pflegemittel** | building the care film on PVC/linoleum/wood — same source |

Household substitutes named on the consumer page
(https://pland.app/blog/reinigungsmethoden-fur-verschiedene-oberflachen---so-bleibt-alles-strahlend-sauber):
**Essig** against limescale · **Natron** against odours and grease · **Zitronensäure** for shine ·
soap and warm water for most surfaces.

### H2. Tücher, Mopps, Schwämme, Zubehör

| Item | Purpose as stated |
|---|---|
| **Mikrofasertücher** | "nehmen Staub, Schmutz und Feuchtigkeit besonders gut auf, ohne Reinigungsmittel zu verschwenden" |
| **Schwämme / Topfschwämme** | stubborn soiling; kitchen grease and food residue |
| **Baumwolltücher** | large areas, "robust und saugfähig" |
| **Fransenmopps / Flachmopps** | floor cleaning |
| **Eimer und Presse** | the press removes excess water "sodass der Boden nicht übermäßig nass wird, was besonders auf glatten Oberflächen gefährlich sein kann" |
| **Besen / Kehrbleche** | quick interim sweeping |
| **Staubsauger** | carpets and hard floors; **HEPA-Filter** for daily carpet vacuuming |
| **Fugenbürsten** | treat joints separately — profi page |
| **Polierpads** | natural-stone gloss refresh — profi page |
| **Pad-Systeme (Encapsulation)** | interim carpet cleaning — profi page |
| **Reinigungskarren** | "alle benötigten Materialien … griffbereit … leicht von Raum zu Raum" |
| **Müllsäcke, Müllzangen** | |
| **Dosiersysteme** | precise dosing; a safety and sustainability lever |
| **Kabelhalter / Akkugeräte** | avoid trip hazards from cables |
| **Warnschilder ("Achtung, rutschig!")** | mandatory before wet work per the safety page |
| **Schmutzfangmatten / rutschfeste Matten** | entrance areas, seasonal and winter slip prevention |

### H3. Maschinen

| Maschine | Purpose as stated |
|---|---|
| **Bodenreinigungsmaschinen** | large areas: Flure, Eingangshallen, Einkaufszentren |
| **Scheuersaugmaschine** | scrubbing plus immediate suction of dirty water, "sodass der Boden schnell wieder betreten werden kann" |
| **Einscheibenmaschine** | intensive hard-floor cleaning, polishing, and **Einpflegen** of care products |
| **Nass-Trocken-Sauger** | named as a machine requiring Einweisung — safety page |
| **Hochdruckreiniger** | same |
| **Dampfreiniger** | upholstery; "tötet Keime und frischt Farben auf" — consumer page |
| **Mobile Osmoseanlage** | pure-water production on site — Reinwasser page |
| **Ionenaustauscher / Mischbettharz** | alternative demineralisation — Reinwasser page |

### H4. Fensterreinigungs-Kit

| Item | Purpose |
|---|---|
| **Fensterabzieher (Gummiabzieher)** | streak-free finish |
| **Einwascher** | applies the agent evenly to the pane |
| **Teleskopstangen** | high or hard-to-reach windows, "sicher vom Boden aus zu arbeiten, ohne Leitern zu verwenden" |
| **Carbonstangen** | pure-water method, "vom Boden aus in bis zu **25 Meter** Höhe" |
| **Waschbürsten** | pure-water method |

### H5. Reinwasser / Osmose — the quantified figures

Source: https://pland.app/blog/reinigen-mit-reinwasser---wie-osmoseanlagen-die-gebaudereinigung-revolutionieren
**Caveat:** this page is partly an advertisement for a third party (Osmobil). Label the figures as
vendor-adjacent if reused.

| Fact | Value |
|---|---|
| Purity of osmosis water | "zu fast **100 %** aus reinen H₂O-Molekülen" |
| Evaporation | "Das verbleibende H₂O verdunstet zu **100 %**" — surfaces may be left wet |
| Running cost, Mischbettharz/Ionenaustauscher | **50–200 € per 1000 Liter**, depending on inlet hardness |
| Running cost, mobile osmosis | "im Mittel bei lediglich **1,- € pro 1000 Liter**" |
| Speed vs. classic method | "ca. beim **3-4 Fachen** … (grade in großen Höhen)" |
| Max. working height from the ground | **25 Meter** with carbon poles |
| Adoption | "in den letzten **15 Jahren** zum Branchenstandard geworden" |
| Chemical exception | only for **Fett oder Öl** — spot chemical use or a manual Grundreinigung |
| Application areas | Glasreinigung · Solar- und Photovoltaikanlagen · Metall- und Kunststofffassaden · Werbeschilder |
| Height-access saving | "kann … auf recht teure und spezielle **Hubsteiger** … verzichtet werden" |

**Ungeprüft:** field practice measures pure-water quality as conductivity/TDS (typically <10 ppm at
the brush), not as "almost 100 % H₂O".

---

## I. Surface → method → agent → caution

Compiled from https://pland.app/blog/reinigungsmethoden-fur-verschiedene-oberflachen-so-reinigen-profis-richtig
(**P**, professional, 22 July 2025) and
https://pland.app/blog/reinigungsmethoden-fur-verschiedene-oberflachen---so-bleibt-alles-strahlend-sauber
(**C**, consumer, 10 November 2025). Where P and C disagree, both rows are kept — see §K2.

| Oberfläche | Verfahren | Mittel | Vorsicht / Verbot | Src |
|---|---|---|---|---|
| **Fliesen und Keramik** | Nasswischen mit Mikrofaserbezug; Hochdruckreinigung im Außenbereich | Alkalische Reiniger gegen Fett und Seifenreste; säurehaltige Reiniger gegen Kalk | Fugen separat mit Fugenbürsten; **säurehaltige Reiniger nicht bei Zementfugen** | P |
| **Fliesen (Haushalt)** | Allzweckreiniger; Abzieher an Duschwänden | Allzweckreiniger | — | C |
| **Fugen** | Paste aus **Backpulver und Wasser**, alte Zahnbürste | Backpulver + Wasser | — | C |
| **Naturstein (Marmor, Granit)** | Feuchtwischen; Polierpads zur Glanzauffrischung | Neutraler Reiniger; **Spezialreiniger für Naturstein** | "Empfindlich gegen **Säure und starke Alkalien**" | P |
| **PVC** | Sprayreinigung; Wischpflege; Einscheibenmaschine bei starker Verschmutzung | geeignetes Pflegemittel | Regelmäßige **Pflegefilmbildung** zur Werterhaltung | P |
| **Linoleum** | wie PVC | wie PVC | "**empfindlicher gegenüber alkalischen Reinigern**" als PVC | P |
| **Teppichböden** | Tägliches Staubsaugen mit **HEPA-Filter**; Zwischenreinigung mit **Pad-Systemen (Encapsulation)**; **Nassshampoonierung / Sprühextraktion** bei Grundreinigung | — | Lange **Trocknungszeiten** — schedule around them | P |
| **Teppichböden (Grundreinigung)** | "mit speziellen Maschinen tiefengereinigt" | — | "Regelmäßiges Staubsaugen reicht hier oft nicht aus" | grundreinigung-wohnung page |
| **Polstermöbel** | Schonende **Trockenextraktion** oder **Schaumpolsterreinigung**; punktuelle Fleckentfernung | Mikrofasertuch + geeigneter Reiniger | "Reinigung immer mit **Materialverträglichkeitstest** beginnen" | P |
| **Textilien und Polster (Haushalt)** | Absaugen; Flecken **tupfen, nicht reiben**; Dampfreiniger | feuchtes Tuch + mildes Mittel; **Natron** gegen Gerüche | "nicht reiben" | C |
| **Edelstahl** | Wischen **immer in Schleifrichtung** | **Edelstahlreiniger (ölhaltig)**, Mikrofasertücher | Gefahr **Flugrost** und **Schlieren** durch falsche Mittel | P |
| **Edelstahl (Haushalt)** | Abwischen; **Natron auf feuchtem Schwamm**; in Schleifrichtung polieren; trocken nachreiben | warmes Wasser + Spülmittel; Natron | **Vermeide Scheuermittel, Stahlwolle, chlorhaltige Reiniger** | C |
| **Glas und Spiegel** | **Abziehertechnik** mit Einwascher und Gummiabzieher | **Glasreiniger auf Alkoholbasis** | **Keine Krepp- oder Zellstofftücher** (Verkratzungsgefahr) | P |
| **Glas und Spiegel (Haushalt)** | Sprühflasche + Mikrofasertuch; Zeitungspapier als Alternative | Glasreiniger **oder Essig-Wasser 1:1** | **Nicht in direkter Sonne reinigen** — Streifenbildung | C |
| **Holzoberflächen** | Leicht angefeuchtetes weiches Tuch, **in Faserrichtung**, trocken nachreiben | mildes Spülmittel + warmes Wasser; Holzpflegemittel mit natürlichen Ölen für geölte/gewachste Möbel | "Holz reagiert stark auf **Feuchtigkeit und aggressive Reinigungsmittel**" | C |
| **IT-Geräte und Bildschirme** | **Trockene, antistatische Tücher**; minimal **Isopropanol-Wasser-Gemisch** bei Bedarf | Isopropanol-Wasser | **"Niemals direkt Flüssigkeit aufs Gerät geben"** | P |
| **Kontaktflächen (Lichtschalter, Türgriffe)** | **Wischdesinfektion** | **VAH-gelistete Produkte** | **Einwirkzeit beachten** und dokumentieren | P |
| **Glas, Solarmodule, Kunststoff-/Metallfassaden (außen, Höhe)** | **Reinwasser (Osmose)** mit Teleskop-/Carbonstange und Waschbürste; Fläche nass stehen lassen | reines H₂O, **kein Chemieeinsatz** | Bei Fett oder Öl punktueller Chemikalieneinsatz oder manuelle Grundreinigung | Reinwasser page |

**Why the choice matters** — the four consequences of the wrong method, verbatim (P): materials
damaged ("durch **Korrosion, Kratzer, Ausbleichen**") · **Optik** degraded · long-term **hygienische
Risiken** · expensive **Reklamationen oder Haftungsfragen**.

**Design consequence:** model prohibitions as first-class rows, not as free text. An
`OberflaechenRegel(oberflaeche, methode, mittel, erlaubt: bool, warnung_text, technik_hinweis)`
lets "Säure auf Zementfuge" exist as `erlaubt=False` with a hard UI warning, and lets technique
instructions ("in Schleifrichtung", "in Faserrichtung", "tupfen, nicht reiben") reach the operative
on the Einsatz. The prohibition rows are the safety-critical half of the table.

---

## J. Arbeitssicherheit und Gesundheit

### J1. The seven safety rules

Source for the whole table:
https://pland.app/blog/arbeitssicherheit-in-der-gebaudereinigung-die-7-wichtigsten-regeln-fur-ein-sicheres-arbeitsumfeld

| # | Regel | Concrete requirements printed |
|---|---|---|
| **1** | **Schutzkleidung tragen** | **Handschuhe** — "Besonders bei der Arbeit mit Desinfektionsmitteln sind **säure- und laugenresistente Handschuhe Pflicht**". **Sicherheitsschuhe** — "**Antirutschsohlen** sind in feuchten Bereichen unverzichtbar". **Atemschutzmasken** in dust- or chemically loaded rooms. **Schutzbrillen** when handling spray cleaners/chemicals. Plus **regelmäßige Überprüfung der Schutzkleidung auf Schäden**. |
| **2** | **Richtiges Heben und Tragen schwerer Lasten** | **Aus den Beinen heben** — knees bent, back straight. **Gewicht verteilen** over both hands/shoulders. **Hilfsmittel nutzen** — Wagen oder Rollcontainer. Regular **Schulungen zur Ergonomie**. |
| **3** | **Vorsicht im Umgang mit Chemikalien** | **Gefahrstoffetiketten lesen** — know and observe the **Sicherheitsdatenblätter** and labels. **Richtige Dosierung** — never overdose; modern **Dosiersysteme** help. **Mischverbote beachten** — some agents must never be combined because they release dangerous vapours (**z. B. Säuren und Chlor**). **Lüftung sicherstellen**. |
| **4** | **Rutschgefahr minimieren** | Slippery floors named: **Fliesen, Laminat oder Marmor**. **Warnschilder aufstellen** ("Achtung, rutschig!") clearly visible. **Passende Reinigungsmittel** — residue-leaving products make surfaces slippery. **Rutschfeste Schuhe**. |
| **5** | **Leitern und Tritte sicher verwenden** | **Stabile Leitern**, regularly checked for damage, only tested models. **Sicher aufstellen** on level ground; **die oberen drei Sprossen dürfen nicht betreten werden**. **Bei Arbeiten in großer Höhe ist die Verwendung von Sicherungsgurten verpflichtend.** Context: Glas- oder Fassadenreinigung. |
| **6** | **Maschinen und Geräte richtig bedienen** | Machines named: **Nass-Trocken-Sauger, Hochdruckreiniger, Scheuersaugmaschinen**. **Einweisung sicherstellen** — thorough training before use. **Regelmäßige Wartung** and defect checks. **Kabelmanagement** — avoid trip hazards via Kabelhalter or Akkugeräte. |
| **7** | **Regelmäßige Schulungen und Unterweisungen** | "Arbeitsschutz ist … ein kontinuierlicher Prozess." Topics named: **Erste Hilfe am Arbeitsplatz** · **Gefahrenanalyse bei neuen Einsatzorten** · **Verhalten im Notfall, z. B. bei einem Chemieunfall**. |

**The page states "Pflicht" and "verpflichtend" without naming any legal basis.** No ArbSchG,
GefStoffV, BetrSichV, TRGS or DGUV rule is cited anywhere in the corpus — treat those duties as
unsourced and see §K4.

### J2. Health hazards — five categories

Source: https://pland.app/blog/gesundheitsrisiken-bei-reinigungskraften---gefahren-erkennen-vorbeugen

| Kategorie | Hazards named | Data point printed |
|---|---|---|
| **1. Chemische Gefahren** | **VOCs**, irritant substances, disinfectants → Atemwegserkrankungen, **Asthma**, **chronische Bronchitis**. Skin: Irritationen, **Kontaktdermatitis**, **Ekzeme**. Eyes: splashes and aerosols. Long term: **quaternäre Ammoniumverbindungen ("Quats")**, **Ethanolamine**, aggressive **Lösemittel**; "erhöhte Risiken für bestimmte **Krebsarten**" | "diejenigen, die **mehr als fünfmal täglich Reinigerspray** verwenden, [berichten] signifikant häufiger Symptome wie Atembeschwerden oder Husten" — **the study is cited with no author, journal or year** |
| **2. Ergonomische Belastungen** | Bücken, Strecken, Heben, Handling von Maschinen und Wagen → complaints in **Rücken, Schultern, Armen**. Vibration from **Polierern oder Bodenpuffern** → **Hand-Arm-Vibrationssyndrom (HAVS)** | "Laut **OSHA** entstehen solche Belastungen durch schlecht angepasste Werkzeuge, unvorteilhafte Körperhaltungen und **nicht genug Pausen**" — **OSHA is a US agency; a German feature needs a German source** |
| **3. Physische Unfallrisiken** | **Rutsch- und Sturzgefahr** (nasse Böden, lose Kabel, abgestellte Geräte) · **Höhenarbeiten** · **elektrische Gefahren** bei schlechter Wartung | — |
| **4. Biologische Risiken** | **Bakterien, Viren, Pilze** via contaminated surfaces and waste · **scharfe Gegenstände** such as **Nadeln** → Stichverletzungen with infection risk · "Werden **Reinigungs- und Desinfektionsarbeiten nicht sauber getrennt** …, erhöht sich das Risiko, dass Keime auf andere Flächen übertragen werden" | Sites named: medizinische Einrichtungen, öffentliche Toiletten, stark frequentierte Bereiche |
| **5. Psychische Belastungen** | **Zeitdruck & Arbeitsintensität** — strict time targets, **enge Einsatzfenster** → Stress, Überlastung, **Burnout** · **Isolation & Unsichtbarkeit** — working alone, often **nachts** · **mangelnde Wertschätzung** | — |

**Five protective-measure groups, as printed:**

1. **PSA** — Schutzbrillen oder Gesichtsschutz for chemical work; **Atemschutzmasken (Halb- oder
   Vollmasken)** where vapours, dust or **Schimmel** are present; rutschfeste Schuhe and gloves.
2. **Ergonomische Arbeitsmittel** — **höhenverstellbare Stiele**, ergonomic grips, light devices;
   regular **Wartung** so **Vibrationen reduziert** werden.
3. **Organisation & Schulung** — "**Arbeitspläne so gestalten, dass Pausen und Wechsel der Aufgaben
   berücksichtigt werden**"; chemical-handling training incl. **Sicherheitsdatenblätter**;
   Dehn- und Entspannungsübungen in Pausen.
4. **Sicherer Umgang mit Gefahrstoffen** — prefer less hazardous formulations; **nie Reinigungsmittel
   mischen**; correct **Lagerung** and transparent **Gefahrstoffkennzeichnung**.
5. **Anerkennung & psychosoziale Absicherung** — visible appreciation, team exchange, measures
   against isolation.

**Design consequence:** point 3 makes the *planner* a safety instrument — a roster that packs
Einsätze without breaks or task variation is an occupational-health defect, not just a scheduling
one. That belongs in `gr-einsatzplanung` as a planning-time check.

### J3. Safety routine per Einsatz (ordered)

Source: the safety page above.

Gefahrenanalyse for a new Einsatzort → issue and inspect PSA for damage → read the
Gefahrstoffetikett / Sicherheitsdatenblatt → dose via Dosiersystem, **never mix** (acids + chlorine)
→ ventilate → place "Achtung, rutschig!" signs before wet work → inspect the ladder, level ground,
never the top three rungs, harness at height → machine only after Einweisung, maintenance current,
cables managed → refresh training regularly (first aid, hazard analysis, chemical-accident
behaviour).

---

## K. Contradictions, gaps and things to verify before shipping

**K1 — DIN attributions that do not match the DIN catalogue (Ungeprüft, but load-bearing).**
The sources attribute "Reinigung von Treppenhäusern" to **DIN 18065** and "Reinigung von
raumlufttechnischen Anlagen" to **DIN 18379**. In the German standards catalogue, DIN 18065 is
normally *Gebäudetreppen — Begriffe, Messregeln, Hauptmaße* (stair geometry, not stair cleaning),
and DIN 18379 is the VOB/C ATV for *Raumlufttechnische Anlagen* (installation works, not cleaning);
hygienic cleaning of RLT systems is usually associated with **VDI 6022**. Hospital cleaning in
practice is driven by the **KRINKO/RKI** recommendation rather than by a "DIN 13063".
**Do not write any of these into a contract template or a compliance feature without checking the
DIN catalogue first.**

**K2 — Two conflicting method articles for the same surfaces.** The professional page prescribes an
ölhaltiger Edelstahlreiniger and alcohol-based Glasreiniger with Einwascher/Abzieher; the consumer
page prescribes warm water + washing-up liquid with Natron, and vinegar-water 1:1 with newspaper.
Both agree only on wiping **in Schleifrichtung**. Which is the house standard is unresolved — decide
it per tenant, do not hard-code one.

**K3 — Interval taxonomies differ between two pages** (see §B) and Grundreinigung/Glas frequencies
are given at two different intervals each. Model both per surface / per glass class.

**K4 — No statute anywhere in this corpus.** ArbSchG, GefStoffV, BetrSichV, TRGS, DGUV rules,
BioStoffV, IfSG, ArbMedVV are never cited, even though the safety and health pages describe duties
that in Germany derive from them. **Ungeprüft** but worth knowing exists: §5 ArbSchG
Gefährdungsbeurteilung; GefStoffV + TRGS 401/500/540 (hazardous substances, skin exposure);
BetrSichV (work equipment, ladders); DGUV Vorschrift 1 and the branch rules for Gebäudereinigung;
DGUV Regel 112-190 (respiratory protection); BioStoffV and TRBA 250 (biological agents in
healthcare); ArbMedVV (occupational health checks for wet work and respirators); Hautschutzplan
duties for Feuchtarbeit (German occupational-medicine practice treats >2 h/day of wet work or
occlusive gloves as the trigger). Verify each before it reaches a feature.

**K5 — No per-room-type Unterhaltsreinigung checklist exists in the corpus.** The only granularity
is the 5-step execution sequence and the 8-step business checklist in `rollen-und-prozesse.md`.
A room-type matrix (Büro / Sanitär / Treppenhaus / Küche / Verkaufsfläche, each with its own task
set and frequency) is **nicht belegt** and must come from customer research.

**K6 — No time standards anywhere.** No m²/h, no **Leistungswerte**, no minutes-per-task figures, no
wage figures. The Angebot is described only as "Reinigungsleistungen + Materialien + Arbeitsstunden".
**Ungeprüft:** Leistungswerte per surface × method are what real bids in this market are built from
(usually RAL/Bundesinnungsverband tables or the company's own measured values). This repo's
`Zone.minutes_per_visit` plus `ZoneCalibration` is a defensible substitute — it *measures* the
Leistungswert instead of quoting one (`apps/planning/models.py:58`, `apps/planning/calibration.py`).

**K7 — Sonderreinigung has no checklist** in the corpus — only three examples (Bauschluss, Fassade,
Graffiti). Likewise the star-rating scale on a Leistungsnachweis is never defined.

**K8 — Wechseltuch washing temperature is unspecified** ("in der dafür vorgesehenen Temperatur").
*Nicht belegt.*

---

## Quellen

**pland.app, crawled 2026-08-29**

- https://pland.app/arbeitslexikon/unterhaltsreinigung
- https://pland.app/arbeitslexikon/grundreinigung
- https://pland.app/arbeitslexikon/glasreinigung
- https://pland.app/arbeitslexikon/reinigungsintervall
- https://pland.app/arbeitslexikon/reinigungsplan
- https://pland.app/arbeitslexikon/vier-farben-system
- https://pland.app/arbeitslexikon/din-normen
- https://pland.app/blog/gebaudereinigung-reinigungsplan-hier-kostenlose-vorlage-herunterladen
- https://pland.app/blog/hier-kostenlose-arbeitsschein-vorlage-herunterladen
- https://pland.app/blog/reinigungsstandards-und-din-normen---was-muss-man-als-gebaudereinigung-einhalten
- https://pland.app/blog/hygienestandards-in-der-gebaudereinigung-2025
- https://pland.app/blog/reinigungsmethoden-fur-verschiedene-oberflachen-so-reinigen-profis-richtig
- https://pland.app/blog/reinigungsmethoden-fur-verschiedene-oberflachen---so-bleibt-alles-strahlend-sauber
- https://pland.app/blog/unterhaltsreinigung-die-ultimative-checkliste
- https://pland.app/blog/wie-sieht-eine-grundreinigung-in-einer-wohnung-aus
- https://pland.app/blog/arbeitssicherheit-in-der-gebaudereinigung-die-7-wichtigsten-regeln-fur-ein-sicheres-arbeitsumfeld
- https://pland.app/blog/gesundheitsrisiken-bei-reinigungskraften---gefahren-erkennen-vorbeugen
- https://pland.app/blog/gebaudereinigung-was-fur-material-brauche-ich
- https://pland.app/blog/reinigen-mit-reinwasser---wie-osmoseanlagen-die-gebaudereinigung-revolutionieren
- https://pland.app/blog/saisonale-reinigungstipps-fur-jede-jahreszeit---und-wie-digitale-tools-wie-pland-dabei-unterstutzen-konnen
- https://pland.app/tutorials/beispiel-geschaftsplan (the 0,15 EUR/m² example only)

**Repository, read 2026-08-29**

- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/reinigungsplan.py` (lines 16-34, 64-89)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py` (Zone, lines 42-87)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/calibration.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/taxonomy/migrations/0003_seed_categories.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/catalog/models.py` (safety_datasheet, hazard_pictograms, lines 63-65)
