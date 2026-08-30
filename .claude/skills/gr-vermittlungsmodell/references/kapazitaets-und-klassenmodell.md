# Kapazitäts- und Klassenmodell

How inline turns "what do you have?" into "who may take this job, and at what base price" — and
what the cleaning equivalent has to be instead.

Sources: https://inline-kurier.de/uber-uns (fleet envelopes),
https://inline-kurier.de/kurierfahrten (tariff class cards), https://inline-kurier.de/faq-s,
https://inline-kurier.de/overnight (eligibility rule sets). Crawled 2026-08-29.

Markers: **Fakt** · **Vorschlag** · **Ungeprüft**.

---

## 1. inline's seven fleet classes, verbatim

**Fakt**, https://inline-kurier.de/uber-uns. The page lists the specs **before** the class label
(verified in the raw capture: the first block has no preceding label, the last label has no
following block). Rows 1–6 are headed „**Maximale** Sendungsmaße und Gewicht"; row 7 is headed
„**Ca.** Sendungsmaße und Gewicht" — maximum vs. approximate. **That distinction is real and must
survive any translation.**

| # | Class | Länge | Breite | Höhe | Gewicht | Extra |
|---|---|---|---|---|---|---|
| 1 | **Bike** | 60 cm | 30 cm | 20 cm | 8 kg | — |
| 2 | **Omnium** (Cargobike) | 65 cm | 55 cm | 55 cm | 50 kg | — |
| 3 | **Bullitt** (Cargobike) | 65 cm | 55 cm | 55 cm | 50 kg | — |
| 4 | **PKW** | 100 cm | 70 cm | 50 cm | 100 kg | — |
| 5 | **Kombi** | 150 cm | 100 cm | 70 cm | 350 kg | „Diagonalmaß max. **180 cm** bis **20 cm Durchmesser** (Rolle, Stange etc.)" |
| 6 | **Transporter** | 320 cm | 150 cm | 180 cm | 1.000 kg | „**Europaletten bis 4 Stück**, Platten bis **300x200 cm**; Stangen, Rollen max. **400 cm**" |
| 7 | **Ladebordwand-Transporter** *(Ca.)* | 400 cm | 200 cm | 200 cm | 1.000 kg | „**Europaletten bis 7 Stck.**; Stangen, Rollen max. **500 cm**; inkl. Ladebordwand oder Hebebühne" |

### The tariff view of the same classes

**Fakt**, https://inline-kurier.de/kurierfahrten. The **priced** class set is shorter than the fleet
set — Omnium and Bullitt collapse into one „Cargobike" card, and the Ladebordwand-Transporter
becomes a **surcharge on Transporter** rather than a class of its own.

| Class | Mindestpreis netto | Included | Load envelope in the tariff |
|---|---|---|---|
| **Bike** | 11,50 € | Anfahrt, 2 km ab Startadresse, **5 min** Lade-/Servicezeit | Formate bis **DIN A2**, diagonal max. 120 cm, bis 8 kg |
| **Cargobike** | 11,50 € | idem | L 65 · B 55 · H 50 cm, diagonal max. 120 cm, bis 50 kg |
| **PKW** | 11,50 € | idem | L 100 · B 70 · H 50 cm, diagonal max. 120 cm, bis 100 kg |
| **Kombi** | 18,50 € | idem | L 150 · B 100 · H 70 cm, diagonal max. 180 cm, bis 350 kg |
| **Transporter** | 46,60 € | Anfahrt bis Abholung, 2 km, **15 min** Lade-/Servicezeit | L 320 · B 150 · H 180 cm, bis 1.000 kg, **max. 4 Paletten** |

Surcharges that are properties of the class, not of the job (**Fakt**):
**Zuschlag XL-Bus** (ab 350 cm Länge oder 180 cm Höhe) 15,00 € netto ·
**Zuschlag Bus mit Ladebordwand**, inkl. Hubwagen, 35,00 € netto.

FAQ restatement (**Fakt**): „Fahrrad, Cargobike, PKW, Kombi, Transporter und bei Bedarf Transporter
mit Ladebordwand – **passend zu Größe und Gewicht der Sendung**."

Note the tariff table and the fleet table **do not agree on the Bike envelope**: the fleet page says
60 × 30 × 20 cm, the tariff says „Formate bis DIN A2, diagonal max. 120 cm". Reported, not
harmonised.

---

## 2. What a class does — the four jobs

**Fakt**, from the tariff structure and the allocation sentence below. A class is not a label; it is
a join. It does exactly four things:

1. **Feasibility.** A consignment that exceeds the envelope cannot be taken by that class at all.
2. **Base price.** Each class has its own Anfahrt and its own Mindestpreis.
3. **Which meters run and at what granularity.** Bike/Cargobike/PKW/Kombi include 5 min service time
   and then bill per further started 5 min at 4,00 €; the Transporter includes **15 min** and bills
   per started 15 min at 16,00 €.
4. **Which surcharges apply at all.** „Alle Aufträge der Kategorien **Bike oder Cargobike** sind
   **zuschlagsfrei**" — bikes are entirely exempt from the fuel surcharge. City-Zuschlag and the
   warm-food surcharge exist only on PKW/Kombi.

### The allocation rule, in one published sentence

**Fakt**, https://inline-kurier.de/uber-uns:

> „Deshalb gilt: wenn **Distanz, Größe und Gewicht** der Sendung es erlauben, übernehmen unsere
> Fahrradkuriere in der Regel Ihre Aufträge in Hamburg."

So the policy is: **the smallest / lowest-impact class that distance, size and weight allow**, with
three inputs. The customer describes the consignment; the platform maps it to the cheapest class
whose envelope fits.

### How the customer states the input

**Fakt**, https://inline-kurier.de/bestellung. Three mutually exclusive entry modes, verbatim:
„Wählen Sie hier aus unseren **Sendungsvorschlägen**, geben Sie eine **eigene Sendung** ein oder
wählen Sie direkt ein **Fahrzeug**." Per Packstück: `Anzahl`, `Inhalt der Sendung`, `Länge` cm,
`Breite` cm, `Höhe` cm, `Gewicht` kg.

Disclaimers (**Fakt**): „Sendungsvorschläge und Maße dienen der Orientierung … Beachten Sie, dass
sich der endgültige Preis bei abweichenden Maßen oder Gewichten nachträglich ändern kann." and „Sie
basieren auf den **Maximalmaßen** der jeweiligen Größenklassen."

**The three-way "preset / custom / pick the resource directly" pattern transfers perfectly.** It is
the single best UI import in this file. The *quantities* do not transfer — see §3.

---

## 3. Capacity in cleaning is TIME and QUALIFICATION, not volume and weight

**State this plainly and do not let it blur.** A courier class is a physical envelope: cm and kg
that either fit or do not. A cleaning class is a **capability envelope**: what the crew is
qualified to do, what machine it brings, how high it can reach, whether it may hold a key. And
capacity itself is not a headcount and not a volume — it is **available hours per qualification per
time window**, because most Objekte must be cleaned 05:00–08:00 or 17:00–22:00.

| Dimension | Courier | Cleaning |
|---|---|---|
| The envelope | L × B × H + kg + Paletten + Diagonalmaß | Qualification + equipment + reachable height + hazard clearance + access authorisation |
| The billable quantity | km + started 5/15-min service blocks | **Minutes on site**, derived from m² × Bodenbelag × Verschmutzungsgrad via a Leistungswert (m²/h) |
| Capacity of the network | 130 couriers, 90 motorised / 40 bikes | Hours per Lohngruppe per Zeitfenster — a **calendar**, not a fleet count |
| What blows the envelope | An oversized parcel | An unqualified operator, a missing machine, an expired certificate, a missing key |
| Where the base price comes from | The firm's own choice | A **legislated floor** per Lohngruppe (allgemeinverbindlicher Mindestlohntarifvertrag, § 7 AEntG) plus the member-ratified margin. → `gr-tarif-und-lohn` |

**Fakt (repo).** Time is already the unit everywhere in this codebase: `Zone.minutes_per_visit`
(`apps/planning/models.py:58`), `Shift.duration_minutes` / `actual_minutes`
(`apps/planning/models.py:149,159`), `Offer.estimated_minutes` (`apps/marketplace/models.py:135`),
and `Offer.implied_hourly` documented as „singura bază reală de comparație între oferte"
(`apps/marketplace/models.py:161-166`). The repo already picked the right unit. What is missing is
the **qualification envelope**.

There is one volume-shaped input, `ServiceRequest.area_sqm` with `MinValueValidator(1)`
(`apps/marketplace/models.py:61-63`, **Fakt**) — and its help text says why: without area the offers
are not comparable. Note it is an **input to the time estimate**, not the billed quantity. Keep that
direction.

---

## 4. Vorschlag: the cleaning capability class model

Everything in this section is **Vorschlag** unless a `file:line` is given. Names are German because
they are domain vocabulary; identifiers are English per the repo convention.

### 4.1 The class set

A small, **closed, enumerated** set — the whole value of inline's model is that there are seven
classes, not seven hundred.

| Klasse | Crew | Equipment envelope | Typical Leistungsarten |
|---|---|---|---|
| **K1 — Einzelkraft** | 1 Person | Handgeräte, Wagen, keine Maschine | Unterhaltsreinigung Büro, Treppenhausreinigung, Praxis nach Feierabend |
| **K2 — Einzelkraft mit Maschine** | 1 Person | + Einscheibenmaschine oder Kleinscheuersaugmaschine | Grundreinigung kleiner Flächen, Zwischenreinigung |
| **K3 — 2er-Team** | 2 Personen | wie K2, doppelt | Objekte mit Zeitfenster-Druck, Umzugs-/Bauzwischenreinigung |
| **K4 — Maschinenteam** | 2+ Personen, mit Vorarbeiter | + Aufsitz-/Großscheuersaugmaschine, Nass-/Trockensauger | Industrie- und Hallenflächen, Grundreinigung großer Objekte |
| **K5 — Glasreinigung bis 3 m** | 1–2 Personen | Wischer, Teleskopstange, Leiter | Glas- und Rahmenreinigung im Innenbereich, Ladenlokale |
| **K6 — Höhenzugang** | Team mit Nachweis | + Hubarbeitsbühne / Gerüst / PSAgA, Bedienberechtigung | Fassaden- und Glasreinigung in Höhe, Außenanlagen |
| **K7 — Bauendreinigung** | Team | + Bauschutt-Handling, Industriesauger, Entsorgung | Bauzwischen-, Bauend-, Bauschlussreinigung |
| **K8 — Hygiene / DDD** | Team mit Sachkunde | + Desinfektionsmittel nach Liste, ggf. Schädlingsbekämpfung | Arztpraxen, Labore, Kitas, Lebensmittelbetriebe |

**Ungeprüft.** The crawled sources are a courier site and establish **nothing** about cleaning
equipment classes, machine categories, DDD (Desinfektion, Desinsektion, Deratisierung) or
height-access qualification requirements. This table is domain knowledge and every row must be
checked against the actual Nachweise the Innung / BG BAU require before it drives eligibility in
production. → `gebaeudereinigung-domain` for the vocabulary, and a Fachmann for the requirements.

### 4.2 The envelope, as fields

A class constrains matching along five axes. All **Vorschlag**:

| Axis | Field shape | Constrains |
|---|---|---|
| **Qualification** | required Lohngruppe / Nachweis codes (Sachkunde, Bedienberechtigung, PSAgA-Unterweisung) | Whether the member firm may bid at all |
| **Equipment** | required machine kinds | Joins to `devices.Device.kind` (`apps/devices/models.py:24-29`, **Fakt** — VACUUM / SCRUBBER / POLISHER / STEAM / OTHER), which already carries `site` and `status` |
| **Reachable height** | `max_height_m` | Fassade, Glas in Höhe |
| **Hazard / hygiene clearance** | flags: Desinfektion, HACCP, RKI-Hygieneplan, Führungszeugnis required | Praxen, Labore, Kitas, Schulen |
| **Access authorisation** | may hold a key / transponder / alarm code; vetting level required | **The axis with no courier analogue at all** |

That last axis deserves its own sentence, because it is the whole asymmetry between the two
industries: **a courier is never authorised to enter unsupervised, so inline's model has no field
for it.** A cleaning class must state whether an operator in that class may hold a
Generalschlüssel, and a class that may must require a vetting level and an insurance sum. See
`references/zentrale-und-disposition.md` §5.

### 4.3 How a class constrains matching

Mirror inline's four jobs, adapted:

1. **Feasibility (hard gate).** An Objekt declares a required class; a member firm declares the
   classes it can staff. A firm that cannot staff the class **is not shown the request at all** —
   not ranked lower, excluded. This is the same shape as the existing candidate filter in
   `suggest_providers`, which already intersects `services__category` and `areas__locality`
   (`apps/marketplace/scoring.py:170-178`, **Fakt**); the class filter is a third intersection.
2. **Base price band.** Per class, derived from the Lohngruppe floor upward. Never a literal.
3. **Which meters run.** inline's "N minutes included, then billed per started 15 min" is the right
   mechanic and maps onto both the Ladehilfe rule and German Zeiterfassung practice. Keep it.
4. **Which surcharges apply.** Erschwernis- and Belastungszuschläge attach to the class of work,
   exactly as the City-Zuschlag attaches to the vehicle class. Values and cumulation rules:
   → `gr-tarif-und-lohn` (only the highest applicable surcharge is paid — they do not stack).

### 4.4 Where the analogy inverts: the tiebreaker

**Fakt** (inline): the smallest capable class wins, and among equals the **nearest free** unit.

**Cleaning:** among capable crews the **same crew as last week** wins. Continuity beats proximity —
the customer wants the same person, the person knows where the Putzmittelraum is and which key opens
the Kellerabgang, and a substitution needs a briefing and an object handover.

**Consequence for code:** continuity must be a **first-class scoring term**, not a nice-to-have.
`WEIGHTS` today has five criteria — price, verification, experience, availability, proximity — and
**none of them is history with this Objekt** (`apps/marketplace/scoring.py:22-28`, **Fakt**). Adding
one is a policy change, so under the eG model it is a **ratified** change (a `DispatchPolicy` row),
not a constant edit. See SKILL.md §1, consequence 2.

**And the tension to name honestly:** the more the customer names the individual, the more the
arrangement reads as Arbeitnehmerüberlassung rather than a service contract with a firm. Continuity
and independence pull against each other. **Ungeprüft** where the line sits — which is exactly why
this must not be designed without advice.

### 4.5 Eligibility rule sets published next to the price

**Fakt**, https://inline-kurier.de/overnight — the Economy national product publishes its
constraints in the tariff block itself: „Angebot **nur in Hamburg (Ring 2)**" · „max. **30 kg pro
Paket**" · „**ein Packstück pro Versand**" · „kein unfreier Versand" · „keine Wochenend- und
Feiertagszustellung" · „kein Versand von Rollen, Holzkisten oder Koffern".

**This is the pattern for cleaning service eligibility** (**Vorschlag**): publish the rule set with
the offer — building height, hazard class, whether a key handover is required, whether the Objekt is
reachable inside the service zone, minimum area, minimum frequency. Note also that inline defines
zones (`RING 1 + Hafen-City` for the City-Zuschlag, `Ring 2` for Economy eligibility) but **never
defines them geographically anywhere on the site** — do better: a PLZ- or polygon-based zone model
that drives both availability and surcharge.

**Fakt (repo).** Zones today are `geo.Locality` FKs with `PROTECT` everywhere and a nullable
`latitude`/`longitude`; `_proximity_score` is a three-step locality approximation — same locality
1.0, declared service area 0.7, otherwise 0.2 (`apps/marketplace/scoring.py:105-115`). That is the
honest placeholder its own docstring says it is.

### 4.6 Rate rows, not hardcoded numbers

**Fakt.** inline's live tariff tables render **unresolved template tokens** — `Stadt-TS`,
`Stadt-CO2`, `OVER-TS`, `OVER-CO2`, `WESTEUROPA`, `OSTEUROPA`, `USA`, `ASIEN`, `ÜBR. LÄNDER` — so
the index-linked and zone-linked numbers are visibly injected from a rate table at render time. The
only concrete index figure published anywhere is „Treibstoffzuschlag **ab August 2026: 5,00 %**".

The lesson is not the tokens (that is a rendering bug); it is that **every rate is a dated row
resolved into the page.** Cleaning_SaaS already does this correctly for wage floors:
`WageFloor.current(kind, on)` filters `valid_from__lte=on` and `valid_to__isnull=True | gte=on`
(`apps/contracts/models.py:83-89`, **Fakt**), and `OfferForm.clean` resolves at `earliest_start`
rather than at "now" (`apps/marketplace/forms.py:51-68`, **Fakt**). Copy that pattern for class base
prices, surcharge percentages and Leistungswerte. Never a literal in code.

---

## 5. The measurement formula — publish it

**Fakt**, https://inline-kurier.de/xxl: national volumetric weight is „**Länge × Breite × Höhe in
cm : 6.000**" per IATA standard; Europe uses „**: 5.000**"; and the billed weight is „der jeweils
**größere Wert** aus Gesamtbruttogewicht oder Volumengewicht". (The two divisors on the same page
contradict each other only in the sense that they apply to different destinations; both are
published.)

Both this and the cleaning analogue are the same thing: **a billable quantity derived from
measurements by a published formula**. The cleaning version is the **Leistungswert** — m²/h by
surface type and soiling degree, the industry's own conversion from measurement to time.
**Vorschlag:** publish the formula the way inline publishes the IATA divisor, and store the
Leistungswert table as dated rows so a change is auditable. The specific values are **Ungeprüft**
here; → `gebaeudereinigung-domain` and `gr-einsatzplanung`, where `Zone.minutes_per_visit` and
`ZoneCalibration` already own the empirical correction loop (`apps/planning/models.py:58,235-292`,
**Fakt**).

---

## 6. Gaps

1. **The Bike envelope differs between the fleet page (60 × 30 × 20 cm) and the tariff page (DIN A2,
   diagonal max. 120 cm).** Reported, not reconciled.
2. **RING 1 and RING 2** are used as pricing and eligibility boundaries and are **never defined
   geographically** anywhere in the corpus.
3. **`order.parcel.mainVolume > 25`** appears in the order markup as a UI threshold; the **unit of
   the volume figure is not published** (m³? dm³? a score?).
4. **Bike/Cargobike tables collapse „Zwischenstopp" and „Aufpreis für warmes Essen" onto one price
   pair** (4,50 €) while PKW/Kombi keep them as separate rows (5,00 € and 4,50 €). Whether bikes
   have a Zwischenstopp fee at all is unclear from the extraction. Do not assume.
5. **No cleaning source material exists in this corpus.** Everything in §4 is **Vorschlag** or
   **Ungeprüft**; the class list, the machine categories and the required Nachweise must be verified
   against the trade's own rules before they gate anyone's ability to bid.

---

## Quellen

- https://inline-kurier.de/uber-uns — the seven fleet classes with every dimension and weight limit,
  the „Maximale" vs. „Ca." headings, the allocation sentence („Distanz, Größe und Gewicht"), fleet
  composition 130 / 90 / 40.
- https://inline-kurier.de/kurierfahrten — the five priced class cards, Mindestpreise, included
  service time per class, XL-Bus and Ladebordwand surcharges, fuel-surcharge exemption for bikes.
- https://inline-kurier.de/bestellung — the three consignment entry modes, per-Packstück fields, the
  „Maximalmaße" disclaimer, the `mainVolume > 25` threshold.
- https://inline-kurier.de/overnight — the Economy national eligibility rule set published beside
  the tariff; Ring 2.
- https://inline-kurier.de/xxl — IATA volumetric divisors : 6.000 / : 5.000, „der größere Wert".
- https://inline-kurier.de/faq-s — the vehicle list restatement.
- Repo: `apps/marketplace/models.py:61-63,135,161-166` · `apps/marketplace/scoring.py:22-28,105-115,170-178`
  · `apps/marketplace/forms.py:51-68` · `apps/planning/models.py:58,149,159,235-292` ·
  `apps/contracts/models.py:83-89` · `apps/devices/models.py:24-29`.
