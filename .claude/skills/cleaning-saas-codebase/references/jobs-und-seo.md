# Jobs und SEO — `apps.jobs`, `config/sitemaps.py`, `templates/robots.txt`

**Covers:** `JobPosting` / `Application`, the posting lifecycle, the apply flow that creates a
user + account + `WorkerProfile`, the JSON-LD actually emitted (every field, verbatim), the
410 + noindex depublication, the Google Indexing queue, the sitemap and robots.txt, and the
SEO gaps that are real today.
**Stand: 2026-08-29.**
**Sources:** `apps/jobs/*.py`, `config/sitemaps.py`, `config/urls.py`, `templates/jobs/*`,
`templates/robots.txt`, `tests/test_application_flow.py`, `tests/test_seo.py` — all opened and
confirmed 2026-08-29; cross-checked against `scratchpad/dossier/jobs.md`.

> **Scope note (Fakt).** `apps.jobs` is a **recruitment** job board — `JobPosting` =
> Stellenanzeige, `Application` = Bewerbung. It is a **supply-side** acquisition funnel, not
> the customer-order marketplace. The customer-order side is `apps.marketplace`
> (`ServiceRequest` → `Offer`). Do not conflate them.

---

## 1. Data model (Fakt)

### `EmploymentType` — `apps/jobs/models.py:6-11`

| Value | German label |
|---|---|
| `FULL_TIME` | Vollzeit |
| `PART_TIME` | Teilzeit |
| `MINIJOB` | Minijob |
| `CONTRACTOR` | Selbstständig |
| `TEMPORARY` | Temporär |

### `JobStatus` — `models.py:14-18`

`DRAFT` "Ciornă" · `PUBLISHED` "Publicat" · `CLOSED` "Închis" · `EXPIRED` "Expirat"

**`EXPIRED` is never written by any code.** Expiry is computed on the fly by `is_live`. There is
no cron, no management command, no signal that transitions `PUBLISHED → EXPIRED`. The dashboard
list fakes the display: `{% if p.status == 'PUBLISHED' and not p.is_live %} (expirat){% endif %}`
(`templates/dashboard/postings.html:10`). Never write code that assumes `status == EXPIRED`
matches a row.

### `JobPosting` — `models.py:21-77`

| Field | Type | Notes |
|---|---|---|
| `account` | FK `accounts.Account`, CASCADE, `related_name="job_postings"` | the employer |
| `title` | `CharField(180)` | |
| `slug` | `SlugField(200, unique=True, editable=False)` | claimed from `ReservedSlug` (max 130 chars) |
| `description` | `TextField` | `help_text="HTML permis restrâns"` — **no sanitiser is installed** |
| `requirements` | `TextField(blank=True)` | **captured but never displayed or emitted anywhere** |
| `category` | FK `taxonomy.ServiceCategory`, PROTECT | leaf only, via `ScopedLeaf.queryset()` |
| `locality` | FK `geo.Locality`, PROTECT | |
| `employment_type` | `CharField(16, choices=EmploymentType)` | |
| `salary_min` / `salary_max` | `DecimalField(8,2)`, nullable | |
| `salary_currency` | `CharField(3, default="EUR")` | |
| `salary_unit` | `CharField(8, choices=[("HOUR","oră"),("MONTH","lună")], default="HOUR")` | **the labels are Romanian and they render on the public German page** |
| `status` | `CharField(12, choices=JobStatus, default=DRAFT, db_index=True)` | |
| `published_at` | `DateTimeField`, nullable | |
| `valid_through` | `DateTimeField`, **not nullable** | comment `:49`: *"Obligatoriu, nu opțional: Google penalizează anunțurile expirate lăsate live."* |
| `views_count` | `PositiveIntegerField(default=0)` | incremented on every live GET; **never displayed** |
| `created_at`, `updated_at` | | |

`Meta`: `ordering = ("-published_at", "-created_at")`,
`indexes = [Index(("status","locality","category"))]`, `verbose_name = "Anunț"/"Anunțuri"`.

```python
@property
def is_live(self) -> bool:                                          # models.py:75-77
    return self.status == JobStatus.PUBLISHED and self.valid_through > timezone.now()
```

**The live predicate exists in four places and must never drift:**
`JobPosting.is_live` (`models.py:77`) · `JobListView.get_queryset` (`views.py:20-22`) ·
`JobSitemap.items()` (`config/sitemaps.py:31-33`) · `apply_view`'s guard (`views.py:71`).
If the sitemap copy drifts, a 410 URL enters the sitemap and Google errors the whole file —
exactly what `config/sitemaps.py:4-7` warns about.

### `ApplicationStatus` — `models.py:80-85`

`NEW` "Nou" · `VIEWED` "Văzut" · `SHORTLISTED` "Preselectat" · `REJECTED` "Respins" ·
`HIRED` "Angajat"

### `Application` — `models.py:88-110`

`job` FK CASCADE `related_name="applications"`, `applicant_account` FK
`accounts.Account` CASCADE `related_name="applications"`, `message`, `status`, `created_at`.
`UniqueConstraint(("job","applicant_account"), name="uniq_application")`.
`Meta.ordering = ("-created_at",)`. **No `updated_at`, no status-change audit trail.**

Docstring (`:89-92`): *"Aplicarea e și mecanismul care creează contul + profilul public, și
evenimentul care ridică relația la ENGAGED (vezi accounts.visibility)."* — `Application` is
load-bearing for the whole visibility model; see `accounts-rechte-sichtbarkeit.md` §6.

### `IndexingTask` — `models.py:124-154` (migration `jobs/0002_indexingtask`)

`url` (`URLField(500)`), `action` (`URL_UPDATED` / `URL_DELETED`), `status`
(`PENDING`/`SENT`/`FAILED`, `db_index=True`), `attempts`, `last_error(300)`, `created_at`,
`sent_at`. `Meta.ordering = ("created_at",)`, `indexes = [Index(("status","created_at"))]`.

Docstring (`:125-134`): the queue exists so that **publishing does not depend on Google being
up**, and because Google recommends the Indexing API over the sitemap for `JobPosting`
(*"indexare în ~2 zile în loc de ~3 săptămâni"*).

---

## 2. Posting lifecycle (Fakt)

| Transition | Where | What happens |
|---|---|---|
| create → `DRAFT` | `PostingCreateView.form_valid`, `dashboard_views.py:41-44` | sets `form.instance.account = request.account`; message *"Anunț salvat ca ciornă."* |
| `DRAFT` → `PUBLISHED` | `PostingPublishView.post`, `dashboard_views.py:62-77` | refuses if `valid_through <= now()`; sets `published_at = published_at or now()`; **enqueues `URL_UPDATED`** |
| `PUBLISHED` → `CLOSED` | same view, same POST | **enqueues `URL_DELETED`**; message *"URL-ul răspunde 410 și iese din sitemap."* |
| `PUBLISHED` → effectively expired | none — `valid_through` passes | `is_live` becomes False; the row's `status` stays `PUBLISHED` |

```python
# apps/jobs/dashboard_views.py:55-77  — the "publish service" is a view
class PostingPublishView(CapabilityRequiredMixin, OwnedByAccountMixin, View):
    required_capability = Capability.EMPLOYER
    def get_queryset(self):
        return JobPosting.objects.filter(account=self.request.account)
    def post(self, request, pk):
        posting = get_object_or_404(self.get_queryset(), pk=pk)
        if posting.status == JobStatus.PUBLISHED:
            posting.status = JobStatus.CLOSED
            enqueue(absolute_url(request, posting), IndexingAction.DELETED)
            ...
        else:
            if posting.valid_through <= timezone.now(): ... return redirect(...)
            posting.status = JobStatus.PUBLISHED
            posting.published_at = posting.published_at or timezone.now()
            enqueue(absolute_url(request, posting), IndexingAction.UPDATED)
        posting.save(update_fields=["status", "published_at", "updated_at"])
```

Traps:

- **It is a toggle with no action parameter.** A double-submitted form publishes and then
  immediately closes. There is no `?action=publish`.
- `OwnedByAccountMixin` on this class is **inert** — the local `get_queryset` shadows it. The
  scoping still works; do not assume removing the local method is safe.
- There is **no `publish_posting()` service**, unlike every other lifecycle in this repo.

### Dashboard views — `apps/jobs/dashboard_views.py`

| View | Capability | Template | Note |
|---|---|---|---|
| `PostingListView` (`:18-32`) | `EMPLOYER` | `dashboard/postings.html` | annotates `application_count` |
| `PostingCreateView` (`:35-44`) | `EMPLOYER` | `dashboard/posting_form.html` | |
| `PostingUpdateView` (`:47-52`) | `EMPLOYER` | `dashboard/posting_form.html` | `OwnedByAccountMixin` → foreign pk = 404 |
| `PostingPublishView` (`:55-77`) | `EMPLOYER` | — | POST only |
| `CandidateListView` (`:80-102`) | `EMPLOYER` | `dashboard/candidates.html` | filters on `?status=` and `?job=`; `paginate_by = 50` with **no pagination UI**. `?job=abc` → 500 (unvalidated) |
| `CandidateDetailView` (`:105-143`) | `EMPLOYER` | `dashboard/candidate_detail.html` | **`get()` mutates data**: flips `NEW → VIEWED` (`:117-120`). Builds `candidate` as an `AccountView` at ENGAGED |

---

## 3. The apply flow: posting → application → user → account → public profile (Fakt)

This chain is the phase-0 growth mechanism: the posting brings the person, applying creates the
account, the account becomes a public profile, the directory grows. The form docstring says so
verbatim (`apps/jobs/forms.py:11-17`).

### `ApplicationForm` — `apps/jobs/forms.py:10-56`

| Field | Type | Label (Romanian source) |
|---|---|---|
| `email` | `EmailField` | `_("Email")` — **deleted from the form when a user is logged in** (`:38-39`) |
| `full_name` | `CharField(128)` | `_("Nume complet")` |
| `phone` | `CharField(32)`, required | `_("Telefon")` |
| `locality` | `ModelChoiceField(active_localities())` | `_("Localitate")` |
| `message` | `Textarea`, optional | `_("Mesaj")` |
| `accept_terms` | `BooleanField`, **required** | `_("Accept termenii și politica de confidențialitate")` |
| `publish_profile` | `BooleanField`, **not required** | `_("Vreau ca profilul meu să fie public și vizibil pentru beneficiari")` |

The comment at `:27-28` is the DSGVO rationale for the second checkbox: *"Consimțământ SEPARAT,
niciodată inclus în T&C: publicarea profilului înseamnă expunerea numelui unei persoane fizice
într-un director indexat."*

`clean_email()` (`:41-47`) rejects an email that already has a `User`, with
*"Există deja un cont cu acest email. Autentifică-te pentru a aplica."*
`clean()` (`:49-56`) contains a duplicate-application check that is **dead code**:
`self._existing_account` is never set.

### `apply_to_job()` — `apps/jobs/services.py:16-63`

```python
@transaction.atomic
def apply_to_job(*, job, data, user=None, request=None) -> Application:
    """
    Idempotent pe (job, cont). Creează userul și contul dacă e nevoie.
    Parola se setează prin linkul de activare trimis pe email — nu cerem
    parolă în formularul de aplicare, pentru că fiecare câmp în plus
    scade rata de aplicare.
    """
    account = _resolve_account(data, user)
    if data.get("publish_profile"):
        publish_profile(account, request)          # writes PROFILE_PUBLICATION consent
    record_consent(account, ConsentType.TERMS, True, request)
    application, _created = Application.objects.get_or_create(
        job=job, applicant_account=account,
        defaults={"message": data.get("message", "")},
    )
    return application
```

`_resolve_account()` (`:38-63`):

- **Logged-in user:** `Account.objects.filter(memberships__user=user).first()` — note this
  **ignores `request.account`**. A user with two accounts may apply as the wrong one.
- **Anonymous:** `User.objects.create_user(email=..., password=None)` then
  `set_unusable_password()` + `save(update_fields=["password"])`, then `create_account(...)`
  with `entity_type=INDIVIDUAL`, `capabilities=[WORKER, CLIENT]`, `locality`, `phone`,
  `contact_email=data["email"]`. `create_account` in turn creates the `Membership`, the two
  `AccountCapability` rows and a **`WorkerProfile`** via `_ensure_profile`.

Resulting object graph for a new applicant:

```
User(email, unusable password)
└── Membership(role=OWNER)
    └── Account(INDIVIDUAL, display_name=full_name, locality, phone, contact_email)
        ├── AccountCapability(WORKER, is_active=True)
        ├── AccountCapability(CLIENT, is_active=True)
        ├── WorkerProfile()                       ← empty, created by _ensure_profile
        ├── ConsentRecord(TERMS, granted=True, policy_version="2026-09-01")
        ├── ConsentRecord(PROFILE_PUBLICATION, granted=True)   ← only if the box was ticked
        └── slug claimed from ReservedSlug        ← permanent
```

**No email is ever sent.** `apply_view` promises *"Ți-am trimis un email cu pașii următori"*
(`views.py:77`) and the service docstring promises an activation link, but there is no
`send_mail`, no allauth trigger and no signal. The new user has an unusable password.

**Every apply POST writes a new `TERMS` consent**, even a repeat application, because
`record_consent` runs before `get_or_create`. That is correct for an append-only log — but
consent counts are not application counts.

### `apply_view` — `apps/jobs/views.py:69-80`

```python
def apply_view(request, slug):
    job = JobPosting.objects.filter(slug=slug).first()
    if not job or not job.is_live:
        raise Http404
    form = ApplicationForm(request.POST or None, job=job, user=request.user)
    if request.method == "POST" and form.is_valid():
        apply_to_job(job=job, data=form.cleaned_data, user=request.user, request=request)
        messages.success(request, "Candidatura a fost trimisă. …")
        return redirect(job.get_absolute_url())
    return render(request, "jobs/detail.html", {"job": job, "form": form})
```

**Trap:** the failure path re-renders `jobs/detail.html` **without `jsonld`**, so a failed
application POST returns a 200 page containing an empty
`<script type="application/ld+json"></script>`. Any change to the detail template's structured
data must account for this second render path.

Tests — `tests/test_application_flow.py` (8 tests):

| Test | Asserts |
|---|---|
| `test_anuntul_e_vizibil_fara_login` (`:21`) | 200 anonymously; `b"Gemeinschaftsfl"` present; `b"application/ld+json"` present |
| `test_candidatura_creeaza_cont_si_profil` (`:27`) | `entity_type == "INDIVIDUAL"`, capabilities `{"WORKER","CLIENT"}`, `worker_profile` exists, `Application` exists |
| `test_consimtamintele_sunt_separate` (`:35`) | consent set is exactly `{"TERMS","PROFILE_PUBLICATION"}` |
| `test_fara_consimtamant_profilul_ramane_nepublicat` (`:41`) | without the checkbox → `status == "DRAFT"` |
| `test_parola_se_seteaza_prin_email_nu_in_formular` (`:47`) | `not user.has_usable_password()` |
| `test_email_existent_nu_creeaza_al_doilea_cont` (`:52`) | `b"deja un cont"` in the response; no second account |
| `test_profil_depublicat_raspunde_410_si_noindex` (`:58`) | 410 + `X-Robots-Tag: noindex` |
| `test_anunt_expirat_raspunde_410` (`:66`) | 410 |

---

## 4. The public detail page and its JSON-LD (Fakt)

### `JobDetailView` — `apps/jobs/views.py:28-60`

Docstring (`:29-33`): the description is visible **without login**; only applying needs an
account — *"Dacă descrierea e în spatele autentificării, anunțul nu se califică pentru Google
for Jobs."*

Three outcomes, mirroring the account flow:

| Case | Result |
|---|---|
| slug not found, but in `ReservedSlug` | **410**, bare `HttpResponse` — **no `X-Robots-Tag`** (`:43-44`) |
| found but `not is_live` | **410** rendering `jobs/gone.html` + `X-Robots-Tag: noindex` (`:46-50`) |
| found and live | 200; `views_count` incremented via `F()` (`:51-53`) |

`views_count` fires on every GET with no session dedupe, no bot filter, no rate limit — **it
counts bots** — and nothing ever displays it.

### `render_jsonld()` — `apps/jobs/views.py:83-96`

```python
def render_jsonld(data: dict) -> str:
    """
    `json_script` emite type="application/json"; Google for Jobs cere
    application/ld+json. Serializăm manual și neutralizăm caracterele care
    ar putea închide tag-ul <script>.
    """
    raw = json.dumps(data, ensure_ascii=False)
    for char, escaped in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026")):
        raw = raw.replace(char, escaped)
    return mark_safe(raw)
```

This is the **only** `mark_safe` in `apps.jobs`. The three-character replacement is the sole
protection on the JSON-LD path for a `description` that contains HTML.

### `build_job_jsonld()` — `apps/jobs/views.py:99-141`, complete field list

| JSON key | Source expression | file:line |
|---|---|---|
| `@context` | `"https://schema.org"` | `:105` |
| `@type` | `"JobPosting"` | `:106` |
| `title` | `job.title` | `:107` |
| `description` | `job.description` (**raw, unsanitised**) | `:108` |
| `identifier` | `{"@type":"PropertyValue","name": job.account.display_name, "value": str(job.pk)}` | `:109-110` |
| `datePosted` | `job.published_at.date().isoformat()` **or `None`** if unpublished | `:111` |
| `validThrough` | `job.valid_through.isoformat()` | `:112` |
| `employmentType` | `job.employment_type` — **emitted raw** | `:113` |
| `hiringOrganization` | `{"@type":"Organization","name": display_name, "sameAs": base + account.get_absolute_url()}` where `base = f"{request.scheme}://{request.get_host()}"` (`:103`) | `:114-118` |
| `jobLocation` | `{"@type":"Place","address":{"@type":"PostalAddress","addressLocality": locality.name, "addressRegion": locality.region.name, "postalCode": locality.postal_code, "addressCountry": "DE"}}` | `:119-128` |
| `baseSalary` | **only when `job.salary_min` is truthy**: `{"@type":"MonetaryAmount","currency": salary_currency, "value":{"@type":"QuantitativeValue","minValue": float(salary_min), "maxValue": float(salary_max or salary_min), "unitText": salary_unit}}` | `:130-140` |

Fields that are **NOT** emitted: `directApply`, `industry`, `occupationalCategory`,
`jobLocationType`, `applicantLocationRequirements`, `qualifications` (`requirements` is unused),
`workHours`, `incentiveCompensation`.

Actual output on the seeded posting, captured verbatim from the running server on 2026-08-29:

```json
{"@context": "https://schema.org", "@type": "JobPosting",
 "title": "Reinigungskraft Norderstedt (bis 40 Std./Monat)",
 "description": "Reinigung der Gemeinschaftsflächen im Haus.",
 "identifier": {"@type": "PropertyValue", "name": "Seniorenresidenz Nord", "value": "1"},
 "datePosted": "2026-08-29",
 "validThrough": "2026-09-28T15:02:00+00:00",
 "employmentType": "MINIJOB",
 "hiringOrganization": {"@type": "Organization", "name": "Seniorenresidenz Nord",
   "sameAs": "http://127.0.0.1:8099/profil/seniorenresidenz-nord/"},
 "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress",
   "addressLocality": "Norderstedt", "addressRegion": "Schleswig-Holstein",
   "postalCode": "22846", "addressCountry": "DE"}},
 "baseSalary": {"@type": "MonetaryAmount", "currency": "EUR",
   "value": {"@type": "QuantitativeValue", "minValue": 14.25, "maxValue": 15.0,
             "unitText": "HOUR"}}}
```

**`"employmentType": "MINIJOB"` is not a value Google accepts.** The recognised set is
`FULL_TIME`, `PART_TIME`, `CONTRACTOR`, `TEMPORARY`, `INTERN`, `VOLUNTEER`, `PER_DIEM`, `OTHER`.
See `bekannte-maengel.md` §M8 for the fix shape — the mapping belongs in `build_job_jsonld`,
**not** in the model, because `Minijob` is a real German product concept (§8a SGB IV) that must
stay in the UI and in `ContractType`.

**`"datePosted": null`** is emitted whenever `published_at` is unset. A `DRAFT` posting normally
410s before reaching this code, but `build_job_jsonld` is callable directly.

### Templates

`templates/jobs/detail.html` — the whole public posting page, 11 lines:

```django
{% extends "base.html" %}
{% block title %}{{ job.title }}{% endblock %}
{% block content %}
<script type="application/ld+json">{{ jsonld }}</script>
<h1>{{ job.title }}</h1>
<p>{{ job.account.display_name }} · {{ job.locality.name }} · {{ job.get_employment_type_display }}</p>
{% if job.salary_min %}<p>{{ job.salary_min }}–{{ job.salary_max }} {{ job.salary_currency }} / {{ job.get_salary_unit_display }}</p>{% endif %}
<div>{{ job.description|linebreaks }}</div>
<h2>Candidatură</h2>
<form method="post" action="{% url 'jobs:apply' job.slug %}">{% csrf_token %}{{ form.as_p }}<button>Trimite candidatura</button></form>
{% endblock %}
```

`{{ job.get_salary_unit_display }}` renders the **Romanian** `oră` / `lună` on a German page,
and `<h2>Candidatură</h2>` is Romanian. `|linebreaks` **escapes**, so the
`help_text="HTML permis restrâns"` on `description` is not honoured in the HTML — but the
JSON-LD path does pass the raw string. Do not switch this to `|safe` without installing a
sanitiser.

`templates/jobs/list.html` (4 lines) and `templates/jobs/gone.html` (2 lines) are equally
minimal. Neither paginates, despite `paginate_by = 20` on `JobListView`.

### Public URLs — `apps/jobs/urls.py` (`app_name = "jobs"`, mounted at the site root)

| Name | Path |
|---|---|
| `list` | `/jobs/` |
| `list_city` | `/jobs/<slug:city>/` |
| `detail` | `/job/<slug:slug>/` |
| `apply` | `/job/<slug:slug>/bewerben/` |

`/jobs/<unknown-city>/` returns **200** with an empty list — the city slug is never validated
(verified 2026-08-29). See `bekannte-maengel.md` §M7.

---

## 5. The Google Indexing queue — `apps/jobs/indexing.py` (Fakt, EXISTS)

Three deliberately separate layers (module docstring `:1-12`):

```
enqueue()    — pune în coadă. Rulează în tranzacția care publică anunțul.
flush()      — golește coada. Rulează dintr-un cron, nu dintr-un request.
_transport   — apelul HTTP propriu-zis. Singurul loc care știe de Google.
```

| Symbol | file:line | Behaviour |
|---|---|---|
| `ENDPOINT` | `:19` | `https://indexing.googleapis.com/v3/urlNotifications:publish` |
| `SCOPE` | `:20` | `https://www.googleapis.com/auth/indexing` |
| `MAX_ATTEMPTS` | `:21` | `5` |
| `enqueue(url, action)` | `:24-29` | `get_or_create(url=…, action=…, status=PENDING)` — idempotent while still pending |
| `absolute_url(request, obj)` | `:32-33` | `request.build_absolute_uri(obj.get_absolute_url())` |
| `flush(limit=100, transport=None)` | `:36-62` | returns a **report dict**, never raises. With the real transport and no credentials it returns `{"skipped": …, "sent": 0, "failed": 0}`. On failure it records `last_error[:300]`, increments `attempts`, and only flips to `FAILED` at `attempts >= MAX_ATTEMPTS` |
| `_credentials_path()` | `:65-66` | reads `settings.GOOGLE_INDEXING_CREDENTIALS` |
| `_transport(url, action)` | `:69-81` | imports `google.auth` / `google.oauth2` **locally** so the dependency stays optional; POSTs `{"url": url, "type": action}` with a 15 s timeout; raises on HTTP ≥ 400 |

Management command: `apps/jobs/management/commands/flush_indexing.py` —
`manage.py flush_indexing --limit 100`, docstring *"De rulat din cron."*

`google-auth` and `requests` are declared in `pyproject.toml`'s
`[project.optional-dependencies].indexing` but are **not installed** in this venv. That is fine:
without `GOOGLE_INDEXING_CREDENTIALS` the real transport is never reached, and the tests inject
a fake transport.

Tests — `tests/test_seo.py::TestIndexingQueue` (`:68-145`), 6 tests: publish enqueues
`URL_UPDATED`; close enqueues `URL_DELETED`; `flush(transport=…)` marks `SENT`; a raising
transport leaves the task `PENDING` with `attempts == 1` and the error text recorded; after
`MAX_ATTEMPTS` it becomes `FAILED`; with an empty `GOOGLE_INDEXING_CREDENTIALS`, `flush()`
sends nothing and leaves the task `PENDING`.

**Not covered:** directory pages (city / city×category) and profiles have no indexing
notification. Only `JobPosting` URLs are enqueued.

---

## 6. sitemap.xml — `config/sitemaps.py` (Fakt, EXISTS)

It lives in **`config/`, not in `apps/jobs/`**. A search for `apps/jobs/sitemaps.py` will fail.

Module docstring (`:1-12`), verbatim:

> *"Regula unică: în sitemap intră DOAR ce răspunde 200. Un anunț expirat sau un profil
> depublicat răspunde 410 — dacă rămâne în sitemap, Google raportează eroare pe tot fișierul,
> iar pentru `JobPosting` asta afectează indexarea anunțurilor valide.*
> *Pentru anunțuri, sitemap-ul e plasa de siguranță, nu canalul principal: Google recomandă
> Indexing API pentru `JobPosting` (indexare în ~2 zile în loc de ~3 săptămâni)."*

| Class | file:line | `changefreq` | `priority` | `limit` | `items()` | `lastmod` |
|---|---|---|---|---|---|---|
| `JobSitemap` | `:24-39` | `daily` | `0.9` | `5000` | `JobPosting.objects.filter(status=PUBLISHED, valid_through__gt=now()).select_related("locality").order_by("-published_at")` | `obj.updated_at` |
| `ProfileSitemap` | `:42-51` | `weekly` | `0.7` | `5000` | `Account.objects.published().providers().distinct().order_by("-published_at")` | `obj.updated_at` |
| `DirectorySitemap` | `:54-78` | `weekly` | `0.8` | **none** (Django default 50000) | list of `(url_name, kwargs)` tuples, resolved by an overridden `location()` | **none** |

`DirectorySitemap.items()` (`:63-74`) builds, in order:

1. `("public:providers", {})` — 1 URL
2. `("public:providers_city", {"city": c.slug})` for each **active** locality
3. `("jobs:list_city", {"city": c.slug})` for each active locality — the job board's only
   presence in this sitemap; the flat `/jobs/` index is in **no** sitemap
4. `("public:providers_city_category", {"city": …, "category": …})` — the full cartesian product

Measured on the current seed data, 2026-08-29: **443 URLs** = 1 + 17 + 17 + (17 × 24), with
**17 active localities** (of 30) and **24 active leaf categories** (of 28 rows total).

```python
SITEMAPS = {"jobs": JobSitemap, "profiles": ProfileSitemap, "directory": DirectorySitemap}
```

Values are **classes, not instances** (Django's sitemap view accepts both).

Routes (`config/urls.py:15-21`) — index + per-section, so the section names become URLs:
`/sitemap.xml`, `/sitemap-jobs.xml`, `/sitemap-profiles.xml`, `/sitemap-directory.xml`.
All four verified 200 on 2026-08-29.

**Launch blocker (Fakt):** sitemap `<loc>` values come from `django.contrib.sites`
(`SITE_ID = 1`), and the `Site` row is still Django's default. Verified output:

```xml
<loc>http://example.com/job/reinigungskraft-norderstedt-bis-40-stdmonat/</loc>
```

The JSON-LD uses a **different** mechanism — `request.get_host()` (`apps/jobs/views.py:103`) —
so the two disagree in any environment where the `Site` row was not updated.
See `bekannte-maengel.md` §M6.

---

## 7. robots.txt (Fakt, EXISTS)

Route: `config/urls.py:22-26`, a `TemplateView` with `content_type="text/plain"`.
`templates/robots.txt`, complete file:

```
User-agent: *
Disallow: /admin/
Disallow: /dashboard/
Disallow: /cont/
Disallow: /accounts/

Sitemap: {{ request.scheme }}://{{ request.get_host }}/sitemap.xml
```

The `Sitemap:` line uses `request.get_host` (works because
`django.template.context_processors.request` is enabled, `config/settings.py:62`), so it is
host-correct **even while the `Site` row is wrong**. Nothing under `/jobs/`, `/job/` or
`/reinigungskraft/` is disallowed — correct.

Verified 200 `text/plain` on 2026-08-29. Test:
`test_robots_indica_sitemapul_si_blocheaza_dashboardul` (`tests/test_seo.py:60-65`).

---

## 8. Sitemap tests — the contract that must not regress

`tests/test_seo.py::TestSitemap` (`:16-56`), 7 tests. Module docstring (`:1-5`): *"Contractul
verificat aici: în sitemap intră DOAR ce răspunde 200."*

| Test | Asserts |
|---|---|
| `test_indexul_listeaza_sectiunile` | `/sitemap.xml` 200 and lists all three section files |
| `test_anuntul_activ_e_in_sitemap` | live posting URL present in `/sitemap-jobs.xml` |
| `test_anuntul_expirat_iese_din_sitemap_si_da_410` | expiry removes it **and** the URL is 410 + noindex |
| `test_anuntul_inchis_iese_din_sitemap` | `CLOSED` removes it |
| `test_profilul_publicat_e_in_sitemap` | published worker profile present |
| `test_profilul_depublicat_iese_din_sitemap_si_da_410` | depublication removes it **and** 410 + noindex |
| `test_directorul_contine_paginile_de_oras` | `/reinigungskraft/<city>/` and `/jobs/<city>/` both present |

---

## 9. The SEO gaps that are real today (Fakt)

Everything below was re-verified on 2026-08-29. Items the older dossiers list as missing
(**sitemap, robots.txt, Indexing API**) now **exist** — do not report them as gaps.

| # | Gap | Evidence |
|---|---|---|
| S1 | **`Site` row is `example.com`** → every sitemap `<loc>` is wrong. Launch blocker. | verified query: `Site.objects.values_list("id","domain")` → `[(1, "example.com", "example.com")]` |
| S2 | **`employmentType: "MINIJOB"`** is not a Google-recognised value | `apps/jobs/views.py:113` |
| S3 | **No `directApply`** in the JSON-LD, although the apply form is on-site — a free win | `build_job_jsonld` field list |
| S4 | **No canonical, meta description, OpenGraph or hreflang** anywhere. `base.html` has only `<title>`, charset, viewport and the messages block | `templates/base.html` (16 lines) |
| S5 | **443 thin directory URLs submitted.** `DirectorySitemap` emits the full city × leaf product with no supply filter, no `limit`, no `lastmod`. Most render an empty list | `config/sitemaps.py:63-74`; measured 443 |
| S6 | **Unknown / inactive city and category slugs return 200**, not 404 — an unbounded space of indexable soft-404s | verified: `/jobs/inexistent-oras/` 200, `/reinigungskraft/nu-exista/nici-asta/` 200 |
| S7 | **The flat `/jobs/` index is in no sitemap** | `DirectorySitemap` emits only `jobs:list_city` |
| S8 | **No JSON-LD on the public profile** — no `LocalBusiness` / `Person` schema | `PublicProfileView.get_context_data`, `apps/accounts/views.py:165-174` |
| S9 | **The `ReservedSlug` 410 branch omits `X-Robots-Tag: noindex`** (both for jobs and for accounts) | `apps/jobs/views.py:43-44`; `apps/accounts/views.py:154-156` |
| S10 | **`JobStatus.EXPIRED` is unreachable** — no cron/command/signal transitions to it | grep: only `models.py:18` and the migration |
| S11 | **No pagination UI** on `/jobs/` (`paginate_by = 20`) or `/reinigungskraft/` (`paginate_by = 24`) | `templates/jobs/list.html`, `templates/accounts/provider_list.html` |
| S12 | **`requirements` never rendered or emitted**; would map to `qualifications` in JSON-LD | grep across templates and `build_job_jsonld` |
| S13 | **No HTML sanitiser** despite `help_text="HTML permis restrâns"` | no `bleach`/`nh3` in `pyproject.toml` or the venv |
| S14 | **`provider_list.html` hard-codes `/profil/{{ v.slug }}/`** instead of reversing `public:profile` | `templates/accounts/provider_list.html:3` |
| S15 | **N+1 on the provider list** — `{{ v.locality }}` dereferences `region` in `Locality.__str__` while the view only does `select_related("locality")` | `apps/geo/models.py:44`; `apps/accounts/views.py:185` |

---

## 10. Recipes

### Vorschlag — map `employmentType` for the JSON-LD only

```python
# apps/jobs/views.py — near build_job_jsonld
SCHEMA_EMPLOYMENT_TYPE = {
    EmploymentType.FULL_TIME:  "FULL_TIME",
    EmploymentType.PART_TIME:  "PART_TIME",
    EmploymentType.MINIJOB:    "PART_TIME",   # Minijob is legally part-time; Google has no MINIJOB
    EmploymentType.CONTRACTOR: "CONTRACTOR",
    EmploymentType.TEMPORARY:  "TEMPORARY",
}
...
"employmentType": SCHEMA_EMPLOYMENT_TYPE.get(job.employment_type, "OTHER"),
"directApply": True,
```

Keep `EmploymentType.MINIJOB` in the model and in the UI — it is the German product term.
Add a test in `tests/test_seo.py` asserting the mapped value, then run
`.venv/bin/python -m pytest -q tests/test_seo.py`.

### Vorschlag — make an unknown city slug 404

```python
# apps/jobs/views.py, JobListView.get_queryset
if city := self.kwargs.get("city"):
    get_object_or_404(Locality, slug=city, is_active=True)
    qs = qs.filter(locality__slug=city)
```

Mirror it in `apps/accounts/views.py::ProviderListView` for `city` and `category`. Note this
changes behaviour for **inactive** localities too, whose URLs may already be indexed — the
project's established pattern for retiring an indexed URL is 410 + noindex, not 404. Decide
which you want before shipping, and add the test.

### Recipe — add a new sitemap section

1. Add a `Sitemap` subclass to `config/sitemaps.py` with `changefreq`, `priority`, a `limit`
   and a `lastmod`.
2. Its `items()` must return **only** things that answer 200 — mirror the live predicate
   exactly, do not re-derive it.
3. Add the key to `SITEMAPS` (`:81-85`). The key becomes `/sitemap-<key>.xml`.
4. Add a test in `tests/test_seo.py::TestSitemap` asserting both membership **and** the
   negative case (a non-live object must be absent).

---

## Quellen

- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/jobs/models.py`, `views.py`, `urls.py`,
  `forms.py`, `services.py`, `indexing.py`, `dashboard_views.py`,
  `management/commands/flush_indexing.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/config/sitemaps.py`, `config/urls.py`,
  `config/settings.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/templates/jobs/detail.html`, `list.html`,
  `gone.html`, `templates/robots.txt`, `templates/base.html`,
  `templates/dashboard/postings.html`
- `/Users/Geronimo/Projects/Cleaning_SaaS/tests/test_application_flow.py`,
  `tests/test_seo.py`
- `scratchpad/dossier/jobs.md` ("SEO surface", gotchas, gaps)
- `scratchpad/dossier/_verified-ground-truth.md` (the verbatim JSON-LD capture)
- Runtime checks 2026-08-29: URL status codes, `Site` row, `DirectorySitemap` URL count,
  active locality / leaf-category counts
