# Verträge, Referenzdaten und Dashboard-UI

**Covers:** `apps.contracts` (creating a contract from an `Application`, the wage-floor gate,
the versioned templates, the frozen body and the e-signature); `apps.geo` + `apps.taxonomy` +
`apps.catalog` seeding through data migrations and how to add a locality or a category without
breaking SEO; and the dashboard / panels / templates conventions with a step-by-step recipe for
adding a dashboard page.
**Stand: 2026-08-29.**
**Sources:** `apps/contracts/*`, `apps/geo/*`, `apps/taxonomy/*`, `apps/catalog/models.py`,
`apps/dashboard/*`, `templates/dashboard/*`, `tests/test_contracts.py` — opened and confirmed
2026-08-29; seeded values re-queried from the live DB; cross-checked against
`scratchpad/dossier/contracts.md`, `reference-data.md`, `dashboard-ui.md`.

> **For the German legal substance** — what a Lohngruppe is, which Zuschläge exist, how the
> Mindestlohntarifvertrag becomes allgemeinverbindlich, how a Minijob is registered — use
> **`gr-tarif-und-lohn`**. This file is about how *this repository* stores and checks it.
> Legal content here is reference material, **not legal advice**.

---

# Part 1 — `apps.contracts`

## 1.1 Models (Fakt)

Module docstring (`apps/contracts/models.py:1-14`) codifies the legal boundary:

| Engagement | Meaning | Status in code |
|---|---|---|
| `DIRECT` — Angajare directă | the unit is the employer, the platform is an HR tool. No licence, no AÜG risk. **The default model.** | allowed |
| `INDEPENDENT` — Dienst-/Werkvertrag | contractor with a Gewerbe, multiple clients, own price. Legal only if the independence is real (§7 SGB IV) | allowed, always warns |
| `AUEG` — Detașare (AÜG) | the platform employs and lends people. Requires an Erlaubnis from the Bundesagentur für Arbeit | **blocked in code** |

```python
CONTRACT_ENGAGEMENT = {                       # models.py:37-42
    ContractType.VOLLZEIT:    EngagementModel.DIRECT_EMPLOYMENT,
    ContractType.TEILZEIT:    EngagementModel.DIRECT_EMPLOYMENT,
    ContractType.MINIJOB:     EngagementModel.DIRECT_EMPLOYMENT,
    ContractType.WERKVERTRAG: EngagementModel.INDEPENDENT,
}
```

**No fallback** — a new `ContractType` without a row here raises `KeyError` inside
`compliance_issues()`, which is called from the detail view's `get_context_data`, i.e. a 500.

`EngagementModel.TEMP_AGENCY` has the DB value **`"AUEG"`**, not `"AÜG"`. Do not "fix" the
spelling; nothing stores it yet but a change would need a data migration.

| Model | file:line | Notes |
|---|---|---|
| `WageFloor` | `:57-89` | `kind` (`GENERAL` = gesetzlicher Mindestlohn §1 MiLoG · `GEBAEUDE` = Branchen-Mindestlohn Gebäudereinigung LG1, allgemeinverbindlich), `hourly_amount`, `valid_from`, `valid_to` (nullable = open), `source_note(200)`. `Meta.ordering = ("kind","-valid_from")`. `current(kind, on=None)` classmethod returns the amount or `None` |
| `MinijobThreshold` | `:92-113` | `monthly_limit`, `valid_from`, `valid_to`, `source_note`. Docstring: since 2022 the Geringfügigkeitsgrenze is dynamic — Mindestlohn × 130 / 3, rounded up |
| `ContractTemplate` | `:116-140` | `contract_type`, `version`, `language` (default `"de"`), `title`, `body` (Django template source), `is_active`. `UniqueConstraint(("contract_type","version","language"))` |
| `ContractDraft` | `:151-253` | `employer`/`worker` FK `accounts.Account` **PROTECT** (`related_name="contracts_offered"` / `"contracts_received"`), `template` FK PROTECT, `contract_type`, `start_date`, `end_date`, `hours_per_month`, `hourly_wage`, `workplace` FK `geo.Locality` PROTECT (**no `related_name`**), `probation_months` (default 6), `vacation_days` (default 20), `rendered_body`, `body_sha256(64)`, `status` |
| `ContractSignature` | `:256-281` | `contract` FK CASCADE, `account` FK PROTECT, `signer_name(160)`, `signed_at`, `document_sha256`, `ip_address`, `user_agent(300)`. `UniqueConstraint(("contract","account"))`. **Immutable**: `save()` raises `RuntimeError` if `self.pk` |

`ContractType` (`:30-34`): `VOLLZEIT` · `TEILZEIT` · `MINIJOB` ("Minijob (până la 40 h/lună)")
· `WERKVERTRAG`.
`DraftStatus` (`:143-148`): `DRAFT` · `SENT` · `SIGNED` · `DECLINED` · `CANCELLED`.
Only `SENT` and `SIGNED` count as an engagement for visibility
(`apps/accounts/visibility.py:64`).

**Why the template body is copied, not referenced** (`ContractTemplate` docstring, `:117-121`):
*"Textul semnat NU se ia niciodată de aici la afișare — se copiază în
`ContractDraft.rendered_body` la generare. Altfel, o editare a șablonului ar rescrie retroactiv
contracte deja semnate."*

**Why a simple electronic signature suffices** (`ContractSignature` docstring, `:257-261`):
eIDAS Art. 25 + §126b BGB Textform; since January 2025, via the amended Nachweisgesetz, also for
documenting the employment relationship. Qualified signatures remain necessary only where the
law requires Schriftform.

## 1.2 The compliance gate (Fakt)

```python
@dataclass(frozen=True)                                   # models.py:45-54
class ComplianceIssue:
    """O constatare de conformitate, cu severitate explicită."""

    code: str
    message: str
    blocking: bool

    def __str__(self) -> str:
        return self.message


def compliance_issues(self) -> list[str]:                 # models.py:193-195
    """Mesajele verificărilor, pentru afișare. Severitatea: `compliance_report`."""
    return [issue.message for issue in self.compliance_report()]


def compliance_report(self) -> list["ComplianceIssue"]:   # models.py:197-249
    """
    Verificările care rulează ÎNAINTE de trimiterea spre semnare.

    Severitatea e o proprietate a fiecărei constatări, nu ceva dedus din text.
    """
    issues: list[ComplianceIssue] = []
    general = WageFloor.current(WageFloor.Kind.GENERAL, self.start_date)
    sector = WageFloor.current(WageFloor.Kind.GEBAEUDE, self.start_date)
    floor = max(x for x in (general, sector) if x is not None) if (general or sector) else None

    is_employment = self.contract_type != ContractType.WERKVERTRAG

    if floor and self.hourly_wage < floor:
        issues.append(ComplianceIssue(
            code="WAGE_FLOOR",
            message=(
                f"{'Salariul orar' if is_employment else 'Onorariul orar'} "
                f"{self.hourly_wage} € este sub pragul de {floor} € valabil la "
                f"{self.start_date:%d.%m.%Y}."
            ),
            blocking=is_employment,
        ))
    if self.contract_type == ContractType.MINIJOB:
        limit = MinijobThreshold.current(self.start_date)
        if limit and self.monthly_gross > limit:
            issues.append(ComplianceIssue(
                code="MINIJOB_LIMIT",
                message=(
                    f"Brutul lunar {self.monthly_gross} € depășește pragul Minijob "
                    f"de {limit} €. Raportul devine asigurat obligatoriu."
                ),
                blocking=True,
            ))
    if self.engagement_model == EngagementModel.TEMP_AGENCY:
        issues.append(ComplianceIssue(
            code="AUEG_LICENCE",
            message="Detașarea de personal necesită licență AÜG. Blocat.",
            blocking=True,
        ))
    if self.contract_type == ContractType.WERKVERTRAG:
        issues.append(ComplianceIssue(
            code="SCHEINSELBSTSTAENDIGKEIT",
            message=(
                "Verifică independența reală a prestatorului (Gewerbe activ, clienți "
                "multipli, preț propriu) — altfel e Scheinselbstständigkeit."
            ),
            blocking=False,
        ))
    return issues
```

Three rules follow:

1. **The applicable floor is the higher of the two**, evaluated at `start_date`, not today.
2. **Severity is a typed property of each finding, never deduced from the message text.**
   Every finding is a frozen `ComplianceIssue(code, message, blocking)`. The flags:
   `WAGE_FLOOR` → `blocking = contract_type != WERKVERTRAG` (the Branchen-Mindestlohn binds
   employers, not an independent contractor's fee), `MINIJOB_LIMIT` → `True`,
   `AUEG_LICENCE` → `True`, `SCHEINSELBSTSTAENDIGKEIT` → `False`.
   `send_for_signature` (`services.py:25-32`) filters on that flag:
   `blocking = [i.message for i in draft.compliance_report() if i.blocking]`.
   Pinned by `tests/test_contracts.py:43-50`
   (`test_severitatea_e_tipizata_nu_dedusa_din_text`). Do **not** reintroduce a substring
   test, and do not "simplify" `WAGE_FLOOR` to a constant `True`.
3. **Before 2025-01-01 there is no wage validation at all** — both `current()` calls return
   `None` and the whole check is skipped. Confirmed:
   `WageFloor.current("GENERAL", date(2024,6,1))` → `None`.

`monthly_gross` (`:189-191`) is `hours_per_month * hourly_wage` quantized to 2 dp — it needs
**`Decimal`** fields; passing `"40"` or `40.0` on an unsaved instance raises `TypeError` or
loses precision. Every fixture passes `Decimal(...)` for this reason.

## 1.3 Services — `apps/contracts/services.py` (Fakt)

| Function | file:line | Behaviour |
|---|---|---|
| `render_contract(draft)` | `:8-22` | renders `draft.template.body` with a **bare `Context`** (no `RequestContext`, no context processors), stores `rendered_body` and `body_sha256` |
| `send_for_signature(draft)` | `:25-33` | returns the blocking list; if empty, freezes the body and sets `status = SENT`. **No status precondition** — see §1.6 C2 |
| `active_template(contract_type, language="de")` | `:36-39` | `filter(is_active=True).order_by("-version").first()` — **lexicographic**, so `"1.10"` ranks below `"1.9"` |
| `sign_contract(draft, account, signer_name, request=None)` | `:42-69` | requires `status == SENT`, the signer to be a party, and no existing signature by that account. Stores `document_sha256 = draft.body_sha256`. When **both** parties have signed, flips `status = SIGNED` |
| `_ip(request)` | `:72-76` | first hop of `HTTP_X_FORWARDED_FOR`, else `REMOTE_ADDR` — **trusted unconditionally**, so `ip_address` is client-spoofable in a direct-exposure deployment. It is evidence data |

`sign_contract` docstring (`:43-47`): *"Se semnează HASH-UL textului înghețat — dacă documentul
s-ar schimba după semnare, hash-ul stocat nu ar mai corespunde și falsul ar fi demonstrabil."*

### The template context contract — exactly six names (`services.py:11-18`)

| Placeholder | Value | Dereferenced sub-attributes actually used by the seeded templates |
|---|---|---|
| `{{ title }}` | `draft.template.title` | — |
| `{{ employer }}` | `accounts.Account` | `legal_name`, `display_name`, `street`, `postal_code`, `locality.name` |
| `{{ worker }}` | `accounts.Account` | `display_name`, `street`, `postal_code`, `locality.name` |
| `{{ draft }}` | `ContractDraft` | `start_date`, `end_date`, `probation_months`, `hours_per_month`, `hourly_wage`, `vacation_days` |
| `{{ monthly_gross }}` | `Decimal` | — |
| `{{ workplace }}` | `geo.Locality` | `.name` — deliberately **not** `Locality.__str__`, which is `"Norderstedt (SH)"` |

Nothing else resolves. Rendering is localized German (`LANGUAGE_CODE = "de"`), so dates come out
as `1. Oktober 2026` and decimals as `14,25` / `570,00`.

## 1.4 Creating a contract from an `Application` (Fakt)

`contract_create(request, application_pk)` — `apps/contracts/views.py:28-60`, an **undecorated
function view** routed at `/dashboard/contracte/din-candidatura/<application_pk>/`.
Docstring: *"Contractul se naște dintr-o candidatură, nu din nimic."*

```python
application = get_object_or_404(
    Application.objects.select_related("job", "applicant_account"),
    pk=application_pk, job__account=request.account)        # foreign application -> 404
if Capability.EMPLOYER not in request.account.capability_set():
    raise Http404                                           # 404, not 403, here
instance = ContractDraft(employer=request.account,
                         worker=application.applicant_account,
                         workplace=application.job.locality)
form = ContractDraftForm(request.POST or None, instance=instance)
if request.method == "POST" and form.is_valid():
    draft = form.save(commit=False)
    draft.employer = request.account
    draft.worker   = application.applicant_account
    draft.template = active_template(draft.contract_type)   # language hard-wired to "de"
    if draft.template is None:
        messages.error(request, "Nu există șablon activ pentru acest tip de contract.")
    else:
        draft.save()
        application.status = ApplicationStatus.HIRED
        application.save(update_fields=["status"])
        return redirect("dashboard:contract_detail", pk=draft.pk)
```

Note: creating the draft flips the `Application` to `HIRED`. The guard is a 404 for both the
foreign-application case and the missing-capability case — an exception to the repo-wide
403/404 split, because this view is not a mixin-based CBV.

`ContractDraftForm.clean()` (`apps/contracts/forms.py:28-40`) builds an **unsaved probe
instance** and stashes `self.compliance_issues` on the form, so the legal problems appear in
the form (`templates/dashboard/contract_form.html:3-4`) **before** the contract is created.

`ContractDetailView` (`views.py:63-111`) handles two POST actions:

| `action` | Guard | Effect |
|---|---|---|
| `send` | `contract.employer_id == request.account.pk` | `send_for_signature`; blocking issues become `messages.error` |
| `sign` | `SignatureForm` valid | `sign_contract(...)`; `ValueError` becomes `messages.error` |

`ContractListView` / `ContractDetailView` build their queryset by combining two querysets with
`|` (`views.py:22-25`, `:69-71`) — so a worker sees contracts received and an employer sees
contracts offered. The `select_related` on the two operands does **not** both survive the union;
do not copy this as a performance pattern.

`templates/dashboard/contract_detail.html` renders `{{ contract.rendered_body|safe }}` (`:12`)
and the SHA-256 as *"Amprentă document"* (`:13`). `|safe` is only safe while
`ContractTemplate.body` is migration-controlled.

## 1.5 Seeded reference data — every row (Fakt, re-queried from the live DB 2026-08-29)

### `WageFloor` — `apps/contracts/migrations/0002_seed_wage_floors.py:15-21`

| `kind` | `hourly_amount` | `valid_from` | `valid_to` | `source_note` | Legal basis |
|---|---|---|---|---|---|
| `GENERAL` | **12.82** | 2025-01-01 | 2025-12-31 | `MiLoG 2025` | gesetzlicher Mindestlohn, §1 MiLoG |
| `GENERAL` | **13.90** | 2026-01-01 | *(open)* | `MiLoG 2026 — DE CONFIRMAT` | idem |
| `GEBAEUDE` | **14.25** | 2025-01-01 | 2025-12-31 | `Gebäudereinigung LG1 Innenreinigung, Mindestlohntarifvertrag 2025` | Branchen-Mindestlohn Gebäudereinigung LG1 (Innenreinigung), allgemeinverbindlich |
| `GEBAEUDE` | **15.00** | 2026-01-01 | *(open)* | `Lohntarifvertrag LG 1, ab 01.01.2026, allgemeinverbindlich (§ 7 AEntG)` | Lohntarifvertrag LG 1, allgemeinverbindlich per Rechtsverordnung nach § 7 AEntG (seeded by `0005_wage_floor_2026.py`) |

### `MinijobThreshold` — same migration, `:22-25`

| `monthly_limit` | `valid_from` | `valid_to` | `source_note` |
|---|---|---|---|
| **556.00** | 2025-01-01 | 2025-12-31 | `Geringfügigkeitsgrenze 2025` |
| **603.00** | 2026-01-01 | *(open)* | `Mindestlohn × 130/3 — DE CONFIRMAT` |

Formula cross-check: 13.90 × 130 / 3 = 602.33 → rounded up to 603.00.

**Stand and provenance.** These values come from the repository's own seed migration, whose
docstring (`:1-9`) warns verbatim: *"ATENȚIE: valorile de mai jos trebuie CONFIRMATE înainte de
a genera contracte reale."* **Two of the five rows are still flagged `— DE CONFIRMAT` in
`source_note`** (`GENERAL` 13.90 and `MinijobThreshold` 603.00). They are **not** verified against an official publication here — treat them as
placeholders until confirmed against the Bundesgesetzblatt / the Mindestlohntarifvertrag and
against `gr-tarif-und-lohn`. Tarif and statutory values change annually; re-check the
`source_note` and the `valid_from`/`valid_to` window before quoting any of them.

**One structural gap remains:** there is **no floor at all before 2025-01-01**. (The 2026
`GEBAEUDE` gap was closed by migration `0005_wage_floor_2026.py`, which caps the 14.25 € row at
2025-12-31 and opens a 15.00 € row from 2026-01-01; pinned by `tests/test_contracts.py:38-41`.)

### `ContractTemplate` — `0003_seed_templates.py`, re-applied by `0004_fix_template_titles.py`

All four rows: `version="1.0"`, `language="de"`, `is_active=True`, `body` prefixed with the
literal `"{% load i18n %}"` (added in `forwards`, `:114`).

| pk (dev DB) | `contract_type` | `title` | body length | Composition |
|---|---|---|---|---|
| 1 | `VOLLZEIT` | `Arbeitsvertrag – Vollzeit` | 1739 | `COMMON_HEADER` + §3 Arbeitszeit + §4 Vergütung + `COMMON_FOOTER` |
| 2 | `TEILZEIT` | `Arbeitsvertrag – Teilzeit` | 1875 | + §3 with the §4 TzBfG non-discrimination clause |
| 3 | `MINIJOB` | `Arbeitsvertrag – geringfügige Beschäftigung (Minijob)` | 2138 | + §4 citing §8 Abs. 1 Nr. 1 SGB IV, Minijob-Zentrale, and the §6 Abs. 1b SGB VI opt-out |
| 4 | `WERKVERTRAG` | `Dienstleistungsvertrag – selbständige Reinigungskraft` | 923 | **standalone**: Auftraggeber/Auftragnehmer header + §1 Gegenstand + §2 Selbständigkeit + §3 Vergütung. **No `COMMON_FOOTER`** — no Urlaub/Kündigung clauses, correctly, because it is not an employment contract |

Titles use a **U+2013 en dash**. Migration `0004`'s docstring explains why they were rewritten:
*"Titlurile conțineau entități HTML și ieșeau dublu-escapate la randare."*

`COMMON_HEADER` covers §1 Beginn und Dauer (with Probezeit) and §2 Tätigkeit und Arbeitsort.
`COMMON_FOOTER` covers §5 Urlaub (referencing §3 BUrlG), §6 Kündigung (§622 BGB, two weeks
during probation) and §7 Nebenabreden (Textform, §126b BGB).

The seed docstring (`0003:1-8`) is explicit that the text is *"un SCHELET juridic corect
structurat, nu un contract gata de semnat"* and must be reviewed once by a **Fachanwalt für
Arbeitsrecht** before real use. Structure follows **§2 NachweisG**.

`0004_fix_template_titles.py` re-runs `0003.forwards` via `importlib.import_module` — a pattern
worth copying when you need to re-apply a seed after a data fix.

## 1.6 Contract traps (Fakt)

| # | Trap |
|---|---|
| C1 | **Severity is a property of each finding, not deduced from the message.** `compliance_report()` returns `ComplianceIssue(code, message, blocking)`; `send_for_signature` filters on `i.blocking` (`services.py:26`). `WAGE_FLOOR` is deliberately `blocking=is_employment` — `False` for a `WERKVERTRAG`, `True` otherwise. Do not replace it with a constant or with a text test. |
| C2 | **`send_for_signature` has no status precondition.** An employer can POST `action=send` on a `SIGNED` contract (the button is hidden by `contract_detail.html:16`, but `views.py:90` only checks ownership). That re-renders the body, writes a **new** `body_sha256`, and resets `status = SENT` — silently invalidating every existing `ContractSignature.document_sha256`, i.e. destroying the evidence the design protects. **Add a status guard before touching this view.** |
| C3 | **`compliance_issues()` is recomputed on every detail-page load** (`views.py:77`) against *today's* `WageFloor` table. A contract signed in 2025 starts showing "sub pragul legal" once a higher 2027 floor is seeded. There is no `checked_at` snapshot. |
| C4 | **A contract starting before 2025-01-01 gets no wage validation at all.** |
| C5 | **`active_template` sorts version strings lexicographically** and is called **without `language`** from `contract_create` (`views.py:48`) — the `language` column is effectively hard-wired to `"de"`. |
| C6 | **`CONTRACT_ENGAGEMENT` has no fallback** → `KeyError` → 500 on the detail page for a new `ContractType`. |
| C7 | **`ContractDraft.clean()` only runs through the ModelForm.** Direct `objects.create(end_date=<before start>)` succeeds — every fixture in the repo creates drafts that way. |
| C8 | **`ContractSignature.save()` raises `RuntimeError`, not `ValidationError`** — a future `ModelAdmin`, a `loaddata` or a bulk fixup script crashes bare. |
| C9 | **`X-Forwarded-For` is trusted unconditionally** (`services.py:74-76`). |
| C10 | **The employer-only account has no link to its contract list.** The `Contractele mele` panel is gated on `Capability.WORKER` (`apps/dashboard/panels.py:62-63`) even though `ContractListView` shows both sides. |
| C11 | **Two `_ip()` helpers exist** — `apps/accounts/services.py:65-69` and `apps/contracts/services.py:72-76`. Fixing one does not fix the other. |
| C12 | **`ContractDraft.workplace` has no `related_name`**, so it is reachable only as `locality.contractdraft_set`, inconsistent with the other four FKs into `Locality`. |
| C13 | **`--reuse-db` in `pytest.ini`**: after adding a data migration the reused test DB will not have the new rows. Run once with `--create-db`. |

Tests — `tests/test_contracts.py` (16): `TestCompliance` pins the seeded values verbatim
(`:33-36`), the 2026 Branchen-Tarif of 15.00 € (`:38-41`), the typed severity
(`:43-50`), the 40 h × 15.00 € = 600.00 € valid Minijob against the 603.00 € 2026 threshold —
at the limit (`:52-56`), the threshold breach at
41 h and at 45 h (`:58-66`), the higher-floor rule (`:68-74`), the Werkvertrag warning
(`:76-79`), and the warning/block asymmetry (`:81-92`). `TestSignature` pins body freezing, the fact that editing
the template does **not** rewrite a signed contract, the shared hash across both signatures,
third-party rejection, double-signing rejection, and signature immutability.

---

# Part 2 — Reference data: `apps.geo`, `apps.taxonomy`, `apps.catalog`

## 2.1 Models (Fakt)

| Model | file:line | Notes |
|---|---|---|
| `geo.Region` | `apps/geo/models.py:4-17` | Bundesland. `name`, `slug`, `code(2)` — all unique. `verbose_name = "Bundesland"/"Bundesländer"` |
| `geo.Locality` | `:20-44` | `region` FK PROTECT, `name`, `slug` (unique **globally**), `postal_code(5)`, `latitude`/`longitude` (nullable, **all None today**), `is_active` (default **False**, `db_index=True`), `sort_order`. `UniqueConstraint(("region","name"))`. `__str__` = `f"{self.name} ({self.region.code})"` — **dereferences `region`, so it is an N+1 unless you `select_related("region")`** |
| `taxonomy.ServiceCategory` | `apps/taxonomy/models.py:5-42` | `parent` self-FK PROTECT (max depth 2), `name` (Romanian, internal), `name_de` (German, public), `slug`, `sort_order`, `is_active` (default True), `is_35a_eligible`. `__str__ = self.name_de or self.name`. `is_leaf` means **"has a parent"**, not "has no children" (`:36-38`) |
| `catalog.*` | `apps/catalog/models.py` | `ProductCategory`, `Product`, `ProductImage`. **Inert** — no views, no URLs, no seed, zero rows |

Docstring rationale, `apps/geo/models.py:21-23`: *"NICIODATĂ text liber — text liber distruge
filtrarea și SEO-ul pe „Reinigungskraft {oraș}"."*
`ServiceCategory.is_35a_eligible` docstring (`:19-22`): §35a EStG lets a private client deduct
20 % of the labour cost of haushaltsnahe Dienstleistungen, capped at €4,000/yr, on condition of
an invoice + bank transfer — *"cel mai puternic argument împotriva concurentului real
(Schwarzarbeit)"*. Those two figures live **only** in that comment and in the German string at
`templates/accounts/profile_public.html:9`; there is no constant and no calculator on the
profile side. (`apps/marketplace/models.py:169-174` does implement the 20 % / €4,000 cap for
offers.)

## 2.2 Seeded rows (Fakt, counts re-queried 2026-08-29)

| Set | Count | Source |
|---|---|---|
| `Region` | **2** — `SH` Schleswig-Holstein, `HH` Hamburg | `geo/0002_seed_localities.py:16-19` |
| `Locality` | **30** total, **17 active** | `geo/0002:22-56` |
| `ServiceCategory` roots | **4** — `wohnungsreinigung`, `gewerbereinigung`, `spezialreinigung`, `haushaltsnahe-dienstleistungen` | `taxonomy/0003_seed_categories.py` |
| `ServiceCategory` leaves | **24**, all active | idem |
| `is_35a_eligible` leaves | **15** | idem |

The **9 leaves that are NOT §35a-eligible**: `bueroreinigung`, `ladenreinigung`,
`gastronomiereinigung`, `praxisreinigung`, `industriereinigung`, `glasreinigung-hoehe`,
`schaedlingsbekaempfung`, `lueftungsreinigung`, `fahrzeugaufbereitung`.

Wave 1 (`is_active=True`, `sort_order` 10–33): norderstedt, henstedt-ulzburg, quickborn,
pinneberg, ahrensburg, kaltenkirchen, bad-segeberg, elmshorn, wedel, bargteheide, rellingen,
halstenbek, schenefeld (SH, 10–22); hamburg-nord, hamburg-eimsbuettel, hamburg-wandsbek,
hamburg-altona (HH, 30–33).
Wave 2 (`is_active=False`, 50–62): bad-bramstedt, bad-oldesloe, barmstedt, tornesch, uetersen,
reinbek, glinde, trittau, itzehoe, neumuenster, hamburg-mitte, hamburg-bergedorf,
hamburg-harburg.

Seed-file docstring (`geo/0002:1-13`): coordinates are left empty **deliberately** — *"se
completează prin geocodare, nu ghicite"* — and wave 2 exists so a locality can be activated
without a deploy.

## 2.3 Conventions for reference data (Fakt)

1. **Never add a free-text place or service field.** Add a row and an FK.
2. **Every FK into `geo.Region`, `geo.Locality`, `taxonomy.ServiceCategory` is `PROTECT`.**
   No exception exists today; do not introduce one.
3. **Seed in a data migration** — never a fixture, never a management command.
4. **Idempotency: `update_or_create(slug=…, defaults={…})`.** `Region` is the one exception,
   keyed on `code` with `get_or_create` (`geo/0002:65-67`). **Never `bulk_create` reference
   data** — it cannot re-run and it skips `save()`.
5. **Historical models only:** `apps.get_model("geo", "Locality")` inside `forwards`.
6. **Write a `backwards` derived from the same constant** so the two cannot drift.
7. **Slugs:** lowercase ASCII, hyphenated, umlauts transliterated (`ä→ae`, `ö→oe`, `ü→ue`,
   `ß→ss`), Hamburg districts prefixed `hamburg-`. **Hand-written in the migration**, never
   `slugify()`d at runtime — that is what makes them stable. **Never rename one.**
8. **`sort_order`:** geo wave 1 = 10–33, wave 2 = 50–62; taxonomy roots 10/20/30/40, leaves
   restart at 10 and step by 10 within each root. Leave gaps.
9. **New localities ship `is_active=False`.** New categories ship as **leaves** under one of the
   four existing roots.
10. **`name` is Romanian (internal), `name_de` is German (public).** Never leave `name_de`
    blank — `templates/accounts/profile_public.html:8` renders `{{ s.name_de }}` directly, so a
    blank one renders an empty `<li>`.
11. **Set `is_35a_eligible` on the legal test:** True iff the service is performed *in or on the
    private client's own household*. When in doubt, False — a wrong True is a tax claim the
    platform put in front of a consumer.
12. **`select_related("region")`** whenever `Locality.__str__` will render.
13. **Deactivate, never delete.** `PROTECT` raises `ProtectedError` as soon as anything
    references the row, and deleting would 404 a URL Google has indexed.

## 2.4 Recipe — activate an already-seeded locality (wave 2 → live)

There is **no admin site**, so the shell is the only route:

```bash
cd /Users/Geronimo/Projects/Cleaning_SaaS
.venv/bin/python manage.py shell -c "
from apps.geo.models import Locality
Locality.objects.filter(slug='itzehoe').update(is_active=True)
"
```

Effects, immediately and without restart:

- `active_localities()` (`apps/accounts/forms.py:12-13`) starts offering it in the onboarding
  form, the account form, the `areas` checkboxes, the job-posting form, the site form, the
  contract form and the service-request form.
- **`DirectorySitemap` grows by 26 URLs** (`config/sitemaps.py:63-74`): one
  `public:providers_city`, one `jobs:list_city`, and one `public:providers_city_category` per
  active leaf (24 today). Those pages are submitted to Google whether or not a single provider
  covers Itzehoe.

**Activation, not row creation, is the SEO-sensitive step.** An empty
`/reinigungskraft/<city>/` returns 200 with *"Niciun prestator."* — a soft-404 in Google's eyes.
Only activate when there is real supply. Do not change `sort_order` at the same time unless you
intend to reorder every dropdown.

## 2.5 Recipe — add a brand-new locality without breaking SEO

Create `apps/geo/migrations/0003_add_localities.py`:

```python
"""
Val 3: extindere spre vest. Slug-urile sunt definitive.
"""

from django.db import migrations

# (region_code, nume, slug, PLZ, activ, ordine)
LOCALITIES = [
    ("SH", "Buxtehude", "buxtehude", "21614", False, 63),
]


def forwards(apps, schema_editor):
    Region = apps.get_model("geo", "Region")
    Locality = apps.get_model("geo", "Locality")
    regions = {r.code: r for r in Region.objects.all()}
    for code, name, slug, plz, active, order in LOCALITIES:
        Locality.objects.update_or_create(
            slug=slug,
            defaults={"region": regions[code], "name": name, "postal_code": plz,
                      "is_active": active, "sort_order": order},
        )


def backwards(apps, schema_editor):
    apps.get_model("geo", "Locality").objects.filter(
        slug__in=[row[2] for row in LOCALITIES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("geo", "0002_seed_localities")]
    operations = [migrations.RunPython(forwards, backwards)]
```

SEO checklist:

1. Pick the slug **once**, transliterate umlauts, and never change it.
2. Check global uniqueness — `Locality.slug` is unique **across regions**, so the SH town
   `schenefeld` (already taken) collides with a Hamburg quarter of the same name. Disambiguate
   with a prefix, not a numeric suffix.
3. Check `(region, name)` — `uniq_locality_per_region` (`apps/geo/models.py:38`).
4. Fill `postal_code` — it lands verbatim in the JSON-LD (`apps/jobs/views.py:125`).
5. Leave `latitude`/`longitude` `None` unless you have real geocoded values.
6. Ship `is_active=False`; flip it with §2.4 when there is supply.
7. Never rename a slug. If a place must be relabelled, change `name` and leave `slug` alone.

Run `manage.py migrate` yourself.

## 2.6 Recipe — add a new service category without breaking SEO

Create `apps/taxonomy/migrations/0004_add_categories.py`:

```python
"""
Frunze noi sub Spezialreinigung. `name` = etichetă internă (RO), `name_de` = public.
"""

from django.db import migrations

PARENT_SLUG = "spezialreinigung"

# (slug, name_ro, name_de, is_35a, ordine)
LEAVES = [
    ("solaranlagenreinigung", "Curățare panouri fotovoltaice",
     "Solaranlagen- und Photovoltaikreinigung", True, 80),
]


def forwards(apps, schema_editor):
    ServiceCategory = apps.get_model("taxonomy", "ServiceCategory")
    parent = ServiceCategory.objects.get(slug=PARENT_SLUG)
    for slug, name, name_de, deductible, order in LEAVES:
        ServiceCategory.objects.update_or_create(
            slug=slug,
            defaults={"parent": parent, "name": name, "name_de": name_de,
                      "sort_order": order, "is_active": True,
                      "is_35a_eligible": deductible},
        )


def backwards(apps, schema_editor):
    apps.get_model("taxonomy", "ServiceCategory").objects.filter(
        slug__in=[row[0] for row in LEAVES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("taxonomy", "0003_seed_categories")]
    operations = [migrations.RunPython(forwards, backwards)]
```

Rules that make this safe:

1. **It must be a leaf** under one of the four existing roots. `ServiceCategory.clean()`
   (`models.py:40-42`) enforces the 2-level cap **but never runs** — there is no admin and no
   ModelForm for this model, so the migration is the only guard.
2. Both labels. `name_de` is what the public sees.
3. German slug, transliterated, permanent — it is the `<slug:category>` segment of
   `public:providers_city_category`.
4. `is_35a_eligible` on the legal test, not on how it sounds. Photovoltaic panels on the
   client's own roof → True; the same service on a commercial hall → the commercial leaf, False.
5. **A new active leaf multiplies the sitemap by the active-city count** — 17 new URLs today,
   all empty 200s until a provider selects the category. Ship it `is_active=False` if nobody
   offers it yet.
6. `sort_order` continues its family's sequence (`spezialreinigung` leaves currently end at 70,
   so 80). Do not renumber siblings.
7. **Never repurpose an existing slug** — the URL is indexed and every
   `AccountService`/`JobPosting`/`Zone`/`ServiceRequest` row pointing at it changes meaning
   silently.

Flipping `is_35a_eligible` on a live category retroactively changes the badge on every provider
profile that offers it (`apps/accounts/views.py:173`). Treat it as a legal change, and record
why in the migration docstring.

## 2.7 Reference-data traps (Fakt)

| # | Trap |
|---|---|
| R1 | **`Locality.__str__` dereferences `region`** → N+1. `templates/accounts/provider_list.html:3` renders `{{ v.locality }}` while `apps/accounts/views.py:185` only does `select_related("locality")`. |
| R2 | **City/category URL segments are never validated.** `/reinigungskraft/zzz/` → 200 (verified), and a **root** category slug is permanently empty because no `AccountService` can point at it. |
| R3 | **`is_active` is a form-layer convention, not a model rule.** No view filters on it; nothing prevents assigning an inactive locality by FK. |
| R4 | **`ServiceCategory.clean()` and `AccountService.clean()` never run.** `grep -rn full_clean apps tests` → nothing; `AccountService` rows are created with `bulk_create`. |
| R5 | **The "leaf" definition is written out twice** — `ScopedLeaf.queryset()` (`apps/accounts/forms.py:23`) uses `.exclude(parent=None).filter(is_active=True)`; `DirectorySitemap` (`config/sitemaps.py:65`) uses `.filter(is_active=True, parent__isnull=False)`. They agree today; keep them in sync. |
| R6 | **`is_leaf` means "has a parent"** — introduce a third level and it starts returning True for a node with children. |
| R7 | **The flat leaf list is not grouped by family.** `ordering = ("sort_order","name")` and every family restarts at 10, so the four families interleave in any checkbox list. Order by `("parent__sort_order","sort_order")` if grouping matters. |
| R8 | **Tests hard-code three seeded slugs** — `norderstedt`, `pinneberg`, `treppenhausreinigung` (`tests/conftest.py:19,24,29`). They are part of the test contract. |
| R9 | **`Product.get_absolute_url()` raises `NoReverseMatch`** — `catalog` is not a registered namespace. Do not call it. |
| R10 | **`Product.slug` is claimed from `f"{brand} {name}"`.** Blank both and it slugs to the literal `"cont"` (the `ReservedSlug.claim` fallback). |
| R11 | **`is_35a_eligible` is not joined with `LegalStatus`.** `apps/accounts/forms.py:84` promises that the worker's legal status *"determină … dacă clientul poate deduce §35a"*, but `apps/accounts/views.py:173` computes the badge purely from the category flags. A provider with `LegalStatus.UNDECLARED` who selects `haushaltshilfe` still gets a *"20 % steuerlich absetzbar"* badge on a public page. **This is the highest-value correctness gap in this subsystem.** |

---

# Part 3 — Dashboard, panels, templates

## 3.1 The panel system — `apps/dashboard/panels.py` (Fakt)

Module docstring (`:1-7`): *"Dashboard-ul, definit ca date, nu ca patru template-uri paralele.
Un cont cu două capabilități vede reuniunea panourilor, nu un al cincilea dashboard scris de
mână."*

```python
@dataclass(frozen=True)
class Panel:                                    # panels.py:14-34
    key: str; title: str; description: str
    url_name: str; capability: str; icon: str = ""; order: int = 100

    @property
    def url(self) -> str | None:
        """Panourile fără rută încă implementată se afișează, dar nu sunt linkuri."""
        if not self.url_name: return None
        try:    return reverse(self.url_name)
        except NoReverseMatch: return None

@dataclass(frozen=True)
class Metric:                                   # :37-42
    key: str; label: str; capability: str
    resolver: str   # numele metodei din DashboardContext
```

`panels_for(capabilities)` (`:102-106`) → `sorted(p for p in PANELS if p.capability in
capabilities, key=(order, title))`.
`metrics_for(capabilities)` (`:109-110`) → filtered list.

`PANELS` (`:45-90`), complete — 20 rows:

| key | title | capability | `url_name` | order |
|---|---|---|---|---|
| `requests` | Cererile mele | `CLIENT` | `dashboard:requests` | 10 |
| `providers` | Caută prestatori | `CLIENT` | `public:providers` | 20 |
| `orders` | Comenzi materiale | `CLIENT` | `""` | 30 |
| `open_requests` | Bursa de cereri | `WORKER` | `dashboard:open_requests` | 12 |
| `open_requests_co` | Bursa de cereri | `PROVIDER` | `dashboard:open_requests` | 12 |
| `my_profile` | Profilul public | `WORKER` | `accounts:profile_edit` | 10 |
| `my_shifts` | Turele mele | `WORKER` | `dashboard:my_shifts` | 15 |
| `my_applications` | Contractele mele | `WORKER` | `dashboard:contracts` | 20 |
| `company_profile` | Profilul firmei | `PROVIDER` | `accounts:profile_edit` | 10 |
| `team` | Echipa | `PROVIDER` | `""` | 40 |
| `sites` | Obiective și zone | `EMPLOYER` | `dashboard:sites` | 30 |
| `planning` | Planificare săptămânală | `EMPLOYER` | `dashboard:planning` | 35 |
| `time_records` | Pontaj | `EMPLOYER` | `dashboard:time_records` | 36 |
| `calibration` | Calibrare estimări | `EMPLOYER` | `dashboard:calibration` | 37 |
| `devices` | Echipamente | `EMPLOYER` | `dashboard:devices` | 38 |
| `discrepancies` | Verificare încrucișată | `EMPLOYER` | `dashboard:discrepancies` | 39 |
| `postings` | Anunțuri de angajare | `EMPLOYER` | `dashboard:postings` | 10 |
| `candidates` | Candidaturi primite | `EMPLOYER` | `dashboard:candidates` | 20 |
| `products` | Produsele mele | `SUPPLIER` | `""` | 10 |
| `stock` | Stoc și prețuri | `SUPPLIER` | `""` | 20 |

`METRICS` (`:92-99`), 6 rows — each `resolver` must match a method on `DashboardContext`
(`apps/dashboard/views.py:9-42`): `open_postings`, `new_applications`, `profile_views`
(**hard-coded 0**), `my_applications`, `published_products`, `contracted_hours`.

## 3.2 Dashboard UI conventions (Fakt)

1. **Never create a role-specific dashboard template or URL.** One `home.html`, one
   `/dashboard/`. New surface = a `Panel` row + a route + a template extending `base.html`.
2. **Declare panels in `PANELS`, never as `{% if %}` in a template.** `home.html` must stay free
   of capability logic.
3. **One capability per `Panel`.** To show a panel to two capabilities, add **two rows** — copy
   the `open_requests` / `open_requests_co` pattern.
4. Panel `title`/`description` are **Romanian**. Dashboard URL segments are **Romanian**. Public
   URL segments are **German**. The one sanctioned crossover is a named German artefact
   (`reinigungsplan.xlsx`).
5. **The route must live in `apps/dashboard/urls.py`** even when the view lives in another app.
   Import as `from apps.<app> import views as <app>_views` (`urls.py:3-7`).
6. Leave `url_name=""` for a panel whose view does not exist yet. Do not omit it, do not point
   it at `#`.
7. Give every panel an explicit `order` on the 10/15/20/30… ladder — the default 100 sinks it.
8. **Every view behind `/dashboard/` enforces authorization itself.** CBVs:
   `CapabilityRequiredMixin` + `OwnedByAccountMixin`. FBVs: the `_guard(request)` shape from
   `apps/devices/views.py:15-20`. Never rely on the panel being hidden.
9. **Scope every queryset to `request.account`** — `OwnedByAccountMixin` when the FK is
   `account`; an explicit filter (`job__account=`, `plan__account=`, `zone__site__account=`,
   `site__account=`) otherwise.
10. **Never put an `Account` into a template when another account is looking at it** — wrap in
    `AccountView` (see `apps/jobs/dashboard_views.py:125-130`).
11. **Render forms with `{{ form.as_p }}` and a bare `<button>`.** Widgets, labels and queryset
    narrowing go on the form class in Python.
12. **State changes are POST + `name="action"` + PRG redirect**, always with `{% csrf_token %}`.
    Never a GET link for a mutation.
13. **Add a metric by adding a `Metric` row AND a same-named method on `DashboardContext`.**
14. **Every `{% for %}` gets an `{% empty %}`** with Romanian copy; every table's empty row uses
    the right `colspan`.
15. **Dates render `d.m.Y`; query-string dates render `Y-m-d`.**
16. **No per-app template directories.** Everything under project-level `templates/<app>/`;
    dashboard pages under `templates/dashboard/`.
17. **If you introduce CSS/JS**, put it under `static/` and link it from a **new block** in
    `base.html` — there is no asset pipeline to conform to. Keep it a single file, no build
    step, unless asked.

### `templates/base.html` — the whole shell (16 lines, Fakt)

```django
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Cleaning SaaS{% endblock %}</title>
</head>
<body>
  {% if messages %}
  <ul class="messages">
    {% for message in messages %}<li class="{{ message.tags }}">{{ message }}</li>{% endfor %}
  </ul>
  {% endif %}
  <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

Only two blocks: `title` and `content`. Messages **are** rendered (older notes saying otherwise
are stale) but are unstyled and un-dismissible — an `error` looks exactly like a `success`.
`{% load static %}` is **not** present and `static/` is empty. Adding
`{% block extra_css %}` to a child without adding it to `base.html` silently renders nothing.

### HTMX (Fakt)

`django_htmx` is in `INSTALLED_APPS` (`config/settings.py:25`) and its middleware is active
(`:48`), **but there are zero `hx-*` attributes in `templates/`** (verified:
`grep -rn "hx-" templates/` → empty) and `htmx.js` is never loaded. Every interaction is a full
form POST + redirect. **There is no HTMX convention in this repo yet.** If you introduce HTMX,
you must add the script tag yourself, and you must decide the partial-template convention — note
that `CandidateDetailView.get()` mutates data (`NEW → VIEWED`,
`apps/jobs/dashboard_views.py:115-121`), so an `hx-trigger="revealed"` on it would burn the
"new" state.

## 3.3 Recipe — add a dashboard page end to end (Vorschlag, following the existing shape)

Worked example: an "Facturi" (invoices) list for `EMPLOYER`.

**Step 1 — the view**, in the app that owns the data:

```python
# apps/contracts/views.py
class InvoiceListView(CapabilityRequiredMixin, OwnedByAccountMixin, ListView):
    required_capability = Capability.EMPLOYER
    template_name = "dashboard/invoices.html"
    context_object_name = "invoices"
    model = Invoice

    def get_queryset(self):
        return super().get_queryset().select_related("customer")
```

For an FBV instead, copy `_guard` from `apps/devices/views.py:15-20` verbatim.

**Step 2 — the route**, in `apps/dashboard/urls.py` (Romanian segment, English `name=`):

```python
path("facturi/", contract_views.InvoiceListView.as_view(), name="invoices"),
```

**Step 3 — the template** at `templates/dashboard/invoices.html`:

```django
{% extends "base.html" %}{% block content %}
<h1>Facturi</h1>
<table><tr><th>Număr</th><th>Client</th><th>Sumă</th><th>Data</th></tr>
{% for i in invoices %}
<tr><td>{{ i.number }}</td><td>{{ i.customer.display_name }}</td>
    <td>{{ i.total_gross }} €</td><td>{{ i.issued_at|date:"d.m.Y" }}</td></tr>
{% empty %}<tr><td colspan="4">Nicio factură.</td></tr>{% endfor %}
</table>
{% endblock %}
```

**Step 4 — the panel**, in `apps/dashboard/panels.py`, on the ladder:

```python
Panel("invoices", "Facturi", "Facturile emise către clienți",
      "dashboard:invoices", Capability.EMPLOYER, order=40),
```

**Step 5 — optional metric**: a `Metric("open_invoices", "Facturi neîncasate",
Capability.EMPLOYER, "open_invoices")` row **and** an `open_invoices()` method on
`DashboardContext` (`apps/dashboard/views.py:9-42`). The `resolver` string is unchecked — a typo
is an `AttributeError` on the **home page**, taking down the whole dashboard for every account
with that capability.

**Step 6 — the test**, in `tests/test_<concern>.py`, following `references/testing.md`:
one test that the owner gets 200, one that a foreign account gets 404, one that an account
without the capability gets 403.

**Step 7 — verify:**

```bash
.venv/bin/python manage.py check
.venv/bin/python -m pytest -q
.venv/bin/python manage.py shell -c "from django.urls import reverse; print(reverse('dashboard:invoices'))"
```

The last line matters: `Panel.url` swallows `NoReverseMatch` and returns `None`, so a bad
`url_name` produces a panel that is silently not a link.

## 3.4 Dashboard traps (Fakt)

| # | Trap |
|---|---|
| D1 | **The account switcher on the home page returns 405.** `templates/dashboard/home.html:7` POSTs to `{% url 'dashboard:home' %}`; `DashboardHomeView` is a `TemplateView` with only `get`. Verified: `POST /dashboard/` → 405. The working endpoint is `accounts:switch` at `/cont/cont/<pk>/activeaza/` — a session-mutating **GET** with no CSRF protection and no `login_required`, which nothing links to. |
| D2 | **`Panel.capability` is a single string, not a list.** `capability=[A, B]` compares a list against a set of strings and matches nothing — no exception, no panel. |
| D3 | **A panel is not a permission.** The URL still resolves. |
| D4 | **Panel order interleaves capabilities.** `sorted(key=(order, title))` is global. |
| D5 | **Panels and view permissions already disagree** — `sites`/`planning`/`time_records`/`calibration` are `EMPLOYER`-only panels but `EMPLOYER`-**or**-`PROVIDER` views. |
| D6 | **`Metric.resolver` is an unchecked string.** A typo takes down the whole home page. |
| D7 | **Metrics run N queries inline** in `get_context_data` — six metrics = six COUNT/SUM queries plus one `reverse()` per panel. No caching. |
| D8 | **`published_products` goes through `Account.products`, whose FK field is `seller`** (`apps/catalog/models.py:42`). `Product.objects.filter(account=…)` raises. |
| D9 | **`paginate_by` is set but no template paginates** — `CandidateListView` 50, `ProviderListView` 24, `JobListView` 20. |
| D10 | **The candidates filter form does not preserve its own selection** (`templates/dashboard/candidates.html:3-9`) — after filtering, both selects reset to "Toate…". |
| D11 | **Templates compare status against raw literals** (`'DRAFT'`, `'PLANNED'`, `'PUBLISHED'`). Renaming a `TextChoices` **value** silently breaks the UI. |
| D12 | **Several redirects hard-code `/dashboard/...` paths** instead of reversing (`apps/planning/views.py:43,57,80,133,171,209`). |
| D13 | **`request.account` can be `None` on any request.** Every new FBV must handle it before calling `capability_set()`. |
| D14 | **`site_form.html` is shared by two create views** and its `<h1>` prints a Python class repr — which is currently a **500** for `ZoneCreateView` (see `bekannte-maengel.md` §M11). Give a new create view its own template. |
| D15 | **Do not translate the Romanian UI to German or the German public slugs to Romanian.** The split is intentional. |

---

## Quellen

- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/models.py`, `services.py`, `views.py`,
  `forms.py`, `migrations/0002_seed_wage_floors.py`, `migrations/0003_seed_templates.py`,
  `migrations/0004_fix_template_titles.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/geo/models.py`,
  `apps/geo/migrations/0002_seed_localities.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/taxonomy/models.py`,
  `apps/taxonomy/migrations/0003_seed_categories.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/catalog/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/dashboard/panels.py`, `views.py`, `urls.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/devices/views.py:15-20` (the `_guard` shape)
- `/Users/Geronimo/Projects/Cleaning_SaaS/templates/base.html`, `templates/dashboard/*.html`
- `/Users/Geronimo/Projects/Cleaning_SaaS/tests/test_contracts.py`
- `scratchpad/dossier/contracts.md`, `reference-data.md`, `dashboard-ui.md`
- Live DB queries 2026-08-29: `WageFloor`, `MinijobThreshold`, `ContractTemplate` rows;
  locality and category counts; `POST /dashboard/` → 405
- Sibling skill for the German legal substance: `gr-tarif-und-lohn`
