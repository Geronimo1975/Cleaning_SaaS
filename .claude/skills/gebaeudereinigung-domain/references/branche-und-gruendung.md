# Branche und Gründung — the regulatory context of a German cleaning company

Covers: what it takes to be a Gebäudereinigung in Germany — Handwerksrolle and Anlage A vs. B,
Gewerbeanmeldung, HWK and IHK, BG BAU, the Bundesinnungsverband and the Innungen, the legal forms —
and what of all that the platform must capture on a company account.
**Stand: 2026-08-29.**
Material: the pland.app `/tutorials/` founding cluster (25 pages, all dated 19.7.2023, crawled
2026-08-29) plus the Erfolgsgeschichten cluster; the live repository (`file:line`, read 2026-08-29).

**Read the density warning first.** The founding cluster is almost entirely qualitative advice. It
contains **one euro-per-square-metre price, one example financial plan, and one external URL**.
There are **no wage tables, no capital-requirement figures, no statute paragraph numbers and no
deadlines** anywhere in it. **DSGVO is the only named legal instrument in all 25 pages.**

Consequently a large part of what a builder needs here is **Ungeprüft** — added domain knowledge,
marked as such, to be verified against primary sources before it reaches code or customer-facing
copy. This is reference material, not legal advice.

---

## A. Handwerksrecht — who may call themselves what

### A1. What the sources actually say (Fakt)

Source for all five rows:
https://pland.app/tutorials/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung

| Statement (verbatim sense) | Meaning |
|---|---|
| "Bei der Gründung einer eigenen Reinigungsfirma gibt es grundsätzlich **keine beruflichen Beschränkungen** oder spezifische Ausbildungsvoraussetzungen." | No entry qualification to found a cleaning company |
| "…es werden keine bestimmten Qualifikationen oder einen **Meistertitel** benötigt, um sich selbstständig zu machen." | No Meisterpflicht |
| "Das Reinigungsgewerbe gehört zum **zulassungsfreien Handwerk**, was bedeutet, dass es keine formellen Qualitätsanforderungen gibt, die erfüllt werden müssen." | Licence-free craft |
| "…der Beruf des **Gebäudereinigers** erfordert eine Ausbildung und die Bezeichnung 'Gebäudereiniger' ist **geschützt**. Nur Personen, die eine entsprechende Ausbildung absolviert haben, dürfen sich offiziell als Gebäudereiniger bezeichnen." | The job title is protected |
| "…während die Erbringung von Gebäudereinigungsdienstleistungen im Allgemeinen von jedem angeboten werden kann, unabhängig von einer spezifischen Ausbildung." | The service is open to anyone |

**Internal contradiction, unresolved on the page:** it is licence-free with "keine formellen
Qualitätsanforderungen" in one paragraph and the title is protected and requires an Ausbildung in
the next. The page never explains how the two interact — what you may call your *company* versus
what you may call *yourself*. It never mentions Handwerksrolle, Anlage A or Anlage B.

Second contradiction: the legal page tells you to "eine **Gewerbeerlaubnis** beantragen"
(https://pland.app/tutorials/welche-rechtlichen-aspekte-muss-ich-bei-der-grundung-einer-reinigungsfirma-beachten)
while the intro page says the trade is licence-free. **Which permit, from whom, is never said.**

### A2. What is not on any of the 25 pages

**Never mentioned:** Handwerksrolle · Handwerkskammer (HWK) · IHK · Anlage A / Anlage B / Anlage B1
of the Handwerksordnung · BG BAU by name · Mindestlohn · Lohngruppen · Tarifvertrag · SOKA ·
Meisterpflicht paragraph references · Transparenzregister · Kleinunternehmerregelung · §14 UStG ·
capital requirements for a GmbH or a UG · tax consequences per legal form · VAT rate ·
retention-period durations · membership fees for an Innung. Also never identified: which "Lizenzen
und Genehmigungen" the 1.000 €/year cost line in the example financial plan pays for, and what
"Zertifizierung als Gebäudereiniger" concretely is (no issuer, no scheme).

### A3. Ungeprüft — the Handwerksordnung picture a builder needs

**Not from the sources. Verify before relying on any of it.**

- *Gebäudereiniger* is a listed craft in the **Handwerksordnung (HwO)**. It moved from **Anlage A**
  (zulassungspflichtig, with Meisterpflicht) to **Anlage B1** (zulassungsfrei) in the 2004 reform,
  and it was **not** among the twelve trades returned to Anlage A in the 2020 reform. So the trade
  is currently **zulassungsfrei** — which is what the source means, imprecisely.
- Being zulassungsfrei does **not** remove registration: the business must still be entered in the
  **Handwerksrolle** at the competent **Handwerkskammer**. For an Anlage-B trade this is a
  notification duty, not a qualification hurdle. **The sources never mention it, and a tenant
  onboarding checklist must include it.**
- **Chamber membership is compulsory** in Germany: a Handwerk business belongs to the **HWK**, a
  non-craft trade business to the **IHK**, each with mandatory contributions. A cleaning company is
  normally HWK. The sources mention neither.
- **BG BAU** (Berufsgenossenschaft der Bauwirtschaft) is the competent statutory accident insurer
  for Gebäudereinigung, and registration is **mandatory shortly after starting the business** — not
  "ggf." as the source implies. Contributions are computed on payroll and a hazard tariff class.
- **Sofortmeldepflicht (§28a Abs. 4 SGB IV):** in Gebäudereinigung specifically, employers must
  report a new employee to the social-insurance system **on the day work starts** — one of only a
  handful of sectors with this duty, and a genuine feature opportunity. Related: the
  **Mitführungspflicht** of ID documents under §2a SchwarzArbG for staff in this sector, and routine
  **FKS (Finanzkontrolle Schwarzarbeit)** audits by the Zoll.
- **Generalunternehmerhaftung (§14 AEntG):** a company using Subunternehmer is liable for the
  subcontractor's minimum wages. Any Subunternehmer feature therefore needs compliance-document
  tracking.

**Repo note.** This repo already asserts the Anlage-B1 position, in a Romanian comment:
"Curățenia de clădiri e Anlage B1 HwO — fără Meisterpflicht, dar cu înregistrare la
Handwerkskammer", carried by `CompanyProfile.hwk_registered`
(`apps/accounts/profiles.py:52-54`). That is a repo assertion, not a sourced fact — it agrees with
the Ungeprüft picture above and should be re-verified before it drives anything user-facing.

**Corroboration from the field, such as it is:** the case studies repeatedly present the
**Meistertitel** as a market signal rather than a legal requirement — "zertifizierter
Meisterbetrieb" (Kille), "legte den Meister ab" (Dennis Krumbach), Meistertitel 2002 (Sascha Dilly),
Meisterkurs completed before founding (Lars Kaufhold). One firm's degree of digitalisation was rated
"ausgezeichnet" on a **Handwerkskammer Bremen** visit
(https://pland.app/erfolgsgeschichten/gebaudereinigung-oelfke-gmbh) — the only appearance of a
Handwerkskammer anywhere in the corpus.

---

## B. The founding checklist as the sources give it

Source: https://pland.app/tutorials/welche-rechtlichen-aspekte-muss-ich-bei-der-grundung-einer-reinigungsfirma-beachten
Seven items, exactly as enumerated:

| # | Item | What the page says it requires | Statute cited |
|---|---|---|---|
| 1 | **Gewerbeanmeldung** | Register with the responsible **Gewerbeamt** and apply for a **Gewerbeerlaubnis** | none (no GewO reference) |
| 2 | **Rechtsformwahl** | Einzelunternehmen, GmbH, UG (haftungsbeschränkt) | none |
| 3 | **Handelsregistereintrag** | Required for certain legal forms, "wie der GmbH" | none (no HGB reference) |
| 4 | **Steuerliche Anforderungen** | Register with the **Finanzamt**; **Umsatzsteuererklärung** and **Gewerbesteuer** | none |
| 5 | **Versicherungen** | **Betriebshaftpflichtversicherung**, and "ggf. eine **Berufsgenossenschaftsversicherung**" | none; BG BAU never named |
| 6 | **Arbeitsrecht** | Anmeldung von Mitarbeitern, Arbeitsverträge, Arbeitszeiten, Arbeitsschutzvorschriften | none (no ArbZG, no ArbSchG) |
| 7 | *(label lost in the source rendering; the bullet text is about data protection)* | Comply with the **DSGVO** and process personal data properly | **DSGVO** — the only named legal instrument in the whole cluster |

Item 7's heading was stripped in the extraction; only ": Du musst die Datenschutzbestimmungen gemäß
der Datenschutzgrundverordnung (DSGVO) einhalten…" survives. The label was almost certainly
"Datenschutz" — inferred, not stated.

**Registration sequence as the source orders it** (the page does not itself claim an order for
steps 2–7): choose the Rechtsform → Gewerbeanmeldung at the Gewerbeamt → Handelsregistereintrag if
the form requires it → register with the Finanzamt and obtain the **Steuernummer** → take out
insurance → employment-law setup incl. **Sozialversicherungspflicht** → DSGVO compliance.

The 13-step founding workflow the same cluster teaches, condensed:
Geschäftsplan → Rechtsform + Recht → Finanzplan → Ausrüstung → Personal → Marketing → Kundenakquise
→ Qualitätssicherung → Networking → Software/Prozesse → Kundenbindung → Buchhaltung → Wachstum
(https://pland.app/tutorials/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung).

---

## C. Legal forms

Source: https://pland.app/tutorials/gmbh-ug-oder-einzelunternehmen
Selection factors named: Größe des Unternehmens · Haftungsbeschränkung · steuerliche Aspekte ·
langfristige Pläne. The page closes by recommending a Rechtsanwalt or Steuerberater.

| Rechtsform | Kapital (as stated) | Haftung | Gründungsaufwand | Weitere Eigenschaften |
|---|---|---|---|---|
| **Einzelunternehmen** | **not stated** | Owner "persönlich für alle geschäftlichen Verbindlichkeiten verantwortlich" | "relativ einfach und kostengünstig" | For small/medium firms run by one owner; full control |
| **GmbH** | **not stated** | Limited — the company is its own **juristische Person**; personal assets protected | "erfordert die Einhaltung bestimmter formeller Anforderungen und kann etwas aufwendiger sein" | Greater **Glaubwürdigkeit**; suited to long-term growth and to taking on partners or investors; needs a Handelsregistereintrag |
| **UG (haftungsbeschränkt)** | "**Deutlich weniger Startkapital**", "ein geringer Betrag ist ausreichend" — **no figure** | Limited to the **Firmenvermögen** | "hohe formale Anforderungen" | Called the "**Mini-GmbH**"; "die häufigste Alternative zur GmbH" |

**Tax consequences per form are named as a decision factor and never explained.** *Nicht belegt.*

**Ungeprüft — the figures the source omits:** GmbH **Stammkapital 25.000 EUR**, half payable on
formation; a UG (haftungsbeschränkt) can be founded from **1 EUR** but must retain **25 % of annual
profit** as a statutory reserve until it reaches GmbH capital, at which point it may convert.
Bookkeeping duty differs too: an Einzelunternehmen below the §241a HGB thresholds may use an
**EÜR (Einnahmen-Überschuss-Rechnung)**, while a GmbH or UG must keep double-entry books and file
annual accounts. Verify all of it.

---

## D. Bookkeeping, invoicing and tax duties

Source: https://pland.app/tutorials/wie-fuhre-ich-als-reinigungsfirma-buch — nine areas:

| Bereich | What the page requires |
|---|---|
| **Kontenplan und Buchhaltungssystem** | A structured chart of accounts over all income and expense categories; a system, manual or software |
| **Erfassen von Geschäftsvorfällen** | Every transaction with Beträge, Daten, Zahlungsbedingungen |
| **Rechnungsstellung** | Invoices must carry **Rechnungsnummer, Leistungsbeschreibung, Datum, Betrag, Zahlungsbedingungen**; keep copies |
| **Umsatzsteuer** | Know the VAT rules for cleaning services; apply the correct **Umsatzsteuersätze**; file **Umsatzsteuervoranmeldungen** on time |
| **Zahlungsverkehr** | Track incoming payments; book expenses; identify **offene Posten und Zahlungsverzüge** |
| **Belegmanagement** | File all Rechnungen, Belege, Kontoauszüge against accounts and postings |
| **Steuerliche Pflichten** | File Umsatzsteuer and Einkommensteuer returns on time |
| **Dokumentation und Aufbewahrung** | Observe the **gesetzliche Aufbewahrungsfristen** — **duration never stated** |
| **Fachliche Unterstützung** | Optional Steuerberater or Buchhalter |

**Angebot — mandatory content** (https://pland.app/tutorials/angebote-richtig-schreiben-als-gebaudereinigung):
detailed service description incl. **Art der Reinigung** and **Häufigkeit** (täglich, wöchentlich,
monatlich) · a list of the **Reinigungsmittel und -geräte** used, with **Marke und Modell** where
required · the price plus payment terms incl. **Fälligkeit** and **Zahlungsmodalitäten** ·
a statement of **Garantie- und Haftungsbedingungen** and of the company's **Versicherungspolice**.
Tips: add Referenzen; personalise; state clear per-service prices incl. **Stundensätze, Arbeitszeit
und Material**; be transparent about extra fees; send it **schriftlich**.

**Rechnung — mandatory content**
(https://pland.app/tutorials/so-stellen-sie-rechnungen-als-gebaudereinigung):
Rechnungsdatum · both parties' full contact data · a detailed description of the services rendered
**including the date the cleaning was performed** · price, **Umsatzsteuersatz**, **Gesamtbetrag** ·
**Fälligkeitsdatum** and Zahlungsmodalitäten · Garantie-/Haftungsbedingungen and Versicherungspolice.
Tips: a unique **Rechnungsnummer** as a traceable sequence; state Arbeitsstunden and price per hour
or service; proofread for wrong amounts and **doppelte Einträge**. The invoice must "genau den im
Angebot vereinbarten Preis und Leistungsumfang widerspiegeln".

**Ungeprüft — what the sources omit and a German product will be asked about:** invoice content is
statutory under **§14 UStG** (and §14a for special cases; §33 UStDV for small-value invoices);
**retention is 10 years** for invoices and accounting records and 6 years for commercial
correspondence (§147 AO / §257 HGB); all digital bookkeeping must satisfy **GoBD** (immutability,
audit trail, Verfahrensdokumentation) — which means an issued invoice must never be editable and a
correction must be a credit note; **§19 UStG Kleinunternehmerregelung** decides whether a founder
charges VAT at all; **§13b Abs. 2 Nr. 8 UStG reverse charge** applies when cleaning services are
supplied to a business that itself supplies cleaning services — an edge case a German cleaning SaaS
will hit; and since **1 January 2025** German B2B businesses must be able to *receive* structured
e-invoices (EN 16931 — XRechnung / ZUGFeRD), with issuing obligations phasing in later. **The
crawled Arbeitslexikon page compresses that staged timeline into "ab 2025 Pflicht für alle
Unternehmen" — do not copy that claim into product copy.** All of it belongs to
**gr-auftrag-und-faktura**; verify the current statute text there.

---

## E. Verbände — Innungen and the BIV

Source: https://pland.app/tutorials/bundesinnungsverband-des-gebaudereiniger-handwerks

| Body | What the page says |
|---|---|
| **Bundesinnungsverband des Gebäudereiniger-Handwerks (BIV)** | "die zentrale Interessenvertretung der Gebäudereinigungsbranche in Deutschland"; supports members on legal and economic questions; develops the trade; promotes **Aus- und Weiterbildung** |
| **Fachinnungen** | Regional bodies for specific regions: local networking, Informationsveranstaltungen, support in regional matters |
| **Innungen** per Bundesland / city | Industry information, member services, technical support, a wide range of Aus- und Weiterbildungsangebote |

**The only external URL in the entire founding cluster:**
https://www.die-gebaeudedienstleister.de/der-verband/mitgliedschaft-im-biv
The page's own caveat: "Die genauen Leistungen können je nach Bundesinnung variieren."

**Membership benefits, six items**
(https://pland.app/tutorials/vorteile-einer-mitgliedschaft-bei-einer-bundesinnung):
Interessenvertretung towards Politik and Behörden · Informationsaustausch on developments,
**gesetzliche Vorgaben** and Branchentrends · Weiterbildung · Netzwerkmöglichkeiten ·
Unterstützung bei rechtlichen und wirtschaftlichen Fragen — explicitly **Tarifgestaltung**,
**Vertragsrecht**, betriebswirtschaftliche Themen · Imageförderung.

**Note.** "Tarifgestaltung" is the **only allusion to collective wage agreements anywhere in the
founding cluster**, and no tariff figure is given. Membership fees are not stated.

**Ungeprüft but load-bearing:** the trade's Rahmen- and Lohntarifvertrag are negotiated between the
**BIV** and **IG BAU** and are generally declared **allgemeinverbindlich**, which is why the wage
floor binds employers who are not members of any Innung. That is exactly the assumption behind
`WageFloor.Kind.GEBAEUDE` in this repo (`apps/contracts/models.py:62-64, 69`). Verify the current
declaration and the rates in **gr-tarif-und-lohn** — never here.

**Trade events named:** the **CMS Berlin** fair ("Cleaning Management Services", three segments
Cleaning / Management / Services) is the named acquisition channel of four case-study firms
(https://pland.app/arbeitslexikon/cms-berlin). **Rationell Reinigen** is named as a trade magazine
channel (https://pland.app/erfolgsgeschichten/volk-volk).

---

## F. What the case studies say about the market

**Vendor-published testimonials.** Structural facts only; see `marktreferenz-pland.md` §E for the
methodology caveats.

| Dimension | What the corpus shows |
|---|---|
| Company size range | 1–5 employees up to 501–1.000, across 31 firms |
| Size bands the market segments itself into | 1-5 · 6-10 · 11-20 · 21-50 · 51-100 · 101-250 · 251-500 · 501-1.000 |
| Countries | Deutschland (29), Österreich (1), Schweiz (1) |
| Company age | From founded-this-year up to "60+ Jahre", 3rd generation, "seit 1982", "seit 1998" |
| Self-description (free text, not a controlled list) | Gebäudereinigung · Gebäudedienstleister · Gebäudedienste · Gebäudedienstleistungen · Facility Management · Gebäudereinigung & Facility Management · Gebäudereinigung & Hausmeisterdienste · Hausmeister & Reinigungsservice · Gebäudereinigung Privathaushalte & Büro |
| Customer stickiness | One firm reports most customers retained **>20 years** |
| Named public-sector customers | a Stadtverwaltung and an Amtsgericht — i.e. **XRechnung is required today**, not eventually |
| A legal boundary a founder hit | Engaging cleaners "auf Rechnung" (as invoicing contractors) was declared not legal by that firm's Steuerberater, so they had to employ them. The term Scheinselbstständigkeit is **not** used on the page | 
| Named self-employment risk in this repo | The same boundary, stated with its statute: §7 SGB IV, and the AÜG licence requirement (`apps/marketplace/models.py:10-14`; `apps/contracts/models.py:11-13`) |

---

## G. What the platform must capture about a company account

### G1. What already exists (Fakt)

| Feld | Where |
|---|---|
| `entity_type` — INDIVIDUAL / COMPANY, immutable after creation | `apps/accounts/enums.py:4-8`; `apps/accounts/models.py:85` |
| `legal_status` — UNDECLARED / MINIJOB (§8a SGB IV) / SELBSTSTAENDIG mit Gewerbeanmeldung / KLEINUNTERNEHMER (§19 UStG) / COMPANY | `apps/accounts/enums.py:24-35`; `models.py:86-88` |
| `legal_name` ("Denumire în registru") | `apps/accounts/models.py:92` |
| `registration_number` — help text "HRB / Gewerbeanmeldung" | `apps/accounts/models.py:93-95` |
| `vat_id` — "USt-IdNr. (DE...)" | `apps/accounts/models.py:96` |
| `tax_number` — "Steuernummer" | `apps/accounts/models.py:97` |
| `verification_level` — NONE / EMAIL / PHONE / DOCUMENTS | `apps/accounts/enums.py:46-50` |
| `CompanyProfile.employees_range`, `founded_year`, `website` | `apps/accounts/profiles.py:46-48` |
| `CompanyProfile.has_liability_insurance`, `insurance_valid_until` — "Prestatorul intră în locuința clientului. Fără acoperire, un furt omoară platforma." | `apps/accounts/profiles.py:49-51` |
| `CompanyProfile.hwk_registered` — "Înregistrat la HWK" | `apps/accounts/profiles.py:52-54` |
| `VerificationDocument.doc_type` — ID · POLIZEILICHES (Führungszeugnis) · **GEWERBE** (Gewerbeanmeldung) · **HRB** (Handelsregister) · **INSURANCE** · QUALIFICATION, with `status`, `expires_at` and a DSGVO `delete_after` | `apps/accounts/compliance.py:7-37` |
| `ConsentRecord` — append-only consent trail with policy version, IP and user agent | `apps/accounts/compliance.py:44-70` |
| Company validity rule — an INDIVIDUAL may not carry `LegalStatus.COMPANY` | `apps/accounts/models.py:175-177` |

**The existing model already covers most of §B's checklist.** That is not an accident: `GEWERBE`,
`HRB`, `INSURANCE` and `hwk_registered` map one-for-one onto founding steps 1, 3, 5 and the
Ungeprüft Handwerksrolle duty.

### G2. What is missing (Vorschlag)

Nothing below exists. Each row states the evidence for wanting it.

| Feld / Modell | Warum | Beleg |
|---|---|---|
| `rechtsform` enum — `EINZELUNTERNEHMEN` / `UG_HAFTUNGSBESCHRAENKT` / `GMBH` | Drives which of the other fields are required; `registration_number` today merges HRB and Gewerbeanmeldung into one field, so a GmbH and a sole trader are indistinguishable | https://pland.app/tutorials/gmbh-ug-oder-einzelunternehmen |
| Split `registration_number` into `handelsregister_nummer` (conditional) and `gewerbeanmeldung_nummer` + `gewerbeanmeldung_datum` + `gewerbeamt` | They are different registers with different authorities and different applicability | founding checklist §B items 1 and 3 |
| `finanzamt`, `gewerbesteuer_pflichtig` | Named tax obligations | §B item 4 |
| `bg_mitgliedsnummer`, `bg_traeger` | The statutory accident insurer is a separate registration from the liability policy already modelled | **Ungeprüft** (BG BAU is never named by the sources) |
| `Versicherung(art, versicherer, policennummer, jahresbeitrag, gueltig_von, gueltig_bis, policentext)` | The Angebot and Rechnung templates must **print the Versicherungspolice statement**, so it has to be a stored, templatable field on the company — not free text per document | https://pland.app/tutorials/angebote-richtig-schreiben-als-gebaudereinigung |
| `garantie_haftung_text` on the company | Same reason: both the Angebot and the Rechnung must carry Garantie- und Haftungsbedingungen | both TUT invoice/quote pages |
| `innung_mitglied`, `innung_name` | A trust signal and a real relationship; the Innung advises on Tarifgestaltung | https://pland.app/tutorials/vorteile-einer-mitgliedschaft-bei-einer-bundesinnung |
| `meisterbetrieb` flag, and a `Meisterbrief` document type | The market treats it as a differentiator even though it is not required | Kille, navus, Kaufhold case studies |
| `CompanyLegalChecklist(obligation, status, erledigt_am, nachweis_dokument)` with the 7 obligations of §B plus Handwerksrolle and Sozialversicherung | Onboarding a company tenant is a state machine (`OFFEN → IN_BEARBEITUNG → ERLEDIGT → NICHT_ZUTREFFEND`), not a form | §B; the doc types already exist in `apps/accounts/compliance.py` |
| `SubunternehmerNachweis` — Unbedenklichkeitsbescheinigung, BG-Bescheinigung, A1 for posted workers, with expiry | **Ungeprüft:** §14 AEntG makes the principal liable for the subcontractor's minimum wages, so these documents must expire and re-request | Ungeprüft; one case study confirms subcontractors are planned like employees |
| `kleinunternehmer` flag on the company, separate from `LegalStatus.KLEINUNTERNEHMER` on the account | It gates VAT on every invoice, and an account's legal status is a coarser thing than a per-year VAT election | https://pland.app/arbeitslexikon/e-rechnung names the Kleinunternehmer exemption |
| Company branding: `logo`, `briefpapier`, `fusszeilentext`, `kopfzeilentext`, `bankverbindung` | Every quote and invoice renders from them | https://pland.app/onboardings/die-wichtigsten-faktura-einstellungen-in-pland |
| `Standort` / `Niederlassung` | Case-study firms run six German locations; a device page mentions "auch für mehrere Standorte" — but **no page describes a Standort entity or how permissions scope to it**. *Nicht belegt* — design it deliberately | https://pland.app/erfolgsgeschichten/… (HBC, LCM); https://pland.app/funktionen/geraeteverwaltung |

### G3. Two rules to keep while adding any of it

1. **Documents, not booleans, are the evidence.** `hwk_registered` is a claim; a `VerificationDocument`
   with `doc_type`, `status`, `expires_at` and `delete_after` is proof with a retention policy. The
   pattern already exists (`apps/accounts/compliance.py:22-37`) — extend it rather than adding more
   flags.
2. **Every legal or tarif value is a time-versioned row.** Follow `WageFloor` /
   `MinijobThreshold`: `valid_from`, optional `valid_to`, a `source_note`, and a `current()`
   classmethod that resolves as of a date (`apps/contracts/models.py:57-114`). Insurance validity,
   Innung membership, certificate expiry and any statutory threshold all have the same shape.

---

## H. Open questions

1. **Which permit is the "Gewerbeerlaubnis" the source tells founders to apply for?** The trade is
   licence-free; the page names no authority and no statute. *Nicht belegt.*
2. **Is the Handwerksrolle entry a duty for this trade, and with which chamber?** The sources never
   mention it; the repo asserts it in a comment. Verify before it becomes a required onboarding step.
3. **Is BG BAU the competent Berufsgenossenschaft for Gebäudereinigung, and what is the registration
   deadline?** *Ungeprüft.*
4. **What does the market mean by "Zertifizierung als Gebäudereiniger"?** Named as a trust-builder
   with no issuer and no scheme. *Nicht belegt.*
5. **How do Standorte / Niederlassungen scope permissions?** No page describes it, and multi-site
   customers exist. Decide it before the first multi-branch tenant.
6. **The example financial plan does not add up.** Itemised annual costs total 150.100 € but the GuV
   states Gesamtkosten 235.800 €; the two example documents for the same fictitious company also
   disagree on year-1 revenue (200.000 € in the business plan vs. 600.000 € in the financial plan),
   and the 25 % tax rate is applied to Betriebsergebnis as a single blended rate attributed to no
   tax type. Sources: https://pland.app/tutorials/beispiel-finanzplan ·
   /beispiel-geschaftsplan. **Do not seed any figure from those pages.** A validator that recomputes
   Gesamtkosten from the line items and warns on a mismatch would be a genuine differentiator.

---

## Quellen

**pland.app, crawled 2026-08-29 — all tutorial pages dated 19.7.2023**

- https://pland.app/tutorials/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung
- https://pland.app/tutorials/welche-rechtlichen-aspekte-muss-ich-bei-der-grundung-einer-reinigungsfirma-beachten
- https://pland.app/tutorials/gmbh-ug-oder-einzelunternehmen
- https://pland.app/tutorials/wie-fuhre-ich-als-reinigungsfirma-buch
- https://pland.app/tutorials/angebote-richtig-schreiben-als-gebaudereinigung
- https://pland.app/tutorials/so-stellen-sie-rechnungen-als-gebaudereinigung
- https://pland.app/tutorials/bundesinnungsverband-des-gebaudereiniger-handwerks
- https://pland.app/tutorials/vorteile-einer-mitgliedschaft-bei-einer-bundesinnung
- https://pland.app/tutorials/was-benotige-ich-als-reinigungsfirma-an-personal
- https://pland.app/tutorials/wie-sieht-ein-finanzplan-aus
- https://pland.app/tutorials/beispiel-finanzplan
- https://pland.app/tutorials/beispiel-geschaftsplan
- https://pland.app/tutorials/was-sollte-ein-geschaftsplan-alles-beinhalten
- https://pland.app/tutorials/wie-finde-ich-kunden-und-auftrage
- https://pland.app/arbeitslexikon/e-rechnung
- https://pland.app/arbeitslexikon/cms-berlin
- https://pland.app/onboardings/die-wichtigsten-faktura-einstellungen-in-pland
- https://pland.app/erfolgsgeschichten (index) plus gebaudereinigung-oelfke-gmbh · volk-volk ·
  erfolgsgeschichte-hbc-services-gmbh · how-lcm-now-has-all-relevant-information-in-one-place ·
  wie-der-meisterbetrieb-kille-gebaudedienste-mit-pland-den-nachsten-wachstumsschritt-geht ·
  wie-spy-clean-arbeitszeiten-endlich-digital-erfassen-und-fur-kunden-dokumentieren-kann

**External URL cited by the source itself**

- https://www.die-gebaeudedienstleister.de/der-verband/mitgliedschaft-im-biv

**Repository, read 2026-08-29**

- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/enums.py` (lines 4-8, 24-35, 46-50)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py` (lines 85-97, 112-114, 175-177)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/profiles.py` (lines 42-65)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/compliance.py` (lines 7-70)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py` (lines 11-13, 57-114)
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/marketplace/models.py` (lines 10-14)
