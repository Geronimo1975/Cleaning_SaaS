# Implementierung — how the marketplace attaches to what already exists

**What this covers:** the concrete Django work. What `apps.jobs` actually is and why it must not be
overloaded with customer orders; how `Account` / `AccountCapability` / `LegalStatus` already carry
the two-sided model; the entities that exist, the ones that do not, and how a `ServiceRequest`
should reach `planning.Shift`; the scoring inputs and their known weaknesses; and the settlement /
split-payment questions that must be answered before a single line of payment code is written.
**Stand: 2026-08-29, re-verified ~20:30 after a concurrent edit round** — `manage.py check` clean,
**190 tests passing**, `apps.marketplace` present with the award→contract seam built.
The repo is under active concurrent editing and is not under version control: re-read before citing.
**Marked:** **Fakt** (code `file:line`, or pland.app URL) / **Vorschlag** / **Ungeprüft**.

---

## 1. `apps.jobs` is a recruitment funnel, not an order book

**Fakt (code).** `apps/jobs/models.py` contains exactly two domain models:

| Model | Meaning | Fields that give it away |
|---|---|---|
| `JobPosting` = **Stellenanzeige** | an employer advertising a *position* | `employment_type` ∈ {FULL_TIME, PART_TIME, MINIJOB, CONTRACTOR, TEMPORARY} (`models.py:6-11`); `salary_min`/`salary_max`/`salary_unit` HOUR\|MONTH (`models.py:38-43`); `valid_through` mandatory for Google for Jobs (`models.py:49-50`) |
| `Application` = **Bewerbung** | a person applying for that position | `status` ∈ {NEW, VIEWED, SHORTLISTED, REJECTED, **HIRED**} (`models.py:80-85`) |

Its stated purpose is supply acquisition: `PLAN-FAZA-0.md:11-17` describes the chain
„anunț publicat → indexat în Google for Jobs → persoana aplică → aplicarea îi creează contul →
profilul devine public → directory-ul crește". `apps/jobs/models.py:89-92` says the same: applying is
also what creates the account and what raises the relation to `ENGAGED`.

`Application` is load-bearing far beyond the job board (**Fakt**):

- it is one of the three things `apps/accounts/visibility.py:90-95` queries to decide `ENGAGED`,
  which unlocks `phone`, `contact_email`, `street`, `postal_code` in `AccountView`
  (`visibility.py:47-50`);
- it is one of the **two** entry points to a contract — `apps/contracts/views.py:28-34`,
  „Contractul se naște dintr-o candidatură, nu din nimic"; the other is a won marketplace `Offer`
  (§4.1);
- awarding a contract sets `Application.status = HIRED` (`apps/contracts/views.py:53-54`).

### Why customer orders must never be pushed into it

1. **The status vocabularies mean different things.** `HIRED` is an employment event. A customer
   order ends in "done and paid", never in "hired". Overloading the enum makes both meanings
   unreadable and silently changes the `_is_engaged` semantics.
2. **The SEO contract is different.** `JobPosting` pages emit `schema.org/JobPosting` JSON-LD and are
   pushed to the Google Indexing API (`apps/jobs/models.py:124-134`). A customer order must **not**
   be indexed — it contains a private address. Mixing them in one model risks leaking one into the
   other's sitemap (`config/sitemaps.py`).
3. **The legal test is different.** A `JobPosting` openly advertises employment; that is lawful and
   desirable. A customer order routed to a natural person is the §7 SGB IV fact pattern
   (`rechtliche-grenzen.md` §3).
4. **`apps.marketplace` already exists and does this correctly.** There is no reason to reuse
   `apps.jobs`; there is only the temptation of a shorter diff.

**Known defect to fix separately (Fakt):** `EmploymentType.MINIJOB` (`apps/jobs/models.py:9`) is
emitted verbatim as `employmentType` in the JSON-LD (confirmed on the rendered job page in
`scratchpad/dossier/_verified-ground-truth.md`). `MINIJOB` is not a schema.org value; valid ones are
FULL_TIME, PART_TIME, CONTRACTOR, TEMPORARY, INTERN, VOLUNTEER, PER_DIEM, OTHER. Map it to
`PART_TIME` **in the JSON-LD builder only** — the German label „Minijob" must stay in the UI.

---

## 2. The two-sided model is already carried by `Account` — do not add a `role`

**Fakt (code), `apps/accounts/enums.py:11-21`:**

```python
class Capability(models.TextChoices):
    """
    Ce POATE FACE contul. Rânduri în AccountCapability, niciodată o coloană `role`.
    O firmă care e și prestator, și cumpărător de materiale primește două rânduri.
    """
    WORKER   = "WORKER",   "Prestator persoană fizică"
    PROVIDER = "PROVIDER", "Prestator firmă"
    SUPPLIER = "SUPPLIER", "Furnizor de materiale"
    CLIENT   = "CLIENT",   "Beneficiar"
    EMPLOYER = "EMPLOYER", "Angajator (publică anunțuri)"
```

Three axes, deliberately orthogonal (**Fakt**):

| Axis | Model / field | Mutability | Question it answers |
|---|---|---|---|
| **What the account IS** | `Account.entity_type` ∈ INDIVIDUAL \| COMPANY (`enums.py:4-8`) | „Imutabil după creare" | which profile model applies (`apps/accounts/profiles.py:37-39`, `63-65`) |
| **What it CAN DO** | `AccountCapability` rows, `UniqueConstraint(account, kind)` (`models.py:229-243`) | grant/revoke (`models.py:149-156`) | which dashboard panels and which views |
| **Under what legal form it works** | `Account.legal_status` ∈ UNDECLARED \| MINIJOB \| SELBSTSTAENDIG \| KLEINUNTERNEHMER \| COMPANY (`enums.py:24-35`) | editable | who the legal payer is, who issues the invoice, whether the platform may collect |

The third axis is the one a marketplace design usually forgets. Its docstring is explicit
(`enums.py:26-29`): „determină cine e plătitorul legal, cine emite factura și dacă platforma poate
încasa. Fără el, §35a EStG și Minijob-ul sunt imposibil de administrat."

Defaults granted at signup (**Fakt**, `apps/accounts/services.py:85-90`):

| Onboarding choice | Capabilities granted |
|---|---|
| `worker` | WORKER + CLIENT |
| `provider` | PROVIDER + CLIENT + EMPLOYER |
| `supplier` | SUPPLIER + CLIENT |
| `client` | CLIENT |

Note that a `provider` is an EMPLOYER by default — that is what lets a cleaning company that wins a
recurring contract go on to post `JobPosting`s, hire, and roster. The whole ladder from marketplace
win to legal execution is already reachable from one capability set.

**Enforcement (Fakt):** `CapabilityRequiredMixin` raises 403, never redirects, „un cont fără
capabilitate nu trebuie să afle ce există la acel URL" (`apps/accounts/permissions.py:23-44`).
`OwnedByAccountMixin` scopes every edit queryset to the active account (`permissions.py:47-57`).
The marketplace uses `Account.is_provider` (WORKER ∪ PROVIDER, `apps/accounts/models.py:158-160`) as
its bid gate (`apps/marketplace/services.py:42-43`, `views.py:150-151`).

**Rule:** a new marketplace feature adds a `Capability` row or a `LegalStatus` check. It never adds a
`role` field, never adds an `if account.entity_type == ...` branch to decide permission, and never
bypasses `AccountView` when rendering another account.

---

## 3. What is built today, precisely

**Fakt (code), all in `apps/marketplace/`, verified 2026-08-29** (models 200 lines, scoring 190,
services 216, views 184, forms 68):

```
accounts.Account ──client──▶ ServiceRequest ──awarded_offer(O2O)──▶ Offer ◀──provider── accounts.Account
                                   │                                  ▲
                                   ├── offers (FK, unique per provider)┘
                                   └── invitations (FK, unique per provider) ── Invitation.score/reasons
        taxonomy.ServiceCategory ──┘ (leaf only)      geo.Locality ──┘
```

| Field / property | Meaning | `file:line` |
|---|---|---|
| `ServiceRequest.is_open` | `status == OPEN and offers_close_at > now()` | `models.py:95-97` |
| `ServiceRequest.visits_per_month` | lookup into `VISITS_PER_MONTH` | `models.py:99-101` |
| `ServiceRequest.is_35a_eligible` | category flag **and** client is INDIVIDUAL | `models.py:103-108` |
| `Offer.monthly_price` | `price_per_visit × visits_per_month` | `models.py:157-159` |
| `Offer.implied_hourly` | `price_per_visit × 60 / estimated_minutes` — „singura bază reală de comparație" | `models.py:161-166` |
| `Offer.deduction_35a` | `min(monthly_price × 12 × 0.20, 4000.00)`, §35a Abs. 2 EStG | `models.py:168-174` |
| `Invitation` | suggestion only, ordered by `-score`, carries `reasons` JSON and `seen_at` | `models.py:177-200` |

Mounted at (**Fakt**, `apps/dashboard/urls.py:46-50`): `/dashboard/cereri/`,
`/dashboard/cereri/noua/`, `/dashboard/cereri/<pk>/`, `/dashboard/bursa/`,
`/dashboard/bursa/<pk>/oferta/` — Romanian dashboard segments, per the repo convention.

Dashboard panels are data, not templates (**Fakt**, `apps/dashboard/panels.py:47-56`): `requests`
for CLIENT, `open_requests` / `open_requests_co` for WORKER / PROVIDER. Adding a capability means
adding a row here, not an `if` in a template.

---

## 4. Vorschlag — the missing entities and where they attach

### 4.1 One seam is built, one is not

**Built — award → contract (Fakt, `apps/marketplace/services.py:125-196`).** A won `Offer` now
produces a `ContractDraft`, and the contract *type* is derived from the provider's `LegalStatus`
rather than chosen by anyone:

```python
CONTRACT_TYPE_BY_STATUS = {
    LegalStatus.SELBSTSTAENDIG:   "WERKVERTRAG",
    LegalStatus.KLEINUNTERNEHMER: "WERKVERTRAG",
    LegalStatus.COMPANY:          "WERKVERTRAG",
    LegalStatus.MINIJOB:          "MINIJOB",
}
```
— `apps/marketplace/services.py:125-131`. `LegalStatus.UNDECLARED` raises `MarketplaceError`
(`services.py:133-146`): „Fără Minijob înregistrat sau Gewerbeanmeldung nu se poate genera un
contract — orice altceva ar fi muncă nedeclarată." **This is the single most important line in the
layer.** It is the point where the platform refuses to paper over undeclared work.

Four further properties worth preserving (**Fakt**, `services.py:148-196`):

| Property | Where |
|---|---|
| only the client may generate it | `services.py:166-167` |
| the request must actually be AWARDED with a winning offer | `services.py:168-170` |
| **the numbers come from the offer, never retyped** — `estimated_minutes × visits_per_month / 60` becomes `hours_per_month`, `implied_hourly` becomes `hourly_wage` | `services.py:184-196` |
| generation is idempotent | `services.py:172-177` |

For a `MINIJOB` provider the generated contract's `employer` is the **client**
(`services.py:187-188`), which is the code stating the same thing `award_warnings` says in prose: in
a private household the customer becomes the employer. Covered by
`tests/test_marketplace.py:371-458` (`TestContractSeam`, 9 tests).

**Not built — award → planning (Fakt).** `grep -rn "planning\|Site\|Zone\|Shift" apps/marketplace/`
still returns nothing. So today an awarded *recurring* request produces a contract but **no `Site`,
no `Zone`, no roster** — the execution spine of §4.3 is missing.

**Known weakness in the built seam (Fakt, `services.py:172-177`):** the idempotency lookup keys on
`(employer, worker, start_date, workplace)` with `contract_type__isnull=False`, not on the offer.
Two genuinely distinct requests from the same client to the same provider, in the same locality,
starting on the same date, collapse onto the first contract. Key it on the `Offer` — or on the
`Assignment` proposed below.

### 4.2 `Assignment` — the missing record of execution

**Vorschlag.** One row per actually-agreed piece of work, created on award. It is the join that both
seams need.

```python
class Assignment(models.Model):
    """
    Ce s-a convenit efectiv, după atribuire. Separat de Offer pentru că oferta e
    o propunere, iar asta e o obligație — se poate reprograma, anula, factura.
    """
    request  = models.ForeignKey("marketplace.ServiceRequest", on_delete=models.PROTECT)
    offer    = models.OneToOneField("marketplace.Offer", on_delete=models.PROTECT)
    provider = models.ForeignKey("accounts.Account", on_delete=models.PROTECT,
                                 related_name="assignments_received")
    client   = models.ForeignKey("accounts.Account", on_delete=models.PROTECT,
                                 related_name="assignments_given")
    # SPOT: o singură dată. RECURRING: legătura către obiectivul creat în planning.
    scheduled_for = models.DateTimeField(null=True, blank=True)
    site          = models.ForeignKey("planning.Site", null=True, blank=True,
                                      on_delete=models.SET_NULL)
    agreed_price  = models.DecimalField(max_digits=8, decimal_places=2)
    agreed_minutes = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=12, choices=AssignmentStatus.choices)
```

`AssignmentStatus`: `AGREED → SCHEDULED → IN_PROGRESS → DONE → INVOICED → PAID`, plus `CANCELLED`
and `DISPUTED`.

Why a separate model rather than more fields on `Offer`: `Offer` is ordered by `price_per_visit`
(`apps/marketplace/models.py:147`) and constrained one-per-provider
(`models.py:148-150`). A rescheduled or partially-delivered job cannot live inside those two
constraints.

**Copy the frozen-text pattern from contracts.** `ContractDraft.rendered_body` +
`body_sha256` freeze the signed text so a later template edit cannot rewrite history
(`apps/contracts/models.py:116-125`, `156-158`; `apps/contracts/services.py:8-22`). An `Assignment`
should freeze the agreed scope the same way, because that text is what a Reklamation is judged
against.

### 4.3 The award transition, per regime

**Vorschlag.** One `services.py` function per regime, both `@transaction.atomic`.

**SPOT** — `award_offer()` additionally creates the `Assignment`:

```
award_offer(request, offer, actor)
  ├─ existing behaviour (services.py:100-119): offer→WON, others→LOST, request→AWARDED
  └─ NEW: Assignment.objects.create(..., status=AGREED, scheduled_for=offer.earliest_start)
```

The contract itself stays a separate, explicit step —
`create_contract_from_offer` is driven by an `action="contract"` POST from the client's request
detail page (`apps/marketplace/views.py:74-81`), not by the award. Keep that separation: awarding is
the client's choice of counterparty; generating a contract is the client accepting the legal role
that follows from the provider's `LegalStatus`. If that status is `UNDECLARED`, `award_warnings()`
says what must happen first (`apps/marketplace/services.py:73-86`) and `contract_type_for` then
refuses outright (`services.py:133-146`).

**RECURRING** — award is a much bigger transaction:

```
award_recurring(request, offer, actor)
  ├─ offer→WON, others→LOST, request→ACTIVE          (needs a new RequestStatus)
  ├─ Dauerauftrag(term, monthly_price, notice_period, escalation_clause)
  ├─ planning.Site.objects.create(account=<provider>, locality=request.locality, ...)
  ├─ for each Leistungsverzeichnis line:
  │     planning.Zone.objects.create(site=..., category=..., minutes_per_visit=...,
  │                                  visits_per_week=..., allowed_weekdays=...)
  └─ Assignment(site=<the new Site>, status=SCHEDULED)
```

Note whose account owns the `Site`: the **provider's**, because `generate_week_plan(account, ...)`
builds capacity from *that account's* signed contracts (`apps/planning/services.py:51-79`) and
`Zone` lookup is scoped `site__account=account` (`services.py:112-116`). Putting the Site on the
client's account would silently produce empty plans.

### 4.4 Where `planning.Shift` comes from — and why nothing here shortcuts it

**Fakt (code).** `generate_week_plan` is deliberately not an optimiser: „un optimizator care
«aproape» respectă plafonul de ore produce o încălcare legală. Aici, dacă o vizită nu încape fără să
spargă o regulă, rămâne NEALOCATĂ și apare în raport cu motivul" (`apps/planning/services.py:4-7`).
Refusals are recorded per worker with a reason (`services.py:82-95`) into
`ShiftPlan.unmet_demand` (`services.py:133-141`, `apps/planning/models.py:102-103`).

`build_capacities` (`services.py:51-79`) is the hard gate: capacity exists only for
`ContractDraft` rows with `status=SIGNED` overlapping the week — „Fără contract semnat, un om nu
poate fi planificat — planificarea nu e locul unde se creează raporturi de muncă."

**This is the answer to "can the platform auto-assign?".** It can — but only inside one account,
only to that account's contracted employees, and only within the ArbZG constraints. That is the
courier-agency half of the product, done lawfully. See `rechtliche-grenzen.md` §6.

**Vorschlag — a capacity pre-check before bidding.** `capacity_report(account, week_start)` already
returns demand / supply / deficit / utilisation (`services.py:172-188`). A provider about to bid on
a recurring request should see whether their contracted hours can absorb it *before* they commit.
That turns a legal constraint into a sales feature and costs one call.

### 4.5 Contract compliance — two entry points, one typed report

**Fakt.** There are now two ways a `ContractDraft` is born, and the rule „never from nothing" holds
on both:

| Entry point | Source | `file:line` |
|---|---|---|
| recruitment | a `jobs.Application` — „Contractul se naște dintr-o candidatură, nu din nimic" | `apps/contracts/views.py:28-34` |
| marketplace | a **won** `Offer` on an AWARDED request | `apps/marketplace/services.py:148-196` |

Both then run the same check, `ContractDraft.compliance_report()`
(`apps/contracts/models.py:196-254`), which returns typed findings rather than strings:

```python
@dataclass(frozen=True)
class ComplianceIssue:
    """O constatare de conformitate, cu severitate explicită."""
    code: str
    message: str
    blocking: bool
```
— `apps/contracts/models.py:44-54`. `compliance_issues()` (`models.py:193-195`) is now only the
message-only wrapper for display; `send_for_signature` filters on `i.blocking`
(`apps/contracts/services.py:25-32`).

The four codes and their severities (**Fakt**, `models.py:206-254`):

| `code` | Condition | `blocking` |
|---|---|---|
| `WAGE_FLOOR` | `hourly_wage` below `max(GENERAL, GEBAEUDE)` resolved at `start_date` | **`is_employment`** — True for VOLLZEIT/TEILZEIT/MINIJOB, **False for WERKVERTRAG** |
| `MINIJOB_LIMIT` | `monthly_gross` above `MinijobThreshold.current(start_date)` | True |
| `AUEG_LICENCE` | engagement model is TEMP_AGENCY | True |
| `SCHEINSELBSTSTAENDIGKEIT` | contract type is WERKVERTRAG | False (advisory) |

The `WAGE_FLOOR` asymmetry carries a real legal distinction, stated verbatim in the docstring
(`models.py:201-204`): „Severitatea e o proprietate a fiecărei constatări, nu ceva dedus din text.
Pragul de salariu blochează un contract de muncă, dar doar avertizează la un Dienstleistungsvertrag:
Mindestlohn-ul de ramură leagă angajatorii, nu onorariul unui prestator independent." The message
even switches noun — „Salariul orar" vs. „Onorariul orar" (`models.py:217`), and `blocking` is
literally `is_employment` (`models.py:211`, `:221`). Do not flatten this into one severity.

**Rule for new checks:** add a `ComplianceIssue` with a stable `code`, and decide `blocking`
explicitly. Never infer severity from message text.

---

## 5. Scoring — inputs, gaps, and what to change carefully

**Fakt (code), `apps/marketplace/scoring.py`.** Weights and computation are tabulated in
`zwei-vergabemodi.md` §2.3. The design premise is stated at `scoring.py:4-11`: an opaque score is
worse than no score, so every score carries its breakdown, and normalisation is **within the
request's own offer set** — „un scor nu are sens absolut, ci doar relativ la ce a primit clientul."

`ScoredOffer.explain()` returns `(label, percent, "pondere N %")` triples
(`scoring.py:51-55`) and the view attaches the legal warnings to each scored offer so they render
next to the award button, not in a separate list (`apps/marketplace/views.py:97-101`).

### 5.1 Known weaknesses

| # | Weakness | Evidence | Consequence |
|---|---|---|---|
| 1 | **No quality axis.** None of the five criteria is past performance. | `scoring.py:22-28` | A provider with 50 completed jobs ranks identically to one with none, given equal price/verification/experience. |
| 2 | `verification` is worth 0.25 but nothing sets `verification_level` automatically. | `scoring.py:101-102`; `VerificationDocument` has no level-derivation rule (`apps/accounts/compliance.py:22-41`) | A quarter of the ranking is driven by a manually-set integer. |
| 3 | `experience` for a company is a 3-flag proxy (0.4 base, +0.4 insurance, +0.2 HWK) that ignores `founded_year` and `employees_range`. | `scoring.py:125-133`; fields exist at `apps/accounts/profiles.py:46-54` | A 20-year-old firm without a recorded policy scores 0.4; a one-week-old firm that ticked two booleans scores 1.0. |
| 4 | `proximity` is a 3-step locality approximation while `Locality.latitude/longitude` exist. | `scoring.py:105-115`; `apps/geo/models.py:30-31`; the code says so itself at `scoring.py:106-110` | A neighbouring-town provider 4 km away scores 0.2, same as one 60 km away. |
| 5 | `WorkerProfile.willing_to_travel_km` is never read by the scorer. | field at `apps/accounts/profiles.py:26`; no reference in `scoring.py` | The provider's own stated radius is ignored. |
| 6 | `suggest_providers` requires **both** category and area to match. | `scoring.py:170-178` | In a thin market a request gets zero `Invitation`s and the client sees „0 prestatori potriviți au fost anunțați" (`apps/marketplace/views.py:59-63`). |
| 7 | Weights are platform-global constants. | `scoring.py:22-28` | Correct for a household; wrong for a tender, where the buyer sets the Bewertungskriterien (`zwei-vergabemodi.md` §3.3). |
| 8 | `insurance_valid_until` is never checked against the request date. | field at `apps/accounts/profiles.py:51`; `scoring.py:129-130` reads only the boolean | An expired policy still earns +0.4. |

### 5.2 Rules for changing the scorer

1. **Keep the breakdown.** Any new criterion must appear in `CRITERION_LABELS`
   (`scoring.py:30-36`) and in `WEIGHTS`, so `explain()` stays complete.
2. **Keep weights summing to 1.00.** Nothing enforces it today — `total` is a plain weighted sum
   (`scoring.py:83`). Add an assertion.
3. **Keep the tie-break deterministic.** `(-total, implied_hourly, pk)` (`scoring.py:91`). A
   nondeterministic ranking is unexplainable to a rejected provider.
4. **Do not let price exceed 0.30.** The comment at `scoring.py:18-21` records why 0.35 was rejected.
5. **Never let scoring create an obligation.** `suggest_providers` returns a list; the caller may
   only create `Invitation` rows (`apps/marketplace/services.py:27-32`).

---

## 6. Test invariants that must keep passing

**Fakt:** `tests/test_marketplace.py` holds 38 tests. Its module docstring names the two invariants
of the whole layer (`tests/test_marketplace.py:1-12`):

> 1. Nu există alocare automată. Sistemul sugerează; prestatorul decide. […] §7 SGB IV.
> 2. O ofertă nu dă acces la datele clientului.

Named tests that any change must not break: `test_sugestia_nu_este_repartizare` (:113),
`test_cel_mai_ieftin_nu_castiga_automat` (:191), `test_o_oferta_nu_deschide_datele_clientului`
(:290), `test_atribuirea_deschide_datele` (:298),
`test_pagina_de_ofertare_nu_arata_adresa` (:308),
`test_minijob_avertizeaza_ca_clientul_devine_angajator` (:271),
`test_pretul_sub_pragul_de_ramura_e_semnalat` (:346), and in `TestContractSeam` (:371-458)
`test_statut_nedeclarat_blocheaza_generarea` (:400) and
`test_cifrele_vin_din_oferta_nu_se_retasteaza` (:406).

Run: `.venv/bin/python -m pytest -q` (Python 3.12.13, Django 5.2.17).

---

## 7. Settlement and split payment — the questions that come before the code

**Nothing here is built.** `PLAN-FAZA-0.md:38-40` explicitly excludes payments, escrow, split
payment and digital signature from Faza 0; the signature part has since been built
(`apps/contracts/models.py:256-281`), the payment part has not.

`PLAN-FAZA-0.md:194-200` records the two blockers, written for the Romanian market but structurally
identical in Germany: there is no fiscally neutral gig worker, and **escrow is a regulated payment
service** — it cannot be built in-house.

### 7.1 Questions that must be answered first, in this order

| # | Question | Why it blocks code | Where the answer lands in the model |
|---|---|---|---|
| 1 | **Who is the legal payer** in each of the four provider constellations? | Determines whether money may flow through the platform at all | `Account.legal_status` (`apps/accounts/enums.py:24-35`) |
| 2 | **Who issues the invoice** — provider to client, or platform in the provider's name (Gutschriftverfahren)? | Different VAT treatment, different document, different retention duty | a new `Invoice` entity + a flag on the account |
| 3 | Is the platform an **agent** (collecting on behalf of the provider) or a **principal** (buying and reselling the service)? | Principal means the platform owes the wage floor and becomes the Auftraggeber for AÜG purposes | affects `Assignment` and every legal check in `rechtliche-grenzen.md` |
| 4 | **Kleinunternehmer (§19 UStG)** providers — how is VAT suppressed on their invoices? | `LegalStatus.KLEINUNTERNEHMER` exists (`enums.py:34`) but nothing consumes it | invoice line-level VAT rule |
| 5 | **§35a EStG** — the platform already *promises* the deduction (`apps/marketplace/services.py:87-91`, `scoring.py:152-156`). Who produces the invoice that makes it claimable, and is the payment traceably by bank transfer? | The promise is currently unbacked by any artefact | `Invoice` + payment method recorded on `Assignment` |
| 6 | **Minijob in a private household** — the client becomes the employer (`services.py:81-86`). Does the platform touch that money at all? | If yes, the platform is arguably running payroll for a household | probably: do not touch it; hand off to Minijob-Zentrale |
| 7 | **KYC for individuals without a Gewerbe** — `PLAN-FAZA-0.md:196-198` names this as the predictable blocker with Stripe Connect / Mangopay / Lemonway | Determines whether WORKER accounts can be paid out at all | account-level KYC state |
| 8 | Which **provider** — Stripe Connect (separate charges & transfers), Mangopay, Lemonway? | `PLAN-FAZA-0.md:197-198` lists these as the realistic EU options | a `PaymentAccount` model hanging off `Account`, per `apps/accounts/models.py:80-83` („mai târziu contul KYC la procesatorul de plăți — toate atârnă aici") |

### 7.2 The four constellations, and what each implies

**Vorschlag / Ungeprüft** — the mapping below is a design proposal; the tax treatment must be
confirmed with a Steuerberater before any of it is implemented.

| Client | Provider `legal_status` | Legal shape | Can the platform collect and split? |
|---|---|---|---|
| private household | `SELBSTSTAENDIG` / `KLEINUNTERNEHMER` | Dienst-/Werkvertrag, provider invoices the client | plausibly yes, as agent — this is the only clean case |
| private household | `MINIJOB` | client is the **employer**, Haushaltsscheck at the Minijob-Zentrale | **no** — do not intermediate wages |
| private household | `UNDECLARED` | undeclared work | **no** — must not be awardable at all; today it only warns (`services.py:73-80`) |
| company | `COMPANY` | B2B service contract, normal VAT, possibly reverse charge | yes, as agent; note **§13b Abs. 2 Nr. 8 UStG** reverse charge when a cleaning business buys cleaning from another (**Ungeprüft** — not on any crawled page) |

### 7.3 Things the data model must already be able to hold

`Account` is deliberately the anchor for this: „Profil, anunțuri, produse, iar mai târziu **contul
KYC la procesatorul de plăți** — toate atârnă aici, nu de User" (**Fakt**,
`apps/accounts/models.py:80-83`). Nothing needs restructuring to add payments; what is needed is:

- a `PaymentAccount` (FK `Account`, processor, external id, KYC status, payout method, verified_at);
- an `Invoice` that is **immutable once issued**, with corrections as credit notes — the same
  freeze-and-hash discipline already used for contracts (`apps/contracts/models.py:169-171`) and the
  same append-only discipline already used for `ConsentRecord`
  (`apps/accounts/compliance.py:67-70`) and `ShiftEvent` (`apps/planning/models.py:217-220`);
- a payment-method field on `Assignment`, because §35a needs "not cash" to be provable.

**Mostly Fakt (sourced below), partly Ungeprüft:** German invoice mandatory content is governed by
§14 UStG, retention is 10 years
(§147 AO / §257 HGB), digital bookkeeping must satisfy GoBD, and B2B businesses must be able to
*receive* structured E-Rechnungen (EN 16931 — XRechnung / ZUGFeRD) since 01.01.2025. Most of that is
**sourced** in the crawl: §14 UStG (invoice / Gutschrift content) is cited on
<https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>; GoBD plus the ten-year
revisionssichere retention on
<https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>; EN 16931,
Richtlinie 2014/55/EU, E-RechV, KoSIT and ZUGFeRD 2.2.0 / XRechnung on
<https://pland.app/blog/gebaudereinigung-xrechnung-pflicht-ab-2025> and
<https://pland.app/arbeitslexikon/e-rechnung>. Only **§19 UStG** and **§147 AO / §257 HGB** remain
**Ungeprüft**. Confirm those before building an invoicing module.

### 7.4 The rule

**Do not write payment code until questions 1–3 have written answers.** A split-payment integration
built on the wrong principal/agent assumption is not refactorable; it is a rebuild plus a tax
correction.

---

## 8. Sequencing — what to build in what order

**Vorschlag**, derived from the dependencies above:

| Order | Work | Unblocks |
|---|---|---|
| ~~0~~ | ~~`WageFloor` GEBAEUDE 2026 row; dated floor in the offer form; typed `ComplianceIssue`; award→contract seam~~ | **done 2026-08-29** — see SKILL.md §3 "Recently fixed" |
| 1 | Re-key `create_contract_from_offer` idempotency on the `Offer`, not on `(employer, worker, start_date, workplace)` | correctness of the seam that just landed |
| 2 | `expire_requests` management command + scheduler | the SPOT lifecycle actually terminating |
| 3 | `Assignment` + `award_offer` creating it | anything downstream of an award; also gives §1 its key |
| 4 | Review after completion → a quality axis in `WEIGHTS` | scoring weakness #1 |
| 5 | Verification ladder: document set → `verification_level` | scoring weakness #2, worth 0.25 |
| 6 | Recurring regime: `SiteVisit`, Leistungsverzeichnis, `Dauerauftrag`, award → `Site`/`Zone` | the entire B2B half of the market |
| 7 | Geocode `Locality`, replace `_proximity_score` | scoring weaknesses #4, #5 |
| 8 | Invoice entity (immutable, EN 16931-capable) | §35a promise, and payments |
| 9 | Payments — only after §7.1 questions 1–3 are answered | settlement |

---

## Quellen

Repository (read 2026-08-29, `/Users/Geronimo/Projects/Cleaning_SaaS`; Python 3.12.13,
Django 5.2.17, `manage.py check` clean, 190 tests passing):

- `apps/marketplace/models.py`, `scoring.py`, `services.py`, `views.py`, `forms.py`
- `apps/jobs/models.py`, `apps/jobs/management/commands/flush_indexing.py`
- `apps/accounts/enums.py`, `models.py`, `services.py`, `profiles.py`, `compliance.py`,
  `permissions.py`, `visibility.py`
- `apps/contracts/models.py`, `services.py`, `views.py`, `migrations/0002_seed_wage_floors.py`
- `apps/planning/models.py`, `services.py`
- `apps/taxonomy/models.py`, `apps/geo/models.py`
- `apps/dashboard/urls.py`, `apps/dashboard/panels.py`
- `config/urls.py`, `config/settings.py`
- `tests/test_marketplace.py`
- `PLAN-FAZA-0.md`, `prompt1.md`

pland.app (crawled 2026-08-29):

- <https://pland.app/blog/digitale-lohnabrechnung-ein-blick-auf-die-vorteile-in-der-gebaudereinigung>
- <https://pland.app/blog/ausschreibungen-in-der-gebaudereinigung-ein-leitfaden-fur-unternehmen>
- <https://pland.app/blog/gutschriften-in-der-gebaudereinigung-ein-leitfaden>
- <https://pland.app/blog/e-rechnungspflicht-alles-was-sie-wissen-mussen>
- <https://pland.app/blog/gebaudereinigung-xrechnung-pflicht-ab-2025>
- <https://pland.app/arbeitslexikon/e-rechnung>
- <https://pland.app/arbeitslexikon/unterhaltsreinigung>

Dossiers: `scratchpad/dossier/_verified-ground-truth.md`, `scratchpad/dossier/jobs.md`,
`scratchpad/dossier/accounts.md`, `scratchpad/dossier/planning-core.md`,
`scratchpad/knowledge/tutorials-gruendung.md`, `scratchpad/knowledge/blog-tarif-arbeitsrecht.md`.
