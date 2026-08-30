# Auftragsarten — the four archetypes and the add-ons

Source: https://inline-kurier.de/kurierfahrten (the canonical document; `/preise-kurierfahrten`,
`/vorteile-kurierfahrt`, `/uberblick`, `/unsere-kunden-kurierfahrt`, `/kontakt-kurierfahrt` are
anchor views with identical body copy — `/uberblick` additionally leaks an internal editor/test
navigation block („Testfälle", „Sidekicks:", „Admin:", „Testseiten:"), so it is not byte-identical),
plus https://inline-kurier.de/bestellung,
https://inline-kurier.de/bestellung/transporthilfe, https://inline-kurier.de/faq-s,
https://inline-kurier.de/dokumentierte-zustellung-kurierfahrt and
https://inline-kurier.de/dokumentierte-zustellung-overnight. Crawled 2026-08-29.

Markers: **Fakt** · **Vorschlag** · **Ungeprüft**.

---

## 1. The four archetypes, side by side

All four are presented as parallel products on one page (**Fakt**).

### 1.1 Kurierfahrt → **Ad-hoc-Einsatz / Sofortreinigung**

| | |
|---|---|
| **inline definition (Fakt)** | „Schneller, direkter Transport in Hamburg und Umgebung – ob gewerblich oder privat." Direktzustellung: „Ihre Sendung wird nicht umgeladen, sondern direkt überbracht." Schnelligkeit: „**Wir fahren sofort nach Auftragseingang los – ohne Wartezeiten.**" |
| **Timing promise (Fakt)** | „oft in weniger als **60 Minuten**"; process step 4: delivery „**im Schnitt 45 Minuten nach Vermittlung**"; „In Hamburg können wir Ihre Sendung in der Regel innerhalb von **30 bis 60 Minuten** abholen" |
| **How it is planned (Fakt)** | Dispatched on receipt, „2. Vermittlung … **per Funk**" |
| **Ordering (Fakt)** | Online **and** phone. „Online können Sie bis zu **vier Tage** im Voraus bestellen." |
| **Published price (Fakt)** | Yes — the full vehicle-class tariff |
| **Cleaning equivalent (Vorschlag)** | Sonderreinigung after a burst pipe, Bauendreinigung after handover, Glasbruch, vandalism, Krankheits-Vertretung call-out |
| **Timing promise for cleaning (Vorschlag)** | **A day-part window** (vormittags / nachmittags) or „innerhalb 24 h" — **never a minute SLA.** The operator must bring materials and usually needs key or access arranged. A 45-minute promise is not portable. |
| **Verdict** | **Holds in shape, breaks in SLA.** Also breaks in weight: for inline this is the flagship; in Gebäudereinigung it is the exception, not the default the form should be built around |

### 1.2 Vorbestellung → **Termingebundener Einsatz**

| | |
|---|---|
| **inline definition (Fakt)** | „Abholung oder Lieferung – wir kommen genau zur vereinbarten Zeit." For „zeitkritische Sendungen, vorbereitete Waren oder Dokumente, die zu einem bestimmten Zeitpunkt abgeholt oder zugestellt werden müssen." |
| **Timing promise (Fakt)** | „Verlässliche Abholung oder Lieferung zum vereinbarten Zeitpunkt"; „Planungssicherheit durch **feste Zeitfenster**" |
| **How it is planned (Fakt)** | „Ob **einmalig, regelmäßig oder im Rahmen einer laufenden Tour**"; „Kombinierbar mit Express- oder Overnight-Services" |
| **Published price (Fakt)** | **No separate price.** It is a scheduling attribute on top of a Kurierfahrt; no pre-booking fee and no discount is published |
| **Cleaning equivalent (Vorschlag)** | Fensterreinigung 2×/Jahr, Grundreinigung zum Quartalsende, Treppenhaus-Intensivreinigung |
| **Verdict** | **Holds cleanly.** Same data shape: a job with a fixed date/window, optionally recurring on a coarse cadence, at the standard rate |

### 1.3 Festtour → **Dauerauftrag / Unterhaltsreinigung**

| | |
|---|---|
| **inline definition (Fakt)** | „Postfächer leeren, Hauspost verteilen oder tägliche Zustellungen"; „regelmäßig anfallende Transporte … vom täglichen Leeren von Postfächern über die interne Hauspostverteilung bis hin zu geplanten Lieferungen zwischen Standorten oder Kunden". Couriers are „**fest in Ihre Abläufe eingebunden**" |
| **Timing promise (Fakt)** | „Feste Tourenpläne und **definierte Zeitfenster**"; „**Tag für Tag**" |
| **How it is planned (Fakt)** | „transparente Routenplanung und **flexible Anpassung bei Änderungen**" |
| **Ordering** | **Fakt (negative):** the corpus contains **no online path for a Festtour** — the wizard has no such product and the sitemap lists only Transporthilfe and dokumentierte Zustellung beside the Startseite. The FAQ says only „Kann ich Festtouren oder Verteilerrunden buchen? **Ja, täglich planbar mit fixen Zeitfenstern** – ideal für Hauspost und regelmäßige Abholungen." *Inferenz:* phone/quote only. (The sentence „Die Beauftragung erfolgt telefonisch." belongs to **Dokumentierte Zustellung**, not to Festtouren — do not re-attribute it.) |
| **Published price (Fakt)** | **None.** It claims „Planbare Kosten und transparente Konditionen" and publishes **no figure, no rate, no minimum** anywhere on the site |
| **Cleaning equivalent (Vorschlag)** | The Unterhaltsreinigungsvertrag on a Leistungsverzeichnis: same Objekt, same days, same person, e.g. Mo/Mi/Fr 06:00–08:00 |
| **Verdict** | **Holds — with the weights inverted.** For inline this is one of four order types; in Gebäudereinigung the recurring contract is the business and the spot job is the exception. Build the recurring model first and derive the spot job from it |

**The break this one carries.** inline's whole structure assumes the job **ends**: spot dispatch,
per-job pricing, per-job independence. Cleaning's economics are a contract that renews weekly for
years. Consequences that have no courier analogue at all:

- one model cannot carry both spot and recurring work (already the repo's own conclusion — see
  `gr-marktplatz-dispatch`, `references/zwei-vergabemodi.md`);
- **§ 613a BGB Betriebsübergang** applies when an Objekt changes provider — the incoming firm may
  inherit the outgoing firm's staff. No courier ever faces this (**Ungeprüft** in detail; the
  crawled sources establish nothing about it — it is domain knowledge, verify before it reaches
  contract text);
- churn, not dispatch latency, is the metric that matters.

### 1.4 Verteilerrunde → **Tourenreinigung**

| | |
|---|---|
| **inline definition (Fakt)** | „Wenn mehrere Empfänger beliefert werden sollen, ist unsere Verteilerrunden-Logistik die effiziente Lösung … wir übernehmen die Abholung und Zustellung **in geplanter Reihenfolge**". Benefit list: „**Eine Tour für mehrere Zustellungen oder Abholungen**", „Optimierte Routenplanung für Zeit- und Kosteneffizienz" |
| **Timing promise (Fakt)** | „**täglich, wöchentlich oder nach Bedarf**" |
| **How it is planned (Fakt)** | „optimierte Routen"; „individuell an Ihre Abläufe anpassen" |
| **Ordering (Fakt)** | Phone. Online the wizard allows **max. 3 Zwischenstopps**; „Für Rundtouren mit weiteren Adressen nehmen wir Ihren Auftrag gerne telefonisch entgegen." |
| **Published price (Fakt)** | **None.** In the ad-hoc tariff there is a *Zwischenstopp* line (5,00 € netto, PKW/Kombi), but the page never states that Verteilerrunden are billed that way |
| **Cleaning equivalent (Vorschlag)** | **Tourenreinigung**: one operator, several Objekte in sequence in one morning — the classic case is **Treppenhausreinigung**, six stairwells before 10:00. Also: one Glasreinigungs-Team doing twelve shopfronts on one street |

**Verdict: holds structurally, breaks economically, and the repo cannot express it at all.**

Why it breaks economically: a courier stop is ~2 minutes and interchangeable. A cleaning stop is
25–90 minutes and **object-specific** — this stairwell has five floors, that one has a Kellerabgang.
Stop duration must be an object attribute with a real estimate, not a constant. Route optimisation
therefore becomes **shift packing under a working-time constraint** (ArbZG breaks, daily maximum),
not a travelling-salesman problem.

**Why the existing per-Objekt shift model does not express it (Fakt, repo):**

| Fact | `file:line` | Why it blocks a Tour |
|---|---|---|
| `Zone.site` is a plain FK — a Zone belongs to exactly one Site | `apps/planning/models.py:48` | A cleaning round spans several Sites; no object groups them |
| `Shift.zone` is a single FK | `apps/planning/models.py:142` | One shift = one Zone = one Site. Six stairwells produce six unrelated shifts |
| `Shift` has `date`, `start_time`, `duration_minutes` — no sequence, no ordinal, no travel time | `apps/planning/models.py:147-149` | Nothing expresses "this is stop 3 of 6" or the Wegezeit between stops |
| The allocator packs each visit independently and starts every worker's day at `DAY_START = time(7, 0)`, stacking shifts back-to-back with no travel gap | `apps/planning/services.py:30,143-151` | Two consecutive Objekte in different localities are planned as if adjacent |
| `_fits()` rejects a worker whose `areas` do not include the Site's locality | `apps/planning/services.py:82-95` | Correct per shift, but there is no notion of a route that legitimately crosses localities |
| `ShiftPlan.unmet_demand` records unplaced visits with a reason | `apps/planning/models.py:103`, `services.py:134-140` | The right reporting hook to extend, once Tours exist |

**Vorschlag** for the missing entity — see `references/umsetzung-im-repo.md` §4 for the field-level
proposal. The short version: a `Tour` owns an ordered list of `TourStop`s, each pointing at a `Zone`
with a per-stop `sequence` and `travel_minutes`; a `Shift` gains an optional FK to the `Tour` so the
ArbZG ceiling is evaluated over the whole round, not per stop.

---

## 2. Add-on services

**Fakt**, prices from https://inline-kurier.de/kurierfahrten (netto / brutto, brutto incl. 19 % MwSt.).

| inline add-on | Published price | Cleaning counterpart (Vorschlag) | Verdict |
|---|---|---|---|
| **Dokumentierte Zustellung** — „mit Nachweisprotokoll und Fotos durch Kurier", surcharge on the ride, charged for **Hin- und Rücktour** | **59,00 € / 70,21 €** | **Leistungsnachweis** per Einsatz | Same structure, **opposite commercial position** — see §3 |
| **Ladehilfen** — Anfahrt in Hamburg (ohne Außenbereiche) incl. **15 min** Service | **20,00 € / 23,80 €**; Außenbereiche +15,00 € / 17,85 €; je weitere angefangene 15 min **12,00 € / 14,28 €** | **Helferstunden / Zusatzkräfte**: Entrümpelung, Möbelrücken vor Grundreinigung, Umzugsreinigung, Event-Clean-up | **Holds almost verbatim** — see §4 |
| **Geldauslage** — courier fronts cash at pickup and recovers it from the recipient | bis 50,00 € **frei**; bis 100,00 € **4,00 €**; bis 200,00 € **8,00 €**; bis 300,00 € **15,00 €** (netto) | **Materialauslage**: Seife, Papierhandtücher, Müllbeutel, Streusalz bought by the operator and re-invoiced | **Holds as a mechanism, wrong frequency and ceiling** — a courier fronts cash once, a cleaning firm stocking a building does it monthly and higher. Add a Materialkatalog with agreed prices, a monthly Verbrauchsabrechnung and a per-Objekt spend cap |
| **Zeit für Service** — „Manches braucht Zeit. Wir warten, bis alles erledigt ist." | **No price of its own.** It is the marketing name for the Lade-/Servicezeit meter already in every vehicle tariff (5 min included, 15 min on Transporter, then 4,00 € per further 5 min / 16,00 € per further 15 min) | **Mehraufwand / Zusatzzeit vor Ort** | **Needs adaptation.** For inline it is a label on an existing meter. For cleaning it must be a real, auditable object with **approval in the loop** — the cleaner records extra time, the Objektverantwortlicher approves, it becomes a distinct invoice line. Without approval it is a dispute generator, because nobody is watching |
| **Wartezeit** (Overnight line) — „Wartezeit bei Abholung/Zustellung je 5 Min" | Express national & World **+6,00 € / 7,14 €**; Economy Europe +5,00 € / 5,95 € | **Wartezeit** at a locked Objekt | Holds as a fee; but for cleaning the failure itself needs a state, not only a price |
| **2. Anfahrt / Adressklärung** (Overnight line) | Express national **ab 10,00 € / 11,90 €**; Express World ab 20,00 €; Economy national +8,50 € | **Vergebliche Anfahrt** | **The single most under-modelled thing in the source.** See `references/zentrale-und-disposition.md` §4 |

Two global tariff rules worth stealing as *shapes*, not values (**Fakt**):

- **Out-of-hours multiplier:** „montags bis freitags **0-7 und 19-24 Uhr**; samstags **0-8 und
  18-24 Uhr**; sonn- und feiertags → **zzgl. 50 %**", with per-class minima (Kombi 40,00 €,
  Transporter 70,00 €, Ladehilfe 30,00 € netto). And crucially: „*Dieser Zuschlag bzw. Aufpreis
  wird **nicht kombiniert** erhoben." **The non-cumulative rule is the right shape** — in the
  Gebäudereinigung only the highest applicable surcharge is paid too. But **the values are wrong
  and the direction is reversed**: cleaning surcharges are tariff-set *employee* entitlements from
  which the customer price is derived, not a margin the platform pockets. → `gr-tarif-und-lohn`.
- **Index-linked pass-through:** the Treibstoffzuschlag is „indexbasiert", adjusted monthly,
  effective **on the 1st**, visible on the page **14 days in advance**, based on the ADAC monthly
  average diesel price of the **vorletzter Monat**, itemised per order on the invoice annex, and
  bikes are exempt entirely. The governance is worth copying wholesale for **Tariflohnerhöhungen
  in Dauerauftragspreisen** (a Preisgleitklausel): a rate from a named public index, published in
  advance, effective on a fixed date, itemised on the invoice.

---

## 3. Dokumentierte Zustellung → Leistungsnachweis, in detail

**Fakt**, https://inline-kurier.de/dokumentierte-zustellung-kurierfahrt. Five-step process:

1. **Prüfung aller Unterlagen** — „Eine Unterschrift attestiert, dass Original und Kopie identisch
   sind."
2. **Versandfertig machen** — „Das Original wird kuvertiert…"
3. **Transport** — „…vom Kurier verschlossen und auf direktem Weg zum Empfänger gebracht."
4. **Zustellung** — „**Fotodokumentation und Protokollierung** der Zustellung – in den Briefkasten
   oder durch persönliche Übergabe mit Unterschrift."
5. **Nachweis** — „Rücklieferung des Zustellungsprotokolls **im Original** an den Auftraggeber und
   Versand der Fotos per E-Mail."

Zustellnachweis fields, verbatim (**Fakt**):

- Name des Auftraggebers und des Empfängers
- Abhol- und Zustelladresse
- Datum und Uhrzeit der Zustellung
- **Besondere Umstände der Zustellung**
- **Angaben zum beauftragten selbständigen Kuriers**

Control principle (**Fakt**): „Während der gesamten Tour arbeiten wir mit dem
**Vier-Augen-Prinzip**, Fahrer und Zentrale stehen in engem Austausch."

The Overnight variant, **CertiChain** (**Fakt**,
https://inline-kurier.de/dokumentierte-zustellung-overnight): „manipulationssichere **codierte
SafeBags**. Jeder SafeBag erhält einen individuellen Code der einer **Frachtbriefnummer** zugeordnet
wird, diese Frachtbriefnummer wird bei **jeder Übergabe in der Transportkette gescannt**." Two
signatures — sender plus an **unabhängiger Zeuge** — enforce the Vier-Augen-Prinzip at sealing.

**Transfer, and where it flips.** The last field is the important one: **the identity of the
independent operator is disclosed to the customer and written into an evidentiary document.** For a
cleaning platform:

| Aspect | inline | Cleaning |
|---|---|---|
| Commercial position | Optional, premium, 59,00 € netto | **Free, always-on, per visit** — every Hausverwaltung expects it and it is the basis of payment and of disputes |
| Frequency | Once per shipment | **Daily, same person, same place, for years** |
| Consequence | An evidentiary artefact | A **continuous behaviour and performance profile of an employee** → § 26 BDSG, Betriebsrat co-determination under § 87 Abs. 1 Nr. 6 BetrVG, necessity test, deletion periods. Photos in an Objekt can capture uninvolved third parties |
| Naming the operator | Part of the evidential value, one-off | Creates a permanent person↔Objekt link visible to the customer. **Vorschlag:** default to a role („Objektteam 4", first name + initial), name the person only where it is contractually required, e.g. key responsibility |

So: **copy the mechanism, do not copy the justification.** The courier's reasoning ("proof of a
completed handover") does not carry a daily record of a named employee.

**Fakt (repo).** Nothing like this exists. `Shift.worker_note` (max 300 chars,
`apps/planning/models.py:160`) and the append-only `ShiftEvent` journal
(`apps/planning/models.py:188-220`) are the two hooks. Photos, checklist items per Raum, and a
customer-side signature have no field. See `references/umsetzung-im-repo.md` §4.4.

---

## 4. Ladehilfen → Helferstunden: the cleanest 1:1 import

**Fakt**, https://inline-kurier.de/bestellung/transporthilfe. The order form is the shortest on the
site: one address (`Wo?`), then `Was?` → **`Helfer` `Personen`** + **`ca. Dauer` `Minuten`**, plus a
free-text „Wobei brauchen Sie Hilfe?".

Billing rule, verbatim (**Fakt**): „Die Ladehilfe wird nach der **tatsächlichen Dauer** berechnet.
Sie geben bei der Bestellung eine geschätzte Dauer an. **Abgerechnet wird in 15-Minuten-Schritten.**"

Note also (**Fakt**): the Ladehilfe form shows **„Anfrage"** instead of a live price, unlike the
Kurierfahrt form's „jetzt Fahrpreis berechnen" — so even inline does not auto-quote multi-person
on-site services despite having a published tariff for them. Worth remembering before promising
instant quotes for a cleaning job with a crew.

**Why this is the closest element on the whole site:** headcount × estimated duration, ordered on
an estimate, billed on actuals in quarter-hour steps — that *is* the Gebäudereinigung
Stundenverrechnungssatz model. Copy the two form fields and the rounding rule verbatim. The euro
values do not transfer (→ `gr-tarif-und-lohn`).

---

## 5. Lifecycle states

### 5.1 What inline publishes

**Fakt.** Kurierfahrt has five published steps and **two customer e-mails**: „Sie werden per E-Mail
über die **Vermittlung** und den **Abschluss** Ihres Auftrags informiert." There is **no live
tracking** on the Kurier line. Overnight, by contrast, has a `Sendungsnummer` and „Echtzeit-Status".

Reconstructed state machine (**Fakt** for the named steps, the arrows are a reconstruction):

```
PLACED → VERMITTELT (e-mail #1) → ANFAHRT → ABGEHOLT → [VIA-STOP ×0..3] → ZUGESTELLT
       → [RETOUR] → BESTÄTIGT (e-mail #2) → ABGERECHNET
```

**Fakt (negative), grep-verified across all 36 pages — zero hits for `storn`, `Reklamation`,
`Beschwerde`, `Zustellversuch`:** the site describes **no** CANCELLED, REJECTED /
no-courier-available, FAILED_PICKUP, FAILED_DELIVERY, RESCHEDULED, MODIFIED_AFTER_PLACEMENT,
DAMAGED/CLAIMED, REFUNDED or DISPUTED state. There is no cancellation policy, no refund rule, no
SLA, no penalty, no escalation path and no Widerrufsbelehrung anywhere in the corpus. Failed
delivery exists **only as a price line** („2. Anfahrt / Adressklärung"), never as a process. Also
undescribed: what happens between PLACED and VERMITTELT — **whether couriers accept jobs or are
assigned them is nowhere published.** That is precisely the layer a cleaning platform most needs.

### 5.2 What the cleaning lifecycle needs

**Vorschlag**, per archetype, aligned with what the repo already has.

| Archetype | States | Repo status |
|---|---|---|
| **Ad-hoc-Einsatz** | DRAFT → OPEN → AWARDED → *(missing: SCHEDULED → IN_PROGRESS → DONE → INVOICED)* ⊥ CANCELLED / EXPIRED | `RequestStatus` = DRAFT / OPEN / AWARDED / CANCELLED / EXPIRED — **ends at AWARDED** (`apps/marketplace/models.py:40-45`, **Fakt**). Nothing after the award |
| **Termingebundener Einsatz** | same, plus a committed window | No committed-window field; only `earliest_start` (`apps/marketplace/models.py:67`, **Fakt**) |
| **Dauerauftrag** | AWARDED → **ACTIVE** → (Nachtrag / Preisanpassung) → GEKÜNDIGT → BEENDET, with per-visit occurrences underneath | **No ACTIVE state, no term, no notice period, no Leistungsverzeichnis.** The occurrence layer exists separately as `ShiftStatus` = PLANNED / CONFIRMED / DECLINED / IN_PROGRESS / DONE / MISSED (`apps/planning/models.py:131-138`, **Fakt**) with **no bridge** from a `ServiceRequest` |
| **Tourenreinigung** | Tour-level: GEPLANT → GESTARTET → ABGESCHLOSSEN; stop-level: ANGEFAHREN → ZUTRITT_OK \| **ZUTRITT_GESCHEITERT** → ERLEDIGT → NACHGEWIESEN | Nothing exists |

The state every cleaning platform needs and inline never names: **ZUTRITT_GESCHEITERT** (access
failed — no key, alarm armed, room occupied, nobody on site). It is chronic in cleaning, it costs
real money because the operator is paid regardless, and it must be a first-class state with a photo
and a timestamp, not a fee line. Details in `references/zentrale-und-disposition.md` §4.

### 5.3 Ordering-channel asymmetry — copy the discipline

Only the ad-hoc Kurierfahrt is self-service. For **Dokumentierte Zustellung** and the whole **XXL**
line that is stated verbatim (**Fakt**, quotes below); for **Festtouren** and full **Verteilerrunden**
it is an *Inferenz* from the absence of any online path plus the ">3 Stopps → telefonisch" rule. Either
way they are **sold by conversation**:

> „Da es sich beim XXL Speditionsversand in der Regel um besonders große, schwere oder sperrige
> Sendungen handelt, ist eine **Online-Bestellung nicht möglich**. Jeder Transport wird individuell
> geplant … Auch der **Preis wird individuell berechnet**."
> — https://inline-kurier.de/xxl/bestellung

and

> „Eine Onlinebestellung ist derzeit noch nicht möglich, da wir die Aufträge **eng betreuen**
> möchten" — https://inline-kurier.de/bestellung (Dokumentierte Zustellung)

**This is the honest pattern and should be embraced, not fought.** Self-service prices the
commodity; anything needing a site survey escalates to a quote flow. Cleaning has a far higher
share of quote-only work (Objektbesichtigung / Aufmaß is industry standard), so the **Anfrage path
must be a first-class flow, not a fallback button.** Do not force a price calculator onto
Unterhaltsreinigung.

Consistent with that, the price is a quote and says so (**Fakt**): „Der tatsächliche Preis kann sich
ändern, wenn sich die Anforderungen des Auftrags ändern oder zusätzlicher Aufwand entsteht." For
cleaning this fits even better — but a **Nachtrag over a monthly Dauerauftrag needs an approval
workflow and an audit trail**, unlike a courier's unilateral re-price of a 45-minute job.

---

## 6. Gaps in the source

1. **Festtouren: no rate, no minimum, no example** — priced by negotiation, despite claiming
   „transparente Konditionen".
2. **Verteilerrunden: no per-stop and no per-round price.** Unstated whether the ad-hoc Zwischenstopp
   fee (5,00 € netto) is the basis.
3. **Vorbestellungen: no premium and no discount published.**
4. **XXL: no price at all** — „Alle Preise … erfahren Sie auf Anfrage."
5. **Zeit für Service has no SKU.** Stated explicitly so nobody invents one.
6. **Contradiction:** `/bestellung/kurierfahrt/dokumentiert` serves a working 4-step wizard while
   two other pages say online ordering of Dokumentierte Zustellung is not possible. Which is
   authoritative is unknown.
7. **No published courier compensation model** — how the members are paid out of any of these order
   types is not answerable from this corpus.
8. **The urgency options are not published.** The wizard asks „Wie eilig ist die Sendung?" and the
   `<select>` options did not survive extraction — the single most important classification field in
   the whole form, and its value set is unknown.

---

## Quellen

- https://inline-kurier.de/kurierfahrten — the four order types, the 5-step process, vehicle tariff,
  extra services, out-of-hours surcharges, FAQ. Anchor-identical: /kurierfahrten/preise-kurierfahrten
  · /vorteile-kurierfahrt · /uberblick · /unsere-kunden-kurierfahrt · /kontakt-kurierfahrt.
- https://inline-kurier.de/bestellung (= /bestellung/kurierfahrt) — wizard steps, max 3
  Zwischenstopps, 4-day online horizon, extras catalogue, „Anfrage" fallback.
- https://inline-kurier.de/bestellung/transporthilfe — Ladehilfe fields and the 15-minute rule.
- https://inline-kurier.de/dokumentierte-zustellung-kurierfahrt — 5 steps, Zustellnachweis fields,
  Vier-Augen-Prinzip, telephone-only ordering.
- https://inline-kurier.de/dokumentierte-zustellung-overnight — CertiChain SafeBag, chain of custody,
  two-signature rule.
- https://inline-kurier.de/xxl/bestellung — phone-only intake, individual pricing.
- https://inline-kurier.de/faq-s — „feste Routen und Wiederholungsaufträge im Kundenprofil".
- Repo: `apps/marketplace/models.py:25-45,67` · `apps/planning/models.py:48,103,131-160,188-220` ·
  `apps/planning/services.py:30,82-95,134-151`.
