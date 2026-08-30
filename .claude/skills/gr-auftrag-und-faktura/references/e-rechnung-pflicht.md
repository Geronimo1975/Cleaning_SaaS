# E-Rechnungspflicht — the German electronic-invoicing obligation

**Covers:** every phase date the crawled sources give, who is affected when, which formats
count as an e-invoice, what does **not** count, the Leitweg-ID, and archiving duties — plus a
blunt assessment of how far each claim can be trusted.

**Stand: 2026-08-29.** Sources are pland.app pages crawled 2026-08-29 (raw text under
`scratchpad/txt/`, each with its `# SOURCE:` URL) and the dossiers
`knowledge/blog-faktura.md` and `knowledge/lexikon-betrieb.md`. Reference material for
building software — not legal or tax advice.

> **Read §4 before you write a single date into code.** The crawled sources are the weakest
> part of this whole knowledge base and they contradict each other.

---

## 1. What an E-Rechnung is

**Fakt.** *"Eine elektronische Rechnung (E-Rechnung) ist **nicht bloß eine Rechnung im
PDF-Format**. Sie folgt spezifischen Standards und kann **maschinell verarbeitet** werden.
Wesentlich ist dabei, dass die Inhalte **strukturiert** und digital übermittelt werden."*
— <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>

**Fakt.** *"Eine E-Rechnung ist ein **elektronisches Dokument im strukturierten
Datenformat** (wie XRechnung oder ZUGFeRD), das **automatisiert verarbeitet** werden kann
und den gesetzlichen Anforderungen für den elektronischen Rechnungsaustausch entspricht."*
— <https://pland.app/arbeitslexikon/e-rechnung>

### 1.1 What is explicitly NOT an e-invoice

**Fakt.** *"**Keine reine PDF-Rechnung mehr ausreichend**"* — <https://pland.app/arbeitslexikon/e-rechnung>

| Not an e-invoice | Why |
|---|---|
| A PDF generated from an invoice template | No structured, machine-readable payload |
| A scanned paper invoice | ditto |
| An invoice image attached to an e-mail | ditto |
| A CSV or an in-house XML that does not meet EN 16931 | Format must satisfy the norm — see §3 |

**Consequence for this repo (Vorschlag).** Do not build "e-invoicing" as a PDF-generation
feature with an XML afterthought. The **structured document is the invoice**; the human-
readable rendering is a by-product (ZUGFeRD) or a separate artefact (XRechnung). Build the
XML generator first and the PDF second.

---

## 2. Who is affected, and when — every date the sources give

**Fakt.** Public sector, stated as the *current* rule at time of writing:

| Rule | Verbatim | Source |
|---|---|---|
| Scope today | *"Derzeit gilt die E-Rechnungspflicht für Unternehmen, die an **öffentliche Auftraggeber** Rechnungen **über 1.000 Euro** stellen."* | <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen> |
| Domain | *"Dies betrifft besonders den Bereich der **Vergabe öffentlicher Aufträge**."* | same |
| Required data | Steuernummer, Kontodaten und die sogenannte **Leitweg-ID** (*"für öffentliche Auftraggeber"*) | same |

**Fakt.** B2B extension — the sources give **two mutually inconsistent formulations**:

| Formulation | Verbatim | Source | Page date |
|---|---|---|---|
| Vague | *"**Spätestens ab 2025** wird die E-Rechnung auch im B2B-Bereich zur Pflicht."* and *"**Ab 2025** soll diese Regelung jedoch auch auf den B2B-Bereich ausgeweitet werden."* | <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen> | May 6, 2025 |
| Definite | *"**Ab dem 1. Januar 2025** … sind **alle Unternehmen** verpflichtet, ihre Rechnungen an andere Unternehmen (**B2B**) elektronisch zu übermitteln."* | <https://pland.app/arbeitslexikon/e-rechnung> | undated lexicon entry |

**Fakt.** Stated effect of the B2B obligation: companies will be legally obliged to issue and
transmit invoices *"ausschließlich in elektronischem Format"*.
(<https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>)

**Fakt.** Stated exemption: *"Ausnahmen nur für **Kleinunternehmer** und bestimmte
Sonderfälle."* — <https://pland.app/arbeitslexikon/e-rechnung>
The Sonderfälle are never enumerated. *Not established from the sources.*

**Fakt.** Stated adaptation deadline: companies must adapt their invoicing processes
*"bis Ende 2024"*. — <https://pland.app/arbeitslexikon/e-rechnung>

**Fakt.** Industry relevance stated: Gebäudereinigung firms *"häufig mit öffentlichen
Auftraggebern zusammenarbeiten"*, so the XRechnung switch matters especially to them.
(<https://pland.app/blog/gebaudereinigung-xrechnung-pflicht-ab-2025>)

### 2.1 What the sources do NOT give

**Fakt (absence, verified by grep across `scratchpad/txt/`).** Nowhere in the crawl:

- any distinction between the duty to **receive** and the duty to **issue** structured invoices;
- any **transition period** (no 2026, 2027 or 2028 milestone);
- any **turnover threshold** governing a transition period;
- any statement that paper/PDF remains permissible during a transition, with or without the
  recipient's consent;
- any **§ 14 / § 14a / § 27 UStG** paragraph reference for the e-invoicing rules;
- the **Wachstumschancengesetz**;
- **Peppol**, **Peppol BIS**, or any transmission-network requirement;
- the definition of a **"sonstige Rechnung"**;
- whether the **1.000 Euro** public-sector threshold is **net or gross**, or whether it is
  **per invoice or per contract**.

All of the above: *nicht belegt / not established from the sources.*

---

## 3. Valid formats

**Fakt.** Format comparison as printed:

| Format | Nature | Where it is used | Source |
|---|---|---|---|
| **XRechnung** | *"Ein strikt maschinenlesbares Format, das speziell für die Anforderungen der **öffentlichen Verwaltung** entwickelt wurde. Es enthält **ausschließlich strukturierte Daten** und ist ideal für automatisierte Verarbeitung, jedoch **weniger flexibel im Design**."* | Public administration; *"der **deutsche Standard** für elektronische Rechnungen an öffentliche Auftraggeber"* | <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen> · <https://pland.app/arbeitslexikon/e-rechnung> |
| **ZUGFeRD** | *"Dieses **hybride** Format kombiniert maschinenlesbare XML-Daten mit einem optisch ansprechenden PDF"* — a PDF file **with embedded structured XML data**; suits automated **and** manual use | *"besonders bei mittelständischen Unternehmen beliebt"*; *"hauptsächlich in der **Privatwirtschaft**"* | same two pages |

**Fakt.** ZUGFeRD expands to *"**Z**entraler **U**ser **G**uide des **F**orums
**e**lektronische **R**echnung **D**eutschland"*. — <https://pland.app/arbeitslexikon/e-rechnung>

### 3.1 XRechnung — technical and governance facts

**Fakt.** All from <https://pland.app/blog/gebaudereinigung-xrechnung-pflicht-ab-2025>:

| Fact | Verbatim |
|---|---|
| Technical nature | *"Die XRechnung ist ein **XML-basiertes Datenmodell**, das den elektronischen Rechnungsaustausch standardisiert."* |
| European norm | *"Sie wurde entwickelt, um die Anforderungen der europäischen Norm **EN 16931** zu erfüllen"* |
| EU directive | *"und die **Richtlinie 2014/55/EU** umzusetzen."* |
| Governance | *"In Deutschland wird der Standard von der **Koordinierungsstelle für IT-Standards (KoSIT)** im Auftrag des **IT-Planungsrats** betrieben."* |
| Federal rule | *"Für die Ausstellung von elektronischen Rechnungen an die **Bundesverwaltung** ist grundsätzlich der Standard XRechnung **in der jeweils aktuellen Fassung** zu verwenden."* |
| Accepted alternative | *"Zusätzlich können andere Formate wie **ZUGFeRD 2.2.0 im Profil XRECHNUNG** verwendet werden, sofern sie den Anforderungen der europäischen Norm **EN 16931**, der **E-Rechnungsverordnung des Bundes (E-RechV)** und den **Nutzungsbedingungen der jeweiligen Rechnungseingangsplattform des Bundes** entsprechen."* |

**Fakt.** EN 16931 is also named as the basis of XRechnung on
<https://pland.app/arbeitslexikon/e-rechnung>.

### 3.2 Format decision table

**Vorschlag**, derived strictly from the facts above:

| Recipient | Format to emit | Extra data required |
|---|---|---|
| Bundesverwaltung / öffentlicher Auftraggeber | **XRechnung, current version** (or ZUGFeRD 2.2.0 Profil XRECHNUNG if the receiving platform's Nutzungsbedingungen allow it) | **Leitweg-ID**, Steuernummer, Kontodaten |
| B2B private sector | ZUGFeRD (hybrid) or XRechnung — the sources name both as structured formats and do not mandate one for B2B | — |
| B2C (Privatkunde) | Not established from the sources. Do **not** assume the obligation covers B2C | — |

⚠️ *"in der jeweils aktuellen Fassung"* means the **standard version is a moving target**.
Store `standard_version` on every emitted document (`"XRechnung 3.x"`, `"ZUGFeRD 2.2.0"`) so
an archived invoice can be re-validated against the version it was issued under. Never hard-
code the version string in a template.

---

## 4. Reliability assessment — read this before encoding anything

**Fakt.** Both e-invoicing blog articles carry the page date **May 6, 2025**, yet still
describe 2025 in the **future tense** ("Spätestens ab 2025 **wird** … zur Pflicht"; "Ab 2025
**soll** … ausgeweitet werden"). The lexicon entry meanwhile asserts a flat "Ab dem
1. Januar 2025 … alle Unternehmen". The crawl is dated 2026-08-29, i.e. the pages are more
than a year stale relative to the crawl and were internally inconsistent when written.

**Ungeprüft — the shape the obligation is generally understood to have.** Everything in this
paragraph is domain knowledge added here, **not** from the sources: the German B2B
e-invoicing duty is staged rather than a single cliff — an obligation to be able to
**receive** structured e-invoices in domestic B2B from the start, with transition periods for
the duty to **issue** running over subsequent years and differentiated by company turnover,
and paper/PDF still permitted during the transition subject to the recipient's agreement.
**None of this is established from the crawled sources. Verify the current § 14 / § 14a UStG
text and the BMF guidance directly before writing any date logic.**

**Ungeprüft.** **§ 13b UStG reverse charge** is highly relevant to Gebäudereinigung (cleaning
services supplied to a business that itself supplies cleaning services shift the VAT liability
to the recipient) and interacts with e-invoice content — the mandatory
"Steuerschuldnerschaft des Leistungsempfängers" note and the suppression of the tax amount.
**Not mentioned on any of the 237 crawled pages.** Verify against the statute.

### 4.1 Design rule that follows

**Vorschlag.** Encode the obligation as **dated, editable configuration**, exactly the way the
repo already handles statutory wage floors:

```python
# apps/contracts/models.py:57-89 — the pattern to copy
WageFloor.current(kind, on=date)     # dated row lookup, valid_from / valid_to
MinijobThreshold.current(on=date)    # same shape
```

So:

```
EInvoiceRule
  scope            = OEFFENTLICH | B2B | B2C
  duty             = MUST_RECEIVE | MUST_ISSUE
  valid_from       (Date)
  valid_to         (Date, null)
  min_amount_eur   (Decimal, null)     # the 1.000-Euro public-sector threshold lives here
  amount_basis     = NETTO | BRUTTO | UNKNOWN   # sources do not say → default UNKNOWN
  turnover_max_eur (Decimal, null)     # transition thresholds, if any turn out to exist
  exempt_legal_status = M2M to LegalStatus values  # KLEINUNTERNEHMER
  source_note      (CharField)         # the URL or statute the row came from
```

`amount_basis = UNKNOWN` is not laziness — the sources genuinely do not say whether the
1.000 Euro is net or gross, and a wrong guess mis-classifies real invoices.

**Never** write `if invoice.issue_date >= date(2025, 1, 1): require_xrechnung()`.

---

## 5. Leitweg-ID

**Fakt.** *"Dabei werden wichtige Pflichtangaben wie die **Steuernummer**, **Kontodaten** und
die sogenannte **Leitweg-ID** (für öffentliche Auftraggeber) automatisch integriert."*
— <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>

**Fakt (competitor behaviour).** PlanD auto-inserts Steuernummer, Kontodaten and Leitweg-ID
into the generated e-invoice.
(<https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>)

**Fakt (absence).** The **format, structure and issuing body of a Leitweg-ID are not
described anywhere in the crawl.** *Nicht belegt.* Do not implement a format validator from
guesswork; store it as a plain string with a length limit and validate only when a verified
specification is on hand.

**Vorschlag.** `leitweg_id` is **per-customer master data**, not per-invoice data. It belongs
on the customer relationship record together with `is_public_authority`, and is copied onto
the invoice snapshot at issue time (like `ContractDraft.rendered_body`).

---

## 6. Archiving

**Fakt.** *"E-Rechnungen müssen nach den Grundsätzen der ordnungsmäßigen Buchführung
(**GoBD**) **digital und revisionssicher für mindestens zehn Jahre** aufbewahrt werden."*
— <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>

**Fakt.** *"Elektronische **Dokumentenmanagementsysteme (DMS)** sind hierfür eine sinnvolle
Investition."* — same page

**Fakt.** The generic invoice article requires that invoices **and payment receipts** be
*"ordnungsgemäß aufbewahren"* and remain accessible for future reference.
— <https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen>

**Fakt.** A **Gutschrift** must carry a **Hinweis auf Aufbewahrungspflicht** and be archived
with all related documents.
— <https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>

**Fakt (adjacent, from the same knowledge base).** The Personalakte page states tax-relevant
documents such as Lohnabrechnungen and Arbeitsverträge must be kept **at least ten years** —
the same horizon.
— <https://pland.app/arbeitslexikon/personalakte>

**Ungeprüft.** The statutory basis for retention is generally **§ 147 AO** and **§ 257 HGB**
(10 years for books, inventories, annual accounts and accounting vouchers, i.e. invoices; 6
years for commercial letters). Not cited on any crawled page. Verify before quoting the
paragraph anywhere user-facing.

**Ungeprüft, and a real tension.** A blanket "keep everything for 10 years" default is itself
a GDPR problem for documents with no retention basis. The repo already models the opposite
pull: `VerificationDocument.delete_after` carries a DSGVO retention date
(`apps/accounts/compliance.py:36`). Invoices are a genuine 10-year case; do not extend that
horizon to everything attached to them (e.g. free-text notes, photos) without a basis.

**Vorschlag.**

```
InvoiceArchive
  invoice           FK, one-to-one
  format            = XRECHNUNG | ZUGFERD | PDF | PAPIER
  profile           (CharField, e.g. "XRECHNUNG" for ZUGFeRD 2.2.0)
  standard_version  (CharField, e.g. "ZUGFeRD 2.2.0")
  payload           (FileField, private storage, write-once)
  payload_sha256    (CharField(64))
  en16931_validated_at (DateTimeField, null)
  transmitted_at    (DateTimeField, null)
  platform          (CharField — the federal Rechnungseingangsplattform, if any)
  retention_until   (DateField)   # issue_date + 10 years, per GoBD
```

- `save()` raises on re-save. Copy `ShiftEvent.save()` (`apps/planning/models.py:217-220`) and
  `ContractSignature.save()` (`apps/contracts/models.py:278-281`).
- `payload_sha256` mirrors the existing `body_sha256` / `document_sha256` convention
  (`apps/contracts/models.py:171, 268`).
- Storage must be private. The repo already has a private-storage precedent in
  `VerificationDocument` — *"NICIODATĂ public. Storage privat, cu termen de retenție."*
  (`apps/accounts/compliance.py:22-23`).

---

## 7. Validation

**Fakt.** The only validation statement in the sources is that alternative formats must meet
**EN 16931**, the **E-RechV** and the receiving platform's **Nutzungsbedingungen**.
(<https://pland.app/blog/gebaudereinigung-xrechnung-pflicht-ab-2025>)
No validator, tool, library or service is named anywhere in the crawl.

**Ungeprüft.** Mature tooling exists for generating and validating UBL/CII against EN 16931
(the KoSIT validator, and Python libraries for embedding ZUGFeRD XML into PDF/A-3). No
recommendation is made here because none was verified for this project.

**Vorschlag.** Validation is a **state-machine gate**, not a send-time check: an invoice
cannot leave `DRAFT` unless (a) the Pflichtangaben validator passes
(`references/rechnungsarten.md` §5) and (b), where an e-invoice is required, the EN 16931
validation passes. Record `en16931_validated_at` on the archive row so a later audit can see
that it was checked, and when.

---

## 8. What this means for `Cleaning_SaaS` specifically

**Fakt (repo).** Nothing e-invoicing related exists. No XML, no PDF renderer, no
`leitweg_id`, no archive model. Verified 2026-08-29 by grep over `*.py` and `*.html`.

**Fakt (repo).** The pieces that *do* exist and should be reused:

| Piece | Location | Role in e-invoicing |
|---|---|---|
| `Account.vat_id` (USt-IdNr.), `Account.tax_number` (Steuernummer) | `apps/accounts/models.py:96-97` | Issuer and recipient identifiers on the XML |
| `Account.legal_name`, `street`, `postal_code`, `locality` FK | `apps/accounts/models.py:92, 99-103` | Postal address blocks |
| `LegalStatus.KLEINUNTERNEHMER` (§19 UStG) | `apps/accounts/enums.py:34` | The one exemption the sources name |
| `EntityType.COMPANY` / `INDIVIDUAL` | `apps/accounts/enums.py:4-8` | B2B vs B2C routing |
| `catalog.Product.vat_rate` default `19.00` | `apps/catalog/models.py:55` | The existing VAT-rate convention. Note it is a per-product default, **not** a dated statutory table — an invoicing layer needs the dated version |
| `WageFloor` / `MinijobThreshold` dated-value pattern | `apps/contracts/models.py:57-113` | The exact shape `EInvoiceRule` should copy |
| Immutability + sha256 precedents | `apps/planning/models.py:217-220`, `apps/contracts/models.py:256-281` | The archive guard |

**Missing and needed (Vorschlag):**
- `is_public_authority` (Boolean) and `leitweg_id` (CharField) on the customer relationship.
- `EInvoiceRule` dated table (§4.1).
- `InvoiceArchive` (§6).
- A `TaxRate` dated table — the repo has no statutory VAT table at all; `19.00` currently sits
  as a model default (`apps/catalog/models.py:55`), which is fine for a catalogue price but
  wrong as the single source of truth for invoicing.

---

## Quellen

pland.app pages (crawled 2026-08-29):
- <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen> (page date: May 6, 2025)
- <https://pland.app/blog/gebaudereinigung-xrechnung-pflicht-ab-2025> (page date: May 6, 2025)
- <https://pland.app/arbeitslexikon/e-rechnung>
- <https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen>
- <https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>
- <https://pland.app/arbeitslexikon/personalakte>
- <https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>

Repository files read for this document (2026-08-29):
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/enums.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/compliance.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/catalog/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`

To verify before encoding any date (not yet checked):
- <https://www.gesetze-im-internet.de/ustg_1980/__14.html> (§ 14 UStG)
- <https://www.gesetze-im-internet.de/ustg_1980/__14a.html> (§ 14a UStG)
- current BMF guidance on the B2B e-invoicing obligation
- <https://www.gesetze-im-internet.de/ustg_1980/__13b.html> (§ 13b UStG reverse charge)
