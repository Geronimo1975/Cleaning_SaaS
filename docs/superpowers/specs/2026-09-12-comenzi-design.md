# Modulul de comenzi (Customer + Order) — design

**Stand:** 2026-09-12. Derivat din `.claude/skills/gr-auftrag-und-faktura` (Vorschlag) și
din codul curent. Scope decis: doar `Customer` + `Order`; fără Quote/Invoice/Payment.

## Scop

Primul strat comercial: cine e clientul unui prestator și ce Auftrag are în execuție.
Comanda e containerul de care se vor lega, în planuri ulterioare, ofertele și facturile.

## Decizii

| Decizie | Alegere |
|---|---|
| App | `apps/billing` (un singur app pentru tot lanțul comercial, evită importuri circulare) |
| Sursa comenzii | Seam în `activate_recurring_request` — activarea creează `Customer`+`Order` în aceeași tranzacție. Fără formular de creare manuală în această iterație. |
| Numerotare | `A-{YYYY}-{NNNN}`, per prestator, per an, sub `select_for_update` pe `DocumentSequence` |
| Câmpuri de facturare pe Order (`billing_mode`, `next_billing_at` …) | **Nu** — vin cu planul de facturi |
| Migrare de date | Backfill din `ServiceRequest.status == ACTIVE`, idempotent prin `source_offer` |
| UI | Views server-rendered în dashboard: `clienti/`, `comenzi/`, `comenzi/<pk>/`, `comenzi/<pk>/stare/` |
| Capabilitate | `PROVIDER` sau `WORKER` (ambele licitează pe bursă); scoping prin `provider` |
| Admin | Da — `Customer`, `Order`, `DocumentSequence`; `order_number`/`source_offer` readonly |

## Modele (`apps/billing/models.py`, `enums.py`)

**Enums** (`TextChoices`, membri EN, etichete RO/DE):
- `DocumentType`: `ORDER = "ORDER", "Auftrag"` (se extinde cu tipuri de facturi mai târziu)
- `OrderStatus`: `ACTIVE "Activă"`, `SUSPENDED "Suspendată"`, `COMPLETED "Încheiată"`, `CANCELLED "Anulată"`
- `ContractKind`: `DIENSTVERTRAG "Dienstvertrag (§611 BGB)"`, `WERKVERTRAG "Werkvertrag (§631 BGB)"`

**Customer** — relație provider↔client, nu a doua tabelă de părți.
`provider` FK Account PROTECT `related_name="customers"`; `account` FK Account PROTECT
`related_name="customer_of"`; `customer_number` CharField(32, blank); `contact_person`
CharField(160, blank); `is_active` bool default True; `created_at` auto_now_add.
Constraints: `UniqueConstraint(provider, account, name="uniq_customer")`,
`CheckConstraint(~Q(provider=F("account")), name="customer_not_self")`.
`verbose_name="Client"`, plural `"Clienți"`. Datele juridice se citesc prin `customer.account`.

**DocumentSequence** — `provider` FK Account CASCADE `related_name="document_sequences"`;
`document_type` CharField(16, choices); `year` PositiveSmallInteger; `prefix` CharField(8,
default "A"); `next_number` PositiveInteger default 1.
`UniqueConstraint(provider, document_type, year, name="uniq_sequence")`.

**Order** — `provider` FK Account PROTECT `related_name="orders"`; `customer` FK Customer
PROTECT `related_name="orders"`; `site` FK `planning.Site` PROTECT `related_name="orders"`;
`category` FK `taxonomy.ServiceCategory` PROTECT `related_name="orders"`; `order_number`
CharField(32); `title` CharField(200); `start_date` DateField; `end_date` DateField null;
`contract_kind` CharField(16, choices, default DIENSTVERTRAG); `accepted_at` DateTimeField
null (Abnahme §641 BGB, doar WERKVERTRAG); `status` CharField(12, choices, default ACTIVE,
db_index); `source_offer` FK `marketplace.Offer` null SET_NULL `related_name="orders"`;
`created_at` auto_now_add.
`UniqueConstraint(provider, order_number, name="uniq_order_number_per_provider")`.
`clean()`: `site.account_id == provider_id`; `customer.provider_id == provider_id`;
`category` frunză (ca `Zone.clean()`); `end_date >= start_date` dacă ambele.
`verbose_name="Comandă"`, plural `"Comenzi"`. Nu e `TimeStampedModel` — se adaugă la lista
„fără timestamps" din `tests/test_common.py`.

## Numerotare (`apps/billing/numbering.py`)

```python
@transaction.atomic
def allocate(provider, document_type, year) -> str
```
`get_or_create` rândul, apoi `select_for_update().get(...)`, format
`f"{seq.prefix}-{year}-{seq.next_number:04d}"`, incrementează, `save(update_fields=...)`.
Garanția de lock ține doar pe Postgres; testul de concurență se sare pe SQLite.

## Servicii (`apps/billing/services.py`)

`class BillingError(ValueError)`.

`create_order_from_request(request, site, *, actor) -> Order`
- cere `request.status == ACTIVE` și `request.awarded_offer`; altfel `BillingError`
- idempotent: dacă există `Order(source_offer=offer)` îl întoarce
- `Customer.objects.get_or_create(provider=offer.provider, account=request.client)`
- `order_number = allocate(offer.provider, DocumentType.ORDER, offer.earliest_start.year)`
- `Order.objects.create(provider=offer.provider, customer=..., site=site,
  category=request.category, order_number=..., title=request.title[:200],
  start_date=offer.earliest_start, source_offer=offer)`; `full_clean()` înainte de save

`transition_order(order, new_status, *, actor) -> Order`
- `actor.pk == order.provider_id`, altfel `BillingError`
- muchii: `ACTIVE→SUSPENDED`, `SUSPENDED→ACTIVE`, `ACTIVE→COMPLETED`,
  `{ACTIVE,SUSPENDED}→CANCELLED`; orice altceva `BillingError`
- `COMPLETED` + `WERKVERTRAG` + `accepted_at is None` ⇒ `accepted_at = timezone.now()`

**Seam** (`apps/marketplace/services.py::activate_recurring_request`): după
`request.save(update_fields=["status"])`, import local
`from apps.billing.services import create_order_from_request` și apel
`create_order_from_request(request, site, actor=actor)`. Rămâne în `@transaction.atomic`.
Funcția întoarce în continuare `site`.

## Dashboard

`apps/dashboard/urls.py` (segmente RO, `name=` EN):
```
clienti/              CustomerListView      name="customers"
comenzi/              OrderListView         name="orders"
comenzi/<int:pk>/     OrderDetailView       name="order_detail"
comenzi/<int:pk>/stare/  order_transition_view (POST)  name="order_transition"
```
Views în `apps/billing/views.py`: `CapabilityRequiredMixin` cu
`required_capability=(Capability.PROVIDER, Capability.WORKER)` + `OwnedByAccountMixin` cu
`account_field="provider"`; `select_related("customer__account", "site", "category")`.
`order_transition_view`: `require_manage(request.membership)`, obiectul din queryset scoped
(404 pentru străin), `BillingError` ⇒ `messages.error` + redirect la detail.

Template-uri în `templates/dashboard/`: `customer_list.html`, `order_list.html`,
`order_detail.html`, extind baza existentă a dashboard-ului; formularul de stare e un
`<form method="post">` cu butoane pentru muchiile permise.

Panouri în `apps/dashboard/panels.py` (cheia `orders` e ocupată de comenzile de materiale):
```
Panel("customers",        "Clienți", "Beneficiarii pentru care execuți comenzi", "dashboard:customers", Capability.PROVIDER, order=50, icon="users")
Panel("service_orders",   "Comenzi", "Aufträge în execuție, suspendate, încheiate", "dashboard:orders",  Capability.PROVIDER, order=52, icon="file")
Panel("customers_w",      … același, Capability.WORKER, order=50)
Panel("service_orders_w", … același, Capability.WORKER, order=52)
```

## Admin (`apps/billing/admin.py`)

`CustomerAdmin`: list `provider, account, customer_number, is_active`; autocomplete
`provider, account`; `list_select_related`.
`OrderAdmin`: list `order_number, provider, customer, site, status, start_date`; filter
`status, contract_kind`; readonly `order_number, source_offer, created_at`; autocomplete
`provider, customer, site, category`.
`DocumentSequenceAdmin`: list `provider, document_type, year, prefix, next_number`.

## Migrații

`0001_initial` — schema.
`0002_backfill_orders` — `RunPython(forwards, noop)`. Pentru fiecare `ServiceRequest`
istoric cu `status="ACTIVE"` și `awarded_offer` non-null: Site =
`Site.objects.filter(account=offer.provider, name=request.title[:160]).first()` (cheia
folosită la activare; dacă lipsește, sare peste cerere); `Customer` get_or_create;
`DocumentSequence` get_or_create + increment (fără `select_for_update` — migrațiile rulează
serial); `Order` create dacă nu există `source_offer=offer`. Logica trăiește în
`apps/billing/backfill.py::backfill_orders(apps)` ca să poată fi testată direct cu
`django.apps.apps`.

## Teste (`tests/test_billing.py`, nume RO)

1. `allocate` dă `A-2026-0001`, apoi `A-2026-0002`; alt an ⇒ `A-2027-0001`.
2. 20 de fire pe Postgres ⇒ 20 numere distincte, fără goluri (skip pe SQLite).
3. `Order.clean()` refuză site străin, customer străin, categorie ne-frunză,
   `end_date < start_date`.
4. `Customer(provider=account=X)` ⇒ `IntegrityError`.
5. Activarea creează Customer + Order cu `start_date == offer.earliest_start`;
   a doua chemare a `create_order_from_request` întoarce același Order.
6. Tranziții legale trec; `COMPLETED→ACTIVE` ridică `BillingError`; `COMPLETED` pe
   WERKVERTRAG setează `accepted_at`; actor străin ⇒ `BillingError`.
7. `backfill_orders(apps)` pe o cerere ACTIVE pre-creată produce exact un Order; a doua
   rulare nu produce altul.
8. `tests/test_isolation.py`: străin ⇒ 404 pe `/dashboard/comenzi/<pk>/`; proprietar ⇒ 200;
   cont fără capabilitate ⇒ 403; POST `stare/` de la MEMBER fără `can_manage` ⇒ 403.
9. `tests/test_common.py`: `Customer`, `Order`, `DocumentSequence` în lista fără timestamps.
10. `tests/test_admin.py` trece fără exemptări noi.

## Ce NU face

- Nu creează formular de comandă manuală / client din afara platformei (plan ulterior).
- Nu atinge `award_offer`, planificarea sau alocarea de lucrători.
- Nu adaugă Quote, Invoice, Payment, TaxRate, cote sau sume în euro.
