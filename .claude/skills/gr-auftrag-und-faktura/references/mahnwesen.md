# Mahnwesen — dunning, default and default interest

**Covers:** when a receivable becomes due, when the customer is in Verzug, the escalation
ladder, mandatory content of a Mahnung, Verzugszinsen rates, who bears the costs, when the
court procedure may start, and exactly what the software has to store and compute.

**Stand: 2026-08-29.** Primary source is one pland.app article, crawled 2026-08-29 and read in
full; secondary sources are the module pages and the dossier `knowledge/blog-faktura.md`.
Reference material for building software — not legal advice.

---

## 1. The two statutory anchors

**Fakt.** Both from
<https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-wie-und-wann-schreibe-ich-am-besten-zahlungserinnerungen-und-mahnungen>
(page date: May 6, 2025).

| Anchor | Verbatim | What it fixes |
|---|---|---|
| **§ 641 Abs. 1 S. 1 BGB** | *"Die **Fälligkeit der Vergütung** erfolgt nach der **Abnahme der Arbeit** gemäß dem Gesetz (BGB § 641 Abs. 1 S. 1)."* | The **due-date anchor** is an acceptance event, not the invoice date and not `created_at` |
| **§ 286 BGB**, called on the page *"Gesetz zur Beschleunigung fälliger Zahlungen"* | *"Kunden haben **30 Tage** Zeit, um die Rechnung zu begleichen oder etwaige Unstimmigkeiten zu melden. Das Gesetz … schreibt eine **30-Tage-Frist verpflichtend** vor."* | The default period, and the fact that it runs **by law**, not by reminder |

**Fakt — the decisive consequence.** *"**Mahnungen dienen nicht mehr der Fristsetzung.**"*
A Mahnung is a **communication**, not a precondition for default.

**Fakt.** Timing advice on the same page: *"Es wird empfohlen, Rechnungen **möglichst bald
nach Abschluss der Arbeiten** zu stellen."*

**Ungeprüft, but load-bearing.** § 641 BGB is a **Werkvertrag** provision. Cleaning contracts
are commonly **Dienstverträge (§ 611 BGB)**, where there is no Abnahme at all. The source page
applies the Werkvertrag rule to cleaning without qualification. **Verify per contract type
before the due-date anchor is hard-wired to an acceptance event.** See
`references/rechnungsarten.md` §8.6 — carry `contract_kind = DIENSTVERTRAG | WERKVERTRAG` and
let it select the anchor.

**Ungeprüft.** The interaction between the 30-day rule and an explicitly agreed Zahlungsziel
(14 / 30 / 60 days — see §2) is **not stated on the page**. Which one governs, and whether a
contractual term can shorten or lengthen the statutory period, is *nicht belegt*.
Make the anchor and the term configurable, and record which one produced the due date.

---

## 2. Payment terms

**Fakt.** *"Je nach Vereinbarung kann dies **14, 30 oder 60 Tage** nach Erhalt der Rechnung
sein."*
(<https://pland.app/blog/die-abschlussrechnung-in-der-gebaudereinigung-so-behalten-sie-den-uberblick>)

Note the wording: **nach Erhalt** der Rechnung, not after the invoice date. Receipt is a
different, harder-to-evidence event than issue. *The page does not say how receipt is to be
determined.* **Vorschlag:** store `sent_at`, `delivery_channel` and, where available,
`delivered_at`; compute the due date from the configured basis and record which basis was
used.

**Fakt.** Payment methods named on the same page: **Überweisung, Scheck, Kreditkarte**
*"oder andere Methoden"*.

**Fakt.** Contractual framing, from the Mahnwesen page: *"Es ist ratsam, Zahlungsfristen auf
Rechnungen zu vermerken und diese **bereits im Vertrag** mit dem Kunden festzulegen.
**Allgemeine Geschäftsbedingungen (AGB)** sollten **Standardfristen und -prozeduren für das
Forderungsmanagement** enthalten."*
Same page adds a segmentation rule: *"große Kundenbestände** können auf **standardisierte
Fristen** setzen, während Unternehmen mit wenigen Kunden **individuelle Fristen** bevorzugen."*

**Fakt (competitor).** The Zahlungsziel is stored **per document type** in the invoicing
settings, alongside Rechnungskürzel, next number, Kopfzeilentext and Fußzeilentext.
(<https://pland.app/onboardings/die-wichtigsten-faktura-einstellungen-in-pland>)

---

## 3. The escalation ladder

**Fakt.** Stages named on
<https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-wie-und-wann-schreibe-ich-am-besten-zahlungserinnerungen-und-mahnungen>.
Stage 0 is on the page as step 1 of the process ("Rechnungsstellung"); the numbering here is
this document's, the labels and content are the page's.

| Stage | German label | What the page prescribes |
|---|---|---|
| 0 | **Rechnungsstellung** | *"klar, präzise und vollständig"* — erbrachte Leistungen, Preise, **Fälligkeitsdaten** |
| 1 | **Zahlungserinnerung** | Sent *"sobald das Zahlungsziel abgelaufen ist"*. **Klare Kommunikation** (state the Fälligkeitsdatum and how to pay) · **Höflichkeit bewahren** (*"Vermeiden Sie aggressive oder einschüchternde Formulierungen"*) · **Klare Fristen** (*"Der Kunde sollte genau wissen, bis wann die Zahlung erfolgen muss"*) · **Kontaktaufnahme** — if the reminder has no effect, phone the customer |
| 2 | **Erste Mahnung** | *"in der Regel eine **freundliche Erinnerung**"* — politely point out the outstanding payment and set a clear deadline |
| 3 | **Zweite Mahnung** | *"den Ton **verschärfen**"*, state payment is **dringend erforderlich**, mention consequences such as **Verzugszinsen oder rechtliche Schritte** |
| 4 | **Letzte Mahnung** | *"der **letzte Schritt vor rechtlichen Schritten**"* — make clear this is the final warning; *"Erwägen Sie, einen **Anwalt** oder ein **Inkassounternehmen** einzuschalten"* |

**Fakt — the intervals between stages are never stated.** How many days sit between
Zahlungserinnerung and Mahnung 1, or between Mahnung 1 and 2, is *nicht belegt / not
established from the sources.* **Make it configuration; do not hard-code a number.**

**Fakt.** *"Bei Nichtreaktion des Kunden **können** Mahnungen verschickt werden."* — the ladder
is optional, which matters because of §5.

---

## 4. Mandatory content of a Mahnung

**Fakt.** Verbatim: *"Eine Mahnung muss den **Hinweis enthalten, dass es sich um eine Mahnung
handelt**, und klare Angaben zu **Absender und Empfänger**, **der betroffenen Rechnung**,
**Verzugszinsen** und **einer aktualisierten Zahlungsfrist** enthalten."*
(<https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-…>)

| # | Required element | Field it implies |
|---|---|---|
| 1 | Hinweis, dass es sich um eine **Mahnung** handelt | the document-type label, rendered literally |
| 2 | Klare Angaben zu **Absender** | issuer block from tenant master data |
| 3 | Klare Angaben zu **Empfänger** | the **Rechnungsempfänger** (the payer) — see `references/rechnungsarten.md` §4 |
| 4 | **Der betroffenen Rechnung** | FK to the invoice, plus its number and date on the document |
| 5 | **Verzugszinsen** | the computed interest amount **and** the rate basis (§6) |
| 6 | Eine **aktualisierte Zahlungsfrist** | `new_due_date` — a *new* deadline per notice, not the invoice's |

**Fakt.** B2C additional duty: *"**Privatkunden müssen ausdrücklich über Fristen und
Konsequenzen von Zahlungsverzug informiert werden.**"* — same page.
**Vorschlag:** a mandatory extra text block rendered only when
`Account.entity_type == EntityType.INDIVIDUAL` (`apps/accounts/enums.py:4-8`), and a validator
that refuses to issue a B2C dunning notice without it.

---

## 5. Verzug, costs and the court procedure

**Fakt.** All from the same page:

| Rule | Verbatim |
|---|---|
| Who pays for dunning | *"Die **Kosten für Mahnungen trägt der Schuldner**."* |
| Court procedure | *"Das **gerichtliche Mahnverfahren** kann nach Zahlungsverzug **sofort** eingeleitet werden."* |

**Consequence (Vorschlag).** `GERICHTLICHES_MAHNVERFAHREN` must be reachable **directly from
`UEBERFAELLIG`**, without traversing stages 1–4. A state machine that forces the ladder is
wrong on the sources' own terms. Model the ladder as the *recommended* path and the direct
jump as an allowed transition, gated on `Membership.can_manage`
(`apps/accounts/models.py:224-226`).

**Fakt (competitor).** **Individuelle Mahngebühren** can be added per notice.
(<https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-…>)

**Fakt (gap).** No amount, cap or basis for a Mahngebühr is given anywhere in the crawl.
*Nicht belegt.* Ship it as a per-stage configured Decimal with no default.

---

## 6. Verzugszinsen

**Fakt.** Verbatim: *"Bei Zahlungsverzug entstehen **Verzugszinsen**, die je nach Kundenart
unterschiedlich hoch sind. **Geschäftskunden** haben einen Zinssatz von **9 % über dem
Basiszinssatz der Bundesbank**, während **Privatkunden 5 % über dem Basissatz** zahlen
müssen."*
(<https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-…>)

| Customer kind | Rate | Repo field that decides it |
|---|---|---|
| **Geschäftskunde (B2B)** | **Basiszinssatz + 9 Prozentpunkte** | `Account.entity_type == EntityType.COMPANY` (`apps/accounts/enums.py:8`) |
| **Privatkunde (B2C)** | **Basissatz + 5 Prozentpunkte** | `Account.entity_type == EntityType.INDIVIDUAL` (`apps/accounts/enums.py:7`) |

**Fakt.** The page names the **spreads** but cites **no statute** for them, and gives **no
day-count convention** and **no compounding rule**. *Nicht belegt.*

**Ungeprüft.** The Basiszinssatz is set by the Deutsche Bundesbank and changes on **1 January**
and **1 July** each year. Not stated on any crawled page. Verify against the Bundesbank
publication before shipping any value.

**Vorschlag — model it exactly like the repo already models statutory wage floors.**
`apps/contracts/models.py:57-89` is the template: a dated table with `valid_from` /
`valid_to`, a `source_note`, and a `current(on=date)` classmethod that picks the row in force.

```python
class BaseInterestRate(models.Model):
    """Basiszinssatz al Bundesbank. Se schimbă de două ori pe an (1.1. și 1.7.) —
    valoare datată, NU constantă în cod. Vezi WageFloor pentru același tipar."""
    rate_percent = models.DecimalField(max_digits=5, decimal_places=3)
    valid_from   = models.DateField()
    valid_to     = models.DateField(null=True, blank=True)
    source_note  = models.CharField(max_length=200, blank=True)   # Bundesbank publication

    @classmethod
    def current(cls, on=None): ...      # same body as WageFloor.current
```

Interest computation (Vorschlag; the arithmetic beyond the spread is **not** in the sources):

```
spread          = 9 if customer is COMPANY else 5      # percentage points
annual_rate     = BaseInterestRate.current(on=default_date).rate_percent + spread
interest        = outstanding_amount × annual_rate/100 × days_in_default / day_basis
```

- `default_date` = the day after the due date, derived per §1–§2.
- `day_basis` is **configuration**, not a constant — the page gives no day-count convention.
- The Basiszinssatz may change **mid-default**. Accrue per rate-validity segment, not once
  over the whole period, or a long default silently uses a stale rate.
- Interest accrues on the **outstanding** amount, so a partial payment resets the base going
  forward. `PARTIALLY_PAID` is a real state, not a UI nicety.

---

## 7. The full dunning run

**Fakt.** Ordered steps as the page describes them, combined with §1–§6:

1. **Rechnungsstellung** promptly after the work is accepted (§ 641 Abs. 1 S. 1 BGB).
2. Wait out the **30-day** window (§ 286 BGB) — or the agreed Zahlungsziel.
3. **Zahlungserinnerung** once the Zahlungsziel has expired: polite, with a clear new deadline
   and payment instructions.
4. **Phone the customer** if the reminder is ignored.
5. **Erste Mahnung** → **Zweite Mahnung** (mention Verzugszinsen / rechtliche Schritte) →
   **Letzte Mahnung** (final warning; consider Anwalt or Inkasso).
6. Charge **Verzugszinsen** (9 pp B2B / 5 pp B2C over Basiszinssatz) and pass **Mahnkosten**
   to the debtor.
7. **Gerichtliches Mahnverfahren** may be started immediately upon Zahlungsverzug — it does
   **not** require any Mahnung first.

---

## 8. What the software must track

**Vorschlag.** Everything below is derived from §1–§7; none of it exists in the repo.

### 8.1 On the invoice

| Field | Why |
|---|---|
| `accepted_at` (Abnahme) | The § 641 due-date anchor |
| `issue_date`, `sent_at`, `delivered_at` (null) | The "nach Erhalt" basis for the Zahlungsziel |
| `payment_term_days` + `payment_term_basis ∈ {ISSUE, RECEIPT, ACCEPTANCE}` | 14/30/60 per agreement; which event it counts from |
| `due_date` (derived, stored) | Store it — a later change to the term must not silently reprice history |
| `outstanding_amount` (derived from payments) | The interest base |
| `default_since` (null) | The day default began; interest accrues from here |
| `status` | See §8.4 |

### 8.2 `Payment`

| Field | Why |
|---|---|
| `invoice` FK, `amount`, `received_at` | Partial payments are normal |
| `booking_reference` | The competitor matches incoming payments *"inklusive **Buchungsnummer**, Kunde und Betrag"* (<https://pland.app/funktionen/umsatzuebersicht>) |
| `method` | Überweisung / Scheck / Kreditkarte / sonstige (§2) |
| immutable `save()` | Same guard as `ShiftEvent.save()` (`apps/planning/models.py:217-220`) — a correction is a new row |

### 8.3 `DunningNotice` + `DunningStageConfig`

**Fakt (competitor, the feature shape to match).** Per invoice, create either a
Zahlungserinnerung or a Mahnung at a chosen **Mahnstufe**; per stage configure **Kopftext**,
**Fußtext** and **Zahlungsziel**; texts can be **saved for reuse** or adjusted individually;
**individuelle Mahngebühren** can be added; the document is then generated automatically for
sending. All open and overdue invoices are visible at a glance.
(<https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-…>)

**Fakt (competitor).** *"Sobald eine Rechnung **überfällig** ist, erstellt PlanD **automatisch
eine Mahnung** - auf Wunsch mit **abgestuften Eskalationsstufen**."*
(<https://pland.app/funktionen/umsatzuebersicht>)
And: *"Hinterlegen Sie Ihre individuellen **Zahlungserinnerungen und Mahnstufen**"*
(<https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>)

```
DunningStageConfig                     # tenant-level, per stage
  account          FK accounts.Account
  stage            ∈ {ZAHLUNGSERINNERUNG, MAHNUNG_1, MAHNUNG_2, LETZTE_MAHNUNG}
  days_after_previous   PositiveSmallInteger   # NOT established from sources — no default
  header_text      TextField
  footer_text      TextField
  payment_term_days     PositiveSmallInteger   # the "aktualisierte Zahlungsfrist"
  fee              Decimal                     # Mahngebühr; no default, no cap known
  UniqueConstraint(account, stage)

DunningNotice                          # one issued document
  invoice          FK
  stage            (same enum)
  sequence_number  CharField           # own gapless number — see rechnungsarten.md §6
  issued_at        DateTimeField
  new_due_date     DateField           # required by §4 item 6
  fee_amount       Decimal
  interest_amount  Decimal             # required by §4 item 5
  interest_rate_percent  Decimal       # the rate actually applied, frozen
  base_rate_percent      Decimal       # the Basiszinssatz used, frozen
  outstanding_at_issue   Decimal
  rendered_body    TextField           # frozen copy — ContractDraft pattern
  body_sha256      CharField(64)
  b2c_notice_included    Boolean       # §4, mandatory for INDIVIDUAL
```

Freeze `interest_rate_percent`, `base_rate_percent` and `outstanding_at_issue` on the notice.
A reissued or re-rendered notice must show the numbers that were on the document that was
actually sent — the same reason `ContractDraft` freezes `rendered_body`
(`apps/contracts/models.py:116-121, 169-171`).

### 8.4 Invoice status machine

**Vorschlag.**

```
ENTWURF ──validate──▶ FREIGEGEBEN ──issue+number──▶ VERSENDET
                                                      │
                          ┌───────────────────────────┤
                          ▼                           ▼
                  TEILWEISE_BEZAHLT ─────────────▶ BEZAHLT
                          │
                    (due_date passed)
                          ▼
                    UEBERFAELLIG
                     │        │
       ┌─────────────┘        └──────────────┐
       ▼                                      ▼
MAHNSTUFE_1 → MAHNSTUFE_2 → LETZTE_MAHNUNG   GERICHTLICHES_MAHNVERFAHREN / INKASSO
       └──────────────┬───────────────────────┘
                      ▼
                (any stage can still reach BEZAHLT)

STORNIERT — reachable ONLY via a linked Stornorechnung, never by deleting the invoice
```

Rules:
- `UEBERFAELLIG` is entered by a **date check**, not by sending a reminder (§1: "Mahnungen
  dienen nicht mehr der Fristsetzung").
- `GERICHTLICHES_MAHNVERFAHREN` is reachable **directly** from `UEBERFAELLIG` (§5).
- `BEZAHLT` is reachable from **every** dunning stage.
- No transition edits the invoice. A correction is a new Storno document
  (`references/rechnungsarten.md` §7).

### 8.5 The dashboard view

**Fakt (competitor).** *"Offene Posten tagesaktuell"* — which invoices are unpaid — and
**tagesaktueller Umsatz**, with open/paid/overdue states.
(<https://pland.app/funktionen/umsatzuebersicht>,
<https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>)

**Vorschlag.** `offene_posten = invoices with status ∈ {VERSENDET, TEILWEISE_BEZAHLT,
UEBERFAELLIG, MAHNSTUFE_*}`. Add it as a `Panel` row in `apps/dashboard/panels.py:45-90`, keyed
to `Capability.PROVIDER` — the dashboard is defined as data there, not as template branches
(`apps/dashboard/panels.py:1-7`).

---

## 9. Open questions — do not close them by guessing

1. **Stage intervals.** Not stated. Configuration, no default. (§3)
2. **Mahngebühr amount / cap.** Not stated. Configuration, no default. (§5)
3. **Day-count convention and compounding for Verzugszinsen.** Not stated. Configuration. (§6)
4. **Statute for the 9 pp / 5 pp spreads.** Not cited on the page. Verify. (§6)
5. **Basiszinssatz values and their change dates.** Not in the sources at all. Verify against
   the Bundesbank. (§6)
6. **Whether an agreed Zahlungsziel overrides the § 286 30-day period**, and in which
   direction. Not stated. (§1)
7. **How "Erhalt der Rechnung" is evidenced** for the 14/30/60-day basis. Not stated. (§2)
8. **Whether § 641 BGB applies at all** to a cleaning Dienstvertrag. Ungeprüft, and it
   determines the due-date anchor. (§1)

---

## Quellen

pland.app pages (crawled 2026-08-29):
- <https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-wie-und-wann-schreibe-ich-am-besten-zahlungserinnerungen-und-mahnungen> (page date: May 6, 2025) — primary source for §1, §3, §4, §5, §6, §7
- <https://pland.app/blog/die-abschlussrechnung-in-der-gebaudereinigung-so-behalten-sie-den-uberblick> — the 14/30/60-day terms and payment methods
- <https://pland.app/onboardings/die-wichtigsten-faktura-einstellungen-in-pland> — Zahlungsziel per document type
- <https://pland.app/funktionen/umsatzuebersicht> — offene Posten, automatic Mahnung, payment matching
- <https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung> — configurable Zahlungserinnerungen und Mahnstufen

Repository files read for this document (2026-08-29):
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/enums.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/dashboard/panels.py`

To verify before shipping (not yet checked):
- <https://www.gesetze-im-internet.de/bgb/__286.html> (§ 286 BGB — Verzug)
- <https://www.gesetze-im-internet.de/bgb/__288.html> (§ 288 BGB — the statute the 9 pp / 5 pp spreads presumably come from; **not cited by the source page**)
- <https://www.gesetze-im-internet.de/bgb/__641.html> (§ 641 BGB — Fälligkeit der Vergütung)
- Deutsche Bundesbank Basiszinssatz publication (values and change dates)
