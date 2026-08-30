# Das inline-Prinzip — die Genossenschaft in voller Länge

Source cluster: https://inline-kurier.de/uber-uns (one long page; the sub-URLs
`/inline-prinzip-1-a-und-o`, `/unternehmen`, `/inline-historie`, `/flotte` are **anchor views of
that same page with identical body copy** — do not expect four documents; `/flotte` additionally
leaks an internal editor/test navigation block („Testfälle", „Sidekicks:", „Admin:", „Testseiten:")
that the other three do not carry, so they are *not* byte-identical), plus
https://inline-kurier.de/impressum and https://inline-kurier.de/datenschutz.
Crawled 2026-08-29.

**Legal note, stated once for this whole file:** everything below about §7 SGB IV, AÜG, GenG, AEntG
and §613a BGB is **reference material for building software, not legal advice**. A Fachanwalt
decides the real case.

Markers: **Fakt** (sourced) · **Vorschlag** (design proposal) · **Ungeprüft** (domain knowledge the
sources do not cover).

---

## 1. What the members actually co-decide

**Fakt**, https://inline-kurier.de/uber-uns, verbatim:

> „Unser Leitspruch lautet ‚Von Fahrern für Fahrer!'. Wir sind als selbstständige Kuriere in einer
> Genossenschaft organisiert. Das bedeutet echte Mitbestimmung, wie zum Beispiel bei der
> Preisgestaltung, der Funk- und Tourenvermittlung sowie der jährlichen Budgetplanung."

Section heading of that block: **„Die wirtschaftliche Selbstständigkeit aller inline Kuriere"**.

Restated in the history section of the same page (**Fakt**):

> „Als selbstständige Fahrer – damals noch im Verein organisiert, heute als Genossenschaft – sind
> wir bei allen wichtigen Entscheidungen mit beteiligt. Wir entscheiden über Preise, das jährliche
> Budget oder **Details in der Funk- und Tourenvermittlung**."

The three co-decision matters — this is the exportable list:

| German | What it actually governs | Cleaning translation |
|---|---|---|
| **Preisgestaltung** | The published tariff the members are paid out of | The Leistungskatalog / minimum Objektstundenverrechnungssatz — **above** the statutory floor only |
| **Funk- und Tourenvermittlung** | The **rules of the dispatch algorithm** — who gets offered which job | The matching/scoring rules: weights for price, verification, proximity, continuity, fairness rotation |
| **jährliche Budgetplanung** | The central office's cost base | The platform budget → the take rate / Mitgliedsbeitrag follows from it |

**The load-bearing nuance.** The second list says *Details in der* Vermittlung. Members author the
**rules**; a Disponent executes each **individual** allocation in real time. Legitimacy comes from
co-decision over the rulebook, not over the jobs. That split is what removes the "the platform
dictates my price and my work" objection at the level where it is legally dangerous, while keeping
second-by-second dispatch centralised.

Claimed cultural effect (**Fakt** that it is claimed; marketing, not a verifiable fact):
„eine Unternehmenskultur, die auf Motivation, Transparenz und persönlicher Verantwortung basiert".

---

## 2. Verein e.V. → eG: the transition, and that it is unfinished

All rows **Fakt**, https://inline-kurier.de/uber-uns.

| Fact | Verbatim |
|---|---|
| Origin | „Was vor über 25 Jahren als Verein engagierter Kuriere begann, wird heute als moderne Genossenschaft fortgeführt." |
| Predecessor | **iKV inline Kurier Verein e.V.** |
| Successor | **inline Kurier eG** — „ist die neue organisatorische Basis der inline Unternehmensgruppe und folgt auf den bisherigen iKV inline Kurier Verein e.V." |
| Date | „Im **Herbst 2025** ist es dann nach langer Vorbereitungszeit endlich so weit – wir werden zur Genossenschaft." |
| Purpose | „Mit der Gründung der eingetragenen Genossenschaft wurde die langjährige Zusammenarbeit **selbständiger Kurierunternehmer** auf eine zukunftssichere, wirtschaftlich stabile Grundlage gestellt." |
| Membership definition | „In der inline Kurier eG sind **wirtschaftlich unabhängig arbeitende Kurierunternehmer** zusammengeschlossen, die gemeinsam faire, nachhaltige und effiziente Transportlösungen bieten." |
| Migration mode | „Die eG übernimmt **schrittweise** die Funktionen der bisherigen inline Kurierdienst GmbH, die eine 100%ige Tochtergesellschaft der eG ist und weiterhin als **Beteiligungsgesellschaft** bestehen wird." |
| Overnight | „Im Zuge der neuen Unternehmensstruktur wird auch die Overnight GmbH **perspektivisch** in die Genossenschaft integriert." |

**So the transition is explicitly incomplete.** The eG is the new top entity; the GmbH survives, in
the site's own word, as a **Beteiligungsgesellschaft** holding the two subsidiary GmbHs; functions
move over step by step. **No completion date is published.** (*Inferenz*, not stated: keeping the
GmbH is what makes a 70 % stake in a non-member firm like XXL possible.)

**Vorschlag for Cleaning_SaaS:** do not model "the eG" as a single flag on the platform. Model the
two layers separately from day one — a governance entity that ratifies rules, and a contracting
entity that signs and invoices — because the migration between them is a multi-year process even in
the source case.

---

## 3. The corporate tree — every published register fact

**Fakt**, https://inline-kurier.de/uber-uns (entity blocks) and https://inline-kurier.de/impressum.

```
                       inline Kurier eG
                  (GnR 1186, AG Hamburg)
                  Sachsenstraße 5-7, 20097 Hamburg
                              |
                              | 100 %
                              v
                   inline Kurierdienst GmbH
                  (HRB 65662, AG Hamburg)
                  Sachsenstraße 5-7, 20097 Hamburg
                              |
                 +------------+-------------+
          100 %  |                          |  70 %
                 v                          v
   inline Overnight Übernacht-      inline XXL Express GmbH
   versand GmbH                     (HRB 82410, AG Hamburg)
   (HRB 71160, AG Hamburg)          Kolenbeekstieg 1, 21435 Stelle
   Sachsenstraße 7, 20097 Hamburg
```

| Entity | Address | Register | Shareholding | Named officers | Phone / Fax |
|---|---|---|---|---|---|
| **inline Kurier eG** | Sachsenstraße 5-7, 20097 Hamburg | AG Hamburg, **GnR 1186** | top entity | Vorstand: **Stefan Hübl, Jan Schulte, Malte Sprie von Staden**; Aufsichtsrat: **Gunnar Gottschalk (Vorsitzender)** | Tel. +49 40 23 500 500 |
| **inline Kurierdienst GmbH** | Sachsenstraße 5-7, 20097 Hamburg | AG Hamburg, **HRB 65662** | **100 % of the eG**, continues as Beteiligungsgesellschaft | Geschäftsführung: **Stefan Hübl** | — |
| **inline Overnight Übernachtversand GmbH** | Sachsenstraße 7, 20097 Hamburg | AG Hamburg, **HRB 71160** | **100 % of inline Kurierdienst GmbH** | GF: **Jasmin Schlömer, André Gottschalk**; Vertrieb: **Mathias Tramper**; Buchhaltung: **Janna Kröger** | Tel. +49 40 23 500 600, Fax +49 40 23 500 606 |
| **inline XXL Express GmbH** | Kolenbeekstieg 1, 21435 Stelle | AG Hamburg, **HRB 82410** | **70 % of inline Kurierdienst GmbH** | GF: **Peter Pohl, Oliver Pohl**; Vertrieb: **Mario Krökel**; Buchhaltung: **Janna Kröger** | Tel. +49 40 23 500 400, Fax +49 40 23 500 444 |

Notes on the tree (all **Fakt** unless marked):

- **The remaining 30 % of inline XXL Express GmbH is not disclosed.** The site states nothing. Do
  not assume.
- **Personnel overlap:** Stefan Hübl is simultaneously eG-**Vorstand** and **Geschäftsführer** of
  the 100 %-owned GmbH.
- Gunnar **Gottschalk** chairs the eG's Aufsichtsrat; André **Gottschalk** is a GF of Overnight. The
  site states no relationship. (**Ungeprüft** whether one exists — do not speculate in code or copy.)
- The Datenschutzerklärung names **all four entities jointly** as „Verantwortlicher" at
  Sachsenstraße 5–7 (**Fakt**, https://inline-kurier.de/datenschutz) — one controller block, but
  **no Art. 26 DSGVO joint-controllership agreement is disclosed**.

### Cooperative-law apparatus (**Fakt**, /impressum)

| Item | Value |
|---|---|
| Legal basis of the imprint | „Informationen gemäß **§ 5 Digitale-Dienste-Gesetz**" |
| Genossenschaftsregister | Amtsgericht Hamburg, **GnR 1186** |
| **Prüfverband** (statutory, §§ 53 ff. GenG) | **Prüfungsverband der Deutschen Verkehrs-, Dienstleistungs- und Konsumgenossenschaften e.V., Gotenstraße 17, 20097 Hamburg** |
| Datenschutzbeauftragter | **Jochen Maaß**, c/o inline Kurier eG, datenschutz@inline-kurier.de (source: /datenschutz) |

**No USt-IdNr is published** anywhere in the 36-page corpus (grep-verified: zero hits for `USt`,
`Umsatzsteuer`, `Steuernummer`, `DE[0-9]`) — a visible gap for a company that prints
„zzgl. gesetzlicher MwSt.". Also absent: § 18 Abs. 2 MStV editorial contact, § 36 VSBG dispute-
resolution statement, OS-platform link, GüKG licence/authority.
**Do not copy these omissions.** For B2C cleaning the VSBG statement is not optional.

---

## 4. Headcount and fleet

All **Fakt**, https://inline-kurier.de/uber-uns.

| Figure | Value |
|---|---|
| Couriers today | **130 Kuriere** („Mit 130 Kurieren im Großraum Hamburg") |
| Motorised | **90** — „90 motorisierte PKW-, Kombi- und Transporterfahrer" |
| Bikes | **40** — „40 Bikes bzw. Cargobikes" / „40 Fahrradkuriere" |
| Founding headcount 1997 | **90 Kuriere** |
| Historic peak | **250 Kuriere**, **bis zu 2500 Aufträgen pro Tag**, „sind wir Marktführer" |
| Response-time claim | „In der Regel sind wir innerhalb weniger Minuten bei Ihnen" (About page) vs. „in der Regel innerhalb von **30 bis 60 Minuten** abholen" (homepage FAQ) |

Treat „innerhalb weniger Minuten" as marketing — the two statements are not identical and the site
never reconciles them.

**Crucially: the site never states how many of the 130 are eG members.** Employed drivers,
non-member subcontractors and members are not distinguished anywhere in the corpus. **Ungeprüft.**

---

## 5. „Von Fahrern für Fahrer!" — the founding logic

**Fakt**, /uber-uns:

> „Nach schlechten Erfahrungen mit anderen **Kurierzentralen** entsteht 1997 der Wunsch, etwas
> Eigenes auf die Beine zu stellen und **bessere Bedingungen für Fahrerinnen und Fahrer** zu
> schaffen."

and the name itself: „der Name inline entsteht aus dem Gedanken heraus, dass Touren immer ‚in line'
und direkt gefahren werden, mit größtmöglicher Optimierung für Kunden und Kuriere."

The eG is the institutional form of a grievance against dispatch centres. Dated timeline (**Fakt**):
1997 founding with 90 couriers · late 1990s boom via Agenturen und Verlage · 2000 inline Overnight
founded, expansion to Berlin · peak 250 couriers / 2500 orders per day · early-2000s Neuer-Markt
collapse · 2008 Weltwirtschaftskrise · 2010 Umweltkurier-Siegel der Hansestadt · 2011 first Hamburg
courier firm with Cargobikes · Corona-Pandemie, response includes the new product „Dokumentierte
Zustellung" · 2024 ClimatePartner accounting begins · **Herbst 2025 conversion to the
Genossenschaft**.

**The positioning transfer, and it lands harder here.** „Von Reinigern für Reiniger" reacts to the
Gebäudereinigung's own notorious pain — Kettenvergabe (subcontracting chains), wage dumping,
unpaid travel time. **Ungeprüft** as a market claim (the crawled corpus is a courier site and
establishes nothing about the cleaning industry) but structurally the same story.

---

## 6. What a Reinigungs-eG must replicate for the model to hold

All **Vorschlag** unless a repo `file:line` or a source URL is given.

### 6.1 Membership: firms, not individuals

**This is the one non-negotiable adaptation.** inline can carry „selbständiger Kurier" because each
job is short, discrete, and executed with the courier's **own vehicle** — a genuine Betriebsmittel.
A cleaner with a platform-issued key, a platform-issued schedule and platform-issued detergents has
no equivalent capital and no meaningful entrepreneurial freedom; that is
**Scheinselbstständigkeit (§ 7 SGB IV)**, and if the cleaner works under the customer's direction it
is **Arbeitnehmerüberlassung** requiring an AÜG-Erlaubnis from the Bundesagentur für Arbeit. The
repo already refuses the individual-brokerage construction in code
(`apps/marketplace/models.py:10-14`, **Fakt**).

So: **membership is held by a Betrieb with its own employees.** In repo terms
(`apps/accounts/enums.py:4-8`, **Fakt**) that means `EntityType.COMPANY`, and — because
Gebäudereinigung is a registered trade — `CompanyProfile.hwk_registered`
(`apps/accounts/profiles.py:54`, **Fakt**) becomes an admission requirement, not a badge.

A `Capability.WORKER` account (a natural person, `apps/accounts/enums.py:17`) may be a **provider on
the marketplace** and an **employee of a member Betrieb** — but must never be an eG member in the
governance sense. Enforce it with a constraint, not a convention.

### 6.2 Co-determination on prices

Members vote the **platform tariff**; the **floor is not votable.** The allgemeinverbindlicher
Mindestlohntarifvertrag Gebäudereinigung (§ 7 AEntG) binds non-tarifgebundene firms too, so:

- `contracts.WageFloor` = law. Effective-dated rows (`apps/contracts/models.py:57-89`, **Fakt**),
  immutable by any vote, resolved **at the date the work starts** — the pattern is already in
  `apps/marketplace/forms.py:51-68` (**Fakt**).
- `PlatformTariff` (**Vorschlag**) = member-governed. Validated against `WageFloor` at the shift
  date; a resolution that would put it below the floor is rejected at save time.

Do not put euro amounts in this skill or in code. → `gr-tarif-und-lohn`.

### 6.3 Co-determination on allocation rules

This is the killer feature: it converts an opaque algorithm into a **ratified rulebook**.

**Fakt (repo).** Today the weights are module constants:
`WEIGHTS = {price 0.30, verification 0.25, experience 0.20, availability 0.15, proximity 0.10}`
(`apps/marketplace/scoring.py:22-28`), with a deliberate comment explaining why price was reduced
from 0.35. `score_offers` normalises inside one request's offer set and returns a per-criterion
breakdown (`scoring.py:58-91`) — the transparency half is already there.

**Vorschlag.** A `DispatchPolicy` row carrying: the weight vector, `valid_from` / `valid_to`, the
resolution reference (Generalversammlung date + item), and a free-text rationale. `score_offers`
resolves the policy effective at `request.published_at`, stores the resolved policy id on the
`Invitation.reasons` JSON (`apps/marketplace/models.py:190`, **Fakt** that the field exists), and
the UI shows "scored under policy v3, adopted 12.03.2026". Requirements this imposes:

1. Weights become **data**, never constants.
2. Re-scoring an old request must reproduce the old ranking → resolve by date, never by "now".
3. A member must be able to read the policy that ranked them last.

### 6.4 Profit participation and the budget

**Fakt (negative).** inline publishes **no commission, no take rate, no Mitgliedsbeitrag figure**,
despite saying members decide pricing and the budget. This is the single number a Cleaning_SaaS
business model most needs and it is absent from the source.

**Vorschlag.** Model it explicitly rather than inheriting the silence: an annual `Budget` the
members ratify, a `FeeSchedule` derived from it (Mitgliedsbeitrag + transaction fee), and a
published per-order breakdown. The honest answer to "why is your commission X %" is "because the
members set the budget" — which only works if the budget is visible.

**Fakt.** eG membership in a **Prüfungsverband is compulsory** (§§ 53 ff. GenG; inline names its
own, see §3). It is a recurring cost that belongs in the budget the members vote on. Do not treat
it as optional.

### 6.5 Suggestion vs. instruction — the line, in code terms

| | Suggestion (lawful brokerage) | Instruction (the thing to avoid) |
|---|---|---|
| Vocabulary | **Vermittlung**, Angebot, Einladung | Zuweisung, Zuteilung, "assigned to you" |
| Who acts last | The **provider** decides to bid; the **client** awards | The platform decides |
| Refusal | Free, unlimited, no consequence | Penalised, or reduces future ranking |
| Price | Provider-set per `Offer` | Platform-set, take it or leave it |
| Repo evidence | `Invitation` docstring „Sugestie, NU repartizare" (`apps/marketplace/models.py:177-181`), `suggest_providers` returns a ranked list (`scoring.py:160-190`), `award_offer` requires `request.client_id == actor.pk` (`services.py:100-119`) — all **Fakt** | none exists, and none may be added |

**A rule that follows and is easy to get wrong:** a *fairness rotation* term in the scoring (a
member who has not had work recently ranks higher) is fine as a **suggestion** weight. The same
term becomes an instruction the moment refusing the suggestion lowers the member's future score.
Ranking-by-refusal is a §7 SGB IV Weisungsrecht indicator wearing an algorithm's clothes.
**Ungeprüft** as to how a court would read it — which is exactly why it should not be built without
advice.

### 6.6 What else transfers cleanly

| inline element | Reinigungs-eG | Verdict |
|---|---|---|
| Two legal layers — **Fakt** only as ownership (eG owns 100 % of the GmbH, which „weiterhin als Beteiligungsgesellschaft bestehen wird"); *who signs the customer contract and bears the risk is nowhere published* (**Ungeprüft**; the Impressum names the eG as Diensteanbieter, the Datenschutzerklärung names all four entities as one Verantwortlicher, and the AAB PDF was not crawled) | A governance entity plus a contracting entity, kept separate from day one | **holds as a design**, not as a documented inline fact — still the most valuable single import |
| Product lines as separate legal entities (Overnight GmbH, XXL GmbH, own GF, own intake number, own T&C regime) | Separate entities per service line — but split by **licensing** (a Personalgestellung entity needs an AÜG-Erlaubnis and must be legally separate), not by vehicle capability | **needs adaptation** |
| 70 % stake in a specialist with founders retaining a minority | Buy in Glas-/Fassadenreinigung with rope access, or Desinfektion | **holds** |
| **Fahrerbetreuung as its own phone line**, +49 40 23 500 555, separate from Kundenbetreuung 500 (**Fakt**, /uber-uns) | A dedicated Mitglieder-/Reinigerbetreuung channel | **holds.** Cheap to copy, high signal: the supply side gets its own door |
| Licence used as a trust asset („lizensierter Postdienstleister", „Wir wahren das Postgeheimnis") — but **the licence number is not published** | Verschwiegenheitsverpflichtung, Art. 28 DSGVO AV-Vertrag for Objekte with personal data, Hygiene-/RKI-Nachweise, Handwerksrolle/Meisterbetrieb, PQ-VOB for public tenders | **needs adaptation** — keep the pattern, store the number and expiry as fields and surface them. Do better than the source |
| Sustainability with a **funding line in the tariff**: „0,7% als CO2-Ausgleichszahlung je Rechnung" on motorised orders, ClimatePartner since 2024 (**Fakt**, /kurierfahrten, /uber-uns) | An earmarked Ökologie-/Materialbeitrag funding EU-Ecolabel products, Dosieranlagen, e-Fahrzeuge | **holds** — the transferable idea is the funding line and the named external auditor with a start year, not the offsetting |

Careful reading required on one figure: „Im Jahr 2024 haben **diese Projekte** dazu beigetragen,
rund **500 Tonnen CO2** zu vermeiden" — that is what the *supported projects* achieved, **not**
inline's own footprint, which is not published. Do not restate it as "inline offset 500 t".

---

## 7. What remains open

Published on inline-kurier.de: **nothing** on any of these. Do not invent.

1. **No Satzung, no Genossenschaftsanteil amount, no Eintrittsgeld, no membership count, no
   Generalversammlung procedure.** How a member joins, what a share costs, quorum rules,
   one-member-one-vote vs. weighted — none of it.
2. **No commission, take rate or Mitgliedsbeitrag figure.**
3. **No membership contract terms** — exclusivity, minimum availability, dispatch obligation,
   penalties for refusing a tour, notice period. This is precisely the layer that decides whether
   the arrangement is brokerage or employment, and it is the layer the site hides.
4. **How many of the 130 couriers are members?** Never stated.
5. **No compensation model for the operators.** How the self-employed couriers are paid, what share
   they keep, how allocation priority works: not answerable from this corpus. Only the *customer*
   side of the tariff is public.
6. **No postal-service licence number or issuing authority**, despite the licence claim.
7. **The remaining 30 % of XXL is undisclosed.**
8. **No completion date for the eG migration** — „schrittweise" and „perspektivisch", both
   open-ended.
9. **No Aufsichtsrat beyond the chairman.**
10. **No employee count** distinct from the courier count. Disponenten, Buchhaltung and Vertrieb are
    named as roles and people but never counted.
11. **No self-service portal for the operators.** `robots.txt` lists `/registrieren/`, `/login/`,
    `/konto/`, `/dashboard/` — all customer-facing; there is no `/fahrer/`, `/kurier/`, `/mitglied/`
    or `/disposition/` path (**Fakt** that these paths were reported; the robots.txt itself was not
    in the crawled corpus, so this is second-hand). *Inferenz:* dispatch runs over Funk and
    telephone. For Cleaning_SaaS this is the most striking non-transferability — **inline has no
    member-facing application, even though the members are the owners.** Building one is the
    product opportunity, not a copy of the source.
12. **The Datenschutzerklärung never mentions the operator side at all** (**Fakt**, /datenschutz).
    For a cleaning platform that is untenable: employee data (Arbeitszeiten per § 17 MiLoG,
    Lohngruppe, Krankmeldungen, Sozialversicherungsnummer, Führungszeugnis for sensitive Objekte)
    needs its own Art. 13 DSGVO / § 26 BDSG information. Do not copy the gap.

---

## Quellen

- https://inline-kurier.de/uber-uns — Genossenschaft, Mitbestimmung, fleet 130/90/40, corporate tree
  with GnR 1186 / HRB 65662 / HRB 71160 / HRB 82410, all named officers, history 1997–Herbst 2025,
  Postdienstleister claim, Umweltkurier-Siegel 2010, ClimatePartner 2024 / 500 t, Fahrerbetreuung
  +49 40 23 500 555, seven capacity classes.
  Identical anchor views: /uber-uns/inline-prinzip-1-a-und-o · /uber-uns/unternehmen ·
  /uber-uns/inline-historie · /uber-uns/flotte.
- https://inline-kurier.de/impressum — § 5 DDG data, Vorstand, Aufsichtsrat,
  Genossenschaftsregister AG Hamburg GnR 1186, Prüfungsverband.
- https://inline-kurier.de/datenschutz — four entities as one Verantwortlicher block,
  Datenschutzbeauftragter Jochen Maaß, Stand Oktober 2025, own servers in Germany.
- https://inline-kurier.de/kurierfahrten — „0,7% als CO2-Ausgleichszahlung je Rechnung".
- https://inline-kurier.de/ — pickup „in der Regel innerhalb von 30 bis 60 Minuten".
- Repo: `apps/marketplace/models.py:10-14,177-181` · `apps/marketplace/scoring.py:22-28,160-190` ·
  `apps/marketplace/services.py:100-119` · `apps/marketplace/forms.py:51-68` ·
  `apps/contracts/models.py:57-89` · `apps/accounts/enums.py:4-21` ·
  `apps/accounts/profiles.py:42-65`.
