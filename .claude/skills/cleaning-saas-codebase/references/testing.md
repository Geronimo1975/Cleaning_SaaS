# Testing — pytest setup, fixtures, style, and a template for a new test

**Covers:** the pytest configuration, every `conftest.py` fixture and exactly what it builds,
the per-module local fixtures, the assertion and login style, what each test module defends,
and a copy-pasteable template for a new test that fits the suite.
**Stand: 2026-08-29.**
**Sources:** `pytest.ini`, `pyproject.toml`, `tests/conftest.py`, all twelve `tests/test_*.py`
— opened and confirmed 2026-08-29; counts taken from
`.venv/bin/python -m pytest --collect-only -q`; cross-checked against
`scratchpad/dossier/testing-config.md`.

---

## 1. Configuration (Fakt)

`pytest.ini` is the **only** pytest configuration — there is no
`[tool.pytest.ini_options]` in `pyproject.toml`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = test_*.py
addopts = -q --reuse-db
testpaths = tests
```

Consequences:

- `python_files = test_*.py` **overrides pytest's default**. A file named `planning_test.py`
  is collected by nobody and fails silently.
- `testpaths = tests` means a bare `pytest` only ever looks in `/tests/`.
- `--reuse-db` currently does nothing: the sqlite test database is in-memory
  (`file:memorydb_default?mode=memory&cache=shared`), so it is rebuilt — migrations and all —
  on every invocation. **If someone points `DATABASE_URL` at Postgres, `--reuse-db` becomes
  real and seed-migration edits stop taking effect until you pass `--create-db`.**

```bash
cd /Users/Geronimo/Projects/Cleaning_SaaS
.venv/bin/python -m pytest -q                    # 190 passed (2026-08-29, ~63 s)
.venv/bin/python -m pytest -q tests/test_seo.py  # one module
.venv/bin/python -m pytest -q --create-db        # after adding a seed migration
.venv/bin/python -m pytest --collect-only -q     # per-file counts
```

`factory_boy` (3.3.3) and `faker` (40.37.0) are **installed but completely unused**. Do not
start using them — the suite's convention is hand-built fixtures with explicit, meaningful
German/Romanian data ("Seniorenresidenz Nord", "Maria Ionescu", "Ulzburger Str. 40"), which is
what makes the byte-level assertions readable.

---

## 2. Placement and naming (Fakt)

1. Every test lives in `/Users/Geronimo/Projects/Cleaning_SaaS/tests/`. There is **no**
   `apps/*/tests.py` and **no** `apps/*/tests/` package. Do not create one.
2. `tests/` has **no `__init__.py`** — it is a rootdir-relative collection directory, not a
   package. Keep it that way.
3. Files are named `test_<domain concern>.py`, not `test_<app>.py`: `test_visibility.py`,
   `test_isolation.py`, `test_application_flow.py`, `test_calibration.py`,
   `test_reinigungsplan.py`.
4. There is exactly **one** `conftest.py`, at `tests/conftest.py` (92 lines).

---

## 3. `tests/conftest.py` — every fixture and what it builds (Fakt)

### `norderstedt` — `:17-19`
```python
@pytest.fixture
def norderstedt(db):
    return Locality.objects.get(slug="norderstedt")
```
Creates **nothing** — it `get`s the row seeded by `apps/geo/migrations/0002_seed_localities.py`:
`("SH", "Norderstedt", "norderstedt", "22846", True, 10)`, i.e. region `SH`,
`postal_code="22846"`, `is_active=True`, `sort_order=10`, `latitude`/`longitude` `None`.

### `pinneberg` — `:22-24`
Same mechanism; seed row `("SH", "Pinneberg", "pinneberg", "25421", True, 13)`.
Used by exactly one test (`tests/test_planning.py:111`) — a second locality is needed to prove
a worker with a `ServiceArea` elsewhere is **not** assigned.

### `category` — `:27-29`
```python
return ServiceCategory.objects.get(slug="treppenhausreinigung")
```
Seeded leaf under `gewerbereinigung`:
`("treppenhausreinigung", "Curățenie scări de bloc și spații comune",
"Treppenhaus- und Gemeinschaftsflächenreinigung", True, 50)` — `name` is the Romanian admin
label, `name_de` the public German one, `is_35a_eligible=True`. It is the only §35a-eligible
leaf under `gewerbereinigung`, so it also exercises the deduction badge.

### `employer` — `:32-43`
Builds, through one atomic `create_account()`:
- `User(email="hr@residenz.de")`, password `"parola-lunga-123"` (10 chars — exactly the
  `MinimumLengthValidator` minimum; `create_user` does not run validators)
- `Account(COMPANY, display_name="Seniorenresidenz Nord", locality=norderstedt,
  legal_status=COMPANY, legal_name="Seniorenresidenz Nord GmbH",
  street="Ulzburger Str. 40", postal_code="22846")`
- `slug` auto-claimed → `"seniorenresidenz-nord"`
- one `Membership(role=OWNER)`
- two `AccountCapability` rows: `EMPLOYER`, `CLIENT`
- one `CompanyProfile`
- then `publish_profile(account)` → a `ConsentRecord(PROFILE_PUBLICATION, granted=True,
  policy_version="2026-09-01")` **and** `status="PUBLISHED"`, `published_at=now()`
- finally `account.user = user` — **an ad-hoc Python attribute, not a model field**

### `worker` — `:46-57`
- `User(email="maria@example.de")`, same password
- `Account(INDIVIDUAL, display_name="Maria Ionescu", locality=norderstedt,
  legal_status=MINIJOB, phone="+49 170 9998877", street="Segeberger Chaussee 9")` —
  **no `postal_code`, no `legal_name`**
- capabilities `WORKER`, `CLIENT` — deliberately **not** `EMPLOYER`, which is what makes every
  "worker gets 403" test work
- one `WorkerProfile`; published; `account.user = user`
- **no `ServiceArea` rows** — load-bearing for the planner's `{contract.workplace_id}` fallback

### `job` — `:60-68`
```python
JobPosting.objects.create(
    account=employer, title="Reinigungskraft Norderstedt (bis 40 Std./Monat)",
    description="Reinigung der Gemeinschaftsflächen.", category=category,
    locality=norderstedt, employment_type=EmploymentType.MINIJOB,
    salary_min=15, salary_max=16, status=JobStatus.PUBLISHED,
    published_at=timezone.now(), valid_through=timezone.now() + timedelta(days=30),
)
```
Already `PUBLISHED` and valid for 30 days → visible anonymously and present in
`sitemap-jobs.xml`. The description is asserted by byte prefix
`b"Gemeinschaftsfl"` — the prefix stops before `ä` to avoid encoding issues.

### `next_monday` — `:71-74`
```python
today = date(2026, 10, 1)                       # a Thursday, isoweekday() == 4
return today + timedelta(days=(7 - today.isoweekday() + 1) % 7 or 7)   # -> date(2026, 10, 5)
```
**No `db`** — a pure computation, grants no database access. `date(2026, 10, 5)` is the same
`MONDAY` constant hard-coded in `test_planning.py:24`, `test_attendance.py:29` and
`test_reinigungsplan.py:16`. The `or 7` branch is dead for this input but keeps the helper
correct if the anchor ever moves to a Monday.

### `signed_contract` — `:77-92`, a **factory fixture** returning a callable
```python
def _make(hours="40", wage="15.00", worker_account=None, start=None):
    draft = ContractDraft.objects.create(
        employer=employer, worker=worker_account or worker,
        template=active_template("MINIJOB"), contract_type="MINIJOB",
        start_date=start or (next_monday - timedelta(days=30)),
        hours_per_month=Decimal(hours), hourly_wage=Decimal(wage),
        workplace=norderstedt,
    )
    render_contract(draft)
    draft.status = DraftStatus.SIGNED
    draft.save(update_fields=["status"])
    return draft
```
- Default start = `2026-10-05 − 30 d` = **`2026-09-05`**, already active in the `MONDAY` week.
- **It bypasses `send_for_signature()` entirely** — so the compliance gate is *not* applied.
  `signed_contract(hours="200")` (used at `test_planning.py:87`) produces a "signed" Minijob
  that massively violates the Geringfügigkeitsgrenze — intentional, to give the planner a
  generous budget. If you are testing the *gate*, use the `draft` factory from
  `tests/test_contracts.py:19-28` and call `send_for_signature` yourself.
- `workplace=norderstedt` is load-bearing: with no `ServiceArea` rows, `build_capacities` falls
  back to `{contract.workplace_id}`.
- Callable multiple times in one test to build several workers' capacity.

---

## 4. Per-module local fixtures (Fakt)

Duplication across modules is **accepted** — `site`, `zone` and `shift` are each redefined with
different shapes in three or four modules. Put a fixture in `conftest.py` only if two or more
modules need it.

| Fixture | file:line | Kind | Builds |
|---|---|---|---|
| `payload` | `test_application_flow.py:10-16` | dict | POST body for `/job/<slug>/bewerben/`: `email`, `full_name`, `phone`, `locality` (pk), `message`, `accept_terms="on"`, `publish_profile="on"` |
| `outsider` | `test_isolation.py:16-24` | Account | `User("altcineva@example.de")`, COMPANY "Alt SRL", `[EMPLOYER]`, sets `.user` |
| `application` | `test_isolation.py:27-29` | Application | `Application(job=job, applicant_account=worker)` |
| `contract` | `test_isolation.py:32-38` | ContractDraft | unsigned MINIJOB, `start_date="2026-10-01"` (a **string**), `hours_per_month=40`, `hourly_wage="14.25"` |
| `draft` | `test_contracts.py:19-28` | callable | `_make(ctype=MINIJOB, hours="40", wage="15.00", start=date(2026,10,1))` → unsigned draft |
| `site` | `test_planning.py:27-32` | Site | "Haus Nord", `street="Ulzburger Str. 40"`, `postal_code="22846"` |
| `zone` | `test_planning.py:35-43` | callable | `_make(name="Etaj 1", minutes=120, visits=2, weekdays="1,2,3,4,5")` |
| `second_worker` | `test_planning.py:46-53` | Account | `User("petra@example.de")`, INDIVIDUAL "Petra Schulz", `[WORKER]`. **No `.user`, not published** |
| `plan` | `test_attendance.py:32-40` | ShiftPlan | signs a 40 h contract, creates Site "Haus Nord" + Zone "Etaj 1" (120 min × 2/wk, `allowed_weekdays="1,3"`), returns `generate_week_plan(employer, MONDAY)` |
| `shift` | `test_attendance.py:43-46` | Shift | publishes `plan` with `actor=employer`, returns `plan.shifts.first()` |
| `zone` | `test_calibration.py:40-46` | Zone | Site "Haus Nord" + Zone "Etaj 1", 120 min × 2/wk, default weekdays |
| `log_shifts` | `test_calibration.py:49-68` | callable | `_log(durations, target_zone=None, start=None)` — `get_or_create`s a PUBLISHED plan on the Monday of `start` (default `TODAY − 60 d`), then one `Shift(status=DONE, actual_minutes=m)` per duration, one per consecutive day |
| `site` / `zone` / `device` / `shift` | `test_devices.py:26-56` | | Site "Haus Nord"; Zone "Etaj 1" 120 min × 2/wk; `Device(label="Aspirator 1", token_hash="pending", token_prefix="")` then `dev.raw_token = dev.issue_token()`; a shift on `timezone.localdate()` at `"08:00"` for 120 min |
| `site` / `zone` | `test_reinigungsplan.py:19-35` | | Site with street + PLZ; `_make(name="Treppenhaus A", minutes=45, visits=2, weekdays="2,4", description="")` |

Module-level constants and helpers:

- `MONDAY = date(2026, 10, 5)  # luni` — `test_planning.py:24`, `test_attendance.py:29`,
  `test_reinigungsplan.py:16`
- `TODAY = timezone.localdate()` — `test_calibration.py:37`, with a comment explaining *why* it
  must be the real clock: `decided_at` is `now()` and the cooldown is measured against it
- `_monday()` — `test_devices.py`, returns the real current week's Monday
- `_payload(shift, runtime=30, external_id="s-1")` — `test_devices.py`, telemetry JSON body
  anchored at 08:10 local on the shift date, `area_sqm=210`, `battery_start=100`,
  `battery_end=62`
- `TestDiscrepancies._complete(self, shift, minutes)` and
  `TestIndexingQueue._publish(self, client, employer, job)` — **method** helpers, not fixtures

---

## 5. Style rules (Fakt — descriptive of what exists; follow exactly)

**Module docstrings.** Every module opens with a Romanian docstring stating **the rule being
defended and why it matters**, not what the module tests. Several quote statute or case law.
Typographic quotes (`„…"`) and Romanian diacritics are used — keep them.

```python
"""Verificările legale trebuie să BLOCHEZE, nu doar să avertizeze."""   # test_contracts.py:1
```
```python
"""
Publicare, pontaj, evidența timpului de lucru.

Pontajul nu e confort: BAG 13.09.2022 (1 ABR 22/21) pe baza §3 Abs. 2 Nr. 1
ArbSchG obligă la înregistrarea întregului timp lucrat. De aceea jurnalul e
append-only și corecțiile păstrează valoarea veche.
"""                                                                     # test_attendance.py:1-7
```

**Structure.** Group tests in classes named `Test<Concern>`, PascalCase **English**:
`TestCompliance`, `TestSignature`, `TestPublishing`, `TestAttendance`, `TestCorrections`,
`TestTimeRecords`, `TestShiftViews`, `TestAnalysis`, `TestProposals`, `TestDecisions`,
`TestCalibrationView`, `TestAuthentication`, `TestIngestion`, `TestApi`, `TestDiscrepancies`,
`TestDeviceDashboard`, `TestRows`, `TestWorkbook`, `TestView`, `TestSitemap`,
`TestIndexingQueue`, `TestVisibility`, `TestIsolation`, `TestAccounts`, `TestApplicationFlow`,
`TestCapacity`, `TestPlanGeneration`, `TestPlanningDashboard`, `TestContractSeam`.
Classes carry **no docstrings** except `TestIndexingQueue` (`test_seo.py:70-73`). Exactly one
module-level function test exists (`test_seo.py:60`); prefer a class.

**Method names.** Romanian, snake_case, a full assertion sentence. Diacritics are **stripped
from names** even though they are kept in docstrings and messages:
`test_rolurile_sunt_randuri_nu_coloane`, `test_slugul_nu_se_schimba_la_redenumire`,
`test_avertismentul_nu_blocheaza_trimiterea`, `test_o_singura_tura_extrema_nu_muta_estimarea`,
`test_duminica_ramane_libera`, `test_cheia_nu_se_stocheaza_in_clar`.
Method docstrings are rare — only when the name is not enough
(`test_isolation.py:61`: `"""Prestatoarea are cont, dar nu e EMPLOYER."""`).

**Database access.** `@pytest.mark.django_db` goes on the **class**, once — never on individual
methods. `transactional_db` and `django_db_reset_sequences` are not used anywhere. Fixtures
that touch the ORM take `db` as their first parameter (`def employer(db, norderstedt)`); pure
fixtures (`next_monday`, `payload`) do not.

**Auth.** `client.force_login(<account>.user)`. Never `client.login()`, never a POST to
`/accounts/login/`. Only fixtures that explicitly set `account.user = user` support this —
`employer`, `worker` (conftest) and `outsider` (`test_isolation.py`). For an account built
inline without `.user`, reach the user through the membership:
`client.force_login(other.memberships.first().user)` (`test_planning.py:197`).

**Assertions.** Plain `assert`. No `unittest` helpers, no `assertContains`, no
`assertRedirects`, no `assertTemplateUsed`, no `assertQuerySetEqual`. Attach a Romanian message
to any assertion whose failure would be cryptic:

```python
assert len(mail.outbox) == 1, "un email per lucrător, nu unul per tură"
assert not analysis.actionable, "mediana rezistă la valori extreme"
assert session.shift is None, "două ture candidate = nicio atribuire"
assert findings == [], "35 min de aspirat la 120 min de curățenie e normal"
```

Error paths use `with pytest.raises(<Exc>):` — the suite uses `ValueError`, `RuntimeError`,
`ShiftError` and `TelemetryError`. Only one test uses `match=`
(`pytest.raises(TelemetryError, match="Câmpuri lipsă")`, `test_devices.py:134`).

Assert on response **bytes** with a `b"..."` prefix short enough to avoid non-ASCII
(`b"Gemeinschaftsfl"`, `b"Nicio tur"`, `b"O SINGUR"`, `b"deja un cont"`), or decode with
`.content.decode()` when comparing URLs. Assert status codes as **integers**, and headers via
`response.headers["X-Robots-Tag"]` or `r["X-Robots-Tag"]` — both forms are in use.
Always `refresh_from_db()` after a service call before asserting on persisted state.

**Parametrize sparingly.** Only one `@pytest.mark.parametrize` exists in the whole suite
(`test_reinigungsplan.py:58-63`, the `frequency_label` mapping). Prefer explicit named tests.

**Imports.** Module-level order: `datetime`/`decimal` stdlib → blank line → `pytest` and
`django.*` → blank line → `apps.*`; sorted alphabetically within each block. Deliberately
**defer an import into the test body** when it exists only to prove a narrow point or to keep
the module header honest — an established idiom here (`test_application_flow.py:59,67-70`,
`test_planning.py:178,188-190`, `test_contracts.py:105-107`, `test_seo.py:80,92,99,111,125,139`).

**Settings.** Use pytest-django's `settings` fixture (auto-restored) — see
`test_seo.py:138-145`. Never `override_settings`, never `os.environ[...] = ...`.

**Language.** Never translate. German for public URLs, template copy, contract text, service
names, weekday abbreviations, legal terms. Romanian for docstrings, assertion messages, test
names. English only for Python identifiers, class names and enum members.

---

## 6. What each test module covers (Fakt, counts from `--collect-only` 2026-08-29)

| Module | Tests | Defends |
|---|---|---|
| `test_accounts.py` | 5 | capabilities as rows (`grant`/`revoke`), slug immutability on rename, slugs never reused, profile created with the account, depublication keeps the row |
| `test_application_flow.py` | 8 | posting visible without login + JSON-LD present; applying creates account + `WorkerProfile` + `Application`; the two consents are separate; without the checkbox the profile stays `DRAFT`; the password is unusable; an existing email does not create a second account; depublished profile 410 + noindex; expired posting 410 |
| `test_isolation.py` | 7 | guessed-ID isolation — foreign candidature/contract/posting all **404**; the owner gets 200; a missing capability is **403**; no account → redirect to onboarding |
| `test_contracts.py` | 16 | `TestCompliance`: dated thresholds not constants, the 2026 Gebäudereinigung tariff of 15.00 €, severity is a typed `ComplianceIssue.blocking` field and not deduced from the message, the valid 40 h × 15.00 € = 600.00 € Minijob against the 603.00 € 2026 threshold (at the limit), the threshold breach at 41 h and at 45 h, the higher of the two wage floors applies, Werkvertrag warns about Scheinselbstständigkeit, a warning does **not** block sending, a violation **does**. `TestSignature`: body frozen at send, editing the template does not rewrite a signed contract, both parties sign the same hash, a third party cannot sign, double signing refused, the signature is immutable |
| `test_planning.py` | 17 | `TestCapacity`, `TestPlanGeneration`, `TestPlanningDashboard` — capacity comes only from signed contracts, the contracted-hour ceiling is hard, 8 h/day, Sunday stays free, `ServiceArea` filtering, unmet demand carries reasons |
| `test_attendance.py` | 22 | `TestPublishing`, `TestAttendance`, `TestCorrections`, `TestTimeRecords`, `TestShiftViews` — publish emits events and one email per worker, the check-in/out state machine, corrections keep the old value in the journal, `time_records` rows and totals |
| `test_calibration.py` | 21 | `TestAnalysis`, `TestProposals`, `TestDecisions`, `TestCalibrationView` — median resists an extreme shift, the double threshold, minimum sample, cooldown, proposals auto-withdraw and get replaced, apply/reject ownership |
| `test_devices.py` | 25 | `TestAuthentication`, `TestIngestion`, `TestApi`, `TestDiscrepancies`, `TestDeviceDashboard` — token stored only as a hash, idempotent ingestion, HTTP status contract, conservative shift matching, discrepancy kinds. Module docstring names a test that deliberately **does not** exist: telemetry must never modify `minutes_per_visit` |
| `test_marketplace.py` | 38 | request → offer → award; no auto-allocation; an offer alone does not expose the client's data (`AccountView`/`Relation`); scoring breakdown and tie-break; `award_warnings`; `TestContractSeam` (`:371-459`, 9 tests) — an awarded offer generates a `ContractDraft` via `create_contract_from_offer()`, WERKVERTRAG-vs-employment selection, the `UNDECLARED`-status block, and idempotency |
| `test_reinigungsplan.py` | 8 | `TestRows`, `TestWorkbook`, `TestView` — the four columns come from real data, inactive zones excluded, the frequency label mapping (the one parametrize), the XLSX header and `Summe` row, the download view |
| `test_seo.py` | 14 | `TestSitemap` (7) — only 200-answering things are in the sitemap, expiry/closing/depublication remove them and produce 410 + noindex, the directory contains the city pages; the module-level robots test; `TestIndexingQueue` (6) — publish enqueues `URL_UPDATED`, close enqueues `URL_DELETED`, flush marks `SENT`, a failure leaves it `PENDING` with the error, `MAX_ATTEMPTS` gives up, no credentials = no send |
| `test_visibility.py` | 9 | the field-level disclosure policy per `Relation` — see `accounts-rechte-sichtbarkeit.md` §6 |
| **Total** | **190** | |

---

## 7. Traps when writing tests here (Fakt)

1. **`account.user` is not a model field.** `Account` has no `user` FK and no `user` property.
   `conftest.py:42,56` and `test_isolation.py:23` attach a Python attribute after creating the
   account. Any account you build **without** that line raises
   `AttributeError: 'Account' object has no attribute 'user'` on `client.force_login(acc.user)`.
   Use `acc.memberships.first().user`.
2. **Never `Locality.objects.create(...)` or `ServiceCategory.objects.create(...)` in a test.**
   Every geo/taxonomy/wage/template row comes from a data migration; an inline row breaks the
   slug-based lookups and a duplicate slug raises `IntegrityError`.
3. **`signed_contract` skips the compliance gate.** Use the `draft` factory when testing the
   gate itself.
4. **The worker's served localities silently come from the contract's `workplace`.**
   `apps/planning/services.py:67-69` falls back to `{contract.workplace_id}` **only** when the
   worker has zero `ServiceArea` rows. "Helpfully" adding a `ServiceArea` to the `worker`
   fixture breaks the planning tests.
5. **`MONDAY = date(2026, 10, 5)` and `next_monday` must agree.** `next_monday` derives Oct 5
   2026 from the anchor `date(2026, 10, 1)`. Change either and `signed_contract`'s default start
   (`2026-09-05`) may fall outside the planning week — zero capacity, a cascade of confusing
   failures.
6. **`test_calibration.py` and `test_devices.py` use the *real* clock.** `TODAY =
   timezone.localdate()` and `_monday()`. `test_calibration.py:35-37` explains why: the cooldown
   is measured against `decided_at`, which is `now()`. Swapping in the 2026 anchor would make
   the tests pass without testing anything.
7. **`EMAIL_BACKEND` says console in settings, but tests get locmem** — Django's
   `setup_test_environment()` swaps it. Do not "fix" `config/settings.py` to name locmem, or
   real emails go silent in the dev server too. Assert on `django.core.mail.outbox`.
8. **Passwords shorter than 10 characters.** `MinimumLengthValidator` is configured with
   `min_length: 10` (`config/settings.py:91-92`). `create_user` does not run validators, so a
   short password in a fixture works — but any test going through a **form** fails. Stick to
   `"parola-lunga-123"`.
9. **`ALLOWED_HOSTS` must keep `testserver`.** It is in the default string; a `.env` setting
   `ALLOWED_HOSTS=example.de` breaks every test with `DisallowedHost`.
10. **`test_isolation.py:36` passes `start_date="2026-10-01"` as a string.** It works because
    Django coerces it on save, but the value read back before a refresh is still a `str`. Prefer
    a real `date` in new code.
11. **After adding a data migration, run once with `--create-db`** (relevant the moment the test
    DB stops being in-memory).
12. **`monthly_gross` needs `Decimal`.** Passing `"40"` or `40.0` for `hours_per_month` on an
    unsaved `ContractDraft` raises `TypeError` or loses precision.

---

## 8. Template for a new test module

Copy this shape verbatim and replace the concern. Save as
`/Users/Geronimo/Projects/Cleaning_SaaS/tests/test_<concern>.py`.

```python
"""
<Concernul, în română>.

<Regula pe care o apără fiecare test și de ce contează — nu ce testează
modulul, ci ce se strică dacă regula cade. Citează paragraful legal dacă
există unul (§16 ArbZG, §7 SGB IV, §35a EStG, DSGVO Art. 7).>
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.enums import Capability
from apps.<app>.models import <Model>
from apps.<app>.services import <service_fn>

MONDAY = date(2026, 10, 5)  # luni


@pytest.fixture
def <local_thing>(db, employer, norderstedt, category):
    """Fixture factory when a parameter must vary; a plain object otherwise."""
    def _make(name="Etaj 1", minutes=120):
        return <Model>.objects.create(
            account=employer, name=name, locality=norderstedt, minutes_per_visit=minutes,
        )
    return _make


@pytest.mark.django_db
class Test<Concern>:
    def test_<afirmatia_in_romana_fara_diacritice>(self, employer, <local_thing>):
        obj = <local_thing>()
        result = <service_fn>(obj, employer)
        obj.refresh_from_db()
        assert obj.status == "<EXPECTED>", "mesaj în română care explică de ce"

    def test_<cazul_de_eroare>(self, employer, <local_thing>):
        with pytest.raises(ValueError):
            <service_fn>(<local_thing>(), employer)


@pytest.mark.django_db
class Test<Concern>View:
    def test_proprietarul_vede_pagina(self, client, employer):
        client.force_login(employer.user)
        assert client.get("/dashboard/<segment-romanesc>/").status_code == 200

    def test_strainul_primeste_404(self, client, worker, <local_thing>):
        """Un cont străin nu află nici măcar că URL-ul există."""
        client.force_login(worker.user)
        obj = <local_thing>()
        assert client.get(f"/dashboard/<segment>/{obj.pk}/").status_code == 404

    def test_fara_capabilitate_primeste_403(self, client, worker):
        client.force_login(worker.user)
        assert client.get("/dashboard/<segment-romanesc>/").status_code == 403
```

Then:

```bash
cd /Users/Geronimo/Projects/Cleaning_SaaS
.venv/bin/python -m pytest -q tests/test_<concern>.py
.venv/bin/python -m pytest -q            # the whole suite must still pass
```

**Every new dashboard view needs all three of the view tests above** — 200 for the owner,
404 for a foreign object, 403 for a missing capability. That triple is the repo's authorization
contract; see `accounts-rechte-sichtbarkeit.md` §3.

---

## Quellen

- `/Users/Geronimo/Projects/Cleaning_SaaS/pytest.ini`, `pyproject.toml`
- `/Users/Geronimo/Projects/Cleaning_SaaS/tests/conftest.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/tests/test_accounts.py`,
  `test_application_flow.py`, `test_attendance.py`, `test_calibration.py`,
  `test_contracts.py`, `test_devices.py`, `test_isolation.py`, `test_marketplace.py`,
  `test_planning.py`, `test_reinigungsplan.py`, `test_seo.py`, `test_visibility.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/config/settings.py:11,91-92,122`
- `scratchpad/dossier/testing-config.md` (fixture graph, conventions, gotchas)
- `.venv/bin/python -m pytest --collect-only -q` (per-file counts, 2026-08-29)
