# Zentrale und Disposition

How the central office works at inline, and what the cleaning version must add: access failure, the
Leistungsnachweis, Reklamation intake, and what has to be logged.

Sources: https://inline-kurier.de/uber-uns, https://inline-kurier.de/kurierfahrten,
https://inline-kurier.de/overnight, https://inline-kurier.de/xxl,
https://inline-kurier.de/bestellung (and its sub-forms), https://inline-kurier.de/faq-s,
https://inline-kurier.de/dokumentierte-zustellung-kurierfahrt,
https://inline-kurier.de/dokumentierte-zustellung-overnight, https://inline-kurier.de/impressum,
https://inline-kurier.de/datenschutz. Crawled 2026-08-29.

Markers: **Fakt** · **Vorschlag** · **Ungeprüft**.

---

## 1. Order intake — channels and hours

**Fakt.** Intake is per service line, and the ordering channel is a deliberate product decision, not
a limitation.

| Channel | Line | Number / URL | Published hours |
|---|---|---|---|
| Online-Bestellportal (wizard) | Kurierfahrt | `/bestellung`, `/bestellung/kurierfahrt` | none published |
| Online-Bestellportal | Overnight | `/bestellung/overnight` | none published |
| Online-Bestellportal | Ladehilfe / Transporthilfe | `/bestellung/transporthilfe` | none published |
| Telefonische Auftragsannahme | Kurierfahrt + Dokumentierte Zustellung | **040 23 500 500** | none published |
| Telefonische Disposition | Overnight | **040-23 500 600** | none published |
| Telefonische Auftragsannahme | XXL Speditionsversand | **040 23 500 400** | **Montag bis Freitag 07:00 – 18:00 Uhr** |
| API | „Unsere **API-Lösungen** für Ihre Kurierlogistik." | — | no endpoint, no docs link, nothing |

Only XXL publishes hours (**Fakt**): „Unsere Auftragsannahme erreichen Sie **Montag bis Freitag von
07:00 bis 18:00 Uhr** unter 040 - 23 500 400. Unsere Mitarbeiterinnen und Mitarbeiter nehmen Ihren
Transportauftrag **persönlich** auf und besprechen die für die Planung wichtigen Details mit Ihnen."

The other two lines publish no opening hours at all, **although the price list charges +50 %
„außerhalb der Geschäftszeiten"** and thereby defines them implicitly as Mo–Fr 07:00–19:00 and Sa
08:00–18:00 (windows from the surcharge table: Mo–Fr 0-7 and 19-24, Sa 0-8 and 18-24, Sun/holidays).
That is an inference from a price table, not a published statement.

Online-order exclusions, verbatim (**Fakt**):

- Dokumentierte Zustellung: „Eine Onlinebestellung ist derzeit noch nicht möglich, da wir die
  Aufträge **eng betreuen** möchten und aufkommende Fragen gerne im direkten Gespräch beantworten."
- XXL: „eine **Online-Bestellung nicht möglich**. Jeder Transport wird individuell geplant."
- Rundtouren beyond 3 stops: „Für Rundtouren mit weiteren Adressen nehmen wir Ihren Auftrag gerne
  **telefonisch** entgegen."
- Lead time: „Online können Sie bis zu **vier Tage** im Voraus bestellen. Telefonisch können Sie
  Ihre Kurierfahrt auch weiter im Voraus beauftragen."

**Cleaning transfer (Vorschlag).** Copy the discipline, invert the horizon. Each Leistungslinie gets
its own owner, its own intake and its own price sheet — Unterhalt / Glas + Fassade / Bau / Sonder /
Personal. But a four-day online horizon is a *dispatch* horizon; cleaning plans months ahead with
generated occurrences. And the standing-order line (Unterhaltsreinigung) is the one that should
**not** be self-service, because it needs an Objektbesichtigung and an Aufmaß — exactly inline's own
reasoning for XXL.

---

## 2. Dispatchers and reachability

**Fakt**, https://inline-kurier.de/uber-uns:

> „Ein großer Pluspunkt ist dabei die **ständige Erreichbarkeit der Fahrer per Funk oder Telefon**
> sowie die jahrelange **Erfahrung unserer Disponenten**."

The **Disponent** is a named human role, advertised as an asset. Dispatch is step 2 of the published
five-step Kurierfahrt process (**Fakt**): „2. **Vermittlung** — Bei inline **per Funk**", followed
by „3. Anfahrt — Direkt nach Vermittlung".

The contact structure is organisationally the important part (**Fakt**, /uber-uns and /impressum):

| Channel | Number | Audience |
|---|---|---|
| Kundenbetreuung / Vorstand | **+49 40 23 500 500** | customers, governance |
| **Fahrerbetreuung** | **+49 40 23 500 555** | **the members/drivers — a separate line** |
| Bewerbungen | e-mail only („Du möchtest Kurier bei uns werden?" — note the informal **Du**) | prospective members |
| inline Overnight | +49 40 23 500 600 | product line |
| inline XXL / Auftragsannahme | +49 40 23 500 400 | product line |

**Supply-side support is a first-class function with its own phone number, not a queue bolted onto
customer support.** Small detail, high signal, trivially copyable as separate support queues.

**The caveat on this table:** the de-boilerplated capture flattens the label→number binding on the
eG block, so the exact pairing of „Kundenbetreuung"/„Vorstand" to 23 500 500 should be re-verified
against the live HTML before it is quoted anywhere operational. The *set* of channels is certain.

Marketing line repeated on every Overnight product (**Fakt**): „**Persönlicher Ansprechpartner statt
anonymer Hotline**."

**Cleaning transfer.** The Disponent role needs a different objective function (**Vorschlag**):

| | Courier Disponent | Cleaning Disponent / Objektleiter |
|---|---|---|
| Optimises | *Now* — minutes | A **recurring Tourenplan over weeks** |
| Main daily problem | Nearest free unit | **Krankheits-Vertretung** — one sick cleaner threatens six contracts |
| Objective | Speed | **Continuity** — the same person at the same Objekt |
| Named contact | A phone number | An **Objektleiter** per Objekt — a real supervisory role required for quality control |

**Fakt (repo).** There is no Disponent role and there cannot be a `role` column — abilities are rows
in `AccountCapability` (`apps/accounts/models.py:229-243`), which is rule 1 of
`cleaning-saas-codebase`. A dispatcher is therefore a capability plus object-scoped permission, not
a role. Also **Fakt**: nothing models Vertretung or absence at all; `Shift.worker` is nullable and
`SET_NULL` (`apps/planning/models.py:143-146`), and `ShiftStatus.DECLINED` exists
(`models.py:134`) with `decline_shift` in `apps/planning/attendance.py:101` — but a decline produces
no substitute and no re-plan. → `gr-einsatzplanung`.

---

## 3. Status, tracking and notification

**Fakt.** The two lines have deliberately different granularity.

| | Kurierfahrt | Overnight |
|---|---|---|
| Identifier | Auftrag in the Bestellhistorie | **Sendungsnummer** |
| Tracking | **none published** | „Sendungsverfolgung mit **Echtzeit-Status**" |
| Notification | e-mail at **Vermittlung** + at **Abschluss**, nothing between | „auf Wunsch per E-Mail, postalisch oder in Ihrer Auftragsliste" |
| Proof of performance | `Signatur` toggle → „Empfängername wird bei Auslieferung erfasst"; optionally the paid Dokumentierte Zustellung | Empfangsbestätigung (paid extra); CertiChain Zustellprotokoll |

Verbatim (**Fakt**): „Wo ist die Sendung? Sie werden **per E-Mail über die Vermittlung und den
Abschluss** Ihres Auftrags informiert – mit allen relevanten Informationen."

**The insight worth copying is that two service lines legitimately have different status
granularity** (**Vorschlag** for cleaning): the ad-hoc Einsatz gets event notifications
(zugewiesen → begonnen → beendet); the Dauerauftrag gets a status board plus a per-visit
Leistungsnachweis.

**And cleaning can do better cheaply.** The courier's two-event model is thin because the job lasts
45 minutes. A cleaning visit lasts hours and repeats weekly, so the natural stream is check-in /
check-out — which is **already legally required** and already in the repo: `Shift.checked_in_at` /
`checked_out_at` / `actual_minutes` with the append-only `ShiftEvent` journal, whose model docstring
cites BAG 13.09.2022 (1 ABR 22/21) + § 3 Abs. 2 Nr. 1 ArbSchG and § 16 ArbZG retention
(`apps/planning/models.py:154-159,188-220`, **Fakt**). The customer-facing notification layer sits on
top of that. → `gr-zeiterfassung` for everything about the record itself.

### The `Signatur` pattern does not transfer

**Fakt**: „Signatur — Empfängername wird bei Auslieferung erfasst." A recipient signs.

**Breaks in the common case.** Office cleaning happens at 05:00 with nobody present; there is no
recipient to sign. Proof must be **device-anchored** — NFC/QR tag at the Objekt, Zeiterfassung,
photo documentation. Which is why the *Dokumentierte Zustellung* pattern, not the *Signatur*
pattern, is the one to copy.

---

## 4. Failed delivery → **Zutrittsversagen**: the biggest hole in the source

**Fakt (negative), grep-verified across all 36 captured pages: zero hits for `storn`,
`Reklamation`, `Beschwerde`, `Zustellversuch`.** inline publishes **no cancellation policy, no
complaint procedure, no refund rule, no SLA, no penalty, no escalation path, no order-modification
rule and no Widerrufsbelehrung.** Failed delivery exists **only as a price line**:

| Fee | Line | Price |
|---|---|---|
| `2. Anfahrt / Adressklärung` | Express national | **ab 10,00 € / 11,90 €** |
| | Express World | ab 20,00 € / 23,80 € |
| | Economy national | plus 8,50 € / 10,12 € |
| | Economy Europe | plus 20,00 € / 23,80 € |
| `Wartezeit bei Abholung / Zustellung je 5 Min` | Express national & World | plus 6,00 € / 7,14 € |
| | Economy Europe | plus 5,00 € / 5,95 € |

The only published *process* handling of a delivery problem anywhere in the corpus is a
precondition on the remote-ordered Dokumentierte Zustellung (**Fakt**): „Voraussetzung ist jedoch,
dass **vor Ort jemand über den Ablauf der Zustellung informiert ist**, die Unterlagen bereit hält
und **Sie als Ansprechpartner bei eventuellen Auslieferproblemen telefonisch erreichbar sind**."

### The cleaning version

**Vorschlag.** In cleaning this is chronic and expensive: the operator travelled, is paid regardless,
and the visit did not happen. It needs a **first-class state**, not a fee line.

Failure modes, each with its own handling:

| Failure | Typical cause | Immediate handling | Consequence |
|---|---|---|---|
| **Kein Zutritt — Schlüssel** | Key missing, wrong key, Schließanlage changed without notice | Photo of the door + timestamp, notify the Objektleiter and the customer contact | Vergebliche Anfahrt billed per the contract; key chain audited |
| **Kein Zutritt — Alarm** | Alarm armed, code changed, code not handed over | Do **not** enter; log and leave | Same, plus an access-data update task |
| **Raum belegt** | Meeting running, tenant present, room locked from inside | Skip that Raum, complete the rest, record the omission on the Leistungsnachweis | Partial performance, not a failure of the visit |
| **Objekt nicht vorbereitet** | Furniture not moved, construction still running, water/power off | Record with photo, request customer decision | Nachtrag or reschedule |
| **Gefahr** | Water damage, glass, biohazard, blocked escape route | Stop work, escalate immediately | Separate incident record; may become a Sonderreinigung order |

**Everything above must produce evidence at the moment of failure, because there is no witness.**
That is the deep difference from the courier case: inline's Vier-Augen-Prinzip is „Fahrer und
Zentrale stehen in engem Austausch" during a 45-minute job. A cleaner is alone in a locked building
at 05:30 and there is nobody to corroborate. Control therefore shifts from live radio contact to
**before** (Einweisung, Reinigungsplan, access data) and **after** (Leistungsnachweis,
Qualitätskontrolle, Objektbegehung). Live location tracking as a substitute would be the wrong
reflex — and a DSGVO/§ 26 BDSG problem. → `gr-zeiterfassung`, `references/geofence-und-dsgvo.md`.

**Fakt (repo).** `ShiftStatus.MISSED` exists (`apps/planning/models.py:137`) and `mark_missed` is an
**employer** action (`apps/planning/attendance.py:169`). There is no worker-initiated
"I was there but could not get in" path, no reason code, and no photo. That is the concrete gap.

---

## 5. The Leistungsnachweis and what must be logged

### 5.1 The record

Modelled on inline's Zustellnachweis (**Fakt**, fields listed verbatim in
`references/auftragsarten.md` §3), adapted. **Vorschlag:**

| Field | Why |
|---|---|
| Objekt + Zone/Raumgruppe | What was cleaned |
| Datum, Beginn, Ende | Ties to the Zeiterfassung record, not a second clock |
| Ausführende Einheit | **Role by default** („Objektteam 4"), the person's name only where contractually required — see below |
| Leistungspositionen abgehakt | From the Leistungsverzeichnis, per Raumgruppe |
| **Besondere Umstände** | inline's own field name, and the most useful one on the whole form |
| Fotos (vorher/nachher, Mängel) | Evidence; with a documented legal basis and a retention period |
| Nicht ausgeführt + Grund | Partial performance is normal and must be recordable |
| Abnahme / Bestätigung | Objektverantwortlicher, where present; device-anchored otherwise |

### 5.2 The privacy problem the courier model hides

**This is where the analogy breaks hardest.** For inline the Zustellnachweis is a **one-off**
evidentiary artefact about a completed handover. In cleaning the *same* record is produced **daily,
for the same person, at the same place, for years** — which makes it a continuous behaviour and
performance profile of an employee.

Consequences (**Ungeprüft** in detail — the crawled corpus is a courier site and establishes none of
this; it is domain knowledge and must be verified before it reaches production):

- **§ 26 BDSG** necessity test for employee data;
- **Betriebsrat co-determination, § 87 Abs. 1 Nr. 6 BetrVG**, for any system suited to monitoring
  performance or behaviour;
- deletion periods that are actually enforced;
- photos in an Objekt can capture uninvolved third parties — tenants, patients, employees of the
  customer — who never consented and do not know the platform exists.

inline itself shows the right mechanism for that last group and then under-uses it: its downloads
include a separate **„Datenschutzhinweise für Empfänger"** (**Fakt**, /datenschutz) — a dedicated
information sheet for the person who has no contract with them. Its content is not in the corpus.
**Vorschlag:** a cleaning platform needs the same document for **Gebäudenutzer / Mieter /
Beschäftigte im gereinigten Objekt**, and it has to cover far more: access times, key issue, photo
documentation of Mängel, cameras in the Objekt.

Note also (**Fakt**) that inline's published Datenschutzerklärung mentions the **operator side with
no word at all** — not the application („Du möchtest Kurier bei uns werden?"), not dispatch, not
settlement. For a cleaning platform that gap is untenable: employee data (Arbeitszeiten per
§ 17 MiLoG, Lohngruppe, Krankmeldungen, Sozialversicherungsnummer, Führungszeugnis for sensitive
Objekte) needs its own Art. 13 DSGVO / § 26 BDSG information. **Do not copy the omission.**

### 5.3 The key chain — steal the CertiChain mechanism

**Fakt.** CertiChain: „manipulationssichere **codierte SafeBags**. Jeder SafeBag erhält einen
individuellen Code der einer **Frachtbriefnummer** zugeordnet wird, diese Frachtbriefnummer wird bei
**jeder Übergabe in der Transportkette gescannt**", plus a two-signature Vier-Augen-Prinzip at
sealing (sender + **unabhängiger Zeuge**).

**Vorschlag:** apply exactly that mechanism to **Schlüsselverwaltung** — uniquely coded item,
scanned at every transfer, two-signature handover, immutable log. Fields: Schlüsselnummer,
Schließanlagen-ID, who held it when, issue and return receipts, and the person responsible.

But the risk model is entirely different, and this is where the courier analogy gives no guidance at
all: the courier's chain of custody protects **one shipment for one day**; the cleaner's key is held
**permanently** and gives unsupervised access to a building. Loss of a Generalschlüssel can mean
replacing a whole Schließanlage — often the single largest insurance exposure a Reinigungsbetrieb
carries. inline's per-order insurance ceilings (5.000 € Kurier / 3.000 € Overnight Warenwert,
**Fakt**) are the wrong shape entirely: cover belongs to the **Betrieb and the Objekt**, not to the
order. **Ungeprüft** as to the specific sums and the insurance products — verify with a broker.

### 5.4 Reklamation intake

**Fakt (negative).** The word does not appear anywhere in the corpus. There is nothing to copy.

**Vorschlag**, because it is not optional in a business built on recurring contracts:

- A Reklamation is raised against an **Objekt + Zeitraum**, not against a person.
- It has a state machine: EINGEGANGEN → GEPRÜFT → NACHARBEIT_ANGESETZT → ERLEDIGT / ABGELEHNT,
  with an SLA per Leistungsart.
- Nacharbeit is a **new Einsatz** that references the original — so the Leistungsnachweis chain
  stays intact and the cost is attributable.
- It feeds the quality axis of the dispatch score. **Which makes it a policy input**, so under the
  eG model the weight it carries is ratified, not hardcoded. And the member being scored must be
  able to see and contest it — a scoring input a member cannot inspect is exactly the opacity the
  cooperative exists to remove.

### 5.5 What must be logged — the minimum list

**Vorschlag.** Every one of these is an event, append-only, with actor and timestamp:

| Event | Note |
|---|---|
| Auftrag eingegangen, Kanal, Aufnehmender | inline logs no equivalent publicly, but a phone-taken order needs an author |
| **Vermittlung**: which policy version ranked, which members were invited, who accepted | The audit trail the eG model requires — see SKILL.md §1 consequence 2 |
| Schlüsselausgabe / -rückgabe | Two signatures |
| Check-in / Check-out | Already `ShiftEvent.Kind.CHECK_IN` / `CHECK_OUT` (`apps/planning/models.py:199-200`, **Fakt**) |
| Zutrittsversagen + Grund + Foto | **Missing** — see §4 |
| Leistungsnachweis erstellt / gegengezeichnet | **Missing** |
| Mehraufwand angemeldet / genehmigt | **Missing** — approval in the loop |
| Reklamation, Nacharbeit, Abschluss | **Missing** |
| Employer correction of hours | Already `ShiftEvent.Kind.CORRECTED` (`models.py:201`) with `correct_minutes` requiring a reason (`apps/planning/attendance.py:148`, **Fakt**) |

**The pattern is already right in the repo and must be reused, not reinvented:** `ShiftEvent.save()`
raises `RuntimeError("Evenimentele de pontaj sunt imutabile.")` if `self.pk` is set
(`apps/planning/models.py:217-220`, **Fakt**), and `ConsentRecord` does the same
(`apps/accounts/compliance.py:67-70`, **Fakt**). A correction is a **new event**, never an
overwrite. Anything added here follows that rule.

---

## 6. Gaps in the source

1. **The dispatch mechanism itself is opaque.** „Vermittlung per Funk" to a „beauftragter
   selbständiger Kurier" — whether couriers **accept** offers or are **assigned** them, how they are
   selected, and how they are paid is nowhere published. This is precisely the layer the cleaning
   platform most needs, and it is the layer the site hides.
2. **No opening hours for the two main order lines**, although the tariff charges +50 % outside
   business hours.
3. **No dispatch SLA, no Disponenten count, no shift coverage.** „Erfahrung unserer Disponenten"
   is a claim with no figure behind it.
4. **No cancellation, complaint, refund, SLA, penalty, escalation or modification policy anywhere.**
5. **Order modification after placement is undocumented.** The Übersicht has `Ändern` links, but
   only before submission.
6. **The API is asserted, never specified** — no endpoint, no docs, no key, no webhook. *Inferenz:*
   `/api/` is an internal JSON API for the SPA order wizard. For cleaning a documented interface is
   worth more than it is for a courier (Hausverwaltungssoftware, DATEV-Lohnexport, customer ERP), so
   the closed-API choice is one **not** to copy.
7. **No member-facing application exists.** `robots.txt` lists only customer paths (`/registrieren/`,
   `/login/`, `/konto/`, `/dashboard/`) and no `/fahrer/`, `/kurier/`, `/mitglied/` or
   `/disposition/`. *Inferenz*, and second-hand: the robots.txt itself was not in the crawled
   corpus. If it holds, the owners of the cooperative have no self-service portal — which is the
   product opportunity, not a pattern to copy.
8. **Guest checkout is unconfirmed.** The wizard says „Bitte melden Sie sich an…"; no page states
   whether an order can complete without an account.

---

## Quellen

- https://inline-kurier.de/uber-uns — Disponenten, „ständige Erreichbarkeit der Fahrer per Funk oder
  Telefon", the channel table incl. Fahrerbetreuung +49 40 23 500 555, XXL intake hours.
- https://inline-kurier.de/kurierfahrten — the 5-step process incl. „Vermittlung … per Funk", the
  two-e-mail status model, out-of-hours surcharge windows, extra-service prices.
- https://inline-kurier.de/overnight — Sendungsverfolgung, cut-offs, `2. Anfahrt / Adressklärung`
  and `Wartezeit je 5 Min` price lines, insurance ceiling 3.000 €.
- https://inline-kurier.de/xxl — telephone-only intake Mo–Fr 07:00–18:00, individual planning.
- https://inline-kurier.de/bestellung and /bestellung/kurierfahrt/dokumentiert — `Signatur`
  („Empfängername wird bei Auslieferung erfasst"), the 3-stop limit, the 4-day horizon, the
  „Ansprechpartner bei eventuellen Auslieferproblemen" precondition.
- https://inline-kurier.de/dokumentierte-zustellung-kurierfahrt / -overnight — Vier-Augen-Prinzip,
  Zustellnachweis fields, CertiChain SafeBag and the two-signature rule.
- https://inline-kurier.de/faq-s — grep-verified absence of storn / Reklamation / Beschwerde /
  Zustellversuch across the whole corpus.
- https://inline-kurier.de/datenschutz — „Datenschutzhinweise für Empfänger" as a separate download;
  no mention of the operator side.
- Repo: `apps/planning/models.py:134,137,143-146,154-159,188-220` ·
  `apps/planning/attendance.py:101,148,169` · `apps/accounts/models.py:229-243` ·
  `apps/accounts/compliance.py:67-70`.
