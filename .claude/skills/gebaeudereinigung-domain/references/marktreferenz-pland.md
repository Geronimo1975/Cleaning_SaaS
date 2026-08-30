# Marktreferenz — pland.app feature matrix vs. this repo

Covers: every page under `pland.app/funktionen/`, every further capability listed on its Übersicht
page, what each does, which role uses it, and a Have / Partial / Missing verdict against
`/Users/Geronimo/Projects/Cleaning_SaaS` — followed by a build order derived from what the case
studies say customers actually adopted.
**Stand: 2026-08-29.**
Material: pland.app crawled 2026-08-29 (22 product pages + 31 case studies + 1 index); the repo read
the same day.

**Source-status warning.** pland.app is a competitor's own marketing site. Feature descriptions are
what the vendor claims its product does; the case-study numbers are **vendor-published
testimonials** — the vendor chose the customers, ran the interviews, wrote the copy and picked the
figures. There is no independent audit and no stated methodology behind any percentage. Use this
file as a map of the feature surface a rival is measured against, never as market evidence.

Verdict column:

| Verdict | Meaning |
|---|---|
| **Have** | An equivalent exists and works in this repo today |
| **Partial** | Some of the mechanism exists; named gaps below |
| **Missing** | Nothing in the repo addresses it |

---

## A. Counting the modules

**Fakt.** The crawl contains **11 files under `/funktionen/`**, but one of them (`uebersicht`) is a
catch-all index, not a module. So the product has **10 dedicated module pages** plus an Übersicht
page listing ~33 further capabilities. Two page tiers behave differently:

- **Tier A** (Einsatzplanung, Zeiterfassung, Lohnabrechnung, Angebot & Rechnung) — long-form,
  3-step narrative, FAQ, testimonial. Almost all extractable mechanics live here. Badge: "500+".
- **Tier B** (Abwesenheitsverwaltung, Arbeitsscheine, Aufgabenmanagement, Geräteverwaltung,
  Materialbestellungen, Umsatz-Übersicht) — short, 3 bullets + one paragraph, no FAQ. Badge: "800+".

The customer count contradicts itself four ways across the site (800+ / 500+ / "Über 500" /
"Über 200"). Treat none of them as a real installed base.

---

## B. The 10 module pages

Source URL for each row is `https://pland.app/funktionen/<slug>` as named.

### B1. Einsatzplanung (`einsatzplanung-gebaeudereinigung`) — *deployment planning*

| Sub-capability (German) | What it does | Rolle | Verdict |
|---|---|---|---|
| Einsätze für Mitarbeiter und Teams planen | Two order shapes: wiederkehrende Unterhaltsreinigung and einmaliger Sonderauftrag | Innendienst | **Partial** — `ShiftPlan` + `Shift` exist (`apps/planning/models.py:96,140`); weekly plans only, no recurrence series, no team shift |
| Fähigkeiten und Verfügbarkeiten | "Filtern Sie Mitarbeiter nach **Qualifikationen und Kapazitäten**" | Innendienst | **Partial** — capacity comes from signed contracts (`apps/planning/services.py:51-56`); **no qualification model at all** |
| Gesetzliche und tarifliche Vorgaben | Automatic warning on violations at plan time; *which rules is never stated* | Innendienst | **Have, and better specified** — four hard constraints, each citing its paragraph (`apps/planning/services.py:9-31`): contracted-hours ceiling, §3 ArbZG 8 h/day, §5 ArbZG 11 h rest, §9 ArbZG Sunday |
| Mobiler Dienstplan | Worker sees upcoming and past Einsätze with **Name, Adresse, Uhrzeit** | Servicekraft | **Partial** — `/dashboard/turele-mele/` (`apps/dashboard/urls.py:40`), web only |
| Push-Benachrichtigungen in Echtzeit | On new assignment or change | Servicekraft | **Partial** — publication sends one e-mail per worker (`apps/planning/attendance.py:48-50`), no push |
| Abwesenheitskalender | Past and upcoming absences, leave requests planned in the same view | Innendienst, Objektleiter | **Missing** |
| Vertretungsplanung | Substitute proposed from **Kapazitäten und Qualifikationen**; the **customer is notified by e-mail** | Innendienst | **Missing** |
| Planungsassistent | "Wer hat noch Zeit? Wer ist in der Nähe?" | Innendienst | **Missing** — locality matching exists as a hard constraint, not a suggestion |

### B2. Zeiterfassung (`zeiterfassung-gebaeudereinigung`) — *time tracking*

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Stempeln im Objekt über die App | Clock in/out, "in Echtzeit für alle einsehbar" | Servicekraft | **Partial** — `Shift.checked_in_at/checked_out_at` (`apps/planning/models.py:157-158`), web only |
| Erfasste Größen: Arbeitsstunden, **Pausen**, **Fahrzeiten** | Pausen/Fahrzeiten can be pre-stored on Einsätze *and* Daueraufträge and applied automatically or manually | Servicekraft, Lohnbuchhaltung | **Missing** for Pausen and Fahrzeiten |
| Nachtragen | "Stempel vergessen? Einfach nachtragen!" — retroactive entry is first-class | Servicekraft | **Partial** — `ShiftEvent.Kind.CORRECTED` exists (`apps/planning/models.py:201`) |
| GPS-Standorterfassung / Standortkontrolle | Verifies presence at the Einsatzort; alerts outside the configured object radius | Innendienst | **Missing** — `Site` has no coordinates or radius (`apps/planning/models.py:21-31`) |
| Automatischer Soll/Ist-Vergleich | Recorded time compared to the Dienstplan, errors flagged | Innendienst | **Partial** — `Shift.variance_minutes` (`models.py:180-185`) computes the delta; there is no approval queue |
| Zeitenfreigabe | Approval with Vorgabe / Erfassung / Custom, tolerances in % or minutes | Innendienst, Lohnbuchhaltung | **Missing** |
| Leistungsnachweise aus der App | Fotos, Bemerkungen, Unterschriften at the Einsatzort | Servicekraft | **Missing** — only `Shift.worker_note` (`models.py:160`) |
| Lohnarten und Zuschläge, Export | DATEV / CSV / Custom / API | Lohnbuchhaltung | **Missing** |

Detail belongs to **gr-zeiterfassung**.

### B3. Lohnabrechnung (`lohnabrechnung-gebaeudereinigung`) — *payroll preparation*

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Anstellungsverhältnisse | Per-employee payroll configuration | Lohnbuchhaltung | **Partial** — `ContractDraft` carries type, hours, wage (`apps/contracts/models.py:151-175`) |
| Lohnarten | User-definable, "Von Lohngruppen 1 bis hin zu speziellen Leistungsarten"; the FAQ says **Lohngruppen 1 bis 9** | Lohnbuchhaltung | **Missing** — no Lohnart, no Lohngruppe field |
| Automatische Zuschlagskalkulation | Nacht-, Sonn-, Feiertagsarbeit **nach Rahmentarifvertrag**, derived **from the Dienstplan**; plus Gefahrenzuschlag and free types. **No percentages are stated anywhere on the site.** | Lohnbuchhaltung | **Missing** |
| Abwesenheitsarten mit Entgeltfortzahlung | Four bases: unbezahlt · Vertragsstunden · geplante Stunden · Stundendurchschnitt | Lohnbuchhaltung | **Missing** |
| Export / Managed Payroll / Self-service | DATEV, CSV, custom, API; or a partner service; or an in-product payroll interface | Lohnbuchhaltung | **Missing** |
| Tarifprüfung | Vendor claim: "Mit PlanD halten Sie automatisch immer alle **tariflichen Vorgaben** ein" | — | **Partial and narrower, but real** — `ContractDraft.compliance_issues()` checks wage floor, Minijob ceiling, AÜG and Werkvertrag independence (`apps/contracts/models.py:193-249`) |

Detail belongs to **gr-tarif-und-lohn**. **Never quote a wage figure from this file.**

### B4. Angebot & Rechnung (`angebot-und-rechnung-gebaudereinigung`) — *quoting and invoicing*

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Angebot aus Produkten und Dienstleistungen | Prices calculated automatically; customer confirms with one click → Angebot becomes Auftrag | Innendienst | **Missing** |
| Automatische Rechnungserstellung | "Ist ein Einsatz abgeschlossen, erstellt PlanD automatisch die Rechnung" | Innendienst | **Missing** |
| Abschlags- und Teilrechnungen | "beliebig viele", consolidated into **einer Schlussrechnung** | Innendienst | **Missing** |
| Dauerrechnungen | Constant recurring amounts | Innendienst | **Missing** |
| Stornorechnungen und Gutschriften | The correction path — never deletion | Innendienst | **Missing** |
| Mahnwesen | Configurable Zahlungserinnerungen and Mahnstufen | Innendienst | **Missing** |
| Rechnungs- und Leistungsempfänger getrennt | Additional Leistungsempfänger per Auftrag | Innendienst | **Missing** |
| E-Rechnung | "in den Standards **ZUGFeRD** und **X-Rechnung**" (marked "Neu"; no mandate date given) | Innendienst | **Missing** |
| Bankanbindung | "PSD2-konforme" account link, invoices auto-marked paid | Innendienst, GF | **Missing** |
| Deckungsbeitrag je Auftrag | "vergleicht in Echtzeit **Ausgaben wie Lohn und Material** mit den **Einnahmen**" | Geschäftsführung | **Missing** |
| Material in Rechnung | Material orders auto-convert to invoice lines with **customer-specific prices** | Innendienst | **Missing** |
| Eigenes Briefpapier / Branding | Own logo, personalised documents | Innendienst | **Missing** |

Detail belongs to **gr-auftrag-und-faktura**. This is the largest single gap in the product.

### B5. Abwesenheitsverwaltung (`abwesenheitsverwaltung`)

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Urlaub und Krankheit in der App melden | With a document attachment (Krankheitsschein) | Servicekraft | **Missing** |
| Automatische Vertretungsvorschläge | "Das System schlägt direkt geeignete Vertretungen vor" | Innendienst | **Missing** |
| Gemeinsamer Abwesenheitskalender in Echtzeit | Objektleitung, Innendienst, Geschäftsführung | all | **Missing** |
| Resturlaub für den Mitarbeiter sichtbar | Remaining leave in the app | Servicekraft | **Missing** |
| Genehmigung durch Vorgesetzte mit einem Klick | Employee auto-notified of the decision | Objektleiter | **Missing** |
| Abwesenheitsart konfigurierbar | Per type: a **Lohnnummer**, whether employees may request it themselves, whether it **reduces the Urlaubsanspruch** | Lohnbuchhaltung | **Missing** |

### B6. Arbeitsscheine (`arbeitsscheine`)

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Arbeitsschein hinter dem Einsatz | Available on the phone at the site | Servicekraft | **Missing** |
| Digitale Unterschrift vor Ort | Customer signs; the signature is stored automatically | Kunde | **Missing** — signature machinery exists but only for contracts (`apps/contracts/models.py:256-281`) |
| Live-Sync von Stunden, Fotos, Unterschriften | Straight into the office | Innendienst | **Missing** |
| QR-Code-Zahlung | "Rechnungen per QR-Code sofort begleichen" | Kunde | **Missing** |
| Umwandlung in eine Rechnung | "Nach der Unterschrift werden Sie automatisch in Rechnungen umgewandelt" | Innendienst | **Missing** |

### B7. Aufgabenmanagement / Ticket-System (`aufgabenmanagement`)

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Listenansicht mit Filter und Suche | | Innendienst | **Missing** |
| **Kanban-Board** | Cards moved by drag & drop between Statusspalten (offen / laufend / abgeschlossen) | Innendienst | **Missing** |
| Polymorphe Verknüpfung | A task attaches to **Mitarbeitern, Kunden, Objekten, Aufträgen, Rechnungen oder Geräten** | all | **Missing** |
| Reklamationen und interne Prozesse | The explicit purpose set | Objektleiter | **Missing** |
| Externe Ticket-Annahme | Customer creates a ticket → auto-assigned to the responsible employee → **taken into account at the next clean** | Kunde → Objektleiter | **Missing** |

### B8. Geräteverwaltung (`geraeteverwaltung`)

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Maschinen, Geräte und Ausstattungen erfassen | Master data per device | Innendienst | **Have** — `Device` with kind, manufacturer, model, serial (`apps/devices/models.py:38-61`) |
| Gerät einem Objekt zuordnen, mit Historie und Standort | | Objektleiter | **Partial** — `Device.site` FK exists (`models.py:48-51`); **no location history** |
| Gerät einer Person oder einem Team zuordnen | Responsibility | Objektleiter | **Missing** |
| **Wartungsintervalle, Prüfintervalle, gesetzliche Prüfungen (z. B. DGUV V3)** with reminders; stated consequence of missing them: "Ausfallzeiten oder **Bußgelder**" | | Innendienst | **Missing** — no interval or test fields on `Device` |
| — *(not on the competitor's page)* | **Telemetry ingestion** with idempotent sessions and shift matching | Innendienst | **Have, and beyond the competitor** — `TelemetrySession` + `POST /api/telemetry/` (`apps/devices/models.py:94-132`, `config/urls.py:28`) |

Note the deliberate boundary in this repo: **device runtime is not cleaning time** — a vacuum may
run 25 of 120 minutes, so telemetry is a source of verification and discrepancy detection, never of
calibration or of Zeiterfassung (`apps/devices/models.py:1-15`).

### B9. Materialbestellungen (`materialbestellungen`)

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Material aus der App melden | Routed automatically to the office | Servicekraft | **Missing** |
| Objektspezifische Verwaltung (Materialschrank) | Allowed articles per object, monthly budget, **0 = unlimited** | Objektleiter | **Missing** |
| Digitale Dokumentation jeder Bestellung | What, when delivered, where needed | Innendienst | **Missing** |
| **Lieferscheine** automatisch | For customers **and** suppliers | Innendienst | **Missing** |
| Umwandlung in Rechnungspositionen | With customer-specific prices | Innendienst | **Missing** |
| Verbrauchsauswertung | Consumption per object | Geschäftsführung | **Missing** |
| — | A **product catalogue** with net/gross prices, safety data sheets and GHS pictograms | Lieferant | **Have, different purpose** — `apps/catalog` is a dealer catalogue (`models.py:35-92`), unpublished by default; it is **not** a Materialschrank |

### B10. Umsatz-Übersicht (`umsatzuebersicht`)

| Sub-capability | What it does | Rolle | Verdict |
|---|---|---|---|
| Offene Posten tagesaktuell | Which invoices are unpaid | Geschäftsführung | **Missing** |
| Beitragsanalyse | Which **Aufträge, Objekte oder Leistungen** contribute most | Geschäftsführung | **Missing** |
| Automatische Mahnung mit Eskalationsstufen | On overdue | Innendienst | **Missing** |
| Automatischer Zahlungsabgleich | Incoming payments matched by **Buchungsnummer, Kunde und Betrag** | Innendienst | **Missing** |

---

## C. The Übersicht page — the further capabilities

Source for all rows: `https://pland.app/funktionen/uebersicht`, grouped there under
Stammdatenverwaltung · Kommunikation · Warenwirtschaft · Qualitätsmanagement · Rechnungsstellung.

| # | German name | Mechanics as stated | Rolle | Verdict |
|---|---|---|---|---|
| 1 | **Deckungsbeiträge** | Per-Auftrag profitability from that order's Ausgaben vs. Einnahmen | GF | Missing |
| 2 | **Angebote verschicken** | Digital dispatch; "Angenommene Angebote werden automatisch abgerechnet" | Innendienst | Missing |
| 3 | **Digitale Objektmappe** | All Fotos, Dokumente and **Tickets** of an Objekt, mobile | Objektleiter | Missing |
| 4 | **Mitarbeiter Chat** | Replaces WhatsApp/SMS/phone; single and group messages | all | Missing |
| 5 | **Qualitätschecks** | Document work with **Bildern, Kommentaren und Sternen** | Objektleiter | Missing |
| 6 | **Tariflöhne** | "sämtliche Lohnarten … **inkl. Lohngruppen 1 bis 9**" | Lohnbuchhaltung | Missing (→ gr-tarif-und-lohn) |
| 7 | **Stammdatenverwaltung** | Mitarbeitern, Kunden, Objekten und Aufträgen | Innendienst | **Partial** — Account, Site, Zone exist; no Kunde, no Auftrag |
| 8 | **Schulungsplattform** | In-app video training, 16+ languages | Servicekraft | Missing |
| 9 | **Dokumentenverwaltung** | Documents attached to Kunden, Objekte, Mitarbeiter | Innendienst | **Partial** — `VerificationDocument` on an Account only (`apps/accounts/compliance.py:22-37`) |
| 10 | **Planungsassistent** | "Wer hat noch Zeit? Wer ist in der Nähe?" | Innendienst | Missing |
| 11 | **Standortkontrolle** | Alert when a time entry is **outside the planned Objekt-Radius** | Innendienst | Missing |
| 12 | **Kunden-Portal** | Customers request **Leistungsnachweise, Tickets oder Zusatzleistungen** | Kunde | Missing |
| 13 | **Lieferscheine** | Auto delivery notes for customers **and** suppliers | Innendienst | Missing |
| 14 | **Digitaler Stundenzettel** | Removes manual re-typing | Servicekraft | **Partial** — `/dashboard/pontaj/` shows records (`apps/dashboard/urls.py:41`); no worker-facing timesheet document |
| 15 | **Leistungsnachweise** | Sent online to the customer | Kunde | Missing |
| 16 | **Digitaler Urlaubsantrag** | Mobile request, auto-notification on approval | Servicekraft | Missing |
| 17 | **Rechtegruppen** | Custom permission groups per employee group | GF | **Partial** — capability rows + membership roles (`apps/accounts/enums.py:11-21,53-56`), not tenant-definable groups |
| 18 | **Schnittstellen** | DATEV, CSV, Custom-Export, direkte API | Lohnbuchhaltung | **Partial** — only the telemetry ingest endpoint exists |
| 19 | **Chats übersetzen** | Automatic message translation | Servicekraft | Missing |
| 20 | **Pausen- & Fahrzeiten** | Stored per Einsatz **and** per Dauerauftrag, auto-applied | Servicekraft | Missing |
| 21 | **Zapier-Integrationen** | Connect e-mail tools, CRM, other industry solutions | GF | Missing |
| 22 | **Benachrichtigungen** | Real-time push on Dienstplan changes | Servicekraft | **Partial** — e-mail on plan publication (`apps/planning/attendance.py:43-50`) |
| 23 | **Rechnungen auf Knopfdruck** | Auto-create and send by mail **or post** | Innendienst | Missing |
| 24 | **Personalisiertes Branding** | Own logo, personalised documents | GF | Missing |
| 25 | **Offline verfügbar** | App works without internet at the Einsatzort | Servicekraft | Missing |
| 26 | **25+ Sprachen** | (conflicts with the "16+" badge on every module page) | Servicekraft | Missing — `USE_I18N=True` but no catalogue |
| 27 | **Kunden Kommunikation** | Auto e-mail to customers about **Ticket-Anfragen** or **Vertretungen** | Kunde | Missing |
| 28 | **Kostenlose Updates** | Monthly, automatic, free | — | n/a |
| 29 | **Künstliche Intelligenz** | AI answers to customer enquiries | Innendienst | Missing |
| 30 | **Happy Birthday** | Reminders for Mitarbeiter-Geburtstage and Firmenjubiläen | Innendienst | Missing |
| 31 | **DSGVO-konform** | *Vendor claim* — "100 % DSGVO-konform … deutschen Datenschutz-Standards" | — | **Partial and better evidenced** — append-only `ConsentRecord`, private storage with `delete_after` on verification documents (`apps/accounts/compliance.py:22-70`) |
| 32 | **Umweltschonend** | Servers on Ökostrom, "klimaneutral" | — | n/a |
| 33 | **Schulungen** | Employee training with vendor experts | GF | n/a |

Plus six Übersicht cards that duplicate the Tier-B module pages (§B5–B10).

### C1. Adjacent product: the KI-Assistentin

Priced separately at **ab 99 € im Monat** (`https://pland.app/ki-assistenz`) — the only price
published anywhere on the site; **PlanD's own core price appears on none of the 22 product pages.**
Three surfaces: telephone (answers 24/7, distinguishes Neukunde / Mitarbeiter / Bewerber), e-mail
(reads, prioritises, creates the matching Aufgabe, drafts a reply — but **never sends by itself**),
and an in-product assistant.

Two governance facts worth copying regardless of whether an assistant is ever built:

- **"Für jeden Nutzer sieht Paula nur das, was dieser Nutzer auch sehen darf."** The assistant
  inherits the permission model; it does not have its own.
- **"Kann Vorgänge archivieren, aber aus Sicherheitsgründen aktuell nicht löschen."**

---

## D. Where this repo is ahead

Not everything is a gap. Five things exist here that the competitor's pages never claim:

| Capability | Where | Why it matters |
|---|---|---|
| **Constraints cite their statute** and a violation leaves demand *unallocated with a reason*, rather than being "almost" respected | `apps/planning/services.py:1-31`; `ShiftPlan.unmet_demand` (`models.py:103`) | The competitor asserts "Verstöße … automatisch informiert" but never lists a single rule |
| **Time-versioned legal values instead of constants** — `WageFloor`, `MinijobThreshold` with `valid_from`/`valid_to` and a `source_note` | `apps/contracts/models.py:57-114` | Rates step on fixed dates; a flat "Stundenlohn per Lohnart" cannot be audited retroactively |
| **Append-only evidence journals** — `ShiftEvent` and `ConsentRecord` both raise on re-save | `apps/planning/models.py:217-220`; `apps/accounts/compliance.py:67-70` | A correction is a new event, never an overwrite — the right shape for a Zoll audit |
| **Measured Leistungswerte instead of quoted ones** — `ZoneCalibration` proposes a corrected `minutes_per_visit` from the median of actual shifts, with a double threshold, a minimum sample, a cooldown and an explicit human decision | `apps/planning/calibration.py:1-40`; `apps/planning/models.py:235-292` | Nothing comparable appears anywhere on pland.app |
| **Device telemetry as cross-verification** with an explicit statement that runtime ≠ working time | `apps/devices/models.py:1-15`, `apps/devices/services.py:13-16` | The competitor's Geräteverwaltung is master data and maintenance reminders only |

---

## E. Build order

### E1. What the case studies actually adopted

**Vendor-published testimonials — 31 pages under `https://pland.app/erfolgsgeschichten/`.** The
counts below are a *lower bound*: a page usually does not say which modules the customer declined.

| Rank | Modul | Adopted in |
|---|---|---|
| 1 | **Digitale Zeiterfassung** (mobile, Start/Pause/Ende) | 31 / 31 |
| 1= | **Mitarbeiter-App** | 31 / 31 |
| 3 | **Einsatzplanung** (drag & drop) | 29 |
| 4 | **Materialbestellung / Materialschrank** | 15 |
| 5 | **Lohnvorbereitung / Export ans Steuerbüro** | 14 |
| 6 | **Angebots- und Rechnungsstellung** | 13 |
| 7 | **Reklamations-/Ticketsystem** | 11 |
| 7= | **Urlaubs- und Abwesenheitsverwaltung** | 11 |
| 9 | **Interne Kommunikation / Chat** | 8 |
| 10 | **GPS-Ortung / Standortnachweis** | 5 |
| 10= | **Auswertungen / Umsatz-Übersicht** | 5 |
| 12 | **Leistungsverzeichnis am Objekt** | 4 |
| 12= | **Mehrsprachigkeit** | 4 |
| 12= | **Dokumenten- und Fotoupload am Objekt** | 4 |
| 15 | **Kundenportal / QR-Code für Kunden** | 3 |
| 15= | **Serienaufträge** | 3 |
| 15= | **Digitale Arbeitsscheine** | 3 |
| 18 | **Offline-Zeiterfassung** | 2 |
| 19 | **Rollen-/Rechteverwaltung** | 1 |

### E2. Which pain points recur most

Same corpus; counted only where the page explicitly names the problem in the "before" state.

| Rank | Schmerzpunkt | Count |
|---|---|---|
| 1 | **Papier-Stundenzettel / Zettelwirtschaft** — collected, lost, illegible, late | 19 |
| 2 | **Planung per Excel / Google Kalender / Outlook / Flipchart** | 17 |
| 2= | **Vorherige Branchensoftware hat versagt** (unusable, too complex, discontinued) | 17 |
| 4 | **Manuelles Abtippen der Stunden → Fehler in der Lohnabrechnung** | 12 |
| 5 | **Materialbestellungen unkontrolliert** (Telefon/WhatsApp, kein Verbrauchsüberblick) | 11 |
| 6 | **Kommunikation über WhatsApp / viele Kanäle** | 9 |
| 7 | **Vertretungen / Krankheitsausfälle neu planen** | 8 |
| 8 | **Lohnabrechnung dauert zu lange** (explicitly 10 days at three firms) | 7 |
| 9 | **Kein Nachweis gegenüber Kunden** — was someone actually on site? | 6 |
| 9= | **Angebote/Rechnungen manuell, spät oder vergessen** | 6 |
| 11 | **Sprachbarriere im Team** | 4 |
| 12 | **Lokale Installation / VPN-Zwang** — no remote access | 3 |
| 13 | **Stationäre Terminals funktionieren nicht** (Fingerabdruck, WLAN, SIM, Wegezeiten) | 2 |
| 13= | **Keine Offline-Fähigkeit** in Kellern und Treppenhäusern | 2 |
| 13= | **Zeitbetrug / überhöhte Stundenangaben** | 2 |
| 16 | **Keine Serienaufträge planbar** | 1 |

### E3. Recommended build order (Vorschlag)

Reading §E1 against §E2 and against §B: three modules are table stakes (Zeiterfassung,
Einsatzplanung, a worker client at 94–100 % adoption); the first *differentiating* modules are
Materialwirtschaft and the payroll hand-off; then Faktura and Tickets.

| Stufe | Build | Why, from the evidence |
|---|---|---|
| **0 — finish what exists** | Objektleiter on `Site`; Qualifikation on the worker; a Zeitenfreigabe queue over the existing `Shift`/`ShiftEvent`; break and Fahrzeit fields | Every later module addresses one of these. The Objektleiter is the addressee of quality checks, tickets and absence approvals (§B in `rollen-und-prozesse.md`), and the repo has no such field at all |
| **1 — Zeitenfreigabe + Stundenzettel + export shape** | The approval workflow and a per-employee monthly document | Pain #1 (19), #4 (12) and #8 (7) are all the same pain: hours that arrive on paper and get retyped. Adoption 31/31 |
| **2 — Abwesenheit + Vertretung** | Absence types with an Entgeltfortzahlung basis, approval, affected-shift reassignment, customer notification | Pain #7 (8), adoption 11; and it is the daily disruption the planner cannot avoid |
| **3 — Materialschrank + Bestellung + Verbrauch** | Per-object allowed articles with a monthly budget, in-app request, approval, consumption | Pain #5 (11), adoption 15 — the **first differentiator**, and `apps/catalog` already carries the product side |
| **4 — Kunde + Auftrag + Angebot + Rechnung** | The whole commercial layer, invoice types included | Pain #9= (6), adoption 13; the largest gap and the one that turns operations into revenue. → **gr-auftrag-und-faktura** |
| **5 — Ticket / Reklamation + Kundenportal** | Customer-raised tickets with a deadline, assignment, photo evidence, auto-notification | Pain #9 (6), adoption 11 and 3; also the cheapest way to give the customer a reason to log in |
| **6 — Arbeitsschein + Leistungsnachweis** | Signature on site, photos, one-click conversion to an invoice | Adoption 3, but it is the artefact that makes step 4 defensible against a customer dispute |
| **7 — Lohnarten, Zuschläge, DATEV/CSV export** | The payroll hand-off proper | Adoption 14. High value, but it must not start before step 1 exists. → **gr-tarif-und-lohn** |
| **8 — Worker client: mobile, offline, multilingual** | | Pain #11 (4) and #13= (2), plus "~10 % of staff speak German" at one 400-person customer. Structural, expensive, and everything above must exist first |
| **9 — Umsatz, Deckungsbeitrag, Kostenstellen** | | Adoption 5; needs step 4 |
| **Deliberately not on this list** | GPS/geofence | Adoption 5, but it is the highest legal risk in the set: works-council co-determination and a documented legal basis come before any coordinate is stored. Decide it in **gr-zeiterfassung**, not by feature parity |

**Two caveats on using §E1 and §E2 at all.** The counts come from a curated set: customers who
churned, implementations that overran and the licence cost are all absent, and the only two frictions
admitted across 31 pages are "Bremser bei den älteren Mitarbeitern" and "Der Preis war anfangs
abschreckend". And no percentage anywhere in the corpus has a stated baseline or methodology — the
only claim whose *shape* is corroborated is payroll time (10 days → 0.5–2 days), because three
unrelated firms of very different sizes report it independently.

---

## F. Gaps and contradictions in the source

1. **Module count** — 11 files under `/funktionen/`, 10 actual modules.
2. **Customer count contradicts itself four ways** — 800+ / 500+ / "Über 500" / "Über 200".
3. **Language count contradicts itself** — 16+ on every module badge, 25+ on the Übersicht page,
   "20+" in two case studies.
4. **Support availability contradicts itself** — "täglich zwischen 9:00 und 18:00 Uhr" on the FAQ
   pages vs. "rund um die Uhr" on the home page.
5. **No core price anywhere** on 22 product pages; only the AI assistant has one.
6. **"Verstöße gegen gesetzliche oder tarifliche Vorgaben" is asserted with no rule list** — no
   statement of whether Höchstarbeitszeit, Ruhezeit, Jugendarbeitsschutz or Mindestlohn are checked.
7. **Lohngruppen 1 bis 9 with no rates** — not one euro figure, percentage or effective date for any
   Lohngruppe or Zuschlag appears on any product page.
8. **"100 % DSGVO-konform" is unsupported** — no AVV, no certification, and the home page says
   "Deutsche Server" while the assistant is hosted in Frankfurt *and* Amsterdam.
9. **Two different objects are both called "Auftrag"** — one picked per Einsatz in the planner
   alongside the Objekt, one created from an Angebot with start/end dates and billing settings. The
   pages never say whether they are the same entity. *Working assumption: they are.*
10. **Kunden-Portal vs. Kunden-Dashboard** are used interchangeably; unclear whether it is one
    surface.
11. **The competitor's own missing features, named by its customers:** Kostenstellen; no admin app
    (the planner cannot add appointments from the road); price perceived as high by very small firms.

---

## Quellen

**pland.app, crawled 2026-08-29**

- https://pland.app/funktionen/uebersicht
- https://pland.app/funktionen/einsatzplanung-gebaeudereinigung
- https://pland.app/funktionen/zeiterfassung-gebaeudereinigung
- https://pland.app/funktionen/lohnabrechnung-gebaeudereinigung
- https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung
- https://pland.app/funktionen/abwesenheitsverwaltung
- https://pland.app/funktionen/arbeitsscheine
- https://pland.app/funktionen/aufgabenmanagement
- https://pland.app/funktionen/geraeteverwaltung
- https://pland.app/funktionen/materialbestellungen
- https://pland.app/funktionen/umsatzuebersicht
- https://pland.app/software-gebaeudereinigung · /gebaeudereinigung-app · /ki-assistenz · /nutzer ·
  /demo · /registrieren · /lohnabrechnung-mit-pland · /hausmeisterdienste-lp · /werk · /werk-lp ·
  https://pland.app (home)
- https://pland.app/erfolgsgeschichten (index) and the 31 individual case studies
- https://pland.app/onboardings/mitarbeiter-in-pland-erstellen · /kunden-objekte-in-pland ·
  /materialbestellungen-in-pland · /ticket-system-in-pland

**Repository, read 2026-08-29**

- `apps/planning/models.py`, `apps/planning/services.py`, `apps/planning/attendance.py`,
  `apps/planning/calibration.py`
- `apps/contracts/models.py`
- `apps/devices/models.py`, `apps/devices/services.py`
- `apps/accounts/enums.py`, `apps/accounts/compliance.py`
- `apps/catalog/models.py`
- `apps/dashboard/urls.py`, `config/urls.py`
