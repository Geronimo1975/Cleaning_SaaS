# Skills — Cleaning_SaaS

> Inventar generat pe **2026-08-30** pentru `/Users/Geronimo/Projects/Cleaning_SaaS`
> (Django 5.2 · Python 3.12 · django-allauth · django-htmx · SQLite dev / psycopg prod · pytest-django · openpyxl)
>
> Surse scanate: `~/.claude/skills/` (**189** skill-uri globale) · `.claude/skills/` (**8** skill-uri de proiect) ·
> `~/.claude/plugins/` (**26** plugin-uri instalate) · `~/.agents/skills/` (63, majoritatea link-uite deja în global)

---

## 1. Skill-uri de proiect — `.claude/skills/` (obligatorii)

Acestea sunt scrise special pentru acest repo și **au prioritate peste orice sfat generic** de Django/marketplace/payroll.

| Skill | Scop | Se declanșează pe |
|---|---|---|
| **`cleaning-saas-codebase`** | Convențiile repo-ului. **Se încarcă întotdeauna** înainte de a citi sau edita orice. Suprascrie Django generic: fără `admin.py`, fără template-uri la nivel de app, fără coloană `role`. | `apps/*`, `config/`, `tests/`, `Account`, `AccountView`, `JobPosting`, `ShiftPlan`, `ContractDraft`, `WageFloor`, `ServiceRequest`; „add a dashboard page", „add a locality", „write a test", „fix the sitemap" |
| **`gebaeudereinigung-domain`** | Skill de fundament: teza de produs (Marktplatz / Dispatch / Betrieb), regulile de denumire DE‑RO‑EN, vocabularul industriei, cele 5 roluri, harta app-urilor care există vs. care nu. | Înainte de a numi orice, de a adăuga un model sau un URL, sau de a răspunde la „ce înseamnă X" |
| **`gr-vermittlungsmodell`** | Modelul de operare: Genossenschaft (eG) de Betriebe independente + Vermittlung centrală (model inline‑kurier.de). Suprascrie instinctul employee‑vs‑gig. | Genossenschaft, Mitglied, Scheinselbstständigkeit, §7 SGB IV, AÜG, Vermittlung, Disposition, Festtour, Kapazitätsklasse, „who sets the price", „can we auto-assign" |
| **`gr-marktplatz-dispatch`** | `apps/marketplace` (ServiceRequest, Offer, Invitation, `scoring.py`, `suggest_providers`), rutele `/dashboard/cereri/` și `/dashboard/bursa/`. | bursă de servicii, ofertă, atribuire, matching, auto-allocation, Ausschreibung, Vergabe, escrow, split payment |
| **`gr-einsatzplanung`** | `apps/planning` (Site, Zone, ShiftPlan, Shift, ShiftEvent, ZoneCalibration, `reinigungsplan.py`), rutele `/dashboard/obiective/`, `/planificare/`, `/turele-mele/`, `/pontaj/`, `/calibrare/`, export XLSX. | Einsatzplan, Dienstplan, Reinigungsplan, Dauerauftrag, Zone, Vertretung, Ruhezeit, `minutes_per_visit`, roster generation |
| **`gr-zeiterfassung`** | Pontaj / Zeiterfassung: `apps/planning/attendance.py`, `ShiftStatus`, `/dashboard/pontaj/`, `tests/test_attendance.py`, `apps/devices/services.py`. | Stundenzettel, Check-in/out, Sollarbeitszeit, Ruhepausen, Geofence, GPS-Ortung, Zoll/FKS-Export, nachgetragene Zeiten |
| **`gr-tarif-und-lohn`** | Tarif & salarizare Gebäudereinigung: `apps/contracts` (WageFloor, MinijobThreshold, `compliance_issues`, `0002_seed_wage_floors.py`), `apps/jobs` (`salary_min/max`). Împiedică hardcodarea sumelor și cumularea greșită a sporurilor. | Lohngruppen LG 1–9, Mindestlohntarifvertrag, RTV, AVE, §7 AEntG, Zuschläge, Minijob-/Midijob-Grenze, DATEV/CSV payroll export |
| **`gr-auftrag-und-faktura`** | Stratul comercial care **încă nu există** în repo: client, comandă, ofertă, facturare. | Kunde, Auftrag, Angebot, Rechnung, XRechnung, ZUGFeRD, EN 16931, GoBD, Mahnung, Leitweg‑ID, Stundenverrechnungssatz, Deckungsbeitrag |

**Ordinea de încărcare recomandată:**
`gebaeudereinigung-domain` → `cleaning-saas-codebase` → skill-ul specific stratului atins (`gr-*`).

---

## 2. Skill-uri globale relevante pentru acest proiect

### 2.1 Backend / Django (nucleu)

| Skill | De ce contează aici |
|---|---|
| **`django`** | Django 5.x: modele, views, migrări, settings, middleware, management commands. Acoperă django-allauth (folosit) și PostgreSQL. ⚠️ Menționează DRF/django-unfold — **nu sunt în stack**, ignoră acele părți. |
| **`django-expert`** | Ghid aprofundat: ORM, debugging queries, migrări, autentificare, teste. Cel mai bun pentru „de ce e lent query-ul ăsta". |
| **`django-tdd`** | pytest-django, factory_boy, mocking, coverage — se potrivește exact peste `pytest.ini` + `tests/conftest.py` existente. |
| **`django-6-senior`** | Referință Django 6.0 (RO): template partials, HTMX, Tasks framework, CSP, async, **migrarea 5.2 → 6.x**. Relevant pentru planificarea upgrade-ului; azi repo-ul e pinned `<6.0`. |
| **`db-admin`** | PostgreSQL 16: EXPLAIN ANALYZE, indexuri, VACUUM, partiționare, backup. Devine critic la migrarea `db.sqlite3` → psycopg. |
| **`deploy`** | Docker Compose, GitHub Actions, Nginx, SSL, backup DB, zero-downtime. Scris pentru Django + **React**. ⚠️ Serviciul `frontend` (Vite, port 5173) **nu se aplică aici** — Cleaning_SaaS e server-rendered cu templates + HTMX, fără build step JS. Restul (db, redis, web, celery, nginx, backup) e direct utilizabil. |
| `graphify` | Knowledge graph peste codebase — util pentru „cum se leagă `apps.marketplace` de `apps.planning`". |

> ⚠️ `database-optimizer` există ca director gol în `~/.claude/skills/` — **fără `SKILL.md`, deci neîncărcabil**. De șters sau de completat.

### 2.2 Frontend — templates server-rendered + HTMX

Repo-ul are `templates/base.html` + 24 template-uri de dashboard, fără build step JS.

| Skill | Notă |
|---|---|
| **`web-design-guidelines`** | Review de conformitate a UI-ului (accesibilitate, best practices). Cel mai potrivit pentru template-urile Django. |
| **`frontend-design`** | Interfețe de calitate producție, fără „aspect generic de AI". |
| **`tailwind-design-system`** / `tailwindcss` | Doar dacă se adoptă Tailwind (momentan nu e în `pyproject.toml`). |
| **`design-review`** | Audit vizual cu screenshots — layout, tipografie, spațiere, ierarhie. |
| **`responsiveness-check`** | Sweep pe breakpoints cu browser automation; pontajul se folosește pe telefon → chiar necesar. |
| **`web-performance-optimization`** | Core Web Vitals, caching, loading. |
| `emil-design-eng`, `taste-skill`, `frontend-2026` | Polish / direcție de design. `frontend-2026` presupune Next.js+React — folosește-l doar ca referință CSS baseline. |
| **`ui-ux-pro-max`** (plugin) | ⚠️ **CLAUDE.md global impune invocarea lui înainte de orice muncă de UI.** |

### 2.3 Testare & automatizare browser

| Skill | Notă |
|---|---|
| **`playwright-skill`** | Auto-detectează dev server, testează login flows, formulare, screenshots. Complementar cu `tests/` (pytest). |
| `responsiveness-check` | vezi mai sus |

### 2.4 SEO / GEO — pentru partea publică (`config/sitemaps.py`, `apps/geo`, `tests/test_seo.py`)

| Skill | Notă |
|---|---|
| **`seo-sitemap`** | Direct aplicabil pe `config/sitemaps.py` + `tests/test_seo.py`. |
| **`seo-technical`** | Crawlability, indexability, robots.txt, CWV, IndexNow. |
| **`seo-schema`** | JSON‑LD: `LocalBusiness`, `JobPosting` (ai `apps/jobs`!), `Service`. Impact mare pentru anunțuri. |
| **`seo-audit`** | Audit complet cu delegare la sub-agenți; de rulat înainte de lansare. |
| `seo`, `geo`, `seo-geo`, `seo-content` | Vizibilitate în AI search, E‑E‑A‑T, llms.txt. |
| `blog-write`, `content-research-writer` | Conținut pentru piața Hamburg / Schleswig‑Holstein. |

### 2.5 Documente & date

| Skill | Notă |
|---|---|
| **`xlsx`** | **Export Reinigungsplan** — repo-ul are `openpyxl` ca extra `[export]` și `apps/planning/reinigungsplan.py`. Skill-ul de referință pentru formule, formatare, charting. |
| **`pdf`** | Leistungsnachweis, contracte, Stundenzettel semnate, viitoarele facturi. |
| **`draw-io`** | Diagrame de arhitectură / flux de dispatch. |
| `obsidian` | Dacă documentația de proiect ajunge în vault. |

### 2.6 Drept german al muncii (Arbeitsrecht) — direct legat de compliance-ul din `apps/contracts`

| Skill | Notă |
|---|---|
| **`rechtsrecherche`** | Identifică paragrafele aplicabile (ArbZG, AÜG, SGB IV, AEntG, MiLoG). Perechea naturală a lui `gr-tarif-und-lohn`. |
| `subsumtion` | Analiză algoritmică a stării de fapt. |
| `anspruchsberechnung` | Calcul pretenții — util ca referință pentru logica de `compliance_issues`. |
| `fallstrategie`, `schriftsatz`, `fallanalyse` | Strategie de caz / redactare documente. Relevante doar dacă produsul generează documente juridice. |

### 2.7 Meta / flux de lucru

| Skill | Notă |
|---|---|
| **`claude-start`** | ⚠️ **Repo-ul nu are `CLAUDE.md`.** Rulează `/claude-start` pentru a-l genera + `.mcp.json` + `settings.json`. Cel mai valoros quick win. |
| **`commit`** | ⚠️ **Repo-ul nu e sub git** (`git init` lipsește). De inițializat înainte. |
| `git-worktree` | Agenți paraleli pe același repo — după `git init`. |
| **`skill-creator`** | Pentru a extinde setul `gr-*` (ex. un viitor `gr-faktura` din stub-ul actual). |
| `find-skills` | Descoperă/instalează skill-uri noi. |
| `handoff`, `decisions`, `next-decision`, `before-building`, `prompt-me` | Continuitate între sesiuni și clarificarea deciziilor deschise (relevant, ai `PLAN-FAZA-0.md`). |
| `changelog-generator`, `brain-to-docs`, `read-all-adrs` | Documentație. Nu există `docs/adr/` încă. |
| `short`, `remind`, `teach`, `setup-help`, `level-up`, `stop-overthinking` | Utilitare de conversație. |

### 2.8 Integrări posibile (nu încă în stack)

`n8n-workflow-patterns`, `n8n-expression-syntax`, `n8n-mcp-tools-expert`, `n8n-validation-expert` — automatizări (notificări turnus, sincronizare payroll). Ai și MCP-uri n8n conectate.
`claude-api` — dacă apare funcționalitate AI în produs. `scrape` — colectare date piață.

---

## 3. Skill-uri de plugin relevante

| Plugin | Skill-uri utile aici |
|---|---|
| **superpowers** | `brainstorming` (obligatoriu înainte de orice feature nou), `systematic-debugging`, `test-driven-development`, `writing-plans`, `executing-plans`, `verification-before-completion`, `requesting-code-review`, `using-git-worktrees` |
| **ui-ux-pro-max** | `ui-ux-pro-max`, `design`, `design-system`, `ui-styling`, `brand` — impuse de CLAUDE.md global pentru UI |
| **code-review** | `/code-review` (+ `ultra` pentru review multi-agent) |
| **code-simplifier** | `/simplify` |
| **commit-commands** | `/commit`, `/commit-push-pr` |
| **hookify** | Hook-uri: ex. rulează `pytest` la fiecare edit în `apps/` |
| **claude-obsidian** | `wiki`, `save`, `think` — dacă documentezi în vault |
| **security-guidance** | `/security-review` — relevant DSGVO (date GPS + pontaj angajați) |
| **pyright-lsp** | Type checking Python |
| **playwright** | MCP browser (tools deja conectate) |
| **stripe** | Doar când ajungi la `gr-auftrag-und-faktura` / plăți |
| **github**, **pr-review-toolkit**, **feature-dev** | După `git init` + remote |

---

## 4. Ce **nu** e relevant pentru acest proiect

Din cele 189 de skill-uri globale, aprox. **110 sunt de grafică web / 3D / animație / marketing** și nu au aplicabilitate într-un SaaS Django server-rendered pentru firme de curățenie:

- **Three.js / WebGL / shadere** (~35): `threejs*`, `react-three-fiber`, `webgl-*`, `globe-gl`, `globe-particles`, `spline-interactive`, `unicorn-studio`, `blender-web-pipeline`, `vantajs`, `cobejs`, `matterjs`, `web3d-integration-patterns`, `lightweight-3d-effects`…
- **Animație / scroll storytelling** (~25): `gsap*`, `motion-framer`, `animejs`, `locomotive-scroll`, `cinematic-*`, `scroll-*`, `animate*`, `improve-animations`, `review-animations`, `find-animation-opportunities`…
- **Efecte vizuale CSS** (~25): `gooey-blob-system`, `liquid-metal-border`, `dither-background`, `progressive-blur`, `corner-lasers`, `beam-glow-states`, `glass-dark-ui`, `skeuomorphic-ui`, `marquee-loop`, `masked-reveal`, `thinking-orbs`…
- **Template-uri de landing/agency** (~12): `agency-grid-layout-minimal`, `documentary-brutalist-agency`, `editorial-portfolio-chapters`, `build-awwwards-quality-sites`, `landing-page-design`, `product-proof-saas`…
- **Alte proiecte / branduri**: `rotocon-brand`, `rotocon-wagtail`, `odoo-19`, `faktory-theme`, `wagtail`, `v0`, `write-swift`, `apple-design`
- **Marketing / personal**: `twitter-algorithm-optimizer`, `tailored-resume-generator`, `competitive-ads-extractor`, `lead-research-assistant`, `domain-name-brainstormer`, `raffle-winner-picker`, `invoice-organizer`, `meeting-insights-analyzer`, `video-downloader`, `autoresearch`, `notebooklm`, `gpt-image-2`, `image-enhancer`, `unsplash-asset-images`, `company-logos`

---

## 5. Acțiuni recomandate

1. **`git init`** — repo-ul nu e sub control de versiune. Blochează `commit`, `git-worktree`, `code-review`, `github`.
2. **`/claude-start`** — generează `CLAUDE.md` la rădăcina proiectului; momentan nu există și se pierde contextul de convenții între sesiuni.
3. **Șterge `~/.claude/skills/database-optimizer/`** — director gol, fără `SKILL.md`.
4. **Creează `.claude/settings.json`** — allowlist pentru `pytest`, `python manage.py`, `ruff` (reduce prompt-urile de permisiune).
5. Când ajungi la facturare: `gr-auftrag-und-faktura` este singurul skill `gr-*` care descrie cod **inexistent** — tratează-l ca spec, nu ca documentație.
