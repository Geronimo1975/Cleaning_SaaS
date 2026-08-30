# Rechtliche Grenzen — what German law does to a Lieferando-style model in this trade

**What this covers:** the legal constraints that decide the data model of the marketplace/dispatch
layer — the allgemeinverbindlicher Mindestlohn/Lohntarifvertrag in the Gebäudereinigung,
Scheinselbstständigkeit, Arbeitnehmerüberlassung and the BAG Konzernprivileg ruling, the
Handwerksrolle position of the trade, and the working-time recording duties that follow the
employer — and the single conclusion they force: **the dispatch layer allocates employees, so
contracts + planning are a legal precondition of the marketplace, not a later phase.**

**Stand: 2026-08-29, re-verified ~20:30 after a concurrent edit round.** The repo is under active
concurrent editing and is not under version control — re-read any file before citing it.
Tariff and statutory values in this trade change every year; every table
below carries its as-of date and its source URL so a future reader can re-check it.

**This is reference material for building software, not legal advice.** Every real case needs a
Steuerberater or a Fachanwalt für Arbeitsrecht.

**Material from:** `scratchpad/knowledge/blog-tarif-arbeitsrecht.md` and
`scratchpad/knowledge/tutorials-gruendung.md` (both citing pland.app page URLs), and the live
repository. Statements are marked **Fakt** / **Vorschlag** / **Ungeprüft**.

---

## 1. The chain of reasoning, compressed

1. A cleaning marketplace's supply side is people who clean.
2. Under German law that person is either **employed** (by someone), **genuinely self-employed**, or
   **undeclared**. There is no fourth, tax-neutral "gig worker" category. `PLAN-FAZA-0.md:194-196`
   already recorded this for the Romanian case and it is at least as true in Germany.
3. If the platform decides *who works when and where*, the platform (or its customer) is behaving
   like an employer, and the arrangement is tested under **§7 SGB IV** (Scheinselbstständigkeit) or
   falls under the **AÜG** (Arbeitnehmerüberlassung), which requires an Erlaubnis from the
   Bundesagentur für Arbeit.
4. Therefore the only lawful automatic allocation is allocation of **employees under a signed
   contract** — which is exactly `apps/planning/services.py:51-79`.
5. Therefore `apps.contracts` and `apps.planning` are not "phase 3". They are what makes a dispatch
   feature legal at all.

The repository already states step 3 and 4 in code comments. **Fakt:**
`apps/marketplace/models.py:10-14`, `apps/marketplace/scoring.py:160-166`,
`apps/contracts/models.py:1-14`.

---

## 2. The wage floor is not optional and not the statutory Mindestlohn

**Fakt (pland.app).** The Gebäudereinigung has its own collectively agreed wage grid, and it has
been declared **allgemeinverbindlich** — generally binding on *every* cleaning business, member or
not, including foreign providers supplying cleaning in Germany.

### 2.1 Lohngruppen and rates — Lohntarifvertrag 2025/2026

Agreed **15.11.2024**, Laufzeit **24 months, 01.01.2025 – 31.12.2026**. Parties: **IG BAU** and the
**Bundesinnungsverband des Gebäudereiniger-Handwerks (BIV)**.
Source for the whole table:
<https://pland.app/blog/tariflohn-2026-in-der-gebaudereinigung-das-sind-die-neuen-stundenlohne-ab-1-januar-2026>
(LG descriptions also on <https://pland.app/blog/lohngruppen-in-der-gebaudereinigung> and
<https://pland.app/blog/gebaudereinigung-tariflohn-tabelle-2024>).

| LG | Tätigkeit (short) | ab 01.01.2025 | ab 01.01.2026 | stated increase |
|---|---|---|---|---|
| **LG 1** | Innen- und Unterhaltsreinigung (incl. Winterdienst) | **14,25 €** | **15,00 €** | +5,26 % |
| LG 2 | Innen-/Unterhaltsreinigung in OP-, Isolier-, Intensiv-, Dialyse-Räumen, TBC-Stationen, Isotopenlabors | 14,71 € | 15,46 € | +5,10 % |
| LG 3 | requiring an additional recognised qualification (Desinfektoren, Strahlenschutz, Gift-/Umweltschutz-Beauftragte) | 15,20 € | 15,95 € | +4,93 % |
| LG 4 | Bauschlussreinigung; Vorarbeitende Innen-/Unterhaltsreinigung | 15,91 € | 16,66 € | +4,71 % |
| LG 5 | priced but „derzeit nicht besetzt" | 16,72 € | 17,47 € | +4,49 % |
| **LG 6** | Glas- und Fassadenreinigung | **17,65 €** | **18,40 €** | +4,25 % |
| LG 7 | work requiring a ≥3-year Berufsausbildung | 18,64 € | 19,39 € | +4,02 % |
| LG 8 | Gesellen*innen with Ausbildereignungsprüfung, responsible for training | 19,67 € | 20,42 € | +3,81 % |
| LG 9 | Fachvorarbeitende Glas- und Außenreinigung | 20,89 € | 21,64 € | +3,59 % |

Pre-2025 baseline, the only two groups the sources give: **LG 1 = 13,50 €**, **LG 6 = 16,70 €**
(+11,1 % and +10,2 % over the two-year term). Sources:
<https://pland.app/blog/die-tarifloehne-im-gebaeudereiniger-handwerk-werden-angehoben>,
<https://pland.app/blog/tarifeinigung-in-der-gebaudereinigungsbranche-mindestlohn-steigt-ab-2025>.

**No Ost rate table appears anywhere in the crawl.** The 2025/2026 rate table is presented as one
nationwide grid, „bundesweit für alle gewerblich Beschäftigten", and gives no Ost rates. One page
does assert a regional differential in general terms —
<https://pland.app/blog/lohngruppen-in-der-gebaudereinigung> says „In den westlichen Bundesländern
liegen die Tariflöhne tendenziell etwas höher als im Osten" — but no Ost figures are given anywhere,
so a separate Ost grid is **not established from the sources**.

### 2.2 Allgemeinverbindlichkeit

| Date stated | Statement | Source |
|---|---|---|
| **28.01.2025** | „Der Tarifvertrag wurde am 28. Januar 2025 durch eine **Rechtsverordnung gemäß § 7 Arbeitnehmer-Entsendegesetz** für allgemeinverbindlich erklärt." | <https://pland.app/blog/tariflohn-2026-...> |
| **01.02.2025** | AVE in force; „gelten bundesweit für alle gewerblich Beschäftigten in der Gebäudereinigung, unabhängig von einer Tarifbindung" | <https://pland.app/blog/die-tarifloehne-im-gebaeudereiniger-handwerk-werden-angehoben>, <https://pland.app/blog/zeitarbeit-in-der-gebaudereinigung-2025-neue-regeln-hohere-lohne-und-wichtige-anderungen> |

The two dates are reconcilable (ordinance signed 28.01., in force 01.02.) but no source says so.
Record both; do not merge them.

Consequences stated on the sources: **all** cleaning businesses must pay at least these rates;
**foreign companies** supplying cleaning in Germany are bound; the **Finanzkontrolle Schwarzarbeit
(Zoll)** audits compliance and breaches lead to „hohen Bußgeldern" — **no amount is given**.

### 2.3 Statutory Mindestlohn and the Minijob ceiling

| Item | Value | Effective | Source |
|---|---|---|---|
| gesetzlicher Mindestlohn | 12,82 €/h | until 31.12.2025 | <https://pland.app/blog/tariflohne-in-der-gebaudereinigung-ein-blick-auf-den-rahmentarifvertrag-2023>, <https://pland.app/blog/das-neue-gpv-tarifwerk-2026> |
| gesetzlicher Mindestlohn | **13,90 €/h** | 01.01.2026 | <https://pland.app/blog/das-neue-gpv-tarifwerk-2026> |
| Minijob-Grenze | **603 €/Monat** ≈ 43 Arbeitsstunden/Monat | 2026 | same |
| Midijob / Übergangsbereich | 603,01 € – 2.000 € | 2026 | same |

The same page flags the operational consequence directly: scheduling must prevent „unbeabsichtigte
Überschreitungen der Verdienstgrenze". That is a **dispatch** requirement, not a payroll one — the
breach is created when the shift is planned.

### 2.4 What this means for the code

**Fakt (code):** the platform models wage floors as dated rows rather than constants
(`apps/contracts/models.py:57-89`) and validates a contract's hourly wage against the higher of the
general and the sector floor, **resolved at `start_date`** (`apps/contracts/models.py:206-221`).

**Fakt (data), verified by query on 2026-08-29:**

| kind | amount | valid_from | valid_to | `source_note` |
|---|---|---|---|---|
| GENERAL | 12,82 € | 2025-01-01 | 2025-12-31 | MiLoG 2025 |
| GENERAL | 13,90 € | 2026-01-01 | — | MiLoG 2026 — DE CONFIRMAT |
| GEBAEUDE | 14,25 € | 2025-01-01 | 2025-12-31 | Gebäudereinigung LG1 Innenreinigung, Mindestlohntarifvertrag 2025 |
| GEBAEUDE | **15,00 €** | 2026-01-01 | — | Lohntarifvertrag LG 1, ab 01.01.2026, allgemeinverbindlich (§ 7 AEntG) |
| Minijob | 556,00 € | 2025-01-01 | 2025-12-31 | Geringfügigkeitsgrenze 2025 |
| Minijob | 603,00 € | 2026-01-01 | — | Mindestlohn × 130/3 — DE CONFIRMAT |

These match §2.1 and §2.3 above. The 2026 rows were added by
`apps/contracts/migrations/0005_wage_floor_2026.py`, whose docstring cites the tariff page directly —
that is the pattern for every future tariff round: **a new dated row plus a `source_note`, never an
edit to an existing amount**, so a back-dated audit still resolves the rate that was actually in
force.

Two rows still carry „DE CONFIRMAT" (to be confirmed) in their `source_note`. Both are corroborated
by the crawl (§2.3) but neither has been checked against a primary text.

**Note on the offer-form warning (Fakt, code, `apps/marketplace/forms.py:51-68`):** the form resolves
`WageFloor.current(WageFloor.Kind.GEBAEUDE, earliest_start)` and **rejects** the offer with a field
error on `price_per_visit` when the implied hourly falls below it (`forms.py:62-67`,
`self.add_error`), printing the as-of date; `form.is_valid()` then fails and `views.py:166-167`
never reaches `submit_offer`, so no `Offer` row is created
(`tests/test_marketplace.py:346-355`). The code's own rationale is not a wage-law one: the comment
at `forms.py:57-59` says an implied hourly under the branch floor „e aproape sigur o durată estimată
greșit" — a mis-estimated duration, caught before it becomes an offer. The severity grading lives on
the contract side instead: the wage-floor
`ComplianceIssue` is `blocking=True` for an employment contract and `blocking=False` for a
`WERKVERTRAG` (`apps/contracts/models.py:211`, `:206-221`). Preserve that asymmetry.

---

## 3. Scheinselbstständigkeit — the criteria that decide the dispatch design

**Fakt (code):** the repository names the test explicitly and twice —
`apps/marketplace/models.py:12-13` („bifează criteriile §7 SGB IV") and
`apps/contracts/models.py:240-253`, which attaches a compliance issue to every `WERKVERTRAG`:
„Verifică independența reală a prestatorului (Gewerbe activ, clienți multipli, preț propriu) —
altfel e Scheinselbstständigkeit."

**Fakt (pland.app), what the sources actually say:** the crawled pages mention
**Sozialversicherungspflicht** as a duty when hiring staff or working with freelancers/Subunternehmer
(<https://pland.app/tutorials/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung>,
Schritt 5) and nothing more. **The term "Scheinselbstständigkeit" does not appear in the crawl, and
§7 SGB IV is never cited on any pland.app page.** The paragraph reference in this repository's code
comes from the code author, not from the crawl.

**Ungeprüft — the criteria, as commonly applied.** Not established by the crawled sources; verify
with a Fachanwalt before building any automated determination. The recurring markers are: no own
Betriebsstätte or business equipment; work performed personally rather than through own staff;
integration into the client's organisation; instruction-bound as to time, place and manner of work;
essentially one client; no own market presence, no own pricing, no entrepreneurial risk.

**The design consequence, and it is not Ungeprüft — it is already the code's stated position:**
a platform that picks the person, sets the time, sets the price and sets the method ticks every one
of those markers at once. This is why the module refuses auto-allocation
(`apps/marketplace/models.py:10-14`) and why `Invitation` is documented as „Sugestie către un
prestator, NU repartizare" (`apps/marketplace/models.py:178-181`).

### 3.1 The three defences the data model already has

| Mechanism | Effect | `file:line` |
|---|---|---|
| Provider sets their own price and duration | preserves „preț propriu" | `Offer.price_per_visit`, `estimated_minutes`, `apps/marketplace/models.py:132-135` |
| Provider decides whether to bid | preserves absence of instruction | `submit_offer` is only ever called from the provider's own view, `apps/marketplace/views.py:146-184` (call site at `:167`) |
| `LegalStatus` is an orthogonal axis to `Capability` | forces the question "under what legal form does this person work?" to be answered on the account, not implied by behaviour | `apps/accounts/enums.py:24-35` |

`LegalStatus` docstring, verbatim (**Fakt**, `apps/accounts/enums.py:25-29`): „Statutul juridic al
prestatorului în DE. Dimensiune ORTOGONALĂ față de Capability și determină cine e plătitorul legal,
cine emite factura și dacă platforma poate încasa."

### 3.2 The warnings that fire before an award

**Fakt (code, `apps/marketplace/services.py:63-97`):** `award_warnings()` returns reasons, never
blocks — with the stated rationale that the platform cannot know whether the provider registered a
Gewerbe in the meantime.

| Trigger | Warning |
|---|---|
| individual provider with `LegalStatus.UNDECLARED` | the arrangement must be either a Minijob registered by Haushaltsscheck at the Minijob-Zentrale, or self-employment with Gewerbeanmeldung — otherwise it is undeclared work |
| `LegalStatus.MINIJOB` and the client is a private household | **the client becomes the EMPLOYER** and must register the relationship with the Minijob-Zentrale (Haushaltsscheck), including accident insurance |
| request is §35a-eligible | payment must be by bank transfer against an invoice; cash is not deductible |
| `verification_level == 0` | no verification level confirmed |

The Minijob warning is the sharpest line in the whole module: it tells a household customer that
hiring through the marketplace makes them an employer. That is the honest statement of what a
"Lieferando for cleaning" actually does in a German private household.

**Ungeprüft:** the Haushaltsscheck procedure and the accident-insurance duty are not described on any
crawled pland.app page; they are the code author's domain knowledge. `apps/accounts/enums.py:32`
cites §8a SGB IV for the household Minijob.

---

## 4. Arbeitnehmerüberlassung (AÜG) — the line the platform must not cross

**Fakt (pland.app), from the BA-Merkblatt summary on
<https://pland.app/blog/zeitarbeit-in-der-gebaudereinigung-2025-neue-regeln-hohere-lohne-und-wichtige-anderungen>:**

| Rule | Content |
|---|---|
| **Erlaubnispflicht** | The Verleiher (agency) needs a valid **Erlaubnis zur Arbeitnehmerüberlassung**; the Bundesagentur für Arbeit publishes a public list |
| **Parties** | **Verleiher** = the worker's employer; **Entleiher** = the company where the worker is deployed |
| **Equal Pay** | after **9 months** of uninterrupted deployment at the same Entleiher, the worker is entitled to the same pay as a comparable permanent employee, unless a Tarifvertrag lawfully deviates |
| **Informationspflichten** | written information on Einsatzdauer, Arbeitsort, Aufgaben and essential working conditions; re-issued on every change |
| **Verbot der Kettenüberlassung** | onward lending is unlawful → Unwirksamkeit der Überlassung |
| **Rechte im Entleihbetrieb** | access to Gemeinschaftseinrichtungen; information about vacancies; equal treatment absent objective grounds |
| **Merkblatt** | BA-Merkblatt **03/2025**, 8 numbered sections; employers must hand it to their temporary workers, per this page at Vertragsabschluss |

**Fakt (code):** the repository blocks this model rather than implementing it.
`apps/contracts/models.py:11-14` documents „DETAȘARE (AÜG) — platforma angajează și «împrumută»
oamenii unității. Cere Erlaubnis de la Bundesagentur für Arbeit. **Blocat în cod până când licența
există.**" `EngagementModel.TEMP_AGENCY` exists (`models.py:27`) and `compliance_report()` emits
`ComplianceIssue(code="AUEG_LICENCE", message="Detașarea de personal necesită licență AÜG. Blocat.",
blocking=True)` (`models.py:234-239`), which `send_for_signature` filters on
(`apps/contracts/services.py:25-32`). There is also no `ContractType` that maps to
`TEMP_AGENCY` in `CONTRACT_ENGAGEMENT` (`models.py:37-42`), so the model cannot be reached from the
marketplace at all — `CONTRACT_TYPE_BY_STATUS` (`apps/marketplace/services.py:125-131`) never
produces it.

**Do not remove that block to make a feature work.** If a task requires lending staff between
accounts, the correct answer is: this needs an Erlaubnis, and until it exists the feature cannot
ship.

### 4.1 The BAG Konzernprivileg ruling

Source: <https://pland.app/blog/bag-urteil-zum-konzernprivileg-neue-massstabe-fur-die-gebaudereinigung>
(page dated 23.02.2026).

| Item | What the page states |
|---|---|
| Court | **Bundesarbeitsgericht (BAG)** |
| **Decision date** | **not stated on the source page** |
| **Aktenzeichen** | **not stated on the source page** |
| Provision at issue | **§ 1 Abs. 3 Nr. 2 AÜG** — the Konzernprivileg |
| Rule before | no permit-requiring Überlassung when employees are deployed between companies of the same group, provided the deployment is not *for the purpose of* deployment. In practice group Service-/Objektgesellschaften lent staff to operating Reinigungsgesellschaften without an Erlaubnis |
| What the BAG changed | the privilege does **not apply blanket** („nicht pauschal"). Decisive is the **tatsächliche Zweck des Arbeitsverhältnisses**. Hiring someone from the outset, or permanently, to work in another group company **is** Arbeitnehmerüberlassung — even inside a group |
| The three criteria | (1) group membership is *not* decisive; (2) whether the employer maintains an **eigene Betriebsorganisation**; (3) whether the work is performed **überwiegend für das eigene Unternehmen** |
| Consequences of getting it wrong | an **Arbeitsverhältnis zum Einsatzunternehmen** can be **fingiert**; **Bußgelder**; **sozialversicherungsrechtliche Nachforderungen**; **tarifrechtliche Konsequenzen (z. B. falsche Entgeltgruppen)** |
| Recommended action | prüfe Einsatzkonzepte; trenne die Betriebsorganisation klar (eigene Führung, **eigene Einsatzplanung**, echte Arbeitgeberfunktionen); erwäge Alternativen (erlaubte Überlassung, echte Werkverträge, Anpassung der Konzernstruktur) |

**Why this matters to a marketplace, not just to a group of companies.**

The court's second and third criteria are exactly the two things a marketplace platform takes over
from its customers. "Eigene Einsatzplanung" is named verbatim as evidence of a real employer. A
platform that runs the Einsatzplanung *for* an account is helping that account keep the criterion —
which is why `apps/planning` is scoped per `Account`
(`ShiftPlan.account`, `apps/planning/models.py:97-99`) and generates plans from *that account's own*
signed contracts (`apps/planning/services.py:58-64`). A platform that instead ran one global roster
across accounts would be assembling precisely the fact pattern the BAG penalises.

**Vorschlag — the report the ruling implies:** per employee, the share of hours worked for their own
employer account vs. for other accounts, over a period. That is computable today from
`Shift.worker`, `Shift.plan.account` and `Shift.billable_minutes`
(`apps/planning/models.py:140-178`), and would be the "überwiegend für das eigene Unternehmen" test
expressed as a number. It does not exist yet.

**Ungeprüft:** the ruling's date and Aktenzeichen. The source does not give them. Anyone shipping a
compliance feature that cites this judgment must source the citation elsewhere.

---

## 5. Handwerksrolle and who may call themselves a Gebäudereiniger

**Fakt (pland.app), all from
<https://pland.app/tutorials/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung>:**

| Statement | Content |
|---|---|
| „Bei der Gründung einer eigenen Reinigungsfirma gibt es grundsätzlich keine beruflichen Beschränkungen oder spezifische Ausbildungsvoraussetzungen." | no professional restriction to found a cleaning company |
| „…es werden keine bestimmten Qualifikationen oder einen **Meistertitel** benötigt…" | no master-craftsman title required |
| „Das Reinigungsgewerbe gehört zum **zulassungsfreien Handwerk**…" | licence-free craft, „keine formellen Qualitätsanforderungen" |
| „…der Beruf des **Gebäudereinigers** erfordert eine Ausbildung und die Bezeichnung «Gebäudereiniger» ist **geschützt**." | the *job title* is protected and requires completed vocational training |
| „…während die Erbringung von Gebäudereinigungsdienstleistungen im Allgemeinen von jedem angeboten werden kann…" | providing the *service* is open to anyone |

**Explicitly absent from all 25 crawled tutorial pages:** Handwerksrolle, Handwerkskammer (HWK),
IHK, Anlage A / Anlage B / Anlage B1 of the Handwerksordnung, BG BAU by name, Meisterpflicht
paragraph references. Verified by grepping the whole 237-page crawl on 2026-08-29: „Handwerksrolle"
appears nowhere at all, and „Handwerkskammer" appears exactly once — as an anecdote about the
Handwerkskammer Bremen praising a customer's degree of digitalisation
(<https://pland.app/erfolgsgeschichten/gebaudereinigung-oelfke-gmbh>), never as a registration duty.

**Fakt (pland.app), the founding checklist actually given** on
<https://pland.app/tutorials/welche-rechtlichen-aspekte-muss-ich-bei-der-grundung-einer-reinigungsfirma-beachten>:
Gewerbeanmeldung at the Gewerbeamt (incl. applying for a Gewerbeerlaubnis); Rechtsformwahl
(Einzelunternehmen / GmbH / UG); Handelsregistereintrag for some forms; registration with the
Finanzamt (Umsatzsteuer, Gewerbesteuer); insurance (Betriebshaftpflicht, „ggf."
Berufsgenossenschaft); Arbeitsrecht (Anmeldung von Mitarbeitern, Arbeitsverträge, Arbeitszeiten,
Arbeitsschutz); DSGVO. **No statute paragraph is cited anywhere except DSGVO.**

**Internal contradiction in the source, worth knowing:** one page says the trade is licence-free with
no formal quality requirements; the legal page tells you to apply for a „Gewerbeerlaubnis". Which
permit, from whom, is never said.

**Ungeprüft — the position the crawl omits.** In the Handwerksordnung, *Gebäudereiniger* is a listed
craft; it moved from Anlage A (zulassungspflichtig, Meisterpflicht) to **Anlage B1**
(zulassungsfrei) in 2004 and was not among the trades returned to Anlage A in the 2020 reform. The
trade is therefore currently zulassungsfrei — but the business must still be **registered in the
Handwerksrolle at the Handwerkskammer**, which for an Anlage-B trade is a notification duty, not a
qualification hurdle. Chamber membership is compulsory. Also Ungeprüft and also omitted by the
crawl: **BG BAU** is the competent statutory accident insurer for this trade.

**Fakt (code):** the repository already carries the field this implies —
`CompanyProfile.hwk_registered` with the comment „Curățenia de clădiri e Anlage B1 HwO — fără
Meisterpflicht, dar cu înregistrare la Handwerkskammer" (`apps/accounts/profiles.py:52-54`), and it
feeds the scoring: +0.2 on the company experience score (`apps/marketplace/scoring.py:131-132`).

**Vorschlag.** The verification ladder for a provider account should mirror this reality:

| `VerificationLevel` | Today | Should also mean, for a COMPANY provider |
|---|---|---|
| 0 NONE | nothing | — |
| 1 EMAIL | email confirmed | — |
| 2 PHONE | phone confirmed | — |
| 3 DOCUMENTS | „documente verificate" (`apps/accounts/enums.py:50`) | Gewerbeanmeldung **or** Handelsregisterauszug + Handwerksrolle/HWK confirmation + valid Betriebshaftpflicht policy |

`VerificationDocument.doc_type` already has GEWERBE, HRB, INSURANCE, QUALIFICATION and
POLIZEILICHES (`apps/accounts/compliance.py:7-13`) — the ladder needs a rule that maps document sets
to levels, which does not exist.

**Note on `_verification_score`:** it divides `verification_level` by 3
(`apps/marketplace/scoring.py:101-102`) and is worth **0.25 of the total score** — a quarter of the
ranking rests on a field that no automated process currently sets.

---

## 6. Working-time duties follow the employer, and the planner already encodes them

**Fakt (code), `apps/planning/services.py:9-15, 27-29, 82-95`.** The weekly plan generator treats
four rules as hard constraints and refuses to place a visit rather than break one:

| Constraint | Value | Cited in code as |
|---|---|---|
| contracted hours budget | from the signed `ContractDraft.hours_per_month` | „plafon legal, nu preferință" |
| max daily working time | 480 min | §3 ArbZG (with the note „10 h doar cu compensare în 6 luni") |
| min rest between shifts | 11 h | §5 ArbZG |
| Sunday free | weekday 7 excluded | §9 ArbZG |
| worker serves the site's locality | `ServiceArea` | — |

Unplaceable visits are recorded with their reason in `ShiftPlan.unmet_demand`
(`apps/planning/models.py:102-103`, `apps/planning/services.py:133-141`). That is the correct shape:
a dispatcher that "almost" respects a legal ceiling produces a legal breach, so it must fail loudly.

**Fakt (code):** time recording is modelled as append-only. `ShiftEvent.save()` raises on any update
(`apps/planning/models.py:217-220`), and the model comment cites **BAG 13.09.2022 (1 ABR 22/21)** and
**§3 Abs. 2 Nr. 1 ArbSchG** for the duty to record *all* working time, with retention „minimum 2 ani
(§16 ArbZG)" (`apps/planning/models.py:154-156`; also `apps/planning/attendance.py:8-11` and
`apps/dashboard/panels.py:72`).

**Partly Ungeprüft — the legal content behind those citations.** Verified by grepping the full crawl
on 2026-08-29: **no** pland.app page cites §16 ArbZG, §17 MiLoG or the ECJ *CCOO* judgment
(C-55/18) — the EuGH ruling is referred to only generically, never by case number.
**§ 3 Abs. 2 Nr. 1 ArbSchG and the underlying BAG time-recording ruling ARE in the crawl**, quoted
verbatim (with the Aktenzeichen written „1ABR 22/21") on
<https://pland.app/blog/stundenzettel-vorlage-fuer-gebaeudereinigungen-kostenlos-herunterladen>:
„Der Arbeitgeber ist nach § 3 Abs. 2 Nr. 1 ArbSchG verpflichtet, ein System einzuführen, mit dem die
von den Arbeitnehmern geleistete Arbeitszeit erfasst werden kann." That corroborates
`apps/planning/models.py:154-156` for the ArbSchG half. Only the §16 ArbZG retention period, §17
MiLoG and the *CCOO* case number remain **Ungeprüft**. Otherwise the pages assert only that „digitale
Zeiterfassung" is a duty in this trade and otherwise name the Arbeitszeitgesetz generically
(<https://pland.app/blog/digitale-zeiterfassung-eine-pflicht-in-der-gebaudereinigung>,
<https://pland.app/blog/digitale-lohnabrechnung-ein-blick-auf-die-vorteile-in-der-gebaudereinigung>).
The single paragraph-level ArbZG citation anywhere in the crawl is **§ 3 Satz 1 Arbeitszeitgesetz**,
quoted on <https://pland.app/arbeitslexikon/erschwerniszuschlaege> as the 8-hours-per-day reference
point for an Erschwerniszuschlag — which does corroborate the planner's `MAX_DAILY_MINUTES = 480`
(`apps/planning/services.py:27`), though the planner cites it independently.
The remaining paragraph references (§16 ArbZG, §17 MiLoG) are the code author's and this dossier's
addition. Also **Ungeprüft** and
specific to this trade: the **Sofortmeldepflicht (§28a Abs. 4 SGB IV)** — a new employee in the
Gebäudereinigung must be reported to social insurance on the first day of work at the latest — and
the **Mitführungspflicht von Ausweispapieren (§2a SchwarzArbG)**. Both are onboarding-deadline
features with no equivalent in the code today.

**The dispatch consequence.** These duties attach to the **employer**, and the employer is the
account that holds the contract — not the platform. Every one of them therefore only makes sense
after `apps.contracts` exists. That is the fourth independent reason contracts precede the
marketplace, alongside §7 SGB IV, the AÜG and the Minijob ceiling.

---

## 7. Zeitarbeit rates — reference only, do not implement

If a task ever proposes an AÜG model, these are the numbers the sources give, so a design can be
costed before it is rejected.

**Entgeltgruppen ab 01.03.2025**, fixed to 30.09.2025, for tarifgebundene Zeitarbeitsunternehmen.
Source: <https://pland.app/blog/zeitarbeit-in-der-gebaudereinigung-2025-neue-regeln-hohere-lohne-und-wichtige-anderungen>

| EG | vorher | ab 01.03.2025 | | EG | vorher | ab 01.03.2025 |
|---|---|---|---|---|---|---|
| 1 | 14,00 € | **14,53 €** | | 5 | 18,51 € | **19,21 €** |
| 2a | 14,31 € | **14,85 €** | | 6 | 20,55 € | **21,33 €** |
| 2b | 14,67 € | **15,23 €** | | 7 | 23,91 € | **24,82 €** |
| 3 | 15,62 € | **16,21 €** | | 8 | 25,60 € | **26,57 €** |
| 4 | 16,51 € | **17,14 €** | | 9 | 26,85 € | **27,87 €** |

The **GVP-Tarifwerk** (Gesamtverband der Personaldienstleister) replaces the previous **BAP** and
**iGZ** agreements from 2026 and has four components — Manteltarifvertrag,
Entgeltrahmentarifvertrag, Entgelttarifvertrag, Branchenzuschlagstarifverträge. A new
Entgelttarifvertrag has applied since 01.10.2025 with three increases: **+2,99 % on 01.01.2026** and
**+2,5 % on 01.09.2026**; EG 1 rises to **14,96 €** in 2026. The value of the 01.10.2025 step is
**not stated**. Source: <https://pland.app/blog/das-neue-gpv-tarifwerk-2026>.
Note the source's own spelling inconsistency: the H1 says „GPV", the body says „GVP"; GVP matches
the expanded name.

**Design note (Vorschlag):** if AÜG is ever built, `Ueberlassung` needs an `equal_pay_faellig_ab`
computed from 9 uninterrupted months at the same Entleiher, and the Kettenüberlassung ban must be a
database constraint — an Entleiher may never itself be a Verleiher for the same worker.

---

## 8. Checklist for reviewing any marketplace/dispatch change

1. Does any code path assign work to a named natural person without a signed `ContractDraft`?
   → §7 SGB IV / AÜG risk. Reject.
2. Does any price validation or wage check use a literal number, or resolve the floor at "now"
   instead of at the date the work starts? → reject. The two correct patterns are
   `apps/marketplace/forms.py:51-68` (blocking field error, resolved at `earliest_start`) and
   `apps/contracts/models.py:206-221` (typed issue, blocking only for employment, at `start_date`).
3. Does a scheduling change let a Minijob worker's projected monthly gross exceed
   `MinijobThreshold.current(date)`? → the breach is created at planning time, not at payroll time.
4. Does the change let one account's roster span another account's workers?
   → BAG Konzernprivileg fact pattern. Reject.
5. Does the change remove or weaken `EngagementModel.TEMP_AGENCY` being blocked
   (`apps/contracts/models.py:234-239`)? → reject unless an Erlaubnis exists.
6. Does the change expose a client's address to a provider who has not *won*?
   → `apps/accounts/visibility.py:106-112` allows only `status="WON"`. Reject.
7. Does the change touch a §35a-eligible category? → the deduction requires an invoice and a bank
   transfer (`apps/marketplace/services.py:87-91`); a flow that ends in cash makes the platform's
   own promise false.

---

## Quellen

pland.app (crawled 2026-08-29):

- <https://pland.app/blog/tariflohn-2026-in-der-gebaudereinigung-das-sind-die-neuen-stundenlohne-ab-1-januar-2026>
- <https://pland.app/blog/die-tarifloehne-im-gebaeudereiniger-handwerk-werden-angehoben>
- <https://pland.app/blog/tarifeinigung-in-der-gebaudereinigungsbranche-mindestlohn-steigt-ab-2025>
- <https://pland.app/blog/lohngruppen-in-der-gebaudereinigung>
- <https://pland.app/blog/gebaudereinigung-tariflohn-tabelle-2024>
- <https://pland.app/blog/tariflohne-in-der-gebaudereinigung-ein-blick-auf-den-rahmentarifvertrag-2023>
- <https://pland.app/blog/das-neue-gpv-tarifwerk-2026>
- <https://pland.app/blog/zeitarbeit-in-der-gebaudereinigung-2025-neue-regeln-hohere-lohne-und-wichtige-anderungen>
- <https://pland.app/blog/bag-urteil-zum-konzernprivileg-neue-massstabe-fur-die-gebaudereinigung>
- <https://pland.app/blog/digitale-lohnabrechnung-ein-blick-auf-die-vorteile-in-der-gebaudereinigung>
- <https://pland.app/blog/digitale-zeiterfassung-eine-pflicht-in-der-gebaudereinigung>
- <https://pland.app/blog/stundenzettel-vorlage-fuer-gebaeudereinigungen-kostenlos-herunterladen>
- <https://pland.app/tutorials/wie-grunde-ich-eine-reinigungsfirma-eine-schritt-fur-schritt-anleitung>
- <https://pland.app/tutorials/welche-rechtlichen-aspekte-muss-ich-bei-der-grundung-einer-reinigungsfirma-beachten>

Repository (read 2026-08-29, `/Users/Geronimo/Projects/Cleaning_SaaS`):

- `apps/marketplace/models.py`, `scoring.py`, `services.py`, `views.py`, `forms.py`
- `apps/contracts/models.py`, `services.py`, `migrations/0002_seed_wage_floors.py`
- `apps/planning/models.py`, `services.py`, `attendance.py`
- `apps/accounts/enums.py`, `profiles.py`, `compliance.py`, `visibility.py`
- `apps/dashboard/panels.py`
- `PLAN-FAZA-0.md`

Dossiers: `scratchpad/knowledge/blog-tarif-arbeitsrecht.md`,
`scratchpad/knowledge/tutorials-gruendung.md`, `scratchpad/dossier/_verified-ground-truth.md`.
