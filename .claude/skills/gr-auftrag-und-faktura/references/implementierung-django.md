# Implementierung — the Django design for the commercial layer

> ## ⚠️ THE WHOLE OF THIS FILE IS **Vorschlag**.
> None of it exists in `/Users/Geronimo/Projects/Cleaning_SaaS`. Verified 2026-08-29 by
> reading every `models.py` under `apps/` and by
> `grep -rniE "invoice|rechnung|faktura|angebot|auftrag|mahnung|dunning" --include="*.py" --include="*.html"`,
> which returns only contract-template prose in
> `apps/contracts/migrations/0003_seed_templates.py:89-104`.
>
> Rows marked **Fakt (repo)** describe code that *does* exist and that this design attaches to.
> Rows marked **Fakt (source)** cite a pland.app page. Everything else is a proposal.

**Stand: 2026-08-29.** Django 5.2.17, Python 3.12.13, venv at
`/Users/Geronimo/Projects/Cleaning_SaaS/.venv`. Baseline before any change: `manage.py check`
clean, 190 tests passing (re-run `pytest` to confirm the current count before trusting this
number — the repo is edited concurrently).

---

## 1. Naming — resolve this before writing a line

**Fakt (repo).** The convention, from `_verified-ground-truth.md` and confirmed against
`apps/dashboard/urls.py`, `apps/marketplace/models.py` and `apps/planning/models.py`:

| Layer | Language | Evidence |
|---|---|---|
| Public URL segments | German | `/jobs/`, `/job/<slug>/bewerben/`, `/reinigungskraft/`, `/profil/` |
| Dashboard URL segments | Romanian | `anunturi`, `candidaturi`, `contracte`, `obiective`, `planificare`, `turele-mele`, `pontaj`, `calibrare`, `echipamente`, `cereri`, `bursa` (`apps/dashboard/urls.py`) |
| Code comments and docstrings | Romanian | `apps/marketplace/models.py:1-15`, `apps/planning/models.py:1-12` |
| Python identifiers, model and field names, URL `name=` | **English** | `ServiceRequest`, `Offer`, `Invitation`, `price_per_visit`, `name="open_requests"` |
| `verbose_name` / `choices` labels / seeded domain data | German or Romanian as the audience requires | `verbose_name = "Cerere de serviciu"` (`apps/marketplace/models.py:89`); German seeded localities and categories |

**Consequence.** The German document names in the domain (`Rechnung`, `Angebot`, `Auftrag`)
are **domain vocabulary**, not class names. Map them:

| German domain term | Django model (English) | Note |
|---|---|---|
| Kunde | `Customer` | a *relationship*, not a new party table — see §3.1 |
| **Objekt** | **`planning.Site`** — **already exists** | `apps/planning/models.py:21-39`, `verbose_name = "Obiectiv"`. **Do not create a second one.** |
| Raum / Bereich / Raumliste row | **`planning.Zone`** — **already exists** | `apps/planning/models.py:42-87` |
| Auftrag | `Order` | |
| Auftragsart | `ServiceCategory` — **already exists** | `apps/taxonomy/models.py:5-42`, leaves only |
| Angebot | `Quote` | |
| Leistungsverzeichnis-Position | `QuoteLine` | generated from `Zone` rows |
| Rechnung | `Invoice` | one model, `document_type` discriminator |
| Rechnungsposition | `InvoiceLine` | |
| Zahlung | `Payment` | |
| Mahnung | `DunningNotice` | + `DunningStageConfig` |

Put the German term in `verbose_name` and in the choice labels, so it reaches the UI without
entering the Python namespace.

---

## 2. App layout

**Vorschlag.** One new app, `apps/billing`, added to `INSTALLED_APPS` after
`apps.marketplace` (`config/settings.py:35`).

```
apps/billing/
    __init__.py
    apps.py
    enums.py          # all TextChoices — mirrors apps/accounts/enums.py
    models.py         # Customer, Order, Quote, Invoice, Payment, DunningNotice, …
    numbering.py      # DocumentSequence allocation, under select_for_update
    validators.py     # Pflichtangaben rules, one named rule per statutory item
    services.py       # issue_invoice, settle_predecessors, run_dunning, …
    calculation.py    # quote calculation + Deckungsbeitrag
    einvoice.py       # XRechnung / ZUGFeRD payload construction
    forms.py
    views.py
    migrations/
```

Why one app and not two: `Quote → Order → Invoice → Payment → DunningNotice` is a single
aggregate chain with cross-model invariants (a Schlussrechnung cannot be issued until its
predecessors are settled). Splitting it produces circular imports.

**Fakt (repo).** `apps/accounts/models.py:246-247` shows the repo's convention for keeping
`models.py` readable while presenting one module:

```python
from .compliance import *   # noqa: E402,F401,F403
from .profiles import *     # noqa: E402,F401,F403
```

Use the same trick if `billing/models.py` grows past ~400 lines.

**Fakt (repo).** There is **no `admin.py` anywhere** in `apps/` (verified by `find`). Do not
introduce one for this app without asking.

---

## 3. Models

### 3.1 `Customer` — a relationship, not a second party table

**Fakt (repo).** `accounts.Account` is described in its own docstring as
*"Entitatea centrală. Profil, anunțuri, produse … toate atârnă aici, nu de User."*
(`apps/accounts/models.py:79-83`) and already carries `legal_name`, `registration_number`,
`vat_id` (USt-IdNr.), `tax_number` (Steuernummer), `street`, `postal_code`, `phone`,
`contact_email` and a `locality` FK (`apps/accounts/models.py:89-107`).

```python
class Customer(models.Model):
    """
    Relația comercială dintre furnizor și beneficiar — NU o a doua tabelă de părți.
    Datele juridice (USt-IdNr., Steuernummer, adresă) rămân pe Account.
    """
    provider = models.ForeignKey("accounts.Account", on_delete=models.PROTECT,
                                 related_name="customers")
    account  = models.ForeignKey("accounts.Account", on_delete=models.PROTECT,
                                 related_name="customer_of")

    customer_number = models.CharField(max_length=32, blank=True)   # own numbering, optional
    contact_person  = models.CharField(max_length=160, blank=True)  # Ansprechpartner

    # Faktura defaults, overridable per document
    payment_term_days  = models.PositiveSmallIntegerField(default=30)
    payment_term_basis = models.CharField(max_length=12, choices=PaymentTermBasis.choices,
                                          default=PaymentTermBasis.ISSUE)
    default_tax_rate   = models.ForeignKey("TaxRate", null=True, blank=True,
                                           on_delete=models.PROTECT)

    # E-Rechnung
    is_public_authority = models.BooleanField(default=False)
    leitweg_id          = models.CharField(max_length=64, blank=True)
    einvoice_format     = models.CharField(max_length=12, choices=EInvoiceFormat.choices,
                                           blank=True)

    # §13b UStG — NEUVERIFICAT, vezi references/rechnungsarten.md §5.2
    reverse_charge_applies = models.BooleanField(default=False)

    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("provider", "account"), name="uniq_customer"),
            models.CheckConstraint(condition=~models.Q(provider=models.F("account")),
                                   name="customer_not_self"),
        ]
        verbose_name = "Client"           # Kunde
        verbose_name_plural = "Clienți"
```

Do **not** duplicate `vat_id`/`tax_number` here. Read them through `customer.account`.

**Fakt (source).** B2B vs B2C drives the default-interest spread (9 pp / 5 pp) and the B2C
duty to state consequences explicitly
(<https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-wie-und-wann-schreibe-ich-am-besten-zahlungserinnerungen-und-mahnungen>).
That distinction is already `Account.entity_type` (`apps/accounts/enums.py:4-8`). **Do not add
a `kunde_typ` field** — it would immediately drift from the Account.

**Fakt (source).** Rechnungsempfänger and Leistungsempfänger are separate roles and one
Rechnungsempfänger may have several Leistungsempfänger
(<https://pland.app/blog/rechnungsempfanger-und-leistungsempfanger-definition-und-unterschiede>,
<https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>). Model both as FKs on
the document (§3.5), not as a flag on `Customer`.

### 3.2 `Order` (Auftrag)

```python
class Order(models.Model):
    """
    Auftrag: containerul care leagă Angebot, Einsätze și Rechnungen.
    Nivelul la care se raportează Deckungsbeitrag.
    """
    provider = models.ForeignKey("accounts.Account", on_delete=models.PROTECT,
                                 related_name="orders")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    site     = models.ForeignKey("planning.Site", on_delete=models.PROTECT,
                                 related_name="orders")          # Objekt — deja există
    category = models.ForeignKey("taxonomy.ServiceCategory", on_delete=models.PROTECT,
                                 related_name="orders")          # Auftragsart

    order_number = models.CharField(max_length=32, unique=True)
    title        = models.CharField(max_length=200)
    start_date   = models.DateField()
    end_date     = models.DateField(null=True, blank=True)

    # Vertragsart decide dacă Abnahme/Gewährleistung se aplică — vezi rechnungsarten.md §8.6
    contract_kind = models.CharField(max_length=16, choices=ContractKind.choices,
                                     default=ContractKind.DIENSTVERTRAG)

    billing_mode     = models.CharField(max_length=16, choices=BillingMode.choices)
    billing_interval = models.CharField(max_length=12, choices=BillingInterval.choices,
                                        blank=True)
    billing_output   = models.CharField(max_length=12, choices=BillingOutput.choices,
                                        default=BillingOutput.DRAFT)
    next_billing_at  = models.DateField(null=True, blank=True)

    total_agreed_net = models.DecimalField(max_digits=12, decimal_places=2, null=True,
                                           blank=True)   # baza pentru Abschlag %
    accepted_at      = models.DateTimeField(null=True, blank=True)   # Abnahme (§641 BGB)

    status     = models.CharField(max_length=12, choices=OrderStatus.choices,
                                  default=OrderStatus.ACTIVE, db_index=True)
    source_offer = models.ForeignKey("marketplace.Offer", null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("provider", "status", "next_billing_at"))]
        verbose_name = "Comandă"          # Auftrag
```

**Fakt (repo).** `Site.account` is the owning Account (`apps/planning/models.py:24-26`), so
`Order.site` must be validated against `Order.provider` in `clean()`. `Zone.clean()`
(`apps/planning/models.py:82-87`) is the existing precedent for cross-FK validation.

**Fakt (source).** Billing settings on the Auftrag: **Manuell** or **Wiederkehrend**, an
**Intervall**, and an output mode **Entwurf erstellen** or **Fertigstellen**; the Aufträge list
filters by **Manuell / Wiederkehrend / Ohne Abrechnung**; all settings stay editable
afterwards. (<https://pland.app/onboardings/wiederholende-rechnungen-mit-pland-erstellen>)

### 3.3 `Quote` (Angebot) and `QuoteLine`

**Fakt (source).** A quote comprises **Angebotsschreiben, Leistungsverzeichnis, Raumlisten,
Sonderaufgaben**; must be sent **in writing**; must state Reinigungsturnus, Stundensätze,
Arbeitszeit, Material, Garantie-/Haftungsbedingungen and the Versicherungspolice; an accepted
quote converts to an Auftrag in one click with Objekt and Auftragsart prefilled.
(<https://pland.app/blog/wie-schreibe-ich-als-gebaudereinigung-gute-angebote>,
<https://pland.app/blog/gebaudereinigung-so-schreiben-sie-angebote>,
<https://pland.app/onboardings/wiederholende-rechnungen-mit-pland-erstellen>)

```python
from apps.marketplace.models import Frequency


class Quote(models.Model):
    provider = models.ForeignKey("accounts.Account", on_delete=models.PROTECT,
                                 related_name="quotes")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="quotes")
    site     = models.ForeignKey("planning.Site", on_delete=models.PROTECT,
                                 related_name="quotes")
    category = models.ForeignKey("taxonomy.ServiceCategory", on_delete=models.PROTECT,
                                 related_name="quotes")

    quote_number = models.CharField(max_length=32, unique=True)
    issue_date   = models.DateField()
    valid_until  = models.DateField()
    frequency    = models.CharField(max_length=12,
                                    choices=Frequency.choices)  # Reinigungsturnus

    # Blocuri de text impuse de sursă
    cover_letter        = models.TextField(blank=True)   # Angebotsschreiben
    warranty_terms      = models.TextField(blank=True)   # Garantie- und Haftungsbedingungen
    insurance_note      = models.TextField(blank=True)   # Versicherungspolice
    special_tasks       = models.TextField(blank=True)   # Sonderaufgaben
    equipment_note      = models.TextField(blank=True)   # Reinigungsmittel/-geräte, Marke+Modell

    # Rezultatul calculului — congelat la trimitere
    calculated_cost_net = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    margin_percent      = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    total_net           = models.DecimalField(max_digits=12, decimal_places=2)
    calculation_input   = models.JSONField(default=dict, blank=True)   # snapshot

    status       = models.CharField(max_length=12, choices=QuoteStatus.choices,
                                    default=QuoteStatus.DRAFT, db_index=True)
    sent_at      = models.DateTimeField(null=True, blank=True)
    decided_at   = models.DateTimeField(null=True, blank=True)
    order        = models.OneToOneField(Order, null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name="quote")
    rendered_body = models.TextField(blank=True)         # congelat, ca la ContractDraft
    body_sha256   = models.CharField(max_length=64, blank=True)


class QuoteLine(models.Model):
    """O poziție din Leistungsverzeichnis. Se generează din planning.Zone."""
    quote       = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="lines")
    position    = models.PositiveSmallIntegerField()      # LV position number
    zone        = models.ForeignKey("planning.Zone", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="quote_lines")
    category    = models.ForeignKey("taxonomy.ServiceCategory", on_delete=models.PROTECT)
    description = models.CharField(max_length=300)
    area_sqm    = models.PositiveIntegerField(null=True, blank=True)
    soiling     = models.CharField(max_length=8, choices=SoilingLevel.choices, blank=True)
    estimated_minutes = models.PositiveIntegerField(null=True, blank=True)
    visits_per_month  = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    quantity    = models.DecimalField(max_digits=10, decimal_places=3)
    unit        = models.CharField(max_length=16, choices=Unit.choices)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    line_net    = models.DecimalField(max_digits=12, decimal_places=2)
    is_special_task = models.BooleanField(default=False)   # Sonderaufgabe
```

**Fakt (repo).** Reuse `marketplace.VISITS_PER_MONTH` = ONE_TIME 1 · WEEKLY `4.33` ·
BIWEEKLY `2.17` · MONTHLY 1 as `Decimal` (`apps/marketplace/models.py:32-37`). Do **not**
define a second frequency→visits map.

**Fakt (repo).** `Zone` already carries `area_sqm`, `minutes_per_visit`, `visits_per_week`
and a leaf-only `category` (`apps/planning/models.py:48-87`). `QuoteLine` reads from it; it
does not restate it.

**Fakt (repo).** A `marketplace.Offer` is **not** a `Quote`. It is a bid on a standardised
`ServiceRequest`, with `price_per_visit`, `estimated_minutes` and a `UniqueConstraint(request,
provider)` (`apps/marketplace/models.py:122-174`). A won Offer becomes `Order.source_offer`.

### 3.4 `Invoice` — one model, one discriminator

```python
class Invoice(models.Model):
    provider = models.ForeignKey("accounts.Account", on_delete=models.PROTECT,
                                 related_name="invoices_issued")
    order    = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="invoices")

    # Rechnungs- vs Leistungsempfänger — DOUĂ chei, niciodată una singură.
    bill_to    = models.ForeignKey(Customer, on_delete=models.PROTECT,
                                   related_name="invoices_billed")     # Rechnungsempfänger
    service_to = models.ForeignKey("accounts.Account", on_delete=models.PROTECT,
                                   related_name="invoices_received")   # Leistungsempfänger

    document_type = models.CharField(max_length=16, choices=DocumentType.choices,
                                     db_index=True)
    advance_mode  = models.CharField(max_length=12, choices=AdvanceMode.choices, blank=True)

    document_number = models.CharField(max_length=32)   # alocat la emitere, nu la creare
    issue_date      = models.DateField(null=True, blank=True)

    # §14 Abs.4 Nr.6 UStG — Zeitpunkt der Leistung
    service_date         = models.DateField(null=True, blank=True)
    service_period_start = models.DateField(null=True, blank=True)   # Leistungszeitraum
    service_period_end   = models.DateField(null=True, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True) # doar ABSCHLAG

    # Sume — toate stocate, nu derivate la afișare (documentul cere toate trei)
    net_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_breakdown = models.JSONField(default=list, blank=True)  # [{rate, net, tax}] per cotă

    # Abschlag
    percent_of_total = models.DecimalField(max_digits=5, decimal_places=2, null=True,
                                           blank=True)
    total_order_net  = models.DecimalField(max_digits=12, decimal_places=2, null=True,
                                           blank=True)

    # Schlussrechnung: predecesorii care se verrechnen
    settles = models.ManyToManyField("self", symmetrical=False, blank=True,
                                     related_name="settled_by")
    # Storno / Gutschrift → factura corectată
    corrects = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="corrections")
    corrects_number = models.CharField(max_length=32, blank=True)   # congelat pe document
    corrects_date   = models.DateField(null=True, blank=True)
    correction_reason = models.TextField(blank=True)

    # Plată
    payment_term_days  = models.PositiveSmallIntegerField(default=30)
    payment_term_basis = models.CharField(max_length=12, choices=PaymentTermBasis.choices)
    due_date       = models.DateField(null=True, blank=True)
    accepted_methods = models.JSONField(default=list, blank=True)
    default_since  = models.DateField(null=True, blank=True)

    # E-Rechnung
    einvoice_format = models.CharField(max_length=12, choices=EInvoiceFormat.choices,
                                       blank=True)
    leitweg_id      = models.CharField(max_length=64, blank=True)   # copiat de pe Customer
    reverse_charge  = models.BooleanField(default=False)

    # Texte, congelate la emitere
    header_text = models.TextField(blank=True)
    footer_text = models.TextField(blank=True)
    notes       = models.TextField(blank=True)

    status     = models.CharField(max_length=24, choices=InvoiceStatus.choices,
                                  default=InvoiceStatus.DRAFT, db_index=True)
    issued_at  = models.DateTimeField(null=True, blank=True)
    sent_at    = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("provider", "document_number"),
                                    condition=~models.Q(document_number=""),
                                    name="uniq_invoice_number_per_provider"),
        ]
        indexes = [models.Index(fields=("provider", "status", "due_date"))]
        verbose_name = "Factură"        # Rechnung
```

`document_number` is blank while `DRAFT` and allocated at issue (§5). The partial unique
constraint tolerates blank drafts.

### 3.5 `InvoiceLine` (Rechnungsposition)

```python
class InvoiceLine(models.Model):
    invoice     = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    position    = models.PositiveSmallIntegerField()
    description = models.CharField(max_length=300)

    # Sursa liniei — o singură referință activă
    zone     = models.ForeignKey("planning.Zone", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="invoice_lines")
    shift    = models.ForeignKey("planning.Shift", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="invoice_lines")
    product  = models.ForeignKey("catalog.Product", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="invoice_lines")
    category = models.ForeignKey("taxonomy.ServiceCategory", null=True, blank=True,
                                 on_delete=models.PROTECT)

    quantity   = models.DecimalField(max_digits=10, decimal_places=3)
    unit       = models.CharField(max_length=16, choices=Unit.choices)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    tax_rate_percent = models.DecimalField(max_digits=4, decimal_places=2)  # congelat
    line_net   = models.DecimalField(max_digits=12, decimal_places=2)
    line_tax   = models.DecimalField(max_digits=12, decimal_places=2)
    line_gross = models.DecimalField(max_digits=12, decimal_places=2)

    # Poziție dinamică — vezi kalkulation-und-deckungsbeitrag.md §6.1
    dynamic_basis = models.CharField(max_length=12, choices=DynamicBasis.choices, blank=True)
    service_date  = models.DateField(null=True, blank=True)   # data Einsatz-ului facturat

    class Meta:
        ordering = ("position",)
        constraints = [
            models.UniqueConstraint(fields=("invoice", "position"), name="uniq_line_position"),
        ]
```

**Critical:** **no `MinValueValidator(0)` on `quantity`, `unit_price`, `line_net`,
`line_tax` or `line_gross`.** A Stornorechnung line is negative by construction
(<https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen>).
Note this differs from the repo's other money fields, which *do* validate positivity
(`apps/catalog/models.py:53`, `apps/marketplace/models.py:133`) — that difference is
deliberate and should carry a comment.

`tax_rate_percent` is **frozen on the line**, copied from the dated `TaxRate` at issue. Never
join to a live rate table when rendering an old invoice.

### 3.6 `Payment` (Zahlung)

```python
class Payment(models.Model):
    """Append-only. O corecție e un rând nou, nu un UPDATE — vezi ShiftEvent."""
    invoice     = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount      = models.DecimalField(max_digits=12, decimal_places=2)   # poate fi negativă
    received_at = models.DateField()
    method      = models.CharField(max_length=16, choices=PaymentMethod.choices)
    booking_reference = models.CharField(max_length=64, blank=True)
    note        = models.CharField(max_length=300, blank=True)
    recorded_by = models.ForeignKey("accounts.Account", null=True, on_delete=models.SET_NULL,
                                    related_name="payments_recorded")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("received_at",)

    def save(self, *args, **kwargs):
        if self.pk:
            raise RuntimeError("Plățile sunt imutabile. Adaugă un rând de corecție.")
        super().save(*args, **kwargs)
```

**Fakt (repo).** The `save()` guard is copied verbatim in shape from
`ShiftEvent.save()` (`apps/planning/models.py:217-220`) and
`ContractSignature.save()` (`apps/contracts/models.py:278-281`).

**Fakt (source).** `booking_reference` exists because incoming payments are matched
*"inklusive **Buchungsnummer**, Kunde und Betrag"*
(<https://pland.app/funktionen/umsatzuebersicht>).

### 3.7 `DunningNotice` and `DunningStageConfig` (Mahnung)

Field lists and rationale are in `references/mahnwesen.md` §8.3 — do not restate them here.
Two rules that belong in the model layer:

- `DunningNotice.save()` raises on re-save. A reissue is a **new notice**.
- `interest_rate_percent`, `base_rate_percent`, `outstanding_at_issue`, `new_due_date` and
  `fee_amount` are **frozen on the notice**, never recomputed at render.

### 3.8 Dated reference tables

**Fakt (repo).** `WageFloor` (`apps/contracts/models.py:57-89`) and `MinijobThreshold`
(`:92-113`) are the repo's established shape for a statutory value that changes over time:
`valid_from` / `valid_to` / `source_note` plus a `current(on=None)` classmethod. Its docstring
says it outright: *"Praguri salariale legale, cu valabilitate în timp — NU constante în cod."*

Copy that shape for **all four** of:

| Table | Holds | Why dated |
|---|---|---|
| `TaxRate` | Umsatzsteuersatz | Statutory, changes; `catalog.Product.vat_rate` default `19.00` (`apps/catalog/models.py:55`) is a catalogue convenience, **not** a source of truth for invoicing |
| `BaseInterestRate` | Basiszinssatz | **Ungeprüft:** changes twice a year. See `references/mahnwesen.md` §6 |
| `EInvoiceRule` | scope / duty / valid_from / min_amount / exemptions | The sources' dates are unreliable. See `references/e-rechnung-pflicht.md` §4.1 |
| `PriceBand` | min/max price per category × unit × region, with `source_note` | All published prices are ranges and contradict each other. See `references/kalkulation-und-deckungsbeitrag.md` §4.3 |

`PriceBand.source_note` must carry the URL the band came from, so the UI can show the user
where a suggested price originated.

### 3.9 `CostSettings` (Stammdaten for the calculation)

Per `accounts.Account`, one row: `hourly_wage_default`, `social_contribution_percent`,
`material_cost_percent`, `transport_cost_percent`, `admin_cost_percent`,
`other_cost_percent`, `office_rent_monthly`, `margin_percent`, `buffer_time_percent`.

Every one of these is a **configured value**. The sources name the components and give **no
formula, no percentage and no worked example**
(`references/kalkulation-und-deckungsbeitrag.md` §3). Ship them with **no defaults** where a
wrong default would silently mis-price, and force the tenant to fill them before the first
quote.

---

## 4. Enums (`apps/billing/enums.py`)

**Fakt (repo).** The convention is `models.TextChoices` with English member names and
Romanian labels, in a separate `enums.py` (`apps/accounts/enums.py`), or inline for
app-local ones (`apps/planning/models.py:90-93, 131-137`).

```python
class DocumentType(models.TextChoices):
    ABSCHLAG      = "ABSCHLAG",      "Abschlagsrechnung"
    TEIL          = "TEIL",          "Teilrechnung"
    SCHLUSS       = "SCHLUSS",       "Schlussrechnung"
    ABSCHLUSS     = "ABSCHLUSS",     "Abschlussrechnung"
    DAUER         = "DAUER",         "Dauerrechnung"
    EINZEL        = "EINZEL",        "Rechnung"
    STORNO        = "STORNO",        "Stornorechnung"
    GUTSCHRIFT    = "GUTSCHRIFT",    "Gutschrift"

class AdvanceMode(models.TextChoices):        # doar pentru ABSCHLAG
    EINFACH   = "EINFACH",   "Einfache Abschlagsrechnung"
    KUMULIERT = "KUMULIERT", "Kumulierte Abschlagsrechnung"

class InvoiceStatus(models.TextChoices):
    DRAFT            = "DRAFT",            "Ciornă"                    # Entwurf
    APPROVED         = "APPROVED",         "Verificată"                # Freigegeben
    ISSUED           = "ISSUED",           "Emisă"
    SENT             = "SENT",             "Trimisă"                   # Versendet
    PARTIALLY_PAID   = "PARTIALLY_PAID",   "Parțial plătită"
    PAID             = "PAID",             "Plătită"                   # Bezahlt
    OVERDUE          = "OVERDUE",          "Restantă"                  # Überfällig
    DUNNING_1        = "DUNNING_1",        "Somație 1"                 # Mahnstufe 1
    DUNNING_2        = "DUNNING_2",        "Somație 2"
    DUNNING_FINAL    = "DUNNING_FINAL",    "Ultima somație"
    LEGAL            = "LEGAL",            "Procedură judiciară"       # gerichtl. Mahnverfahren
    CANCELLED        = "CANCELLED",        "Stornată"                  # doar via Storno

class QuoteStatus(models.TextChoices):
    DRAFT = "DRAFT", "Ciornă"; SENT = "SENT", "Trimisă"
    ACCEPTED = "ACCEPTED", "Acceptată"; REJECTED = "REJECTED", "Respinsă"
    EXPIRED = "EXPIRED", "Expirată"

class OrderStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Activă"; SUSPENDED = "SUSPENDED", "Suspendată"
    COMPLETED = "COMPLETED", "Încheiată"; CANCELLED = "CANCELLED", "Anulată"

class BillingMode(models.TextChoices):
    MANUAL    = "MANUAL",    "Manuell"
    RECURRING = "RECURRING", "Wiederkehrend"
    NONE      = "NONE",      "Ohne Abrechnung"

class BillingOutput(models.TextChoices):
    DRAFT    = "DRAFT",    "Entwurf erstellen"
    FINALISE = "FINALISE", "Fertigstellen"

class BillingInterval(models.TextChoices):
    WEEKLY = "WEEKLY", "Wöchentlich"; MONTHLY = "MONTHLY", "Monatlich"
    CUSTOM = "CUSTOM", "Individuell"

class DynamicBasis(models.TextChoices):
    PLANNED_TIME = "PLANNED_TIME", "Soll-Zeit"
    PAID_TIME    = "PAID_TIME",    "Lohnzeit"
    PER_VISIT    = "PER_VISIT",    "Nach Termin"

class Unit(models.TextChoices):
    QM = "QM", "m²"; ROOM = "ROOM", "Raum"; FLOOR = "FLOOR", "Stockwerk"
    WINDOW = "WINDOW", "Fenster"; SANITARY = "SANITARY", "Sanitäranlage"
    HOUR = "HOUR", "Stunde"; LFM = "LFM", "laufender Meter"
    PIECE = "PIECE", "Stück"; FLAT = "FLAT", "Pauschal"

class EInvoiceFormat(models.TextChoices):
    XRECHNUNG = "XRECHNUNG", "XRechnung"
    ZUGFERD   = "ZUGFERD",   "ZUGFeRD"
    PDF       = "PDF",       "PDF"
    PAPER     = "PAPER",     "Papier"

class PaymentTermBasis(models.TextChoices):
    ISSUE = "ISSUE", "Ab Rechnungsdatum"
    RECEIPT = "RECEIPT", "Ab Erhalt der Rechnung"
    ACCEPTANCE = "ACCEPTANCE", "Ab Abnahme"

class PaymentMethod(models.TextChoices):
    TRANSFER = "TRANSFER", "Überweisung"; CHEQUE = "CHEQUE", "Scheck"
    CARD = "CARD", "Kreditkarte"; OTHER = "OTHER", "Sonstige"

class ContractKind(models.TextChoices):
    DIENSTVERTRAG = "DIENSTVERTRAG", "Dienstvertrag (§611 BGB)"
    WERKVERTRAG   = "WERKVERTRAG",   "Werkvertrag (§631 BGB)"

class SoilingLevel(models.TextChoices):
    LIGHT = "LIGHT", "Leicht"; NORMAL = "NORMAL", "Normal"; HEAVY = "HEAVY", "Stark"
```

`SoilingLevel.HEAVY` matters: heavy soiling reclassifies work as **Grundreinigung** with its
own pricing regime (<https://pland.app/blog/glasreinigung-welche-leistungen-sind-alles-enthalten-und-wie-kalkuliere-ich-sie>).

`ContractKind` is a **different axis** from `contracts.ContractType`
(`apps/contracts/models.py:30-34`), which classifies the *worker* engagement. Do not conflate
them.

---

## 5. Numbering — gapless, per year, per type, per tenant

**Fakt (source).** Requirements: "eindeutige Rechnungsnummer für jede Rechnung", numbers may
be "eine Abfolge von Zahlen **oder Buchstaben**", "sollte **fortlaufend** sein", a Storno gets
its **own new** number. Competitor mechanism: per document type a **Kürzel** plus a
**"Nächste Rechnungsnummer"**; 200 ⇒ next document `RE-201`, then +1.
(<https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen>,
<https://pland.app/blog/teilrechnung-alles-was-sie-wissen-mussen>,
<https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen>,
<https://pland.app/onboardings/die-wichtigsten-faktura-einstellungen-in-pland>)

```python
class DocumentSequence(models.Model):
    """
    Numerotare fără goluri, pe an, pe tip de document, pe furnizor.
    Numărul se alocă DOAR la emitere, sub lock — niciodată la crearea ciornei,
    altfel o ciornă abandonată lasă un gol în serie.
    """
    provider      = models.ForeignKey("accounts.Account", on_delete=models.CASCADE,
                                      related_name="document_sequences")
    document_type = models.CharField(max_length=16, choices=DocumentType.choices)
    year          = models.PositiveSmallIntegerField()
    prefix        = models.CharField(max_length=8, default="RE")   # Rechnungskürzel
    next_number   = models.PositiveIntegerField(default=1)
    # Setări per tip de document (sursa le ține tot per tip)
    header_text   = models.TextField(blank=True)     # Kopfzeilentext
    footer_text   = models.TextField(blank=True)     # Fußzeilentext
    payment_term_days = models.PositiveSmallIntegerField(default=30)   # Zahlungsziel
    letterhead    = models.ImageField(upload_to="letterhead/", blank=True)  # Briefpapier

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("provider", "document_type", "year"),
                                    name="uniq_sequence"),
        ]
```

```python
# apps/billing/numbering.py
from django.db import transaction

@transaction.atomic
def allocate(provider, document_type, year) -> str:
    seq = (DocumentSequence.objects
           .select_for_update()
           .get(provider=provider, document_type=document_type, year=year))
    number = f"{seq.prefix}-{year}-{seq.next_number:05d}"
    seq.next_number += 1
    seq.save(update_fields=["next_number"])
    return number
```

Rules:
1. Call `allocate()` **inside the same transaction** that flips the status to `ISSUED`.
2. Never derive a number from `pk`.
3. Never reuse a number from a cancelled document — a Storno consumes its **own** next number.
4. `select_for_update()` is required. **Note:** SQLite (the current dev DB, `db.sqlite3`) does
   not implement row-level locking; the guarantee only holds on PostgreSQL. `psycopg` and
   `dj-database-url` are declared but **not installed** in the venv
   (`_verified-ground-truth.md`), so this must be resolved before production.
5. The year rolls over: a new `DocumentSequence` row per year, created lazily by
   `get_or_create` at the first issue of the year.

---

## 6. Immutability of issued invoices

**Fakt (repo).** Three precedents already in the codebase:

| Precedent | Location | Mechanism |
|---|---|---|
| `ShiftEvent.save()` | `apps/planning/models.py:217-220` | raises `RuntimeError` if `self.pk` |
| `ContractSignature.save()` | `apps/contracts/models.py:278-281` | same, plus `document_sha256` |
| `ContractDraft.rendered_body` + `body_sha256` | `apps/contracts/models.py:127, 170-171` | template text copied at generation so later template edits cannot rewrite a signed document |
| `ConsentRecord.save()` | `apps/accounts/compliance.py:67-70` | *"Append-only. Nu se actualizează niciodată."* |

**Vorschlag.**

```python
LOCKED_STATUSES = {InvoiceStatus.ISSUED, InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID,
                   InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.DUNNING_1,
                   InvoiceStatus.DUNNING_2, InvoiceStatus.DUNNING_FINAL,
                   InvoiceStatus.LEGAL, InvoiceStatus.CANCELLED}

MUTABLE_AFTER_ISSUE = {"status", "sent_at", "delivered_at", "default_since"}

def save(self, *args, **kwargs):
    if self.pk:
        old = Invoice.objects.get(pk=self.pk)
        if old.status in LOCKED_STATUSES:
            changed = {f.name for f in self._meta.fields
                       if getattr(old, f.attname) != getattr(self, f.attname)}
            if changed - MUTABLE_AFTER_ISSUE:
                raise RuntimeError(
                    f"Factura {old.document_number} e emisă. Corectează printr-o "
                    f"Stornorechnung, nu prin editare. Câmpuri: {sorted(changed)}"
                )
    super().save(*args, **kwargs)
```

Plus:
- `InvoiceLine.save()` and `.delete()` refuse when `invoice.status in LOCKED_STATUSES`.
- `Invoice.delete()` refuses unconditionally for a non-`DRAFT` invoice.
- The rendered document (PDF and/or XML) is written once into `InvoiceArchive` with a
  `payload_sha256` (`references/e-rechnung-pflicht.md` §6) and never regenerated. A regenerated
  PDF that differs from the one the customer holds is a compliance incident, not a convenience.
- `retention_until = issue_date + 10 years` (GoBD; the *rule* is **Ungeprüft**, the
  10-year figure is **Fakt** from
  <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>).

---

## 7. State machines

### 7.1 Quote

```
DRAFT ──send──▶ SENT ──accept──▶ ACCEPTED ──convert──▶ Order created
                  │                                     (Quote.order set, one-to-one)
                  ├──reject──▶ REJECTED
                  └──valid_until passed──▶ EXPIRED
```
Freeze `rendered_body` + `body_sha256` on `send`. The quote the customer accepted must be
reproducible after the price list changes.

### 7.2 Invoice

The full diagram, transitions and the "court procedure is reachable directly" rule are in
`references/mahnwesen.md` §8.4. Three cross-model invariants belong in `services.py`, not in
`save()`:

1. **`SCHLUSS` gate.** A Schlussrechnung cannot leave `DRAFT` until every `ABSCHLAG`/`TEIL`
   invoice on the same `Order` is recorded in `settles` and offset.
   (<https://pland.app/arbeitslexikon/schlussrechnung>)
2. **`ABSCHLUSS`/`SCHLUSS` require order completion.** Only issuable when the Auftrag is
   finished (`Order.status == COMPLETED` or `accepted_at` set).
3. **`STORNO`/`GUTSCHRIFT` require a target.** `corrects` non-null, and `corrects_number` /
   `corrects_date` frozen onto the correcting document at issue.

### 7.3 Warranty clock

**Fakt (source).** Abschlag → warranty starts only at **Abnahme der Gesamtleistung**;
Teil → warranty starts **immediately** on the part-payment.
(<https://pland.app/arbeitslexikon/abschlagsrechnung>, <https://pland.app/arbeitslexikon/teilrechnung>)

```
Warranty(order, invoice|null, start_date, duration_months)
    TEIL      → start_date = payment.received_at
    ABSCHLAG  → start_date = order.accepted_at   (null until Abnahme)
```

**Ungeprüft.** This whole mechanism presupposes a **Werkvertrag**. Gate it on
`Order.contract_kind`; for `DIENSTVERTRAG` there may be no Abnahme and no Gewährleistung at
all. See `references/rechnungsarten.md` §8.6.

---

## 8. Services (`apps/billing/services.py`)

**Fakt (repo).** The repo puts business logic in `services.py` per app — `apps/accounts/services.py`,
`apps/contracts/services.py`, `apps/planning/services.py`, `apps/marketplace/services.py`,
`apps/devices/services.py`. Follow that; do not put it in views.

| Function | Contract |
|---|---|
| `issue_invoice(invoice, *, actor)` | Run the Pflichtangaben validator → allocate the number → set `issue_date`, `due_date`, freeze texts and tax rates → build the archive payload → status `ISSUED`. All inside **one** `transaction.atomic`. |
| `cancel_invoice(invoice, reason, *, actor)` | Create a `STORNO` with `corrects=invoice`, mirrored **negative** lines, its own number; then set `invoice.status = CANCELLED`. Never `delete()`. |
| `issue_credit_note(invoice, lines, reason, *, actor)` | As above but `document_type=GUTSCHRIFT`, partial lines allowed, and the mandatory "Hinweis auf Aufbewahrungspflicht" appended. |
| `build_final_invoice(order)` | Gather predecessors → populate `settles` → compute the residual **per tax rate at net + tax level**, not on the gross total (`references/rechnungsarten.md` §3). |
| `generate_recurring_invoices(on_date)` | For each `Order` with `billing_mode=RECURRING` and `next_billing_at <= on_date`: pull the Shifts in the Leistungszeitraum, resolve dynamic positions, then either save a draft or finalise, per `billing_output`. Advance `next_billing_at`. |
| `resolve_dynamic_line(order, product, basis, period)` | `PLANNED_TIME` → Σ `Shift.duration_minutes`; `PAID_TIME` → Σ `Shift.billable_minutes`; `PER_VISIT` → count of Shifts. Worked example to unit-test in §10. |
| `register_payment(invoice, amount, received_at, …)` | Append a `Payment` → recompute outstanding → move to `PARTIALLY_PAID` / `PAID`. |
| `mark_overdue(on_date)` | Date-driven only. A reminder does **not** cause default (§ 286 BGB). |
| `issue_dunning_notice(invoice, stage, *, actor)` | Compute interest per rate-validity segment, freeze the rates, allocate a number, require the B2C notice when `entity_type == INDIVIDUAL`. |
| `contribution_margin(order, period)` | `Σ invoiced_net − Σ labour_cost − Σ material_cost`, from a snapshot. See `references/kalkulation-und-deckungsbeitrag.md` §7. |

---

## 9. Dashboard wiring

**Fakt (repo).** `apps/dashboard/panels.py:1-7` states the design: the dashboard is data, not
four parallel templates — *"Adăugarea unei capabilități noi înseamnă un rând aici, nu un `if`
într-un template."* `Panel.url` returns `None` for a route that does not resolve yet
(`apps/dashboard/panels.py:24-34`), so panels can ship before their views. The `PANELS` list
is at `apps/dashboard/panels.py:45-90`.

**Fakt (repo).** `order` is scoped per capability, and the existing `Capability.PROVIDER` rows
use orders 10 (`company_profile`), 12 (`open_requests_co`) and 40 (`team`); `my_profile` at
order 10 belongs to `Capability.WORKER`. The
operational panels — `sites`, `planning`, `time_records`, `calibration`, `devices`,
`discrepancies` — are keyed to **`Capability.EMPLOYER`**, orders 30–39, not to `PROVIDER`.
Check which capability owns `planning.Site` in the version you are editing before picking a
capability for the invoicing panels, and pick free `order` values.

**Vorschlag — routes** (Romanian segments, English `name=`, matching `apps/dashboard/urls.py`):

```python
path("clienti/",              billing_views.CustomerListView.as_view(),  name="customers"),
path("clienti/nou/",          billing_views.CustomerCreateView.as_view(),name="customer_create"),
path("comenzi/",              billing_views.OrderListView.as_view(),     name="orders"),
path("comenzi/<int:pk>/",     billing_views.OrderDetailView.as_view(),   name="order_detail"),
path("oferte/",               billing_views.QuoteListView.as_view(),     name="quotes"),
path("oferte/noua/",          billing_views.quote_create_view,           name="quote_create"),
path("oferte/<int:pk>/acceptare/", billing_views.quote_accept_view,      name="quote_accept"),
path("facturi/",              billing_views.InvoiceListView.as_view(),   name="invoices"),
path("facturi/<int:pk>/",     billing_views.InvoiceDetailView.as_view(), name="invoice_detail"),
path("facturi/<int:pk>/emitere/",  billing_views.invoice_issue_view,     name="invoice_issue"),
path("facturi/<int:pk>/stornare/", billing_views.invoice_cancel_view,    name="invoice_cancel"),
path("incasari/",             billing_views.PaymentListView.as_view(),   name="payments"),
path("somatii/",              billing_views.DunningListView.as_view(),   name="dunning"),
```

**Vorschlag — panels**, added to `PANELS` in `apps/dashboard/panels.py`:

```python
Panel("customers", "Clienți", "Kunden și Objekte facturabile",
      "dashboard:customers", Capability.PROVIDER, order=50),
Panel("quotes", "Oferte", "Angebote și conversia în Auftrag",
      "dashboard:quotes", Capability.PROVIDER, order=52),
Panel("invoices", "Facturi", "Rechnungen, Abschlag/Teil/Schluss, E-Rechnung",
      "dashboard:invoices", Capability.PROVIDER, order=54),
Panel("dunning", "Somații", "Offene Posten și Mahnstufen",
      "dashboard:dunning", Capability.PROVIDER, order=56),
```

**Fakt (repo).** Templates live **outside** the apps, under `templates/dashboard/` — there are
no app-level template directories. Follow that.

**Authorisation.** Gate every write on `Membership.can_manage`
(`apps/accounts/models.py:224-226`) and scope every queryset to the acting Account. The repo
has an isolation test suite (`tests/test_isolation.py`); extend it rather than inventing a new
scoping mechanism.

---

## 10. Tests to write

**Fakt (repo).** `tests/` holds 12 test modules plus `conftest.py`; `pytest.ini` sets
`DJANGO_SETTINGS_MODULE=config.settings`, `testpaths=tests`, `addopts=-q --reuse-db`; 190 tests
pass as of the current check. Add `tests/test_billing.py` in the same style — do **not** put tests
inside the app.

| # | Test | Asserts |
|---|---|---|
| 1 | Numbering is gapless across 50 concurrent issues | no gaps, no duplicates |
| 2 | An abandoned draft consumes no number | sequence unchanged |
| 3 | Issuing in a new year starts a new sequence row | prefix + year correct |
| 4 | Editing any non-whitelisted field on an `ISSUED` invoice raises | `RuntimeError` |
| 5 | `Invoice.delete()` on a non-draft raises | `RuntimeError` |
| 6 | `Payment.save()` on an existing row raises | `RuntimeError` |
| 7 | A Storno mirrors the original with negative lines and its own number | sums net to zero |
| 8 | A Schlussrechnung cannot leave DRAFT with an unsettled predecessor | validation error |
| 9 | Schlussrechnung residual is computed per tax rate at net+tax level | not on the gross total |
| 10 | Kumulierte Abschlagsrechnung deducts earlier payments | matches §3 of rechnungsarten.md |
| 11 | An `ABSCHLAG` without `expected_delivery_date` when the service is not yet rendered fails validation | Pflichtangabe |
| 12 | An invoice without `service_to` fails validation | Leistungsempfänger mandatory |
| 13 | Interest for a `COMPANY` uses base + 9 pp; for an `INDIVIDUAL` base + 5 pp | rates from the dated table |
| 14 | Interest accrues per Basiszinssatz validity segment across a rate change | not one flat rate |
| 15 | A B2C dunning notice without the consequences block fails validation | §4 of mahnwesen.md |
| 16 | `OVERDUE` is entered by date, with no reminder sent | § 286 BGB |
| 17 | `LEGAL` is reachable directly from `OVERDUE` | no forced ladder |
| 18 | Dynamic position: 2 planned Shifts, 1 hour approved of 2 planned ⇒ `PAID_TIME` bills 1 h and `PER_VISIT` bills 2× Anfahrt | the source's own worked example |
| 19 | `WEEKLY` frequency uses `Decimal("4.33")` from `marketplace.VISITS_PER_MONTH` | no second constant |
| 20 | A non-leaf `ServiceCategory` on an invoice line fails validation | mirrors `Zone.clean()` / `ServiceRequest.clean()` |
| 21 | Invoice line totals use `Decimal` throughout, never float | rounding |
| 22 | Deckungsbeitrag: revenue 100 − variable 60 = 40 | the source's own worked example |
| 23 | A negative Deckungsbeitrag is flagged | source calls it a threat to profitability |
| 24 | Tenant isolation: Account A cannot read Account B's invoices | extends `tests/test_isolation.py` |
| 25 | Tax rate is frozen on the line — changing `TaxRate` does not alter an issued invoice | snapshot |

---

## 11. Build order

1. `TaxRate`, `BaseInterestRate`, `PriceBand`, `EInvoiceRule` — the dated tables, with the
   `WageFloor` pattern and a seed migration carrying `source_note` URLs.
   (The repo's seed-migration precedent: `apps/contracts/migrations/0002_seed_wage_floors.py`,
   `apps/taxonomy/migrations/0003_seed_categories.py`.)
2. `Customer` + `CostSettings`.
3. `DocumentSequence` + `numbering.allocate()` + tests 1–3.
4. `Invoice` + `InvoiceLine` + immutability guards + tests 4–5, 21, 25.
5. `validators.py` (Pflichtangaben, one named rule per statutory item) + tests 11–12, 20.
6. `Payment` + status transitions + tests 6, 16.
7. `Order` + `Quote` + `QuoteLine` + the calculation + tests 18–19, 22–23.
8. Storno / Gutschrift / Schlussrechnung offsetting + tests 7–10.
9. `DunningStageConfig` + `DunningNotice` + interest + tests 13–15, 17.
10. Dashboard routes, panels, templates + test 24.
11. E-invoice payload + `InvoiceArchive` — **last**, and only after the current § 14 UStG text
    and the BMF guidance have been checked (`references/e-rechnung-pflicht.md` §4).

Run after every step:
```bash
/Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python manage.py check
/Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python -m pytest -q
```

---

## 12. Things this design deliberately does NOT do

| Not done | Why |
|---|---|
| A second `Objekt` model | `planning.Site` is it (`apps/planning/models.py:21-39`) |
| A second frequency enum | `marketplace.Frequency` + `VISITS_PER_MONTH` exist (`apps/marketplace/models.py:25-37`) |
| A `role` column anywhere | The repo uses capability **rows** (`apps/accounts/models.py:229-243`) |
| A hard-coded e-invoicing date | Sources unreliable (`references/e-rechnung-pflicht.md` §4) |
| Hard-coded m²/h Leistungswerte | Not in the sources; `ZoneCalibration` measures them instead (`apps/planning/models.py:235-292`) |
| Hard-coded price defaults | Published ranges contradict each other 3–5× (`references/kalkulation-und-deckungsbeitrag.md` §4.3) |
| Default Mahnstufe intervals or Mahngebühren | Not stated on any page |
| A Deckungsbeitrag II tier | No allocation rule in the sources |
| A signature field on an invoice | Incompatible with XRechnung; the one source demanding it is questionable |
| An `admin.py` | The repo has none anywhere |
| Automatic assignment of work to a person | `apps/marketplace/models.py:10-14` — §7 SGB IV Scheinselbstständigkeit and AÜG. The commercial layer must not reintroduce it through the back door |

---

## Quellen

Repository files read for this document (all 2026-08-29):
- `/Users/Geronimo/Projects/Cleaning_SaaS/config/settings.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/config/urls.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/enums.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/compliance.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/taxonomy/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/geo/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/catalog/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/migrations/0003_seed_templates.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/marketplace/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/devices/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/dashboard/urls.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/dashboard/panels.py`
- `scratchpad/dossier/_verified-ground-truth.md` (environment, test baseline, language convention)

pland.app pages that constrain this design (crawled 2026-08-29):
- <https://pland.app/arbeitslexikon/abschlagsrechnung>
- <https://pland.app/arbeitslexikon/teilrechnung>
- <https://pland.app/arbeitslexikon/schlussrechnung>
- <https://pland.app/arbeitslexikon/dauerrechnung>
- <https://pland.app/blog/die-stornorechnung-fehler-korrigieren-und-klarheit-schaffen>
- <https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>
- <https://pland.app/blog/rechnungsempfanger-und-leistungsempfanger-definition-und-unterschiede>
- <https://pland.app/blog/gebaudereinigung-rechnungen-korrekt-stellen>
- <https://pland.app/blog/teilrechnung-alles-was-sie-wissen-mussen>
- <https://pland.app/blog/mahnwesen-in-der-gebaudereinigung-wie-und-wann-schreibe-ich-am-besten-zahlungserinnerungen-und-mahnungen>
- <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>
- <https://pland.app/blog/wie-schreibe-ich-als-gebaudereinigung-gute-angebote>
- <https://pland.app/blog/gebaudereinigung-so-schreiben-sie-angebote>
- <https://pland.app/blog/glasreinigung-welche-leistungen-sind-alles-enthalten-und-wie-kalkuliere-ich-sie>
- <https://pland.app/onboardings/die-wichtigsten-faktura-einstellungen-in-pland>
- <https://pland.app/onboardings/wiederholende-rechnungen-mit-pland-erstellen>
- <https://pland.app/onboardings/dynamische-positionen-in-rechnungen-mit-pland>
- <https://pland.app/funktionen/angebot-und-rechnung-gebaudereinigung>
- <https://pland.app/funktionen/umsatzuebersicht>

Sibling references in this skill:
- `references/rechnungsarten.md`
- `references/e-rechnung-pflicht.md`
- `references/kalkulation-und-deckungsbeitrag.md`
- `references/mahnwesen.md`
