# Rechnungsarten — the German invoice document types and their legal differences

**Covers:** Abschlagsrechnung, Teilrechnung, Schlussrechnung, Abschlussrechnung,
Dauerrechnung, Stornorechnung, Gutschrift — when each is used, what each must contain, how
they interact, the Rechnungsempfänger/Leistungsempfänger split, and the § 14 UStG mandatory
content list.

**Stand: 2026-08-29.** Material comes from the pland.app crawl of 2026-08-29 (raw pages under
`scratchpad/txt/`, each carrying its `# SOURCE:` URL) plus the dossiers
`knowledge/blog-faktura.md` and `knowledge/lexikon-betrieb.md`. Every factual row cites the
page it came from. Reference material for building software — not legal or tax advice.

Statement markers used throughout: **Fakt** (sourced), **Vorschlag** (design proposal),
**Ungeprüft** (added domain knowledge the crawled sources do not cover).

---

## 1. The seven document types at a glance

**Fakt.** Sources: <https://pland.app/arbeitslexikon/abschlagsrechnung> ·
<https://pland.app/arbeitslexikon/teilrechnung> · <https://pland.app/arbeitslexikon/schlussrechnung> ·
<https://pland.app/arbeitslexikon/dauerrechnung> ·
<https://pland.app/blog/abschlagsrechnung-teilrechnung-schlussrechnung-alles-was-sie-wissen-mussen> ·
<https://pland.app/blog/die-abschlussrechnung-in-der-gebaudereinigung-so-behalten-sie-den-uberblick> ·
<https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen> ·
<https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>

| Type | Bills what | Timing vs. performance | Warranty (Gewährleistung) effect | Synonyms on the pages |
|---|---|---|---|---|
| **Abschlagsrechnung** | "einen **Teilbetrag im Voraus** für eine **noch nicht vollständig erbrachte** Leistung"; refers to the **general project progress**; fixes **prozentuale Anteile der Gesamtsumme** | May be issued **before** the service is rendered | Gewährleistungspflichten **treten erst nach der Abnahme der Gesamtleistung ein** | Anzahlungsrechnung, **Akontorechnung** |
| **Teilrechnung** | "**spezifische und bereits abgeschlossene Teilleistungen**"; concrete **Meilensteine oder Teilergebnisse**; one or several items | Issued **after** that part is complete | Gewährleistungspflichten **beginnen unmittelbar nach den Teilzahlungen** | **Teilschlussrechnung** |
| **Schlussrechnung** | "sämtliche erbrachten Leistungen … die Gesamtkosten"; **offsets all Abschlags- und Teilzahlungen** and shows the difference | Only **after the whole project is finished** | not stated | **Endrechnung** |
| **Abschlussrechnung** | The closing invoice of a cleaning engagement, built from the contract (Reinigungsfrequenz, Flächen, Leistungen, Preise) plus materials/resources consumed | At completion of the engagement | not stated | — |
| **Dauerrechnung** | "wiederkehrende oder **kontinuierliche** Leistungen"; lists the recurring services, the **Abrechnungszeitraum** and the total for that period; **replaces** issuing a separate invoice per clean | Recurring — monthly, weekly, or another agreed interval | not stated | fortlaufende Rechnung, Pauschalrechnung (blog cluster only) |
| **Stornorechnung** | Corrects errors/discrepancies in an already-issued invoice; carries **negative amounts**; references the original | After the original invoice was issued | not stated | **Korrekturrechnung**, and — per that one page — "Gutschrift" (see §8.1) |
| **Gutschrift** | Document issued **by the service provider** to correct an earlier invoice or refund the customer, "ähnlich wie bei einer Stornorechnung" | After the original invoice | not stated | — |

**Fakt.** The Abschlag/Teil distinction is printed **verbatim identically** on both lexicon
pages, in both directions — it is a deliberate, load-bearing distinction, not incidental
wording. (`/arbeitslexikon/abschlagsrechnung`, `/arbeitslexikon/teilrechnung`)

### 1.1 The two sub-types of Abschlagsrechnung

**Fakt.** <https://pland.app/arbeitslexikon/abschlagsrechnung>,
<https://pland.app/blog/abschlagsrechnung-richtig-erstellen-schritt-fur-schritt-anleitung>

| Sub-type | Arithmetic |
|---|---|
| **Einfache Abschlagsrechnung** | A separate invoice per rendered Teilleistung; the residual is computed in the **Schlussrechnung** |
| **Kumulierte Abschlagsrechnung** | Bills **everything performed so far** and **deducts the payments from earlier invoices**, giving the customer a running cumulative view |

**Vorschlag.** One `document_type = ABSCHLAG` with a second enum
`advance_mode = EINFACH | KUMULIERT`. Same document, different arithmetic — not two types.

---

## 2. Pflichtangaben as actually printed, per document type

These are the lists the pages print. **None of them is presented as the § 14 UStG list**; see
§5 for that.

### 2.1 Abschlagsrechnung

**Fakt.** <https://pland.app/arbeitslexikon/abschlagsrechnung> (items 1–9 of the lexicon list),
and <https://pland.app/blog/abschlagsrechnung-richtig-erstellen-schritt-fur-schritt-anleitung>
(same list, plus the delivery-date sentence).

| # | Field (verbatim German) | Note |
|---|---|---|
| 1 | Kennzeichnung als Abschlagsrechnung | the type label is itself mandatory |
| 2 | Name und Anschrift des Leistungserbringers und des Kunden | both parties |
| 3 | Rechnungsnummer | |
| 4 | Rechnungsdatum | |
| 5 | Bezeichnung der Leistung und deren Umfang | |
| 6 | Wert der Leistung als Nettobetrag | |
| 7 | Auf die Leistung angewendeter Steuersatz, Steuerbetrag und Bruttobetrag | all three, separately |
| 8 | Steuernummer des Leistungserbringers | |
| 9 | Bankverbindung des Leistungserbringers | |
| 10 | **Erwarteter Lieferzeitpunkt**, wenn die Leistung noch nicht erbracht wurde | blog page only: *"Die Rechnung muss auch als Abschlagsrechnung gekennzeichnet sein und den erwarteten Lieferzeitpunkt angeben, wenn die Leistung noch nicht erbracht wurde."* |

**Fakt.** The Abschlagsrechnung list contains **no Zahlungsfrist** and **no USt-IdNr.** The
Teilrechnung list does contain both. This asymmetry is in the sources, not an extraction
error.

### 2.2 Teilrechnung

**Fakt.** <https://pland.app/arbeitslexikon/teilrechnung>

| # | Field (verbatim German) |
|---|---|
| 1 | Name und Anschrift des Leistungsempfängers (Kunde) |
| 2 | Name und Anschrift des Leistungserbringers (Anbieter) |
| 3 | Rechnungsnummer |
| 4 | Rechnungsdatum |
| 5 | Bezeichnung der erbrachten Teilleistung |
| 6 | Betrag der Teilleistung als Nettobetrag |
| 7 | Angabe des anwendbaren Steuersatzes, Steuerbetrag und Bruttobetrag |
| 8 | **Steuernummer und/oder Umsatzsteueridentifikationsnummer** des Leistungserbringers |
| 9 | **Zahlungsfrist** |
| 10 | Bankverbindung des Leistungserbringers |

**Fakt (second, longer list).** The blog cluster prints a 14-item list for a Teilrechnung
which is generic-commercial rather than cleaning-specific:
Rechnungsnummer ("eindeutige Nummer… sollte fortlaufend sein") · Rechnungsdatum ·
**Lieferdatum** · Name und Adresse des Verkäufers · Name und Adresse des Kunden ·
Beschreibung der gelieferten Waren oder erbrachten Dienstleistungen (with Menge, Einheiten,
Einzelpreis, Gesamtpreis) · **Mengeneinheiten** (Stück, Stunden, Kilogramm) · Preis pro
Einheit · Gesamtbetrag (incl. taxes and fees) · Zahlungsbedingungen (incl. Fälligkeitsdatum
and accepted payment methods) · Steuern und Gebühren · Bankverbindung ·
Informationen zur Lieferung · Hinweise oder Anmerkungen (e.g. warranty info, return terms).
Sources: <https://pland.app/blog/teilrechnung-alles-was-sie-wissen-mussen>,
<https://pland.app/blog/abschlagsrechnung-teilrechnung-schlussrechnung-alles-was-sie-wissen-mussen>

### 2.3 Schlussrechnung

**Fakt.** <https://pland.app/arbeitslexikon/schlussrechnung>. The page frames these as what
"enthalten sein sollte", not as statutory Pflichtangaben.

| Block | Verbatim requirement |
|---|---|
| Rechnungsdatum und -nummer | "ein eindeutiges Rechnungsdatum und eine eindeutige Rechnungsnummer" |
| Kontaktinformationen | of the cleaning company **and** the customer |
| Leistungsbeschreibung | "eine detaillierte Aufstellung der erbrachten Reinigungsleistungen sowie der jeweiligen **Preise und Einheiten**" |
| **Abschlags- und Teilzahlungen** | "sollten diese Beträge **aufgeführt und verrechnet** werden" |
| Gesamtbetrag | total for all services and associated costs |
| Zahlungsbedingungen | "klare Zahlungsbedingungen und Fristen" |

**Fakt.** The blog cluster adds: Ausstellungsdatum · Namen und Adressen des Verkäufers und
des Kunden · detaillierte Aufschlüsselung der erbrachten Leistungen oder gelieferten Waren ·
zugehörige Kosten · Steuern und Gebühren · Gesamtsumme; and states the Schlussrechnung must
show the **verbleibender Restbetrag** after Abschlagszahlungen.
(<https://pland.app/blog/schlussrechnung-einfach-erklart-bedeutung-aufbau-und-gesetzliche-vorgaben>,
<https://pland.app/blog/abschlagsrechnung-richtig-erstellen-schritt-fur-schritt-anleitung>)

### 2.4 Abschlussrechnung (cleaning-specific closing invoice)

**Fakt.** <https://pland.app/blog/die-abschlussrechnung-in-der-gebaudereinigung-so-behalten-sie-den-uberblick>

Kontaktdaten (name, address, phone, e-mail) · Rechnungsdatum und **fortlaufende
Rechnungsnummer** · Kundeninformationen (Firmenname, Ansprechpartner, Rechnungsadresse) ·
Leistungen und Preise **including the Reinigungsfrequenz and the zu reinigende Flächen** ·
Gesamtbetrag · Fälligkeitsdatum · akzeptierte Zahlungsmethoden.

Same page: payment terms are **14, 30 oder 60 Tage nach Erhalt der Rechnung**, "je nach
Vereinbarung"; payment methods named are Überweisung, Scheck, Kreditkarte "oder andere
Methoden".

### 2.5 General cleaning invoice

**Fakt.** <https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen> (duplicated
almost verbatim at <https://pland.app/tutorials/so-stellen-sie-rechnungen-als-gebaudereinigung>)

- Das Datum der Rechnungserstellung.
- Die vollständigen Kontaktdaten des Reinigungsunternehmens sowie des Kunden.
- Eine detaillierte Beschreibung der erbrachten Reinigungsleistungen, **einschließlich des
  Datums, an dem die Reinigung durchgeführt wurde**.
- Der Preis für die Reinigungsleistungen sowie der Umsatzsteuersatz und der Gesamtbetrag.
- Die Bedingungen für die Zahlung, einschließlich des Fälligkeitsdatums und der
  Zahlungsmodalitäten.
- Eine Erklärung der **Garantie- und Haftungsbedingungen** des Reinigungsunternehmens sowie
  seiner **Versicherungspolice**.

Additional rules stated on the same page:
- "Verwenden Sie eine **eindeutige Rechnungsnummer für jede Rechnung** … Verwenden Sie eine
  **Abfolge von Zahlen oder Buchstaben**" → numbers may be numeric **or** alphanumeric.
- The invoice must reflect *"genau den im Angebot vereinbarten Preis und Leistungsumfang"*.
- Invoices and payment receipts must be *"ordnungsgemäß aufbewahren"* and stay accessible.
- Line detail must state "der Art der Reinigungsdienstleistungen, der **Arbeitsstunden** und
  des **Preises pro Stunde oder Dienstleistung**".

### 2.6 Stornorechnung — the seven-part structure

**Fakt.** <https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen>

1. **Kopfdaten** — Unternehmensinformationen, Kundeninformationen, and **eine eindeutige
   Rechnungsnummer** (i.e. the Storno gets its **own new number**, not the original's).
2. **Deutlich sichtbar** die Bezeichnung **"Stornorechnung"** oder **"Korrekturrechnung"**.
3. **Referenz zur ursprünglichen Rechnung** — its **Rechnungsnummer und -datum**.
4. **Korrekturdetails** — what was wrong and how it is corrected: Positionen, Beträge, Gründe.
5. **Negative Beträge** — *"Stellen Sie sicher, dass die Beträge korrekt negativ sind."*
6. **Gesamtbetrag** — positive and negative amounts netted; shows how much is being corrected.
7. **Unterschrift und Ausstellungsdatum** *"um ihre Gültigkeit zu bestätigen"*.

⚠️ Item 7 is questionable and is **incompatible with a pure XRechnung**, which carries no
signature. German invoices generally require no signature. Flagged, not implemented. See §8.3.

**Fakt — reasons for a Stornorechnung** (same page): 1. Fehler in der ursprünglichen Rechnung
(Berechnung, falsche Einträge, Auslassungen) · 2. Retouren oder Rückerstattungen ·
3. nachträglich gewährte Preisnachlässe oder Rabatte · 4. Änderungen in den
Vertragsbedingungen.

### 2.7 Gutschrift

**Fakt.** <https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>

Verbatim: *"Da eine Gutschrift rechtlich mit einer Rechnung gleichgestellt ist, müssen auf
eine Gutschrift auch dieselben Pflichtangaben wie auf einer normalen Rechnung."*

| # | Field |
|---|---|
| 1 | Name & Anschrift des Leistungsempfängers |
| 2 | Datum der Ausstellung |
| 3 | Steuernummer |
| 4 | Genaue Bezeichnung der Produkte oder Leistungen |
| 5 | Rechnungsnummer |
| 6 | Steuerbetrag und Steuersatz |
| 7 | **Kennzeichnung, dass es sich um eine Gutschrift handelt** |
| 8 | **Hinweis auf Aufbewahrungspflicht** |

Also required by the page: *"der genauen Gründe für ihre Ausstellung, der korrigierten
Beträge und der **Referenz zur ursprünglichen Rechnung**"*.

**Fakt.** This is the closest the whole cluster comes to a "normal invoice" field list — and
it is presented as the *Gutschrift* list. It notably **omits the Leistungsdatum**.

**Fakt — reasons for a Gutschrift in cleaning** (same page): Qualitätsmängel oder
unzureichende Leistung · fehlerhafte Rechnungsstellung (falsche Mengenangaben oder
Preisberechnungen) · vereinbarte Rabatte oder Sonderkonditionen not applied on the invoice ·
Stornierung von Leistungen.

**Fakt — process before issuing** (same page): identify the problem precisely → **discuss it
transparently with the customer** so both sides agree on the solution → issue the Gutschrift
→ **adjust the Umsatzsteuer correctly** and report to the tax authority where required →
check contract terms (Rückzahlungen, Kündigungsfristen) → archive the Gutschrift and all
related documents.

### 2.8 Dauerrechnung

**Fakt.** <https://pland.app/arbeitslexikon/dauerrechnung>. The Dauerrechnung page gives
**no Pflichtangaben list at all** — only content elements and a 4-step process:

Content: die wiederkehrenden Reinigungsleistungen · der **Abrechnungszeitraum** · die
**Gesamtkosten für diesen Zeitraum**.

Process:
1. **Identifizieren Sie die wiederkehrenden Kosten** — which recurring services/fees belong in it.
2. **Festlegen des Abrechnungszeitraums** — "monatlich, wöchentlich oder nach individueller Vereinbarung".
3. **Erstellen Sie die Rechnung** — via accounting software / billing tool; all costs, the
   period and the total shown clearly.
4. **Kommunizieren Sie die Rechnung an den Kunden** — physically, by e-mail, or via an
   **Online-Portal**.

**Fakt.** The page states the Dauerrechnung is standard for cleaning because it *"erspart den
Kunden die Notwendigkeit, bei jeder Reinigung eine separate Rechnung auszustellen oder zu
empfangen."* Typical scenario named in the blog cluster: **Unterhaltsreinigung**, gewerbliche
Mietverträge, Wartungsverträge; created **once** and then "läuft automatisch weiter".
(<https://pland.app/blog/dauerrechnungen-in-der-gebaudereinigung>)

---

## 3. How the types interact — the arithmetic

**Fakt.** Rules stated across `/arbeitslexikon/schlussrechnung`,
`/arbeitslexikon/abschlagsrechnung`, `/blog/abschlagsrechnung-richtig-erstellen-schritt-fur-schritt-anleitung`
and `/blog/abschlagsrechnung-teilrechnung-schlussrechnung-alles-was-sie-wissen-mussen`:

```
Einfache Abschlagsrechnung   → separate document per Teilleistung
                               Restbetrag settled in the Schlussrechnung

Kumulierte Abschlagsrechnung → zu_zahlen = Σ(alle bisher erbrachten Leistungen)
                                          − Σ(bereits gezahlte Abschläge)

Schlussrechnung              → Restbetrag = Gesamtsumme
                                          − Σ(Abschlagszahlungen + Teilzahlungen)
                               and every predecessor must be PRINTED with its amount

Stornorechnung               → Gesamtbetrag = Σ(positive Positionen) + Σ(negative Positionen)
```

**Fakt — the Schlussrechnung build procedure** (<https://pland.app/blog/teilrechnung-alles-was-sie-wissen-mussen>,
<https://pland.app/blog/abschlagsrechnung-teilrechnung-schlussrechnung-alles-was-sie-wissen-mussen>):
1. Collect all relevant Teilrechnungen. 2. Check Rechnungsnummern, Daten, Mengen, Preise.
3. Sum the amounts. 4. Present the Schlussrechnung **listing all relevant Teilrechnungen with
their amounts**. 5. Verify tax and business requirements. 6. Retain copies of both the
Teilrechnungen and the Schlussrechnung.

**Ungeprüft — and important.** § 14 Abs. 5 UStG governs advance/partial-payment invoices, and
a Schlussrechnung must show and deduct the previously invoiced **net amounts and their VAT**,
not just gross totals. Offsetting only at gross level risks double VAT liability under
§ 14c UStG. Verify against the statute before implementing; then implement the offset at the
`net + tax` level per tax rate, never on a single gross figure.

---

## 4. Rechnungsempfänger vs. Leistungsempfänger

**Fakt.** <https://pland.app/blog/rechnungsempfanger-und-leistungsempfanger-definition-und-unterschiede>

| Role | Definition (verbatim sense) | Rule that binds the software |
|---|---|---|
| **Rechnungsempfänger** | "die natürliche Person oder juristische Einheit, die eine Rechnung erhält und für die wirtschaftlichen Transaktionen oder erbrachten Dienstleistungen in Rechnung gestellt werden"; carries responsibility for paying and normally books it | May be the Endkunde, a **Zwischenhändler**, a Geschäftseinheit, or a **zentrale Buchhaltungsabteilung**. *"muss nicht unbedingt auf der Rechnung selbst stehen, es reicht aus, wenn diese Information auf dem Umschlag vorhanden ist, **sofern die Rechnung nicht bereits elektronisch versandt wird**"* |
| **Leistungsempfänger** | "die Partei, die die erbrachte Leistung oder erhaltene Ware in Anspruch nimmt"; has the legal claim to performance | *"der Leistungsempfänger muss **zwingend** auf der Rechnung vermerkt sein, wenn der Kunde die **Vorsteuer** abziehen möchte"* — name **and** address on the invoice |

**Fakt.** *"Der Rechnungsempfänger muss nicht zwangsläufig identisch mit dem
Leistungsempfänger sein."* The two are separate roles.

**Fakt (competitor behaviour).** PlanD models them separately and allows **several**
Leistungsempfänger per Rechnungsempfänger: *"Verwalten Sie individuell Ihre
Rechnungsempfänger und fügen Sie bei Bedarf zusätzliche Leistungsempfänger hinzu."*
(<https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>)

**Vorschlag for this repo.**
- `Invoice.bill_to` → FK, the Rechnungsempfänger (payer / booking entity).
- `Invoice.service_to` → FK, the Leistungsempfänger. **Non-null and always rendered.**
- Because the envelope-only exception dies the moment the invoice is electronic, and the
  product's whole direction is electronic: **always render both**. The exception is not worth
  a branch.
- The natural anchor for both is `accounts.Account` (`apps/accounts/models.py:79`), which
  already carries `legal_name`, address, `vat_id`, `tax_number`.

---

## 5. § 14 UStG mandatory content

### 5.1 What the crawled sources actually say about § 14 UStG

**Fakt.** Across all 237 crawled pages, **§ 14 UStG is cited exactly once** — in the
Gutschrift article, and only to characterise a Gutschrift as *"so etwas wie eine umgekehrte
Rechnung"*. There is **no complete, labelled § 14 UStG field list anywhere in the crawl**.
The pages that print Pflichtangaben (§2 above) cite **no statute at all** — no § 14 UStG, no
§ 632a BGB, no VOB/B.
Source: <https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>; absence
verified by grep across `scratchpad/txt/`.

Items conspicuously **absent** from every list the pages print:
USt-IdNr. as a § 14 requirement · the fortlaufende Rechnungsnummer *described as statutory* ·
the **Zeitpunkt der Lieferung oder sonstigen Leistung** as a named statutory item · the
**Aufschlüsselung der Entgelte nach Steuersätzen und Steuerbefreiungen** · the
**Kleinbetragsrechnung** threshold · any **Reverse-Charge / § 13b UStG** hint · any
**Steuerbefreiung** note requirement.

### 5.2 The § 14 Abs. 4 UStG list — **Ungeprüft**

⚠️ **The whole of §5.2 is Ungeprüft.** It is not in the crawled sources. It is the standard
enumeration of § 14 Abs. 4 UStG as generally understood, reproduced here because an invoice
validator cannot be built from blog lists. **Before it reaches code, verify it against the
current statute text at <https://www.gesetze-im-internet.de/ustg_1980/__14.html> and the
BMF guidance, and record the version you checked.**

| # | § 14 Abs. 4 UStG item (Ungeprüft) | Field it implies |
|---|---|---|
| 1 | Vollständiger Name und vollständige Anschrift des **leistenden Unternehmers** | issuer block (from tenant master data) |
| 2 | Vollständiger Name und vollständige Anschrift des **Leistungsempfängers** | `service_to` — see §4 |
| 3 | Die vom Finanzamt erteilte **Steuernummer** oder die **USt-IdNr.** des leistenden Unternehmers | `Account.tax_number` / `Account.vat_id` (`apps/accounts/models.py:96-97`) |
| 4 | **Ausstellungsdatum** | `issue_date` |
| 5 | Eine **fortlaufende Nummer** mit einer oder mehreren Zahlenreihen, die zur Identifizierung der Rechnung einmalig vergeben wird | `document_number` from a gapless per-year sequence |
| 6 | **Menge und Art** der gelieferten Gegenstände / **Umfang und Art** der sonstigen Leistung | line `quantity`, `unit`, `description` |
| 7 | **Zeitpunkt der Lieferung oder sonstigen Leistung** (or of the Entgeltvereinnahmung for an advance payment) | `service_date` / `service_period_start`–`service_period_end` |
| 8 | Das nach **Steuersätzen und einzelnen Steuerbefreiungen aufgeschlüsselte Entgelt** und jede im Voraus vereinbarte **Minderung des Entgelts** | tax-rate subtotals table + discount fields |
| 9 | Der anzuwendende **Steuersatz** sowie der auf das Entgelt entfallende **Steuerbetrag** — oder im Fall einer Steuerbefreiung ein **Hinweis auf die Steuerbefreiung** | `tax_rate`, `tax_amount`, `exemption_note` |
| 10 | In den Fällen des § 14b Abs. 1 Satz 5 UStG ein **Hinweis auf die Aufbewahrungspflicht** des Leistungsempfängers | the "Hinweis auf Aufbewahrungspflicht" the Gutschrift page also demands (§2.7 item 8) |

Additional **Ungeprüft** items that a Gebäudereinigung validator will need:
- **"Gutschrift"** as a literal word on a self-billed document (§ 14 Abs. 2 UStG).
- **"Steuerschuldnerschaft des Leistungsempfängers"** where § 13b UStG reverse charge applies
  — highly relevant, because cleaning services supplied to a business that itself supplies
  cleaning services shift the VAT liability. None of the 237 pages mentions this.
- **Kleinunternehmer** note (§ 19 UStG) — the repo already has
  `LegalStatus.KLEINUNTERNEHMER` (`apps/accounts/enums.py:34`), so the flag exists; the
  required wording does not, and must be sourced.
- **Kleinbetragsrechnung** (§ 33 UStDV) reduced field set below a threshold — threshold value
  not established from the sources.

**Vorschlag.** Build the validator as a list of named rules with `(rule_id, applies_to_types,
message)`, not as a `full_clean()` blob, so each rule can carry the source it came from and
be switched off per document type. Run it as the gate between `DRAFT` and `ISSUED`.

---

## 6. Numbering

**Fakt.** Requirements found in the sources:
- "eindeutige Rechnungsnummer für jede Rechnung"; may be "eine Abfolge von Zahlen **oder
  Buchstaben**" (<https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen>)
- "eindeutige Nummer… **sollte fortlaufend sein**" (<https://pland.app/blog/teilrechnung-alles-was-sie-wissen-mussen>)
- "fortlaufende Rechnungsnummer" (<https://pland.app/blog/die-abschlussrechnung-in-der-gebaudereinigung-so-behalten-sie-den-uberblick>)
- A Stornorechnung takes **its own new** unique number, not the original's
  (<https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen>)

**Fakt (competitor mechanism).** PlanD stores, **per document type** (Rechnung, Angebot,
Gutschrift, Stornorechnung usw.): a **Rechnungskürzel**, a **"Nächste Rechnungsnummer"**, a
**Kopfzeilentext**, a **Fußzeilentext** and a **Zahlungsziel**, plus a Briefpapier/
Hintergrundbild upload. Worked example on the page: "Nächste Rechnungsnummer" = 200 ⇒ the
next document is **RE-201**, then it counts up by 1.
(<https://pland.app/onboardings/die-wichtigsten-faktura-einstellungen-in-pland>)

**Vorschlag.** `DocumentSequence(account, document_type, year, prefix, next_number)` with a
`UniqueConstraint` on `(account, document_type, year)`, allocated under
`select_for_update()`. Gapless per year, per type, per tenant. Details in
`references/implementierung-django.md` §5.

---

## 7. Immutability and correction

**Fakt (mechanism).** The sources never say "an invoice may not be edited". What they *do*
say is that a correction is made by issuing a **new document with its own number and negative
amounts** that references the original by number and date
(<https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen>), and
that a Gutschrift must carry a **reference to the original transaction** and be **archived**
with all related documents
(<https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>).

**Fakt.** E-Rechnungen must be stored **digital und revisionssicher für mindestens zehn
Jahre** under the **GoBD**
(<https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>).

**Ungeprüft.** "Revisionssicher" is generally understood to mean an issued invoice must not
be alterable at all — which is the reason the Storno mechanism exists. Treat the *rule* as
Ungeprüft; treat the *mechanism* (never edit, never delete, always a new linked negative
document) as the design, because the sources fully support the mechanism.

**Vorschlag.** The repo already has two precedents to copy verbatim:
- `ShiftEvent.save()` raises `RuntimeError` on any re-save (`apps/planning/models.py:217-220`).
- `ContractSignature.save()` does the same, plus a `document_sha256`
  (`apps/contracts/models.py:256-281`).
- `ContractDraft` freezes the rendered template body into `rendered_body` + `body_sha256` at
  generation, so later template edits cannot rewrite a signed document
  (`apps/contracts/models.py:116-171`). Do exactly this for issued invoice documents.

---

## 8. Contradictions and gaps in the sources — do not paper over these

1. **Storno vs. Gutschrift are conflated on one page and separated on another.**
   `/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen` calls a Stornorechnung
   *"auch als Korrekturrechnung oder Gutschrift bezeichnet"*, while
   `/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden` treats the Gutschrift as a
   separate document that is merely *"ähnlich wie bei einer Stornorechnung"* and gives it a
   **different** mandatory-field list.
   **Vorschlag:** two distinct `document_type` values sharing one `corrects` self-FK. Decide
   deliberately; do not let the ambiguity leak into the enum.

2. **The § 14 UStG description of the Gutschrift is internally inconsistent on its own page.**
   The article opens by defining the Gutschrift as *"ein Dokument, das vom **Dienstleister**
   ausgestellt wird"*, then says under § 14 UStG *"nicht der Kunde bekommt eine Rechnung,
   sondern lässt dem Rechnungssteller eine Gutschrift … zukommen. Dieser zahlt dann den
   entsprechenden Betrag an den Kunden zurück."* — i.e. self-billing by the customer and a
   provider-issued refund in the same paragraph. Recorded verbatim; **verify against the
   statute before implementing**. Source: same page.

3. **"Unterschrift" on a Stornorechnung** (§2.6 item 7) is questionable and incompatible with
   a structured XRechnung. Do not build a signature requirement into the invoice model.

4. **Dauerrechnung has no stated legal requirements at all** — no Pflichtangaben, no VAT
   treatment, and no rule for what happens when price or scope changes mid-term. The blog page
   mentions "trotz einiger geringer Einschränkungen" and never names the limitations.
   *Not established from the sources.*
   (<https://pland.app/blog/dauerrechnungen-in-der-gebaudereinigung>)

5. **The Abschlagsrechnung/Teilrechnung field lists disagree with each other** on Zahlungsfrist
   and USt-IdNr. (§2.1 vs §2.2). Both are recorded; the validator should take the union and
   flag which rule came from which page.

6. **Cleaning contracts are usually Dienstverträge (§ 611 BGB), not Werkverträge.**
   **Ungeprüft**, but decisive: the sources' Abnahme/Gewährleistung framing (and § 641 BGB
   in `references/mahnwesen.md`) implicitly assumes a Werkvertrag. Whether Abnahme and
   Gewährleistung apply at all depends on the contract type. **Vorschlag:** carry
   `contract_kind = DIENSTVERTRAG | WERKVERTRAG` on the Order, because it changes the entire
   warranty state machine. The repo already distinguishes
   `ContractType.WERKVERTRAG` for the *labour* side (`apps/contracts/models.py:34`) — that is
   a different axis (worker engagement), do not conflate them.

7. **§ 632a BGB (Abschlagszahlungen for Werkverträge)** and **VOB/B § 16** (Abschlags-,
   Teilschluss- and Schlusszahlungen) are the statutes that actually govern §1's document
   ladder. Neither is cited anywhere in the crawl. **Ungeprüft.**

---

## 9. Competitor feature surface (context, not requirements)

**Fakt.** Document types PlanD lists as supported: Angebot · Auftrag · Auftragsbestätigung ·
Arbeitsschein · Rechnung · **wiederkehrende Rechnung** · **Dauerrechnung** ·
**Abschlagsrechnung** · **Teilrechnung** · **Schlussrechnung** · **Stornorechnung** ·
**Gutschrift** · **Lieferschein** · Zahlungserinnerung · Mahnung (mehrstufig).
Sources: <https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung> ·
<https://pland.app/software-gebaeudereinigung> · <https://pland.app/funktionen/uebersicht>

**Fakt.** *"Erstellen Sie **beliebig viele** Abschlags- und Teilrechnungen und führen Sie
diese in **einer Schlussrechnung** zusammen."*
(<https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>)

**Fakt.** Invoice creation is triggered by completion: *"Ist ein Einsatz abgeschlossen,
erstellt PlanD automatisch die Rechnung"* (same page). A digitally signed **Arbeitsschein**
is *"in Echtzeit in die Fakturierung übergeben"*
(<https://pland.app/software-gebaeudereinigung>).

**Fakt.** Dispatch channels: ausdrucken · PDF-Download · automatisch per E-Mail · über das
**Kunden-Dashboard** · **Postversand** · **QR-Code** payment on the Arbeitsschein.
(<https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>, `/funktionen/uebersicht`,
`/funktionen/arbeitsscheine`)

**Fakt.** Accounting integrations named: **DATEV** and **Lexware**; payroll additionally
Relog/Addison; a **PSD2-konforme Bankanbindung** marks invoices paid automatically and
matches incoming payments *"inklusive Buchungsnummer, Kunde und Betrag"*.
(<https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>,
<https://pland.app/funktionen/umsatzuebersicht>,
<https://pland.app/blog/abschlagsrechnung-teilrechnung-schlussrechnung-alles-was-sie-wissen-mussen>)

**Fakt — announced but undocumented in the crawl:** **Sammelrechnungen**, invoice dispatch by
e-mail, and **Terminausfälle** mapped through dynamische Positionen — mentioned only in a
webinar teaser (Webinar 2, 12.02.2026). No mechanics given.
(<https://pland.app/tutorials-1/webinare>)

**Vendor claims, not facts:** "Steuerliche Einhaltung… stellt so sicher, dass Ihre Rechnungen
jederzeit den geltenden Gesetzen entsprechen"; "sorgt automatisch dafür, dass alle
rechtlichen Anforderungen erfüllt sind". Do not mirror this wording in our own product copy.

---

## Quellen

pland.app pages (crawled 2026-08-29):
- <https://pland.app/arbeitslexikon/abschlagsrechnung>
- <https://pland.app/arbeitslexikon/teilrechnung>
- <https://pland.app/arbeitslexikon/schlussrechnung>
- <https://pland.app/arbeitslexikon/dauerrechnung>
- <https://pland.app/blog/abschlagsrechnung-richtig-erstellen-schritt-fur-schritt-anleitung>
- <https://pland.app/blog/abschlagsrechnung-teilrechnung-schlussrechnung-alles-was-sie-wissen-mussen>
- <https://pland.app/blog/teilrechnung-alles-was-sie-wissen-mussen>
- <https://pland.app/blog/schlussrechnung-einfach-erklart-bedeutung-aufbau-und-gesetzliche-vorgaben>
- <https://pland.app/blog/dauerrechnungen-in-der-gebaudereinigung>
- <https://pland.app/blog/die-abschlussrechnung-in-der-gebaudereinigung-so-behalten-sie-den-uberblick>
- <https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen>
- <https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>
- <https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen>
- <https://pland.app/blog/rechnungsempfanger-und-leistungsempfanger-definition-und-unterschiede>
- <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>
- <https://pland.app/tutorials/so-stellen-sie-rechnungen-als-gebaudereinigung>
- <https://pland.app/onboardings/die-wichtigsten-faktura-einstellungen-in-pland>
- <https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>
- <https://pland.app/funktionen/umsatzuebersicht>
- <https://pland.app/funktionen/uebersicht>
- <https://pland.app/funktionen/arbeitsscheine>
- <https://pland.app/software-gebaeudereinigung>
- <https://pland.app/tutorials-1/webinare>

Repository files read for this document (2026-08-29):
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/enums.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py`

Statute text to verify §5.2 against (not yet checked):
- <https://www.gesetze-im-internet.de/ustg_1980/__14.html>
