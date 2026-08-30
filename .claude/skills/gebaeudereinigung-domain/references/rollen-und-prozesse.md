# Rollen und Prozesse

Covers: the five operating roles of a German cleaning company (Geschäftsführung, Innendienst,
Lohnbuchhaltung, Objektleiter, Servicekraft) — what each is responsible for, what each sees, what
each does daily — the full Objektleiter duty list, and the end-to-end operational workflows from
site survey to invoice.
**Stand: 2026-08-29.**
Material: the pland.app `/onboarding-user/`, `/onboardings/`, `/funktionen/`, Arbeitslexikon, blog
and Erfolgsgeschichten clusters (crawled 2026-08-29; every row carries its URL), plus the live
repository (`file:line`, read 2026-08-29). Rows marked **Ungeprüft** are added domain knowledge.

---

## A. The five roles

The competitor publishes exactly five role-specific onboarding tracks. They are the industry's own
role names and the ones to use in German-facing copy.

Source for the role list and descriptions: `https://pland.app/onboarding-user/geschaftsfuhrung` ·
`/innendienst` · `/lohnbuchhaltung` · `/objektleiter` · `/servicekraft`

| Rolle | Deutsche Selbstbeschreibung (as printed) | Client |
|---|---|---|
| **Geschäftsführung** | *(the page carries no description text at all — only the word "Geschäftsführung")* | Dashboard |
| **Innendienst** | "PlanD für Innendienstler — Diese Lektionen behandeln die Planung und Organisation von Mitarbeitern draußen im Einsatz über das PlanD Dashboard" | Dashboard |
| **Lohnbuchhaltung** | "Zur erfolgreiche Lohnabrechnung in Stunden — Eine genaue Übersicht in die Lohnabrechnung … Von Lohngruppen über Zuschläge bis hin zur fertigen Lohnabrechnung" | Dashboard |
| **Objektleiter** | "Als Objektleiter mit PlanD durchstarten — … Von Kunden Tickets bis hin zur digitalen Objektmappe" | Dashboard **and** mobile |
| **Servicekraft** | "Mit der PlanD App durchstarten — … alles was Sie brauchen um mit der PlanD App zu arbeiten. Vom Login bis zur Zeiterfassung" | Mobile only |

### A1. Important: five roles, four access levels

**Fakt.** The competitor markets five roles but its employee record offers exactly **four**
Zugriffsrechte: **Servicekraft · Objektleiter · Innendienst · Administrator**
(https://pland.app/onboardings/mitarbeiter-in-pland-erstellen). Geschäftsführung and
Lohnbuchhaltung are **training audiences, not access levels** — how they map onto the four is never
stated on the pages.

**This is a design lesson, not a bug to copy.** A role is three different things at once:

| Axis | Example | Where it belongs |
|---|---|---|
| Who someone *is* in the org chart | Lohnbuchhalterin | an attribute of the person |
| What someone *may see and do* | can approve time records | authorisation |
| What someone is *responsible for* on a given object | Objektleiter of Objekt #17 | a per-object assignment |

Conflating them is exactly what this repo already refuses to do: authorisation comes from
`AccountCapability` rows plus object ownership, never from a `role` column
(`apps/accounts/enums.py:11-15`; `apps/accounts/permissions.py:1-7`). Keep that. A future
"Objektleiter" is an **assignment on the Objekt**, not a global permission — the competitor's own
rule is that only Administrator/Objektleiter users may be *selected* as an object's Objektleiter
(https://pland.app/onboardings/kunden-objekte-in-pland).

### A2. Repo mapping (Fakt)

| Operating role | Nearest thing in this repo today | Gap |
|---|---|---|
| Geschäftsführung | `Membership.role = OWNER` (`apps/accounts/models.py:209-211`); `MembershipRole.OWNER/ADMIN` gate `can_manage` (`:224-226`) | No company-wide reporting surface |
| Innendienst | `Membership.role = ADMIN` or `MEMBER` on an employer account; the dashboard planning views | No dedicated permission tier |
| Lohnbuchhaltung | **nothing** | No payroll module, no approval role, no export |
| Objektleiter | **nothing** — `Site` has no `objektleiter` FK (`apps/planning/models.py:21-31`) | The single most-cited missing role field |
| Servicekraft | `Account` with `Capability.WORKER` (`apps/accounts/enums.py:17`); sees `/dashboard/turele-mele/` | No mobile client; dashboard-only |

---

## B. What each role does

### B1. Geschäftsführung — managing director / owner

| Aspect | Detail | Quelle |
|---|---|---|
| **Responsible for** | Steering the company: process planning, financial position, capacity | https://pland.app/tutorials/warum-sollte-man-eine-gebaudereiniger-software-nutzen |
| **Sees** | Objekte, Mitarbeiter, Materialien, **Verbräuche**, Umsatz, Profitabilität | https://pland.app/nutzer; https://pland.app/software-gebaeudereinigung |
| **Does daily** | Reads the Umsatz-Übersicht and open items; decides on Angebote above a threshold; approves growth and hiring | https://pland.app/funktionen/umsatzuebersicht |
| **Named capabilities** | **Controlling-Modul** for a quick view of the financial position; simplify/automate Buchhaltung; Mitarbeiterverwaltung; Arbeitszeiterfassung; optimise Personaleinsatzplanung and avoid **Leerstände**; fast data access for decisions | https://pland.app/tutorials/warum-sollte-man-eine-gebaudereiniger-software-nutzen |
| **Also cares about** | The Reinigungsplan as a transparency and budgeting instrument for the Reinigungsaufwand | https://pland.app/arbeitslexikon/reinigungsplan |
| **Training track** | Einführung · Abwesenheiten · Ticket-System · Faktura Einstellungen · Wiederholende Rechnungen · Dynamische Positionen · Export von Stammdaten | per-lesson "Für wen" lists |

### B2. Innendienst — back office

| Aspect | Detail | Quelle |
|---|---|---|
| **Responsible for** | Planning and organising the field staff; master data; invoicing | https://pland.app/onboarding-user/innendienst |
| **Sees** | The Dashboard in full: Mitarbeiter, Objekte/Kunden, Einsatzplaner, Dienstplan, Zeitenfreigaben, Abwesenheiten, Tickets, Materialwesen, Angebote, Aufträge, Rechnungen, Einstellungen | https://pland.app/onboardings/einfuhrung-in-die-pland-software |
| **Does daily** | Creates and moves Einsätze; fills open shifts; processes the Zeitenfreigabe queue; handles absences and substitutions; raises material orders; creates the invoice right after the Einsatz ends | https://pland.app/nutzer; https://pland.app/onboardings/freigabe-von-zeiterfassungen |
| **Named capabilities** | Manage Aufträge and Kunden; Kundensupport; digital management of **Arbeitsscheine** and **Materialbestellungen**; react to field notes and questions; Dokumentenverwaltung; internal communication | https://pland.app/tutorials/warum-sollte-man-eine-gebaudereiniger-software-nutzen |
| **Training track** | The longest — 17 of the 18 lessons | https://pland.app/onboarding-user/innendienst |
| **Repo today** | Owns `/dashboard/anunturi/`, `/candidaturi/`, `/contracte/`, `/obiective/`, `/planificare/`, `/cereri/` | `apps/dashboard/urls.py:16-48` |

### B3. Lohnbuchhaltung — payroll accounting

| Aspect | Detail | Quelle |
|---|---|---|
| **Responsible for** | Turning released hours into a correct payroll run | https://pland.app/onboarding-user/lohnbuchhaltung |
| **Sees** | Zeitenfreigaben, Fahrzeiten, Lohnarten and Zuschläge, per-employee **Lohnzeit** (Plan-Zeit / erfasste Zeit / Lohn-Zeit), Faktura settings | https://pland.app/onboardings/freigabe-von-zeiterfassungen; /lohnarten-und-zuschlage-in-pland |
| **Does monthly** | Re-checks the shifts the Disposition released (**Vier-Augen-Prinzip**), then triggers the export | https://pland.app/erfolgsgeschichten/wie-glanzhelden-… |
| **Named capabilities** | Define Lohnarten and Zuschläge per Lohngruppe; set Entgeltfortzahlung per absence; export DATEV / CSV / custom / API, or hand the run to a payroll service | https://pland.app/funktionen/lohnabrechnung-gebaeudereinigung |
| **Hard rule the role enforces** | When night, holiday and Sunday surcharges coincide, **only the highest applies** ("siehe Lohntarifvertrag") | https://pland.app/onboardings/lohnarten-und-zuschlage-in-pland |
| **Repo today** | Does not exist. `ContractDraft.compliance_issues()` is the only wage check (`apps/contracts/models.py:193-249`). Route all payroll work to **gr-tarif-und-lohn**. | |

### B4. Objektleiter / Objektleitung — site manager

The pivotal role in this industry: the only person who sees both the customer and the worker.

**Duty list — every duty the sources attribute to the Objektleiter, in full:**

| # | Duty | Quelle |
|---|---|---|
| 1 | Conduct the **Objektbesichtigung** at the start of every new maintenance-cleaning contract: size of rooms, **number of toilets**, and discuss with the customer what is cleaned and how; collect and note everything needed for the plan | https://pland.app/arbeitslexikon/unterhaltsreinigung |
| 2 | Derive and own the **Reinigungsplan** — which days, how regularly, which services in which rooms, and that services are documented after each clean | https://pland.app/arbeitslexikon/unterhaltsreinigung |
| 3 | Use the plan as assurance that nothing is forgotten, and as the **Nachweis** of work performed "insbesondere im Falle von Beschwerden oder Streitigkeiten" | https://pland.app/arbeitslexikon/reinigungsplan |
| 4 | Run the **Qualitätskontrolle** after the clean: check that all tasks were done to the customer's satisfaction | https://pland.app/arbeitslexikon/unterhaltsreinigung; https://pland.app/blog/unterhaltsreinigung-die-ultimative-checkliste |
| 5 | Review the cleaner's documentation (photos, comments, stars) from the phone and **raise a Ticket** where something is missing | https://pland.app/arbeitslexikon/unterhaltsreinigung |
| 6 | Receive the completion notification for every Einsatz; ensure the **Leistungsnachweis** reaches the customer | https://pland.app/arbeitslexikon/reinigungsplan |
| 7 | Own **Reklamationen** for all their objects; see customer tickets immediately, assign them, and close them with a photo of the fixed issue plus a Bemerkung | https://pland.app/funktionen/uebersicht; https://pland.app/onboardings/ticket-system-in-pland |
| 8 | Hold the **digitale Objektmappe** — all photos, documents and tickets per object — on the phone | https://pland.app/funktionen/uebersicht |
| 9 | Keep the **Leistungsverzeichnis** per object current and available to the crew in the app | https://pland.app/funktionen/uebersicht; https://pland.app/erfolgsgeschichten/erfolgsgeschichte-temberger |
| 10 | Create and manage **Einsatzpläne**; monitor performance and cleaning quality **in real time** and correct where needed; track **Arbeitsfortschritt** and **Zeitaufwand**; ensure work orders finish on time | https://pland.app/tutorials/warum-sollte-man-eine-gebaudereiniger-software-nutzen |
| 11 | Place **Materialbestellungen** and approve or correct what the crew ordered | https://pland.app/tutorials/warum-sollte-man-eine-gebaudereiniger-software-nutzen; https://pland.app/erfolgsgeschichten/wie-der-navus-… |
| 12 | **Approve absences** and see the Auftragslage for the period before deciding | https://pland.app/funktionen/abwesenheitsverwaltung; https://pland.app/erfolgsgeschichten/erfolgsgeschichte-temberger |
| 13 | Take part in the **Zeitenfreigabe** — the Objektleiter is one of the three named audiences for that lesson | https://pland.app/onboardings/freigabe-von-zeiterfassungen |
| 14 | Generate **Berichte** for management or for the customer | https://pland.app/tutorials/warum-sollte-man-eine-gebaudereiniger-software-nutzen |
| 15 | Ensure **Einhaltung von Vertragsbedingungen** at the objects they supervise | https://pland.app/tutorials/was-benotige-ich-als-reinigungsfirma-an-personal |
| 16 | Communicate with the customer as the named contact for their objects | https://pland.app/tutorials/was-benotige-ich-als-reinigungsfirma-an-personal |

**Structural facts:** an Objekt has exactly one assigned Objektleiter, selectable only from users
with Administrator or Objektleiter rights (https://pland.app/onboardings/kunden-objekte-in-pland).
Ticket assignment defaults to employees who have **already worked at that object**, with an
explicit "load all users" escape hatch (https://pland.app/onboardings/ticket-system-in-pland).

**Repo today:** no Objektleiter exists. `Site` has `account`, `name`, `locality`, `street`,
`postal_code`, `is_active` and nothing else (`apps/planning/models.py:21-31`). Adding
`Site.objektleiter` is the highest-leverage single field in the operations layer — it is the
addressee of quality checks, tickets and absence approvals.

### B5. Servicekraft / Reinigungskraft — the operative

| Aspect | Detail | Quelle |
|---|---|---|
| **Responsible for** | Performing the cleaning "gemäß den vereinbarten Standards und Anforderungen" | https://pland.app/tutorials/was-benotige-ich-als-reinigungsfirma-an-personal |
| **Sees** | Their own Dienstplan with **Name, Adresse, Uhrzeit** per Einsatz — upcoming *and past*; released hours; remaining holiday | https://pland.app/funktionen/einsatzplanung-gebaeudereinigung; https://pland.app/nutzer |
| **Does per shift** | Clock in on site → work the checklist → document with photos and comments → get the Arbeitsschein signed → clock out; record Fahrzeit to the next Einsatz | https://pland.app/funktionen/zeiterfassung-gebaeudereinigung; /arbeitsscheine |
| **Also does** | Orders material from the object; files Urlaubsantrag and Krankmeldung; opens and completes Tickets; chats | https://pland.app/funktionen/materialbestellungen; /abwesenheitsverwaltung |
| **Non-functional requirements this role imposes** | Offline capture (cellars, stairwells have no signal); very low training burden ("Wer WhatsApp kann, kann auch PlanD"); the app language follows the user — the competitor claims 16+ (badges) or 25+ (Übersicht) languages, and one 400-person customer reports only ~10 % of staff speak German | https://pland.app/erfolgsgeschichten/wie-pland-zwei-ex-soldaten-…; /erfolgsgeschichte-temberger; /how-lcm-now-has-all-relevant-information-in-one-place |
| **Repo today** | `/dashboard/turele-mele/` (`apps/dashboard/urls.py:40`) is the only worker surface; no mobile client, no offline mode, no i18n catalogue | |

### B6. Two supporting roles the sources also name

| Rolle | Duties as printed | Quelle |
|---|---|---|
| **Vorarbeiter / Teamleiter** | Organise Arbeitsabläufe; supervise Reinigungsqualität; coordinate the cleaning staff; train new employees; act as customer contact | https://pland.app/tutorials/was-benotige-ich-als-reinigungsfirma-an-personal |
| **Spezialisierte Fachkräfte** | Specific services such as Teppich- or Fensterreinigung | same |

---

## C. Who sees what — a permission sketch (Vorschlag)

Not implemented. Derived from §B, expressed in this repo's existing idiom (capability rows plus
object ownership, never a `role` column).

| Surface | Servicekraft | Objektleiter | Innendienst | Lohnbuchhaltung | Geschäftsführung |
|---|---|---|---|---|---|
| Own Dienstplan / own shifts | ✅ | ✅ | ✅ all | — | ✅ all |
| Other workers' shifts | — | ✅ own objects | ✅ all | — | ✅ all |
| Check-in / check-out | ✅ own | ✅ own | — | — | — |
| Zeitenfreigabe queue | — | ✅ own objects | ✅ all | ✅ all | ✅ all |
| Lohnarten, Zuschläge, export | — | — | — | ✅ | ✅ |
| Objektmappe, Leistungsverzeichnis | ✅ read, own objects | ✅ own objects | ✅ all | — | ✅ all |
| Zugangscode / Alarmcode | ✅ read, own objects, audited | ✅ own objects | ✅ all | — | ✅ all |
| Tickets / Reklamationen | ✅ assigned | ✅ own objects | ✅ all | — | ✅ all |
| Absence approval | request only | ✅ own team | ✅ all | — | ✅ all |
| Material order | request only | ✅ approve | ✅ approve | — | ✅ |
| Angebot / Rechnung | — | — | ✅ | ✅ read | ✅ |
| Umsatz, Deckungsbeitrag | — | — | ✅ | — | ✅ |
| Personalakte | own only | — | ✅ | ✅ | ✅ |

Two rules that come straight from the sources and must survive any implementation:

1. **Access codes are secrets.** The Zugangscode lives on the object's "Sonstiges" tab in the
   competitor's product (https://pland.app/onboardings/kunden-objekte-in-pland). Encrypt at rest and
   audit reads — a cleaning company holding the door codes of hundreds of buildings is a
   high-value target.
2. **Whatever the assistant layer is, it inherits the permission model.** The competitor states it
   explicitly for its AI: "Für jeden Nutzer sieht Paula nur das, was dieser Nutzer auch sehen darf",
   and it "kann Vorgänge archivieren, aber aus Sicherheitsgründen aktuell **nicht löschen**"
   (https://pland.app/ki-assistenz). Both are good defaults.

---

## D. End-to-end workflows

### W1 — Set up a recurring Unterhaltsreinigung contract

Source: https://pland.app/blog/unterhaltsreinigung-die-ultimative-checkliste ·
https://pland.app/arbeitslexikon/unterhaltsreinigung

1. **Objektbegehung.** The Objektleiter inspects the object with the customer.
2. **Capture the drivers:** Raumgröße, **Bodenbelag**, **Anzahl Toiletten**, Nutzungsintensität,
   Hygieneanforderungen.
3. **Derive the Reinigungsplan** — per area: Leistung, Beschreibung, Frequenz.
4. **Fix the Reinigungsintervall** from the six factors (see `reinigungsarten-normen-qualitaet.md` §B).
5. **Write the Angebot:** Reinigungsleistungen + benötigte **Materialien** + **Arbeitsstunden**.
6. **Stock the on-site Materialschrank** — "Gerade bei sensiblen Oberflächen ist es wichtig, dass
   dem Reinigungspersonal stets die richtigen Materialien zur Verfügung stehen."
7. **Attach the Einsatz data:** Notfallpläne, Alarmanlagen-Codes, other documents; recurring special
   instructions go in a **Beschreibungsfeld** (worked example: "dass jeden Freitag der Müll geleert
   werden soll").
8. **Publish the Einsatzplan** to the assigned cleaners.
9. **Execute** (W2).
10. **Objektleitung prüft das Ergebnis.**
11. **Document the Leistungsnachweis** (photos + comments) and send it to the customer.

The same page adds two more business steps: install a **QR-Code am Objekt** as a two-way channel —
the cleaner scans it to document why a job ran long (worked example: "**15 Minuten länger**" every
time), the customer scans it to raise a complaint that the Objektleitung sees immediately — and
**digitise the Einsatzplanung** whether the work is recurring or one-off.

### W2 — Execute one Unterhaltsreinigung visit (the 5-step pass)

Source: https://pland.app/blog/unterhaltsreinigung-die-ultimative-checkliste

1. **Abfallentsorgung** — empty bins, replace liners.
2. **Staubsaugen** — vacuum, remove dust from floors.
3. **Oberflächenreinigung** — Tische, Schreibtische, Regale, Arbeitsflächen wiped damp, then
   **trocken gewischt**.
4. **Reinigung von Sanitäranlagen** — Toiletten, Waschbecken, Spiegel with suitable agents.
5. **Bodenreinigung** — floors mopped **last**.

This is one ordered pass across the object, not a per-room checklist. A per-room-type matrix is
*nicht belegt* — see `reinigungsarten-normen-qualitaet.md` §K5.

### W3 — Grundreinigung of a dwelling (8 areas, in the printed order)

Source: https://pland.app/blog/wie-sieht-eine-grundreinigung-in-einer-wohnung-aus

| # | Bereich | Tasks as printed |
|---|---|---|
| 1 | **Böden intensiv reinigen** | Hartböden (Fliesen, Parkett, Laminat) thoroughly; remove ingrained dirt and stains; **Versiegeln von Oberflächen bei Bedarf**. Teppichböden machine deep-cleaned. **Ecken, Fugen und Sockelleisten** treated especially thoroughly. |
| 2 | **Fenster und Fensterrahmen** | Inside and outside, incl. Rahmen, Fensterbänke, **Dichtungen**; panes **streifenfrei poliert**; Jalousien or Rollläden cleaned too. |
| 3 | **Heizkörper und Lüftungsschlitze** | Radiators inside and out (dust impairs heat output); Lüftungsschlitze und -gitter for air circulation. |
| 4 | **Küche intensiv reinigen** | All surfaces, **Arbeitsplatten und Schränke** degreased; **Herd, Backofen, Kühlschrank, Mikrowelle innen und außen** incl. **Dichtungen und Lüftungsschlitze**; **Fliesen und Wandbereiche hinter Herd und Spüle**. |
| 5 | **Badezimmer** | **Kalkablagerungen** on Armaturen, Fliesen, Duschköpfe; Duschen und Badewannen — Seifenreste and **Schimmel**; Spiegel, Waschbecken und WC hygienically cleaned and **desinfiziert**. |
| 6 | **Türen und Türrahmen** | Dirt, **Fingerabdrücke**, dust; **Türgriffe und Beschläge** cleaned and **desinfiziert**. |
| 7 | **Wände und Decken** | Light soiling on walls; **Spinnweben** in corners and on the ceiling; **Lampen und Leuchten** to improve light output. |
| 8 | **Möbelpflege** | Polstermöbel deep-cleaned; Holzmöbel treated with care products; **Glasflächen** of tables, cabinets, shelves polished streak-free. |

Trigger events named: "einmal jährlich oder bei speziellen Anlässen wie einem **Umzug** oder einer
**Renovierung**".

### W4 — Digital Arbeitsschein lifecycle

Source: https://pland.app/blog/hier-kostenlose-arbeitsschein-vorlage-herunterladen

Auftrag exists → create the Arbeitsschein (Leistungen and per-line Stundenanzahl auto-filled) →
cleaner opens it in the app on site → performs the work, adds photos, timestamps, comments →
**customer signs on the smartphone on site** → the docket is filed behind the Einsatz →
one click converts it into a Rechnung.

**Freeze the record at signature.** Everything after that is a new version, never an edit.

### W5 — Order to cash

Source: https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung ·
https://pland.app/erfolgsgeschichten/wie-ow-harder-dank-pland-50-arbeitszeit-in-der-verwaltung-spart

1. Store **Produkte und Dienstleistungen** with prices.
2. Create the **Angebot**; prices are calculated from the stored items.
3. Send it by e-mail **or post**.
4. Customer confirms **with one click** → the Angebot becomes an **Auftrag**;
   "Angenommene Angebote werden automatisch abgerechnet".
5. Send the **Auftragsbestätigung**.
6. Plan the **Einsätze** (recurring or one-off).
7. Perform the Einsatz; get the **Arbeitsschein** signed on site.
8. **Einsatz abgeschlossen → the Rechnung is created automatically**; the signed docket goes
   "in Echtzeit in die Fakturierung".
9. Send the Rechnung: E-Mail / PDF / print / Kundenportal / post; optional QR code for instant payment.
10. Payment arrives → the invoice is auto-matched by **Buchungsnummer, Kunde und Betrag**.
11. Overdue → automatic **Mahnung** at the configured Mahnstufen.

Detail belongs to **gr-auftrag-und-faktura**. None of it exists in this repo.

### W6 — Dienstplan → Zeiterfassung → Lohndaten

Sources: https://pland.app/funktionen/einsatzplanung-gebaeudereinigung ·
/zeiterfassung-gebaeudereinigung · /lohnabrechnung-gebaeudereinigung

1. Stammdaten in place: Mitarbeiter, Kunden, Objekte, Aufträge.
2. Create Einsätze and assign the right person — filter by **Qualifikationen und Kapazitäten**;
   the planning assistant answers "Wer hat noch Zeit? Wer ist in der Nähe?".
3. The system warns on **Verstöße gegen gesetzliche oder tarifliche Vorgaben**. *Which rules are
   checked is never stated on the source pages.* This repo checks four explicitly:
   contracted-hours ceiling, §3 ArbZG max 8 h/day, §5 ArbZG 11 h rest, §9 ArbZG Sunday free
   (`apps/planning/services.py:9-31`).
4. The worker is notified in real time and sees **Name, Adresse, Uhrzeit**.
5. On site: start Zeiterfassung, apply Pausen- und Fahrzeiten (auto or manual), end Zeiterfassung.
6. Optional: upload the Leistungsnachweis — Fotos, Bemerkungen, Unterschrift.
7. **Soll/Ist-Vergleich** against the Dienstplan plus **Standortkontrolle** against the object
   radius → discrepancies flagged.
8. Add forgotten punches (**nachtragen**) — they stay distinguishable from live records.
9. **Zeiten freigeben** → the digital Stundenzettel.
10. Zuschläge derived from the **Dienstplan** (not from the raw clock times) per Rahmentarifvertrag;
    Lohnarten applied per Anstellungsverhältnis.
11. Export to the Lohnbüro, or hand the run to a payroll service.

Steps 5–9 belong to **gr-zeiterfassung**; steps 2–4 to **gr-einsatzplanung**; step 10 onwards to
**gr-tarif-und-lohn**.

### W7 — Krankmeldung → Vertretung

Source: https://pland.app/funktionen/einsatzplanung-gebaeudereinigung ·
https://pland.app/onboardings/abwesenheiten-in-pland

1. The worker files Krankheit or Urlaub **in the app** and attaches the Krankheitsschein.
2. It appears in the shared **Abwesenheitskalender** (Objektleitung, Innendienst, Geschäftsführung).
3. The approver sees the Auftragslage for that period before deciding — "Können wir uns das
   leisten?" — then approves in one click.
4. The **Betroffene Einsätze** panel lists every affected assignment. Each is either reassigned
   immediately (the substitute gets a push notification) or turned into an **Offene Schicht**.
5. The system suggests substitutes **based on Kapazitäten und Qualifikationen**, and filters by
   whether the person has already worked at that object.
6. **The customer is notified by e-mail about the absence and the substitution** — configurable per
   tenant.
7. In the planner the absent worker shows an **orange bar**, their Einsätze turn **grey**, and a
   reassigned Einsatz appears on the substitute's row marked as a **Vertretungseinsatz**.

Note step 6: customer notification is part of the substitution flow, not an afterthought — so a
`Vertretung` record needs a `kunde_informiert_am` timestamp.

### W8 — Reklamation / Ticket

Sources: https://pland.app/arbeitslexikon/reklamationsmanagement ·
https://pland.app/onboardings/ticket-system-in-pland

**The 7 ordered tasks of Reklamationsmanagement:**

1. **Annahme und Erfassung** — complaints systematically received and documented.
2. **Analyse** — identify the exact cause.
3. **Lösungsfindung** — develop a suitable solution.
4. **Kommunikation mit dem Kunden** — keep the customer informed of the processing status and the
   solution.
5. **Verbesserungsmaßnahmen** — feed the insight back into processes.
6. **Nachverfolgung und Qualitätskontrolle** — verify the solution actually worked.
7. **Reporting und Analyse der Reklamationsdaten** — detect trends, act preventively.

**Sector-specific priorities named:** schnelle Reaktionszeit (cleanliness is time-critical) · klare
Kommunikation of cleaning standards · **kurze Kommunikationswege** to reach the responsible cleaner
fast · Flexibilität · Qualitätskontrolle · Schulung des Personals · Dokumentation.

**Operational lifecycle:** three creation channels — Dashboard, the worker app, and the
**Kunden-Dashboard** reached per object via a downloadable **QR-Code** or a shared link. The
customer states the issue, gives an e-mail address (all updates are auto-sent there) and may attach
photos. Assignment defaults to employees who have worked at that object. The assignee completes it
by uploading a **photo of the fixed Reklamation** plus a **Bemerkung**; the customer is notified
with photo and remark. A customer ticket is also **taken into account at the next clean**
(https://pland.app/software-gebaeudereinigung).

**Two model requirements that follow:** every complaint carries a **Bearbeitungsfrist** that is
monitored automatically, and **every step is auto-documented** — no silent status changes.

### W9 — Material from the object

Source: https://pland.app/onboardings/materialbestellungen-in-pland ·
https://pland.app/funktionen/materialbestellungen

1. The cleaner taps the needed items in the app, from that object's **Materialschrank**.
2. The order routes automatically to the office; who ordered what, and remaining stock, are visible.
3. The Leitung approves or corrects the quantity.
4. A **Lieferschein** is generated — for the **customer** and for the **supplier** — and can be sent
   for signature.
5. The order closes and moves to the Erledigt tab.
6. It converts into an invoice line with **customer-specific prices**.
7. Consumption per object per month feeds the Verbrauchskontrolle.

Structural rules: articles are attached per object with a **monthly quantity budget**; **budget 0 =
unlimited**; if nothing is attached, the cleaner may order **any** created article.

### W10 — Hiring / Personaleinstellung

Source: https://pland.app/arbeitslexikon/personaleinstellung

1. The employee hands over the usual employment documents **against confirmation of receipt**.
2. These explicitly include a **Bescheinigung des letzten Arbeitgebers über den im laufenden
   Kalenderjahr bereits genommenen Urlaub**.
3. Working conditions are put in writing in an **Arbeitsvertrag nach dem Nachweisgesetz** and signed
   by both parties.
4. **One copy is handed to the employee.**
5. "Die Vertrags- und **Arbeitssprache ist Deutsch**."

Point 5 is a genuine constraint on a product whose workforce is largely non-German-speaking: the
*contract* is German, the *app* is not. This repo already defaults `ContractTemplate.language` to
`"de"` (`apps/contracts/models.py:125`).

### W11 — Reinigungsintervall governance

Source: https://pland.app/arbeitslexikon/reinigungsintervall

1. Determine the interval from the six factors.
2. Record it in a **Reinigungsplan**.
3. Track execution via **Checklisten**.
4. Manage it through a digital system.
5. **Review and adjust regularly** for seasonal variation, changed building use, new hygiene
   requirements.

Step 5 is why an interval needs a revision history, not just a current value.

---

## E. Change management — what the case studies say actually works

These are customer statements on a vendor's marketing site. Treat them as directional, not as
evidence. Sources: the 31 pages under `https://pland.app/erfolgsgeschichten/`.

| Lever | Reported by |
|---|---|
| A written **Dienstanweisung** stating where working time begins and which button to press | Landsberg |
| Visualising the app to staff before rollout | Emons |
| Restricting each role's visible functions so a cleaner only sees a cleaner's screens | Kille |
| Banning the previous channel outright — WhatsApp forbidden **per Betriebsanweisung** | Volk & Volk |
| Reported rollout durations | "über Nacht" (ProNordic) · one weekend (KI-Gebäudereinigung) · two appointments (navus) · ~4 weeks to full use (OW Harder) · ~1 month for the complete planning tool (Stier) · ~3 months to onboard nearly all employees (Reinigungsklinik) |

Two named frictions are the only negative signals across 31 curated pages: "Bremser bei den älteren
Mitarbeitern" (Landsberg) and "Der Preis war anfangs abschreckend" (KI-Gebäudereinigung). That is
itself a measure of how heavily edited the set is.

**Non-functional requirements the role analysis makes mandatory** (from the same corpus):
cloud, no VPN · offline-first mobile capture · multilingual, per-user language, with in-chat
translation · very low training burden · role-scoped UI · absolute reliability of the hours data
("Gerade bei der Stundenerfassung dürfen keine Fehler auftreten" — a competitor lost that account
over exactly this) · fast human support · data-migration support.

---

## F. Open questions

1. **How are Geschäftsführung and Lohnbuchhaltung represented as access levels?** The competitor's
   pages never say (presumably Administrator and Innendienst). Decide it deliberately here.
2. **Is the Vier-Augen-Prinzip a hard workflow gate or a convention?** One case study treats it as a
   real step; the product pages never describe it as a module. *Nicht belegt.*
3. **Who may approve an absence — the Objektleiter, the Innendienst, or both?** The sources show
   both paths without a rule.
4. **What triggers the automatic complaint notification to the customer** — a status change only, or
   a configurable SLA? *Nicht belegt.*
5. **Does the location feature record a track or only check-in/check-out points?** One case study
   says "GPS-Tracking", another "GPS-basierte Check-in-Funktion" — materially different for privacy
   law. Decide this in **gr-zeiterfassung** before writing any geo code.
6. **How do Kostenstellen work — per Objekt, per Kunde, or per Auftrag?** A case study blocks a full
   invoicing rollout on it, and nothing in the corpus defines it.

---

## Quellen

**pland.app, crawled 2026-08-29**

- https://pland.app/onboarding-user/geschaftsfuhrung · /innendienst · /lohnbuchhaltung ·
  /objektleiter · /servicekraft
- https://pland.app/onboardings/einfuhrung-in-die-pland-software ·
  /mitarbeiter-in-pland-erstellen · /kunden-objekte-in-pland ·
  /auftrage-und-einsatzplanung-in-pland · /freigabe-von-zeiterfassungen ·
  /lohnarten-und-zuschlage-in-pland · /abwesenheiten-in-pland · /ticket-system-in-pland ·
  /materialbestellungen-in-pland
- https://pland.app/funktionen/einsatzplanung-gebaeudereinigung ·
  /zeiterfassung-gebaeudereinigung · /lohnabrechnung-gebaeudereinigung ·
  /angebot-und-rechnung-gebaudereinigung · /abwesenheitsverwaltung · /arbeitsscheine ·
  /materialbestellungen · /umsatzuebersicht · /uebersicht
- https://pland.app/arbeitslexikon/unterhaltsreinigung · /reinigungsplan · /reinigungsintervall ·
  /reklamationsmanagement · /personaleinstellung
- https://pland.app/blog/unterhaltsreinigung-die-ultimative-checkliste ·
  /wie-sieht-eine-grundreinigung-in-einer-wohnung-aus ·
  /hier-kostenlose-arbeitsschein-vorlage-herunterladen
- https://pland.app/tutorials/warum-sollte-man-eine-gebaudereiniger-software-nutzen ·
  /was-benotige-ich-als-reinigungsfirma-an-personal
- https://pland.app/nutzer · /software-gebaeudereinigung · /ki-assistenz
- https://pland.app/erfolgsgeschichten and the individual case studies named above

**Repository, read 2026-08-29**

- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/enums.py` (Capability, MembershipRole)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py` (Membership, lines 202-226)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/permissions.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py` (Site, lines 21-31)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/services.py` (lines 9-31)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py` (line 125, lines 193-249)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/dashboard/urls.py`
