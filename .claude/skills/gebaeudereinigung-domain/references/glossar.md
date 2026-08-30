# Glossar — the naming authority for Cleaning_SaaS

Covers: every German domain term this project uses or will use, with its meaning, why the software
needs it, and where it comes from.
**Stand: 2026-08-29.**
Material: the pland.app Arbeitslexikon, blog, `/funktionen/`, onboarding and Erfolgsgeschichten
clusters (crawled 2026-08-29, each row carries its URL), plus the live repository at
`/Users/Geronimo/Projects/Cleaning_SaaS` (each repo row carries `file:line`, read 2026-08-29).

**Spelling is normative.** When a German string reaches seed data, an export, a template or a
customer document, use exactly the spelling in column 1. Where two spellings are both attested,
both are listed and the preferred one is marked.

Short source keys used in the Quelle column:

| Key | Expands to |
|---|---|
| `AL/<slug>` | `https://pland.app/arbeitslexikon/<slug>` |
| `BLOG/<slug>` | `https://pland.app/blog/<slug>` |
| `FKT/<slug>` | `https://pland.app/funktionen/<slug>` |
| `ONB/<slug>` | `https://pland.app/onboardings/<slug>` |
| `TUT/<slug>` | `https://pland.app/tutorials/<slug>` |
| `ERF/<slug>` | `https://pland.app/erfolgsgeschichten/<slug>` |
| `repo:<path>:<line>` | file in this repository |
| **Ungeprüft** | not in the crawled sources — added domain knowledge, verify before use |

---

## A. Betrieb, Rollen, Organisation

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Gebäudereinigung** | The trade, and the company practising it | The tenant entity; the whole product domain | AL/facility-management; TUT/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung |
| **Gebäudereiniger** | The trained cleaner. **Protected job title** — only someone with the completed Ausbildung may officially use it | A qualification field on a person; marketing copy must not misuse the word | TUT/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung |
| **Gebäudedienstleister / Gebäudedienste** | Building-services provider — broader self-description than "Reinigung" | Free-text `branche` values in the market vary; do not build a closed list from "Gebäudereinigung" alone | ERF index page |
| **Reinigungsfirma** | Cleaning company (colloquial) | The tenant, in founder-facing copy | TUT/wie-grunde-ich-… |
| **Meisterbetrieb / Gebäudereinigermeister** | Master-craftsman business / master cleaner | A trust signal customers filter on; a company-profile flag | ERF/wie-der-meisterbetrieb-kille-… |
| **Geschäftsführung** | Managing director / owner | Sees objects, staff, material, consumption, revenue, profitability. A training audience, not an access level in the competitor's own system | FKT/uebersicht; ONB/… role pages |
| **Innendienst** | Back office | Plans deployments, keeps master data, invoices. Main dashboard user | ONB/mitarbeiter-in-pland-erstellen |
| **Außendienst** | Field staff | The mobile population; ratio to Innendienst is extreme in this trade | ERF/wie-landsberg-… |
| **Lohnbuchhaltung / Lohnbuchhalterin** | Payroll accounting / payroll clerk | Second pair of eyes before payroll; receives the export | ONB/freigabe-von-zeiterfassungen |
| **Objektleiter / Objektleitung** | Site manager | Distinct permission tier: inspection, quality control, ticket handling, absence approval | AL/reinigungsplan; ONB/kunden-objekte-in-pland |
| **Servicekraft** | Service/cleaning operative (the competitor's access-right name) | Lowest access level; app-only user | ONB/mitarbeiter-in-pland-erstellen |
| **Reinigungskraft / Reinigungspersonal** | Cleaner / cleaning staff | The mobile app's main user; also the public URL segment `/reinigungskraft/` in this repo | AL/reinigungsplan; repo:apps/accounts/public_urls.py:10 |
| **Vorarbeiter / Teamleiter** | Foreman / team leader | Organises workflow, trains new staff, first customer contact | TUT/was-benotige-ich-als-reinigungsfirma-an-personal |
| **Verwaltungspersonal** | Administrative staff | Bookkeeping, HR, customer care, scheduling | TUT/was-benotige-ich-als-reinigungsfirma-an-personal |
| **Springer** | Floating/relief cleaner with no fixed site | Worst case for billing and planning — one case study reports up to 40 different Objekte per month | ERF/wie-landsberg-… |
| **Subunternehmer** | Subcontractor | Plannable like an employee but a different liability and billing path | TUT/wie-grunde-ich-…; ERF/wie-christian-kwiatkowski-… |
| **Disposition / Disponent** | Dispatching / dispatcher | Releases shifts before payroll | ERF/wie-glanzhelden-… |
| **Niederlassungsleiter** | Branch manager | Multi-site tenant structure | ERF/erfolgsgeschichte-hbc-services-gmbh |
| **Betriebsleiter** | Operations manager | Role appearing on case-study pages | ERF/goldener-elch |
| **Prokurist / Prokuristin** | Authorised signatory (Prokura) | Decision-maker persona; may sign contracts | ERF/gebaudereinigung-oelfke-gmbh |
| **Betriebsanweisung / Dienstanweisung** | Written works instruction / directive | How firms enforce app use and define when working time starts | ERF/volk-volk; ERF/wie-landsberg-… |
| **Medienbruch** | A manual re-keying step between two systems | The thing an all-in-one product is sold to eliminate | ERF/wie-ow-harder-… |
| **Zettelwirtschaft** | "Paper chaos" — the industry's own word for the status quo ante | The problem statement; named in 19 of 31 case studies | ERF cluster |

---

## B. Objekt, Bereich, Leistung

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Objekt** | The building or site being cleaned | Central operational entity; anchors zones, devices, material, tickets, plan | AL/unterhaltsreinigung; repo:apps/planning/models.py:21-22 (`Site`, verbose_name "Obiectiv") |
| **Bereich / Ort** | Area or location inside an Objekt (floor, corridor, sanitary block) | Planning granularity — not the whole building | BLOG/gebaudereinigung-reinigungsplan-hier-kostenlose-vorlage-herunterladen; repo:apps/planning/models.py:42-47 (`Zone`) |
| **Raum** | Room | Reinigungspläne are structured per room or area | AL/reinigungsplan |
| **Objektbesichtigung / Objektbegehung** | Pre-contract site survey | Captures room count, area, **number of toilets**, floor covering, customer wishes — the inputs to the plan and the quote | AL/unterhaltsreinigung; BLOG/unterhaltsreinigung-die-ultimative-checkliste |
| **Objektmappe (digitale)** | Site dossier: all photos, documents and tickets of an Objekt, mobile | The Objektleiter's main mobile screen | FKT/uebersicht |
| **Leistungsverzeichnis (LV)** | Line-item specification of areas, frequencies and quality levels; becomes contractual in tenders | What the Objektleiter checks against and what the customer is billed for. **Missing entirely from this repo.** | FKT/uebersicht; ERF/erfolgsgeschichte-temberger |
| **Raumbuch** | Room book — the underlying register of areas with type, m², floor covering, cleaning group | The data layer under an LV. **Ungeprüft** (the crawled sources never name it) | Ungeprüft |
| **Leistung** | A single service line (Staubwischen, Staubsaugen, Wischen …) | Service-catalogue entity; also an invoice line | BLOG/gebaudereinigung-reinigungsplan-… |
| **Zugangscode / Alarmcode** | Door or alarm code for the site | Must be stored as a secret with audited access — not free text on the record | ONB/kunden-objekte-in-pland; BLOG/unterhaltsreinigung-die-ultimative-checkliste |
| **Notfallplan** | Emergency plan attached to the Einsatz | One of the named Einsatz attachments | BLOG/unterhaltsreinigung-die-ultimative-checkliste |
| **Kunde** | Customer / client | Billing counterpart; may own several Objekte. **No `Kunde` model exists** — a client is an `Account` with `Capability.CLIENT` | ONB/kunden-objekte-in-pland; repo:apps/accounts/enums.py:20 |
| **Rechnungsempfänger** | Invoice recipient | Can differ from the party the service is delivered to | FKT/angebot-und-rechnung-gebaudereinigung |
| **Leistungsempfänger** | Service recipient | The other half of the same split; several per Auftrag are possible | FKT/angebot-und-rechnung-gebaudereinigung |
| **Kostenstelle** | Cost centre | Named by a case study as the missing feature blocking a full invoicing rollout | ERF/wie-landsberg-… |

---

## C. Reinigungsarten und Frequenzen

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Unterhaltsreinigung** | Routine cleaning at fixed intervals; keeps rooms at an already-clean level. Typically floors, surfaces, furniture, sanitary facilities, waste and dust | The recurring, contract-based volume business → recurrence rules and Dauerrechnung | AL/unterhaltsreinigung |
| **Grundreinigung** | Intensive periodic cleaning that removes built-up soiling; includes walls and ceilings | Episodic, separately priced, separately staffed. Its interval is per surface, not global | AL/grundreinigung |
| **Sichtreinigung** | Surface-level cleaning: only visible soiling removed, for a tidy appearance | A *lower* service level that must be nameable in a contract and priced differently | BLOG/reinigungsstandards-und-din-normen-… |
| **Sonderreinigung** | Cleaning outside the regular scope — after construction, façade, graffiti removal | One-off job type with its own quoting and docket flow | BLOG/reinigungsstandards-und-din-normen-… |
| **Glasreinigung / Fensterreinigung** | Professional cleaning of glass: windows, doors, façade elements | Own m²-based pricing, own method and object taxonomy, own qualification | AL/glasreinigung |
| **Bauendreinigung / Bauschlussreinigung** | Final clean after building works | Distinct service leaf, seeded in this repo as `bauendreinigung` | repo:apps/taxonomy/migrations/0003_seed_categories.py:43-44 |
| **Fassadenreinigung** | Façade (and paving) cleaning | Height work; different equipment and risk assessment | repo:…0003_seed_categories.py:47-48 |
| **Treppenhausreinigung** | Stairwell and common-area cleaning | Named as the typical no-signal location → an offline requirement on any mobile capture | ERF cluster; repo:…0003_seed_categories.py:37-38 |
| **Teppichgrundreinigung** | Deep carpet cleaning — Shampoonieren, Extrahieren, Dampfreinigen | A Grundreinigung sub-type with long drying times → a scheduling constraint | AL/grundreinigung |
| **Bodengrundreinigung** | Deep hard-floor cleaning — Schrubben, Strippen, neues Wachsen/Versiegeln | Grundreinigung sub-type | AL/grundreinigung |
| **Fenstergrundreinigung** | Deep window cleaning incl. frames and sills | Grundreinigung sub-type | AL/grundreinigung |
| **Sanitärgrundreinigung** | Deep sanitary cleaning — limescale on WCs, basins, showers, taps | Grundreinigung sub-type | AL/grundreinigung |
| **Reinigungsintervall** | The cleaning interval | The recurrence rule that generates every Einsatz | AL/reinigungsintervall |
| **Reinigungsfrequenz** | How often a given task is performed | The 4th column of the Reinigungsplan template | BLOG/gebaudereinigung-reinigungsplan-… |
| **täglich / wöchentlich / monatlich / vierteljährlich / halbjährlich / jährlich / saisonal** | The interval classes, as the union of two source pages | The enum must be the union — neither page carries all seven | AL/reinigungsintervall (no saisonal); AL/reinigungsplan (saisonal, no quarterly/annual) |
| **Nutzungsintensität** | Intensity of use of a building | An interval driver — "a toilet used by 100 people needs more frequent cleaning than one for 5" | BLOG/unterhaltsreinigung-die-ultimative-checkliste |
| **Besucherfrequenz** | Persons per day using the building | An interval driver; store it so an interval can be re-justified | AL/reinigungsintervall |
| **Hygieneanforderung** | Hygiene requirement level | Interval driver and agent-selection gate | AL/reinigungsintervall |
| **Werterhaltung** | Preservation of asset value | The stated purpose of both facility management and cleaning intervals — a sales argument and a reporting axis | AL/facility-management |

---

## D. Reinigungsplan, Nachweise, Qualität

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Reinigungsplan** | Written concept describing how, where and how often a building is cleaned | The per-area contract of task, frequency, responsibility and control. Used as **evidence** in complaints and disputes, so versions must be immutable and timestamped | AL/reinigungsplan; BLOG/gebaudereinigung-reinigungsplan-… |
| **Reinigungsplan-Spalten** | The template columns: **Bereich/Ort · Leistung · Beschreibung · Reinigungsfrequenz** (+ optional Materialien, spezielle Anweisungen) | The canonical export schema German customers expect. This repo exports exactly these plus Dauer je Einsatz, Wochentage, Minuten/Woche | BLOG/gebaudereinigung-reinigungsplan-…; repo:apps/planning/reinigungsplan.py:18-26 |
| **Arbeitsschein** | Work docket signed by the customer on site | The bridge from Einsatz to Rechnung; proof of performance. **Missing from this repo** | BLOG/hier-kostenlose-arbeitsschein-vorlage-herunterladen |
| **Leistungsnachweis** | Proof of the services delivered, sent to the customer | Photos, comments, star rating; the customer-facing evidence after each clean | AL/unterhaltsreinigung; FKT/zeiterfassung-gebaeudereinigung |
| **Qualitätskontrolle / Qualitätscheck** | Post-clean verification by the Objektleiter | Photos + comments + star rating; can raise a Ticket on a defect | AL/unterhaltsreinigung; FKT/uebersicht |
| **Reklamation** | Customer complaint | Full ticket lifecycle with a processing deadline, cause analysis and reporting | AL/reklamationsmanagement |
| **Reklamationsmanagement / Beschwerdemanagement** | Complaint management | 7 ordered tasks from intake to trend reporting | AL/reklamationsmanagement |
| **Bearbeitungsfrist** | Processing deadline on a complaint | Must be monitored automatically | AL/reklamationsmanagement |
| **Ticket** | The work item a complaint or task becomes | Kanban-style states; can attach to staff, customer, object, order, invoice or device | FKT/aufgabenmanagement |
| **Erfüllungsgehilfe** | Vicarious agent | Complaints may concern the company's own services *or its agents'* — a liability-scope distinction | AL/reklamationsmanagement |
| **Optische vs. hygienische Reinigungsdefizite** | Visible-dirt defects vs. germ-load defects | The DIN EN 13549 defect classification; a required field on a quality record | AL/din-normen |
| **Checkliste** | Checklist used to control and document work done | The execution artefact under a Reinigungsplan | AL/reinigungsintervall |
| **Sterne / Sternebewertung** | Star rating on a documented clean | An explicit field on the proof of service. Scale and rater are **not stated on the source pages** | AL/reinigungsplan; FKT/uebersicht |

---

## E. Planung und Einsatz

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Einsatz** | A single deployment/shift at an Objekt | The atomic scheduling unit; time, docket and invoice all hang off it | FKT/einsatzplanung-gebaeudereinigung; repo:apps/planning/models.py:140 (`Shift`) |
| **Einsatzplanung / Einsatzplaner** | Deployment planning and the planner screen | Customers call it "das Herzstück"; adopted in 29 of 31 case studies | FKT/einsatzplanung-gebaeudereinigung; ERF cluster |
| **Dienstplan** | Duty roster | The Soll side of the Soll/Ist comparison, and the source of surcharge time windows | AL/dienstplan |
| **Personaleinsatzplanung (PEP)** | Workforce deployment planning | Matching qualified staff to sites at the right time | AL/personaleinsatzplanung |
| **Schichtplanung / Schicht** | Shift planning / shift | Used interchangeably with Einsatzplanung by several firms | ERF cluster |
| **Teameinsatz** | One Einsatz with several assignees | Edits need per-member *and* per-series scoping | ONB/auftrage-und-einsatzplanung-in-pland |
| **Wiederkehrender Einsatz / Serienauftrag** | Recurring deployment generated from an interval | The decisive purchase criterion for one case-study firm; changes apply **only to the future**, and detached occurrences are immune | ONB/auftrage-und-einsatzplanung-in-pland; ERF/gores-facility-services-gmbh |
| **Dauerauftrag** | Standing order | Can carry stored Pausen- und Fahrzeiten | FKT/uebersicht |
| **Sonderauftrag** | One-off special job | Ad-hoc order type; triggers a push notification to the worker | FKT/einsatzplanung-gebaeudereinigung |
| **Offene Schicht / unbesetzter Einsatz** | Open, unstaffed shift | Found via the planner's magnifier, assigned by drag-and-drop | ONB/abwesenheiten-in-pland |
| **Vertretung / Vertretungseinsatz** | Substitution / cover for an absent worker | The highest-frequency daily disruption in this trade. Suggested from **Kapazitäten und Qualifikationen**; the customer is notified by e-mail | FKT/einsatzplanung-gebaeudereinigung |
| **Objekterfahrung** | Prior experience at a specific object | A planner filter, and it restricts the default ticket-assignee list | ONB/auftrage-und-einsatzplanung-in-pland |
| **Qualifikation** | Qualification / skill | Input to substitution ranking and to machine-assignment blocking | FKT/einsatzplanung-gebaeudereinigung |
| **Kapazität** | Free capacity of a worker in the period | The other substitution input; the capacity bar turns red when exceeded | ONB/auftrage-und-einsatzplanung-in-pland |
| **Planungsassistent** | Planning assistant answering "who still has time? who is nearby?" | Availability + proximity suggestion | FKT/uebersicht |
| **Tourenplanung** | Route/tour planning | Minimises travel; also used to time-shift methods with long drying times | BLOG/reinigungsmethoden-fur-verschiedene-oberflachen-so-reinigen-profis-richtig |

---

## F. Zeit und Abwesenheit

Detail rules live in **gr-zeiterfassung**. This table fixes the vocabulary only.

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Zeiterfassung** | Working-time recording | A legal duty in this trade, and the universal entry module — present in 31 of 31 case studies | FKT/zeiterfassung-gebaeudereinigung |
| **Stempeln / Stempel** | Clocking in and out | "Stempel vergessen? Einfach nachtragen" — retroactive entry is a first-class supported action | FKT/zeiterfassung-gebaeudereinigung |
| **Stundenzettel** | Timesheet | The paper artefact being replaced; "digitaler Stundenzettel" is the sales hook | AL/stundenzettel |
| **Sollarbeitszeit / Soll-Zeit / Vorgabe** | Planned/target time | One of three values kept per record | ONB/freigabe-von-zeiterfassungen |
| **Ist-Zeit / Erfassung** | Actually recorded time | Second of the three | ONB/freigabe-von-zeiterfassungen |
| **Lohn-Zeit** | The approved time that goes to payroll | Third of the three — a three-value audit trail per record | ONB/freigabe-von-zeiterfassungen |
| **Soll/Ist-Vergleich** | Target/actual comparison | The automatic error check that feeds the approval queue | FKT/zeiterfassung-gebaeudereinigung |
| **Zeitenfreigabe / Freigabe** | Release/approval of recorded hours | The review queue; approval basis is Vorgabe, Erfassung or Custom | ONB/freigabe-von-zeiterfassungen |
| **Unter- und Überschreitung** | Underrun / overrun beyond a tolerance | Tolerance expressed in percent **or** minutes | ONB/freigabe-von-zeiterfassungen |
| **Nachgetragene Zeiten** | Retro-entered times | Must remain distinguishable from live-captured times | ONB/freigabe-von-zeiterfassungen |
| **Standortfehler** | Clock-in/out too far from the Objekt | An approval trigger; the competitor's threshold is 800 m | ONB/freigabe-von-zeiterfassungen |
| **Standortkontrolle** | Location check against the object radius | Requires a per-object radius on the site record | FKT/uebersicht |
| **Einfache Zeiterfassung** | Unplanned time entry with no Einsatz behind it, e.g. a QR-code clock-in | Its own error type in the approval queue | ONB/freigabe-von-zeiterfassungen |
| **Fahrzeit / Fahrzeiterfassung** | Travel time between two Einsätze, recorded and paid | Only counts inside a configurable **maximale Zwischenzeit** | ONB/fahrzeiterfassung-mit-pland |
| **Maximale Zwischenzeit** | Maximum gap between two Einsätze for travel time to count | Competitor default: 3 hours, adjustable | ONB/fahrzeiterfassung-mit-pland |
| **Pause / Ruhepause** | Statutory break | Break minimums are a hard validator on a planned shift | AL/dienstplan |
| **Abwesenheit / Abwesenheitsart** | Absence / absence type | Tenant-definable types; each carries an Entgeltfortzahlung rule | ONB/abwesenheiten-in-pland |
| **Urlaub / Urlaubsantrag** | Holiday / leave request | Mobile request, one-click approval, auto-notification | FKT/abwesenheitsverwaltung |
| **Krankmeldung / Krankheitsschein** | Sick note / sick certificate | Filed in-app with a document attachment | FKT/abwesenheitsverwaltung |
| **Urlaubsanspruch** | Holiday entitlement | Derived from weekly working days; see gr-tarif-und-lohn for the branch figure | ONB/urlaubsanspruch-von-mitarbeitern |
| **Resturlaub** | Remaining holiday entitlement | Employee self-service; removes office visits | FKT/abwesenheitsverwaltung |
| **Wartezeit** | Qualifying period before holiday accrues | A configurable rule for new hires | ONB/einstellungen-fur-die-urlaubstageberechnung |
| **Übernahme (in einen neuen Zyklus)** | Carry-over of unused holiday days | Configurable; the options are **not enumerated on the source pages** | ONB/einstellungen-fur-die-urlaubstageberechnung |
| **Entgeltfortzahlung** | Continued pay during an absence | Basis is one of four: unbezahlt · Vertragsstunden · geplante Stunden (Planstunden) · Stundendurchschnitt | FKT/lohnabrechnung-gebaeudereinigung; ONB/abwesenheiten-in-pland |
| **Überstunden** | Overtime | Payroll and cost control; can be converted into extra holiday days | ONB/urlaubsanspruch-von-mitarbeitern |
| **Pontaj** | *(Romanian)* time recording | The dashboard segment `/dashboard/pontaj/` in this repo — Romanian by convention | repo:apps/dashboard/urls.py:41 |

---

## G. Lohn und Tarif — vocabulary only

**Never quote a euro figure or a percentage from this file. Load `gr-tarif-und-lohn`.**

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Tarifvertrag** | Collective agreement | The wage floor and the surcharge rules in this trade | FKT/lohnabrechnung-gebaeudereinigung |
| **Rahmentarifvertrag (RTV)** | Framework collective agreement | Stated basis for automatic night/Sunday/holiday surcharges and for the branch holiday entitlement | FKT/lohnabrechnung-gebaeudereinigung; ONB/einstellungen-fur-die-urlaubstageberechnung |
| **Lohntarifvertrag** | Wage collective agreement | Stated basis for minimum wages, and for the non-cumulation rule on coinciding surcharges | ONB/lohnarten-und-zuschlage-in-pland |
| **Allgemeinverbindlichkeit (AVE)** | Declaration that a collective agreement binds all employers in the trade | Why a wage floor applies even to non-member firms — encoded as a comment in this repo | repo:apps/contracts/models.py:62-64; Ungeprüft for the mechanism |
| **Lohngruppe** | Collectively agreed wage group | Drives the hourly rate. The competitor supports **Lohngruppen 1 bis 9** | FKT/uebersicht; FKT/lohnabrechnung-gebaeudereinigung |
| **Mindestlohn** | Statutory minimum wage | The general floor; `WageFloor.Kind.GENERAL` in this repo | repo:apps/contracts/models.py:68 |
| **Branchenmindestlohn** | Sector minimum wage (Gebäudereinigung) | The higher of the two floors applies; `WageFloor.Kind.GEBAEUDE` | repo:apps/contracts/models.py:69, 206-209 |
| **Lohnart** | Wage type mapping hours to a pay line | User-definable; a prerequisite for any Zuschlag | ONB/lohnarten-und-zuschlage-in-pland |
| **Stundenlohn** | Hourly wage paid to the worker | An attribute of the Lohnart | ONB/lohnarten-und-zuschlage-in-pland |
| **Stundensatz / Verrechnungssatz** | Hourly rate charged to the customer | Distinct from Stundenlohn — never conflate the two | ERF/erfolgsgeschichte-temberger |
| **Zuschlag / Zuschlagsart** | Surcharge | Named kinds: Nacht-, Sonntags-, Feiertags-, Gefahrenzuschlag, plus free-defined types | FKT/zeiterfassung-gebaeudereinigung; FKT/lohnabrechnung-gebaeudereinigung |
| **Erschwerniszuschlag** | Hardship surcharge | A named Arbeitslexikon entry in the tariff cluster | AL/erschwerniszuschlaege |
| **Nichtkumulation der Zuschläge** | Only the highest surcharge applies when night, Sunday and holiday coincide | Implemented as a hard rule by the competitor, citing the Lohntarifvertrag | ONB/lohnarten-und-zuschlage-in-pland |
| **Anstellungsverhältnis** | Employment relationship | Per-employee payroll configuration, versioned by validity dates | FKT/lohnabrechnung-gebaeudereinigung |
| **Vollzeit / Teilzeit / Minijob** | Full-time / part-time / marginal employment | All three must be planned together in one roster | AL/dienstplan; repo:apps/contracts/models.py:30-34 |
| **Geringfügigkeitsgrenze** | Minijob monthly earnings ceiling | Exceeding it predictably converts the relationship into a fully insured one — modelled as time-versioned rows | repo:apps/contracts/models.py:92-114 |
| **Lohnabrechnung / Entgeltabrechnung** | Payroll run / pay statement | The most-quantified pain point in the case studies | FKT/lohnabrechnung-gebaeudereinigung |
| **Vorbereitende Lohnabrechnung / vorbereitende Entgeltabrechnung** | Payroll pre-processing | The handoff artefact to the payroll bureau — what the software actually produces | AL/cafm |
| **Lohnbüro / Steuerbüro / Steuerberater** | Payroll bureau / tax office / tax adviser | The export recipient | FKT/lohnabrechnung-gebaeudereinigung |
| **Lohnliste / Lohnzeit** | Per-employee payroll list showing Plan-Zeit, erfasste Zeit and Lohn-Zeit | The reconciliation screen before export | ONB/freigabe-von-zeiterfassungen |

---

## H. Kaufmännisch — Angebot, Auftrag, Rechnung

Detail rules live in **gr-auftrag-und-faktura**. None of these entities exists in the repo.

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Angebot** | Quote / offer | Becomes an Auftrag on customer confirmation; accepted quotes are billed automatically in the competitor's flow | FKT/angebot-und-rechnung-gebaudereinigung |
| **Auftragsbestätigung** | Order confirmation | Middle step of the order-to-cash chain | ERF/wie-ow-harder-… |
| **Auftrag** | Order / contract job | The commercial parent of Einsätze and of every invoice; also the level at which Deckungsbeitrag is reported | AL/deckungsbeitrag; FKT/angebot-und-rechnung-… |
| **Auftragsart** | Order/service type (Glasreinigung, Unterhaltsreinigung …) | Planner filter and invoice classification; one case study reports the rate and tariff adjust automatically per Auftragsart | ONB/auftrage-und-einsatzplanung-in-pland; ERF/erfolgsgeschichte-temberger |
| **Kalkulation** | Cost calculation behind a price | Five named components for a Grundreinigung: Flächenberechnung, Arbeitsstunden, Materialeinsatz, Personal-/Lohnkosten, sonstige Kosten | AL/grundreinigung |
| **Pauschalpreis** | Flat/lump-sum price | One of the two named pricing modes | AL/grundreinigung |
| **Leistungswert** | m²/hour performance value per surface and method | The real currency of bidding in this market. **The crawled sources publish none.** | Ungeprüft |
| **Rechnung** | Invoice | The commercial output; must mirror the agreed price and scope of the Angebot exactly | TUT/so-stellen-sie-rechnungen-als-gebaudereinigung |
| **Abschlagsrechnung** | Advance/progress invoice for a not-yet-complete service; fixes **percentage shares of the total**; may precede performance | Warranty starts only on acceptance of the whole service | AL/abschlagsrechnung |
| **Anzahlungsrechnung / Akontorechnung** | Synonyms for Abschlagsrechnung | Same document, different customer vocabulary | AL/abschlagsrechnung |
| **Kumulierte Abschlagsrechnung** | Cumulative variant: bills everything so far minus prior payments | A distinct calculation mode, not a separate document type | AL/abschlagsrechnung |
| **Teilrechnung / Teilschlussrechnung** | Invoice for a **completed** partial service or milestone | Warranty for that part starts immediately | AL/teilrechnung |
| **Schlussrechnung / Endrechnung** | Final invoice offsetting all prior Abschlags- and Teilzahlungen | Only issuable when the Auftrag is complete | AL/schlussrechnung |
| **Dauerrechnung** | Standing invoice for recurring services over an Abrechnungszeitraum | Replaces one invoice per clean | AL/dauerrechnung |
| **Abrechnungszeitraum** | Billing period | Field on a Dauerrechnung; typical values monatlich, wöchentlich, individuell | AL/dauerrechnung |
| **Leistungszeitraum** | Service period an invoice bills | Determines which Einsätze are pulled into the invoice | ONB/dynamische-positionen-in-rechnungen-mit-pland |
| **Stornorechnung** | Cancellation invoice | Correction path — never deletion | FKT/angebot-und-rechnung-… |
| **Gutschrift** | Credit note | Own document type with its own numbering settings | FKT/angebot-und-rechnung-… |
| **Sammelrechnung** | Collective invoice | Announced by the competitor, not documented | ONB webinar page |
| **Dynamische Position** | Invoice line billed after the fact by Soll-Zeit, Lohnzeit or per Termin | Enables performance-based billing instead of flat rates | ONB/dynamische-positionen-in-rechnungen-mit-pland |
| **Pflichtangaben** | Mandatory invoice fields | Must be validated before an invoice can be issued. The crawled pages cite **no statute** for them | AL/abschlagsrechnung; AL/teilrechnung |
| **Rechnungsnummer / Rechnungskürzel** | Invoice number and its prefix | Numbering must be gapless and the counter's changes logged | ONB/die-wichtigsten-faktura-einstellungen-in-pland |
| **Zahlungsziel** | Payment term | Printed on the invoice; drives liquidity forecasting | ONB/die-wichtigsten-faktura-einstellungen-in-pland |
| **Mahnwesen / Mahnstufe / Zahlungserinnerung** | Dunning, dunning level, payment reminder | Multi-level, per-tenant configurable escalation | FKT/angebot-und-rechnung-… |
| **Offene Posten** | Open (unpaid) items | The receivables view, needed daily | FKT/umsatzuebersicht |
| **Buchungsnummer** | Booking/transaction number | The key for auto-matching incoming payments | FKT/umsatzuebersicht |
| **E-Rechnung** | Electronic invoice in a structured, machine-processable format | Public-sector customers require it today | AL/e-rechnung |
| **XRechnung** | The German standard for e-invoices to public authorities, based on **EN 16931** | One of the two required output formats | AL/e-rechnung |
| **ZUGFeRD** | Hybrid format: PDF with embedded structured XML; mainly private sector | The other required output format | AL/e-rechnung |
| **Kleinunternehmer** | Small-business VAT status (§19 UStG) | An exemption flag on the company; also a `LegalStatus` value in this repo | AL/e-rechnung; repo:apps/accounts/enums.py:34 |
| **Deckungsbeitrag (DB)** | Contribution margin = **Erlöse − variable Kosten** | Per-Auftrag profitability; a negative DB is flagged as a threat to the business | AL/deckungsbeitrag |
| **Gesamtdeckungsbeitrag** | Sum of contribution margins across all jobs | Tests whether fixed costs are covered | AL/deckungsbeitrag |
| **Umsatz / tagesaktueller Umsatz** | Revenue / revenue as of today | The finance dashboard | FKT/umsatzuebersicht |
| **BWA (betriebswirtschaftliche Auswertung)** | Monthly management accounts | Depends on timely invoicing — a stated customer outcome | ERF/wie-wischbar-… |
| **Lieferschein** | Delivery note | Auto-generated for the customer **and** the supplier when material is requested | FKT/uebersicht |

---

## I. Material, Geräte, Arbeitssicherheit

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Materialwesen** | Materials management | The nav area holding Artikel and orders | ONB/materialbestellungen-in-pland |
| **Materialschrank** | The per-object material cabinet: which articles are allowed here and at what monthly budget | Budget 0 = unlimited; if nothing is attached, any article may be ordered | ONB/materialbestellungen-in-pland |
| **Artikel** | An orderable material item with photo, supplier and group (e.g. Tücher, Chemie) | The material catalogue row | ONB/materialbestellungen-in-pland |
| **Materialbestellung** | A material order raised by the cleaner on site | Routed to the office, convertible into an invoice line with customer-specific prices | FKT/materialbestellungen |
| **Lieferant** | Supplier | Receives orders and delivery notes by e-mail | ONB/materialbestellungen-in-pland |
| **Verbrauch / Verbrauchskontrolle** | Consumption and its control | Per object per month; feeds cost control | ERF cluster |
| **Reinigungskarren / Reinigungswagen** | Cleaning trolley | Carries everything needed room to room; the unit material is stocked to | BLOG/gebaudereinigung-was-fur-material-brauche-ich |
| **Dosiersystem** | Dosing system | Prevents overdosing — a safety **and** sustainability lever | BLOG/arbeitssicherheit-… |
| **Mischverbot** | Prohibition on mixing certain agents (e.g. acids and chlorine) | A self-referential constraint with a hard UI warning | BLOG/arbeitssicherheit-… |
| **Sicherheitsdatenblatt** | Safety data sheet | Must be attached to every chemical and reachable on site | BLOG/arbeitssicherheit-…; repo:apps/catalog/models.py:63-65 |
| **Gefahrstoffkennzeichnung / Gefahrstoffetikett** | Hazardous-substance labelling | Must be known and observed by staff; GHS pictograms are stored per product in this repo | BLOG/arbeitssicherheit-…; repo:apps/catalog/models.py:65 |
| **PSA (Persönliche Schutzausrüstung)** | Personal protective equipment | Issue, inspection and expiry tracking per person | BLOG/arbeitssicherheit-… |
| **Unterweisung / Einweisung** | Formal instruction / machine induction | Must block machine assignment when missing | BLOG/arbeitssicherheit-… |
| **Gefährdungsbeurteilung** | Risk assessment | Named on the source as "Gefahrenanalyse bei neuen Einsatzorten" | BLOG/arbeitssicherheit-… |
| **Geräteverwaltung** | Equipment management | Machines assigned to an object and to a person/team, with maintenance, inspection and statutory test intervals | FKT/geraeteverwaltung |
| **Wartungsintervall / Prüfintervall** | Maintenance interval / inspection interval | Missing them causes downtime or fines | FKT/geraeteverwaltung |
| **DGUV V3** | Named example of a statutory electrical test for equipment | The interval belongs on the equipment *type*, with a per-device override and a stored test report | FKT/geraeteverwaltung; Ungeprüft for the interval values |
| **Telemetrie** | Machine runtime data reported by a device | In this repo: a source of **verification**, not of Zeiterfassung and not of calibration | repo:apps/devices/models.py:1-15 |

Full equipment, agent and machine lists: `reinigungsarten-normen-qualitaet.md` §H.

---

## J. Hygiene, Normen, Fachbegriffe der Ausführung

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Vier-Farben-System** | Colour-coded cloths reserved to areas: **Rot** WC/urinals, **Gelb** rest of bathroom, **Grün** kitchen and patient rooms, **Blau** offices/living/children's rooms | Prevents Keimverschleppung. **Make the mapping tenant-configurable** — the source cites no norm for it and conventions differ | AL/vier-farben-system |
| **Wechseltuchmethode** | One fresh cloth per new room or area | Makes cloth demand a computable function of the plan | AL/vier-farben-system |
| **Keimverschleppung / Kreuzkontamination** | Germ carry-over / cross-contamination | The hazard the colour system exists to prevent | AL/vier-farben-system; BLOG/hygienestandards-in-der-gebaudereinigung-2025 |
| **Hygienebereich / Hygienezone** | Hygiene zone classification of an area | Gates which agents are permitted and sets a minimum frequency | AL/vier-farben-system; BLOG/hygienestandards-… |
| **Wischdesinfektion** | Wipe disinfection | Requires a VAH-listed product and a recorded contact time | BLOG/reinigungsmethoden-…-profis-richtig |
| **Einwirkzeit** | Contact/dwell time of a disinfectant | Must be timed and documented as liability evidence | BLOG/reinigungsmethoden-…-profis-richtig |
| **VAH-Liste** | List of tested disinfectants (Verbund für Angewandte Hygiene) | A `vah_gelistet` flag gates product selection in hygiene zones | BLOG/hygienestandards-… |
| **RKI (Robert Koch-Institut)** | German federal public-health institute | Its guidelines govern sensitive zones such as hospitals | BLOG/hygienestandards-… |
| **DIN-Norm** | A DIN standard | **Voluntary unless made binding by contract or law** — in tenders it routinely is. Model norm applicability per contract | AL/din-normen |
| **Zertifizierung** | Certification against a norm | Usable as a quality mark and a tender advantage | AL/din-normen |
| **Schleifrichtung** | Grain/brushing direction on metal | A technique instruction that must reach the operative | BLOG/reinigungsmethoden-…-profis-richtig |
| **Faserrichtung** | Grain direction on wood | Same | BLOG/reinigungsmethoden-…-strahlend-sauber |
| **Materialverträglichkeitstest** | Material compatibility (patch) test | A mandatory pre-step on textiles → a checklist item | BLOG/reinigungsmethoden-…-profis-richtig |
| **Flugrost** | Flash rust on stainless steel | A named damage mode → a liability record | BLOG/reinigungsmethoden-…-profis-richtig |
| **Schlieren** | Streaks/smears | The classic quality defect on glass and stainless steel | BLOG/reinigungsmethoden-…-profis-richtig |
| **Pflegefilmbildung / Einpflegen / Wischpflege** | Building and maintaining a protective care film on a floor | A distinct method type with its own frequency, separate from cleaning | BLOG/reinigungsmethoden-…-profis-richtig |
| **Sprühextraktion / Nassshampoonierung** | Spray extraction / wet shampooing of carpets | Long drying times → a scheduling constraint | BLOG/reinigungsmethoden-…-profis-richtig |
| **Encapsulation / Pad-System** | Interim carpet cleaning by encapsulation | A frequency tier between Unterhalt and Grund | BLOG/reinigungsmethoden-…-profis-richtig |
| **Trockenextraktion** | Dry extraction on upholstery | A gentle-method flag | BLOG/reinigungsmethoden-…-profis-richtig |
| **Abziehertechnik** | Squeegee technique with Einwascher and rubber blade | The professional glass method | BLOG/reinigungsmethoden-…-profis-richtig |
| **Reinwasser** | Pure, demineralised water | A chemical-free method family with its own consumables model | BLOG/reinigen-mit-reinwasser-… |
| **Osmoseanlage** | Reverse-osmosis unit | Equipment entity with a per-1000 L running cost | BLOG/reinigen-mit-reinwasser-… |
| **Mischbettharz / Ionenaustauscher** | Mixed-bed resin / ion exchanger | The costlier alternative demineralisation route | BLOG/reinigen-mit-reinwasser-… |
| **Sockelleiste** | Skirting board | A Grundreinigung checklist item | BLOG/wie-sieht-eine-grundreinigung-in-einer-wohnung-aus |
| **Schmutzfangmatte** | Dirt-trapping entrance mat | A seasonal task and a winter slip-prevention measure | BLOG/saisonale-reinigungstipps-… |
| **Hand-Arm-Vibrationssyndrom (HAVS)** | Hand-arm vibration syndrome | An occupational-health risk tied to machine maintenance | BLOG/gesundheitsrisiken-bei-reinigungskraften-… |

---

## K. Facility Management und Branchenkategorien

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Facility Management (FM)** | Managing and maintaining buildings, plant and installations | The customer's business discipline; cleaning sits inside it | AL/facility-management |
| **Infrastrukturelles Gebäudemanagement** | Services around the building: Gebäudereinigung, Hausmeisterdienste, Sicherheits-/Wachdienste, Gärtnerdienste, Parkraumüberwachung, Müllentsorgung, Catering | The FM domain the product sells into | AL/facility-management |
| **Technisches Facility Management** | Operating the building and its plant: Wartung, Inspektionen, Gebäudetechnik, Modernisierungen, Reparaturen | Adjacent scope — where an expansion path lies | AL/facility-management |
| **Kaufmännisches Facility Management** | Commercial FM: Controlling, Betriebskostenabrechnung, Flächenmanagement, Objektbuchhaltung, Vertragsmanagement | The vocabulary a large FM client will use | AL/facility-management |
| **CAFM** | Computer-Aided Facility Management — the software layer over FM | The product category this SaaS competes in | AL/cafm |
| **Hausmeisterdienst / Hauswartung** | Caretaker/janitorial services | Frequently bundled with cleaning; a second vertical for the competitor | pland.app/hausmeisterdienste-lp |
| **Winterdienst** | Winter/gritting service | A seasonal service leaf, seeded in this repo | repo:apps/taxonomy/migrations/0003_seed_categories.py:66 |
| **Gartenpflege** | Grounds maintenance | Seeded leaf; §35a-eligible | repo:…0003_seed_categories.py:64-65 |
| **Entrümpelung** | Clearance and disposal | Seeded leaf | repo:…0003_seed_categories.py:67-68 |
| **Haushaltsnahe Dienstleistungen** | Household-related services | The parent category whose leaves are §35a-deductible for a private client | repo:…0003_seed_categories.py:58-59 |
| **Ausschreibung** | Tender | Where DIN norms and an LV become contractually binding | AL/din-normen |
| **CMS Berlin** | The German cleaning-industry trade fair ("Cleaning Management Services") | The main acquisition channel named by four case studies | AL/cms-berlin |
| **Rationell Reinigen** | German trade magazine for the cleaning industry | A named acquisition channel | ERF/volk-volk |

---

## L. Recht, Gründung, Verbände

Full treatment in `branche-und-gruendung.md`.

| Begriff | Bedeutung | Warum die Software das braucht | Quelle |
|---|---|---|---|
| **Gewerbeanmeldung** | Trade registration at the Gewerbeamt | A field on the company account; also a verification document type in this repo | TUT/welche-rechtlichen-aspekte-…; repo:apps/accounts/compliance.py:10 |
| **Handelsregister / HRB** | Commercial register and its entry number | Conditional on legal form; a verification document type | TUT/welche-rechtlichen-aspekte-…; repo:apps/accounts/compliance.py:11 |
| **Rechtsform** | Legal form: Einzelunternehmen, UG (haftungsbeschränkt), GmbH | Drives which registration and tax fields apply | TUT/gmbh-ug-oder-einzelunternehmen |
| **Zulassungsfreies Handwerk** | Licence-free craft | The source's classification of the cleaning trade — but see the contradiction noted in `branche-und-gruendung.md` | TUT/wie-grunde-ich-… |
| **Handwerksrolle** | The register of craft businesses kept by the Handwerkskammer | A registration duty even for licence-free trades. **Never mentioned by the crawled sources**; this repo models it as `CompanyProfile.hwk_registered` | repo:apps/accounts/profiles.py:52-54; Ungeprüft |
| **Handwerkskammer (HWK)** | Chamber of skilled crafts | Membership and the Handwerksrolle entry | repo:apps/accounts/profiles.py:54; Ungeprüft |
| **Innung / Fachinnung / Bundesinnung** | Guild, regional specialist guild, federal guild | Membership is a company-profile flag; benefits include advice on Tarifgestaltung | TUT/bundesinnungsverband-des-gebaudereiniger-handwerks |
| **Bundesinnungsverband des Gebäudereiniger-Handwerks (BIV)** | Federal guild association of the trade | Described as "die zentrale Interessenvertretung der Gebäudereinigungsbranche in Deutschland" | TUT/bundesinnungsverband-… |
| **Berufsgenossenschaft** | Statutory accident-insurance institution | A company insurance record; relevant to the Arbeitsunfall risk | TUT/welche-rechtlichen-aspekte-… |
| **Betriebshaftpflichtversicherung** | Business liability insurance | Printed on Angebot and Rechnung; a company-profile flag in this repo | TUT/angebote-richtig-schreiben-als-gebaudereinigung; repo:apps/accounts/profiles.py:50-51 |
| **Nachweisgesetz** | Employment Documentation Act | Requires written, signed employment terms, one copy to the employee | AL/personaleinstellung |
| **Personalakte** | Personnel file | Typed document store with per-type retention and access control | AL/personalakte |
| **Aufbewahrungsfrist** | Statutory retention period | Drives deletion scheduling. Tax-relevant HR documents: **mindestens zehn Jahre** per the source | AL/personalakte |
| **Personalfragebogen / Einstellungsfragebogen** | Personnel questionnaire / pre-hire questionnaire | Standardised intake with legal limits on which questions are admissible | AL/personalfragebogen |
| **Betriebsrat** | Works council | Must consent to questionnaire content; co-determines the Dienstplan | AL/personalfragebogen; AL/dienstplan |
| **Zoll / FKS** | Customs / Finanzkontrolle Schwarzarbeit | Audits working-time records in this trade; records must be retrievable in minutes | ERF/erfolgsgeschichte-temberger |
| **Scheinselbstständigkeit** | Bogus self-employment (§7 SGB IV criteria) | Why the platform must never auto-assign work to an individual | repo:apps/marketplace/models.py:10-14 |
| **Arbeitnehmerüberlassung / AÜG** | Temporary agency work; needs a licence from the Bundesagentur für Arbeit | Blocked in code until a licence exists | repo:apps/contracts/models.py:11-13, 234-239 |
| **Betriebsübergang (§613a BGB)** | Transfer of undertaking | Endemic here: when a cleaning contract moves contractor, the site's staff often transfer by operation of law. **Ungeprüft** — a site-handover concept the model will eventually need | Ungeprüft |
| **DSGVO** | GDPR | Consent records, retention dates and private storage for verification documents already exist in this repo | repo:apps/accounts/compliance.py:22-70 |
| **§35a EStG** | Private clients deduct 20 % of the labour component of household services, capped at 4.000 €/year, against invoice and bank payment | The strongest argument against the real competitor (Schwarzarbeit); a property of the service category, not marketing copy | repo:apps/taxonomy/models.py:19-26; repo:apps/marketplace/models.py:168-174 |

---

## M. Repo term ↔ German term mapping

Use this before naming anything new. Left column is what the code says; right column is what the
German user must read.

| Repo identifier (`file:line`) | German term | Note |
|---|---|---|
| `Site` (`apps/planning/models.py:21`) | **Objekt** | `verbose_name` is Romanian ("Obiectiv"); German only in exports |
| `Zone` (`apps/planning/models.py:42`) | **Bereich** (column header "Bereich / Ort") | `apps/planning/reinigungsplan.py:19` |
| `Zone.minutes_per_visit` (`:58`) | **Dauer je Einsatz** | `reinigungsplan.py:23` |
| `Zone.visits_per_week` (`:61`) | **Reinigungsfrequenz** | Rendered as "täglich" / "N× wöchentlich" — `reinigungsplan.py:29-34` |
| `Zone.weekly_minutes` (`:79`) | **Minuten / Woche** | `reinigungsplan.py:25` |
| `Zone.category.name_de` | **Leistung** | `reinigungsplan.py:20, 47` |
| `Zone.description` (`:53`) | **Beschreibung** | `reinigungsplan.py:21` |
| `ShiftPlan` (`apps/planning/models.py:96`) | **Dienstplan** (weekly) | Romanian verbose_name "Plan săptămânal" |
| `Shift` (`apps/planning/models.py:140`) | **Einsatz / Schicht** | Romanian verbose_name "Tură" |
| `ShiftEvent` (`:188`) | **Pontaj-Journal** — append-only time-record log | No German UI surface yet |
| `Shift.checked_in_at / checked_out_at` (`:157-158`) | **Check-In / Check-Out** | |
| `Shift.actual_minutes` (`:159`) | **Ist-Zeit** | `duration_minutes` is the **Soll-Zeit** |
| `ZoneCalibration` (`:235`) | *(no established German term)* | Proposal-only correction of `minutes_per_visit` |
| `Account` + `Capability.CLIENT` | **Kunde** | There is no `Kunde` model |
| `Account` + `Capability.WORKER` | **Reinigungskraft** (natural person) | |
| `Account` + `Capability.PROVIDER` | **Dienstleister / Gebäudedienstleister** (company) | |
| `Account` + `Capability.SUPPLIER` | **Lieferant** | |
| `Account` + `Capability.EMPLOYER` | **Arbeitgeber** — publishes Stellenanzeigen | |
| `LegalStatus.MINIJOB` (`enums.py:32`) | **Minijob in Privathaushalten (§8a SGB IV)** | |
| `LegalStatus.SELBSTSTAENDIG` (`:33`) | **Selbstständig mit Gewerbeanmeldung** | |
| `LegalStatus.KLEINUNTERNEHMER` (`:34`) | **Kleinunternehmer (§19 UStG)** | |
| `JobPosting` (`apps/jobs/models.py:21`) | **Stellenanzeige** | Recruitment, **not** the customer marketplace |
| `Application` | **Bewerbung** | Public URL `/job/<slug>/bewerben/` |
| `ServiceRequest` (`apps/marketplace/models.py:48`) | **Dienstleistungsanfrage / Auftragsanfrage** | The customer-side marketplace request |
| `Offer` (`:122`) | **Angebot** | Marketplace offer — do **not** reuse the name for a Faktura quote without disambiguating |
| `Invitation` (`:177`) | **Vorschlag / Empfehlung** | Explicitly a suggestion, never an assignment |
| `ContractDraft` (`apps/contracts/models.py:151`) | **Arbeitsvertrag / Vertragsentwurf** | Templates default to `language="de"` |
| `ContractType.VOLLZEIT / TEILZEIT / MINIJOB / WERKVERTRAG` (`:30-34`) | Already German | Keep as-is |
| `WageFloor` (`:57`) | **Mindestlohn / Branchenmindestlohn** | Time-versioned rows |
| `MinijobThreshold` (`:92`) | **Geringfügigkeitsgrenze** | |
| `Device` (`apps/devices/models.py:38`) | **Gerät / Maschine** | Romanian verbose_name "Echipament" |
| `TelemetrySession` (`:94`) | **Telemetriesitzung** | Runtime, not working time |
| `ServiceCategory.name_de` (`apps/taxonomy/models.py:15`) | The public German service name | The pattern for every future German label field |
| `Locality` (`apps/geo/models.py:20`) | **Ort / Stadt** | Never free text — SEO depends on the closed list |
| `Region` (`apps/geo/models.py:4`) | **Bundesland** | |

---

## Quellen

pland.app, crawled 2026-08-29:

- https://pland.app/arbeitslexikon (index) and the entries: cafm, facility-management, din-normen,
  reinigungsintervall, reinigungsplan, unterhaltsreinigung, grundreinigung, glasreinigung,
  vier-farben-system, dienstplan, personaleinsatzplanung, personaleinstellung, personalakte,
  personalfragebogen, hr-software, reklamationsmanagement, deckungsbeitrag, abschlagsrechnung,
  teilrechnung, schlussrechnung, dauerrechnung, e-rechnung, cms-berlin, stundenzettel,
  erschwerniszuschlaege
- https://pland.app/blog/gebaudereinigung-reinigungsplan-hier-kostenlose-vorlage-herunterladen
- https://pland.app/blog/hier-kostenlose-arbeitsschein-vorlage-herunterladen
- https://pland.app/blog/reinigungsmethoden-fur-verschiedene-oberflachen-so-reinigen-profis-richtig
- https://pland.app/blog/reinigungsmethoden-fur-verschiedene-oberflachen---so-bleibt-alles-strahlend-sauber
- https://pland.app/blog/reinigungsstandards-und-din-normen---was-muss-man-als-gebaudereinigung-einhalten
- https://pland.app/blog/hygienestandards-in-der-gebaudereinigung-2025
- https://pland.app/blog/unterhaltsreinigung-die-ultimative-checkliste
- https://pland.app/blog/wie-sieht-eine-grundreinigung-in-einer-wohnung-aus
- https://pland.app/blog/arbeitssicherheit-in-der-gebaudereinigung-die-7-wichtigsten-regeln-fur-ein-sicheres-arbeitsumfeld
- https://pland.app/blog/gesundheitsrisiken-bei-reinigungskraften---gefahren-erkennen-vorbeugen
- https://pland.app/blog/gebaudereinigung-was-fur-material-brauche-ich
- https://pland.app/blog/reinigen-mit-reinwasser---wie-osmoseanlagen-die-gebaudereinigung-revolutionieren
- https://pland.app/blog/saisonale-reinigungstipps-fur-jede-jahreszeit---und-wie-digitale-tools-wie-pland-dabei-unterstutzen-konnen
- https://pland.app/funktionen/uebersicht · einsatzplanung-gebaeudereinigung ·
  zeiterfassung-gebaeudereinigung · lohnabrechnung-gebaeudereinigung ·
  angebot-und-rechnung-gebaudereinigung · abwesenheitsverwaltung · arbeitsscheine ·
  aufgabenmanagement · geraeteverwaltung · materialbestellungen · umsatzuebersicht
- https://pland.app/onboardings/einfuhrung-in-die-pland-software · mitarbeiter-in-pland-erstellen ·
  kunden-objekte-in-pland · auftrage-und-einsatzplanung-in-pland · freigabe-von-zeiterfassungen ·
  fahrzeiterfassung-mit-pland · lohnarten-und-zuschlage-in-pland ·
  einstellungen-fur-die-urlaubstageberechnung · urlaubsanspruch-von-mitarbeitern ·
  urlaubstage-im-urlaubsantrag · abwesenheiten-in-pland · ticket-system-in-pland ·
  materialbestellungen-in-pland · die-wichtigsten-faktura-einstellungen-in-pland ·
  wiederholende-rechnungen-mit-pland-erstellen · dynamische-positionen-in-rechnungen-mit-pland ·
  export-von-stammdaten
- https://pland.app/tutorials/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung ·
  welche-rechtlichen-aspekte-muss-ich-bei-der-grundung-einer-reinigungsfirma-beachten ·
  gmbh-ug-oder-einzelunternehmen · was-benotige-ich-als-reinigungsfirma-an-personal ·
  angebote-richtig-schreiben-als-gebaudereinigung ·
  so-stellen-sie-rechnungen-als-gebaudereinigung ·
  bundesinnungsverband-des-gebaudereiniger-handwerks
- https://pland.app/erfolgsgeschichten and the 31 individual case studies referenced above
- https://pland.app/hausmeisterdienste-lp

Repository (`/Users/Geronimo/Projects/Cleaning_SaaS`), read 2026-08-29:

- `apps/accounts/enums.py`, `apps/accounts/models.py`, `apps/accounts/profiles.py`,
  `apps/accounts/compliance.py`, `apps/accounts/public_urls.py`
- `apps/geo/models.py`
- `apps/taxonomy/models.py`, `apps/taxonomy/migrations/0003_seed_categories.py`
- `apps/jobs/models.py`, `apps/jobs/urls.py`
- `apps/catalog/models.py`
- `apps/contracts/models.py`, `apps/contracts/migrations/0002_seed_wage_floors.py`
- `apps/planning/models.py`, `apps/planning/services.py`, `apps/planning/attendance.py`,
  `apps/planning/calibration.py`, `apps/planning/reinigungsplan.py`
- `apps/devices/models.py`, `apps/devices/services.py`
- `apps/marketplace/models.py`, `apps/marketplace/scoring.py`
- `apps/dashboard/urls.py`, `apps/dashboard/panels.py`
- `config/settings.py`, `config/urls.py`
