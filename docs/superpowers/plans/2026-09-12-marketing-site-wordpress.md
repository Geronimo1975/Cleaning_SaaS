# Site de marketing WordPress — plan de implementare

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un al doilea stack (WordPress + MariaDB) pe același VPS cu Traefik, la `www.DOMENIU`, iar Django la `app.DOMENIU` cu un singur link înapoi spre site.

**Architecture:** Două compose-uri independente pe rețeaua externă `gethub_gethub-network`; Traefik rutează după `Host`. Django primește o setare `MARKETING_SITE_URL` expusă printr-un context processor și folosită în două template-uri. WP se operează manual (temă, plugin-uri, pagini); repo-ul livrează doar infrastructura și textele paginilor.

**Tech Stack:** Docker Compose, Traefik v2.11 (existent pe server), `wordpress:6-php8.3-apache`, `mariadb:11`, Django 5.2, pytest-django.

**Spec:** `docs/superpowers/specs/2026-09-12-marketing-site-wordpress-design.md`

## Global Constraints

- Limbi: comentarii/docstring/teste în română; identificatori Python și `name=` de URL în engleză; copy public și paginile WP în germană.
- `DOMENIU` rămâne placeholder în `.env.example` și README; nu se inventează un domeniu.
- Zip-ul ThemeForest nu intră în git (`themeforest-*.zip` în `.gitignore`).
- Fără SSO, API, webhook sau includere de HTML din WP în Django.
- Comenzile Python se rulează cu `.venv/bin/python` (nu există `pip`, nu există `python` global garantat).
- Commit-urile se termină cu liniile de atribuire din sesiune.
- Working tree partajat cu alte sesiuni: `git status` înainte de fiecare scriere; comite doar fișierele task-ului.

---

### Task 1: `MARKETING_SITE_URL` în Django + link în template-uri

**Files:**
- Modify: `config/settings.py` (după linia 17, blocul `ALLOWED_HOSTS`)
- Modify: `config/settings.py:71-76` (lista `context_processors`)
- Modify: `apps/dashboard/context_processors.py` (funcție nouă la final)
- Modify: `templates/base.html:9-15` (header nou înainte de `messages`)
- Modify: `templates/app.html:46` (`<header class="topbar">`)
- Test: `tests/test_legal.py` (clasă nouă la final)

**Interfaces:**
- Produces: `settings.MARKETING_SITE_URL: str` (gol implicit); variabila de template `marketing_site_url` pe orice pagină.

- [ ] **Step 1: Scrie testele care pică**

Adaugă la finalul `tests/test_legal.py`:

```python
@pytest.mark.django_db
class TestMarketingLink:
    """Logo-ul paginilor publice duce la site-ul de marketing când e configurat."""

    def test_fara_setare_logo_duce_la_jobs(self, client, settings):
        settings.MARKETING_SITE_URL = ""
        response = client.get("/impressum/")
        assert b'class="brand" href="/jobs/"' in response.content

    def test_cu_setare_logo_duce_la_site(self, client, settings):
        settings.MARKETING_SITE_URL = "https://www.example.de"
        response = client.get("/impressum/")
        assert b'class="brand" href="https://www.example.de"' in response.content
```

- [ ] **Step 2: Rulează testele — trebuie să pice**

Run: `.venv/bin/python -m pytest tests/test_legal.py::TestMarketingLink -q`
Expected: 2 failed (`base.html` nu are încă `class="brand"`).

- [ ] **Step 3: Setarea**

În `config/settings.py`, imediat după blocul `if DEBUG: ALLOWED_HOSTS.append("testserver")`:

```python
# Site-ul de marketing (WordPress, pe www.). Gol = nu există încă; logo-ul
# paginilor publice duce atunci la /jobs/, pentru că nu avem rută `/`.
MARKETING_SITE_URL = os.getenv("MARKETING_SITE_URL", "").rstrip("/")
```

- [ ] **Step 4: Context processor**

La finalul `apps/dashboard/context_processors.py`:

```python
def marketing(request):
    """Link-ul spre site-ul WordPress. Separat de `navigation`, care iese
    devreme fără cont activ — dar link-ul e necesar și pe paginile publice."""
    from django.conf import settings

    return {"marketing_site_url": settings.MARKETING_SITE_URL}
```

În `config/settings.py`, în lista `context_processors`, după linia
`"apps.dashboard.context_processors.navigation",` adaugă:

```python
                "apps.dashboard.context_processors.marketing",
```

- [ ] **Step 5: Template-uri**

În `templates/base.html`, înlocuiește `<body>` … `{% if messages %}` cu:

```html
<body>
  <header class="public-top">
    <a class="brand" href="{% if marketing_site_url %}{{ marketing_site_url }}{% else %}/jobs/{% endif %}">
      <span class="brand-mark">PF</span> ProFM
    </a>
  </header>
  {% if messages %}
```

În `templates/app.html`, în interiorul `<header class="topbar">`, ca prim
copil (înaintea a ce există deja):

```html
      {% if marketing_site_url %}<a class="btn btn-sm" href="{{ marketing_site_url }}">Site</a>{% endif %}
```

Logo-ul din sidebar-ul aplicației rămâne spre `dashboard:home` — un
utilizator logat vrea acasă în aplicație, nu pe pagina de marketing.

- [ ] **Step 6: Rulează testele — trebuie să treacă**

Run: `.venv/bin/python -m pytest tests/test_legal.py -q`
Expected: toate PASS.

Run: `.venv/bin/python -m pytest -q`
Expected: 0 failed (numărul total poate diferi de 324 după alte commit-uri).

- [ ] **Step 7: Commit**

```bash
git add config/settings.py apps/dashboard/context_processors.py templates/base.html templates/app.html tests/test_legal.py
git commit -m "Link spre site-ul de marketing: MARKETING_SITE_URL în paginile publice și în topbar"
```

---

### Task 2: `.env.example`, `.gitignore`

**Files:**
- Modify: `.env.example:4-7`
- Modify: `.env.example` (bloc nou la final)
- Modify: `.gitignore` (linie nouă)

- [ ] **Step 1: Gazdele**

În `.env.example` înlocuiește:

```
ALLOWED_HOSTS=example.de,www.example.de

# Doar pentru varianta Traefik: gazda pe care o rutează.
APP_HOST=example.de
```

cu:

```
# Aplicația trăiește pe `app.`; `www.` e site-ul WordPress (docker-compose.wp.yml).
ALLOWED_HOSTS=app.example.de

# Doar pentru varianta Traefik: gazda pe care o rutează.
APP_HOST=app.example.de

# Site-ul de marketing. Gol cât timp nu există.
MARKETING_SITE_URL=https://www.example.de
```

- [ ] **Step 2: Variabilele WP**

La finalul `.env.example`:

```
# WordPress (docker-compose.wp.yml). Stack separat, aceeași rețea Traefik.
WP_HOST=www.example.de
WP_DB_NAME=wordpress
WP_DB_USER=wordpress
WP_DB_PASSWORD=schimba-ma
```

- [ ] **Step 3: gitignore**

Adaugă la finalul `.gitignore`:

```
# Tema ThemeForest — licență personală, se urcă manual în WP.
themeforest-*.zip
```

- [ ] **Step 4: Verifică**

Run: `git status --short | grep themeforest`
Expected: nicio linie (zip-ul nu mai apare ca untracked).

- [ ] **Step 5: Commit**

```bash
git add .env.example .gitignore
git commit -m "Env: app. pentru Django, www. + variabile WP; zip-ul temei rămâne în afara git-ului"
```

---

### Task 3: `docker-compose.wp.yml` + `deploy/wp-uploads.ini`

**Files:**
- Create: `docker-compose.wp.yml`
- Create: `deploy/wp-uploads.ini`

**Interfaces:**
- Consumes: `WP_HOST`, `WP_DB_NAME`, `WP_DB_USER`, `WP_DB_PASSWORD` din `.env` (Task 2).
- Produces: volumele `cleaning_wp_data`, `cleaning_wp_db`; serviciile `wp`, `wpdb` (numele contează pentru Task 4).

- [ ] **Step 1: php.ini pentru upload**

`deploy/wp-uploads.ini`:

```ini
; revslider.zip are 10,7 MB; limita implicită PHP e 2M.
upload_max_filesize = 64M
post_max_size = 64M
memory_limit = 256M
```

- [ ] **Step 2: Compose**

`docker-compose.wp.yml`:

```yaml
# Site-ul de marketing (WordPress) — stack separat de aplicație.
#
# Aceeași mașină, același Traefik, altă gazdă (`WP_HOST`, adică www.). Nu
# partajează nimic cu Django: nici baza, nici volumele, nici rețeaua internă.
# Se pornește cu `docker compose -f docker-compose.wp.yml up -d`.

services:
  wpdb:
    image: mariadb:11
    restart: unless-stopped
    environment:
      MARIADB_DATABASE: ${WP_DB_NAME}
      MARIADB_USER: ${WP_DB_USER}
      MARIADB_PASSWORD: ${WP_DB_PASSWORD}
      MARIADB_RANDOM_ROOT_PASSWORD: "1"
    volumes:
      - wp_db:/var/lib/mysql
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - wp_internal

  wp:
    image: wordpress:6-php8.3-apache
    restart: unless-stopped
    environment:
      WORDPRESS_DB_HOST: wpdb
      WORDPRESS_DB_NAME: ${WP_DB_NAME}
      WORDPRESS_DB_USER: ${WP_DB_USER}
      WORDPRESS_DB_PASSWORD: ${WP_DB_PASSWORD}
      # În spatele Traefik, WP vede HTTP; fără asta generează link-uri http://
      # și intră în buclă de redirect.
      WORDPRESS_CONFIG_EXTRA: |
        if (isset($$_SERVER['HTTP_X_FORWARDED_PROTO']) && $$_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https') { $$_SERVER['HTTPS'] = 'on'; }
    volumes:
      - wp_data:/var/www/html
      - ./deploy/wp-uploads.ini:/usr/local/etc/php/conf.d/uploads.ini:ro
    depends_on:
      wpdb:
        condition: service_healthy
    networks:
      - wp_internal
      - traefik
    labels:
      traefik.enable: "true"
      traefik.docker.network: gethub_gethub-network

      traefik.http.routers.wp-http.rule: Host(`${WP_HOST}`)
      traefik.http.routers.wp-http.entrypoints: web
      traefik.http.routers.wp-http.middlewares: wp-https-redirect

      traefik.http.middlewares.wp-https-redirect.redirectscheme.scheme: https
      traefik.http.middlewares.wp-https-redirect.redirectscheme.permanent: "true"

      traefik.http.routers.wp.rule: Host(`${WP_HOST}`)
      traefik.http.routers.wp.entrypoints: websecure
      traefik.http.routers.wp.tls: "true"
      traefik.http.routers.wp.tls.certresolver: letsencrypt

      traefik.http.services.wp.loadbalancer.server.port: "80"

networks:
  wp_internal:
  traefik:
    external: true
    name: gethub_gethub-network

volumes:
  wp_data:
  wp_db:
```

- [ ] **Step 3: Validează**

Run (cu un `.env` local care conține cele 4 variabile `WP_*`; dacă nu ai, `cp .env.example .env` temporar și șterge-l după):

```bash
docker compose -f docker-compose.wp.yml config >/dev/null && echo OK
```

Expected: `OK`. Dacă `docker` lipsește local, verifică sintaxa YAML cu
`.venv/bin/python -c "import yaml,sys; yaml.safe_load(open('docker-compose.wp.yml'))"` — dacă nici `yaml` nu e în venv, notează în commit că validarea se face pe server.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.wp.yml deploy/wp-uploads.ini
git commit -m "Stack WordPress pentru www.: compose separat pe același Traefik"
```

---

### Task 4: Backup MariaDB + volum WP

**Files:**
- Modify: `deploy/backup-db.sh:31-45`

**Interfaces:**
- Consumes: serviciile `wpdb` și volumul `cleaning_wp_data` din Task 3; `WP_DB_USER`, `WP_DB_PASSWORD`, `WP_DB_NAME` din `.env`.

- [ ] **Step 1: Ramura WP**

În `deploy/backup-db.sh`, după blocul `docker run … private_$TIMESTAMP.tar.gz`
și înaintea liniilor `find`, adaugă:

```bash
# WordPress — doar dacă stack-ul rulează pe această mașină. Site-ul de
# marketing nu are date legale, dar are conținut pe care nimeni nu-l rescrie
# de plăcere.
if docker compose -f docker-compose.wp.yml ps --status running wpdb 2>/dev/null | grep -q wpdb; then
    WP_DB_USER=$(env_value WP_DB_USER)
    WP_DB_PASSWORD=$(env_value WP_DB_PASSWORD)
    WP_DB_NAME=$(env_value WP_DB_NAME)
    docker compose -f docker-compose.wp.yml exec -T wpdb \
        mariadb-dump -u "$WP_DB_USER" -p"$WP_DB_PASSWORD" "$WP_DB_NAME" \
        | gzip > "$BACKUP_DIR/wp_db_$TIMESTAMP.sql.gz"
    docker run --rm \
        -v cleaning_wp_data:/data:ro \
        -v "$BACKUP_DIR":/backup \
        alpine tar czf "/backup/wp_files_$TIMESTAMP.tar.gz" -C /data .
fi
```

Și la `find`-uri adaugă:

```bash
find "$BACKUP_DIR" -name 'wp_*' -mtime +"$KEEP_DAYS" -delete
```

- [ ] **Step 2: Verifică sintaxa**

Run: `bash -n deploy/backup-db.sh && echo OK`
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add deploy/backup-db.sh
git commit -m "Backup: include baza și fișierele WordPress când stack-ul rulează"
```

---

### Task 5: README de deploy

**Files:**
- Modify: `deploy/README.md` (secțiune nouă după varianta Traefik, înaintea liniei `---`)

- [ ] **Step 1: Secțiunea**

Inserează înaintea primului `---` din `deploy/README.md`:

````markdown
## Site-ul de marketing (WordPress, `www.`)

Stack separat, `docker-compose.wp.yml`, pe același Traefik. Aplicația Django
stă pe `app.DOMENIU`, WordPress pe `www.DOMENIU`; se leagă doar prin
linkuri (`MARKETING_SITE_URL` în `.env`, CTA-urile din WP spre
`https://app.DOMENIU/accounts/signup/`).

DNS: două A records, `www` și `app`, ambele → `85.215.69.83`.

```bash
cd /opt/cleaning
# .env: WP_HOST, WP_DB_NAME, WP_DB_USER, WP_DB_PASSWORD, MARKETING_SITE_URL
docker compose -f docker-compose.wp.yml up -d
```

Apoi în browser, la `https://www.DOMENIU`: instalarea WP (limbă, admin),
`Design → Themes → Upload` cu `wilmer.zip` din arhiva ThemeForest, iar tema
cere la activare plugin-urile `wilmer-core`, `js_composer`, `revslider`
(sunt în `wilmer/includes/plugins/` din aceeași arhivă). Limita de upload e
ridicată la 64 MB prin `deploy/wp-uploads.ini`.

Paginile și textele: `docs/marketing/pages.md`. Zip-ul temei nu e în git —
licența e personală.

Backup-ul din `deploy/backup-db.sh` include WP automat când `wpdb` rulează.
````

- [ ] **Step 2: Commit**

```bash
git add deploy/README.md
git commit -m "README: pornirea site-ului WordPress lângă aplicație"
```

---

### Task 6: `docs/marketing/pages.md` — structura și textul paginilor

**Files:**
- Create: `docs/marketing/pages.md`

Copy în germană, ton B2B sobru. Fiecare pagină: titlu, secțiuni cu heading +
text, CTA-ul exact. Textul de mai jos este conținutul final al fișierului —
nu se scurtează, WPBakery-ul se completează din el.

- [ ] **Step 1: Scrie fișierul**

````markdown
# Paginile site-ului de marketing (www.)

Toate CTA-urile duc la `https://app.DOMENIU/accounts/signup/`; link-ul
„Anmelden" din header la `https://app.DOMENIU/accounts/login/`. Tema Wilmer
e de construcții: **toate** imaginile de demo se înlocuiesc cu fotografii de
curățenie profesională (clădiri de birouri, case de scări, echipamente).

Meniu header: Start · Leistungen · Für Betriebe · Für Reinigungskräfte ·
Für Auftraggeber · Blog · Kontakt · [Anmelden] · [Jetzt starten]

Footer: Impressum · Datenschutz · link „Stellenangebote" →
`https://app.DOMENIU/jobs/`.

---

## Start

**Hero**
H1: Gebäudereinigung, sauber organisiert.
Text: ProFM verbindet Reinigungsbetriebe, Reinigungskräfte und Auftraggeber
in Schleswig-Holstein und Hamburg — mit Einsatzplanung, Zeiterfassung und
rechtssicheren Verträgen an einem Ort.
CTA: Jetzt starten

**Drei Säulen** (3 coloane)
- Für Betriebe — Aufträge finden, Wochenpläne erstellen, Stunden im Rahmen
  der Verträge halten.
- Für Reinigungskräfte — Stellen in Ihrer Nähe, klare Schichten, Pontaj per
  Klick.
- Für Auftraggeber — Reinigungsbedarf ausschreiben, Angebote vergleichen,
  geprüfte Betriebe beauftragen.

**Wie es funktioniert** (3 pași)
1. Konto anlegen — Betrieb, Reinigungskraft oder Auftraggeber; ein Konto
   kann mehrere Rollen haben.
2. Bedarf oder Angebot einstellen — Stellenanzeige, Reinigungsanfrage oder
   Angebot.
3. Arbeiten — Vertrag, Wochenplan, Zeiterfassung, alles dokumentiert.

**Vertrauen** (bandă cu 3 puncte)
- Mindestlohn Gebäudereinigung wird bei jedem Vertrag geprüft.
- Zeiterfassung nach § 16 ArbZG, unveränderbar protokolliert.
- Keine automatische Zuweisung von Personen — Betriebe entscheiden selbst.

CTA final: Jetzt starten

---

## Leistungen

H1: Was ProFM leistet

**Marktplatz** — Auftraggeber schreiben Reinigungsbedarf aus, Betriebe geben
Angebote ab. Die Bewertung der Angebote folgt Regeln, die die Mitglieder
gemeinsam festlegen — kein Betrieb wird bevorzugt.

**Stellenanzeigen** — Betriebe veröffentlichen Stellen; die Anzeigen sind
öffentlich, ohne Anmeldung lesbar und bei Google for Jobs gelistet.

**Einsatzplanung** — Objekte, Zonen, Reinigungsintervalle. Der Wochenplan
berücksichtigt Vertragsstunden, Höchstarbeitszeit, Ruhezeiten und Sonntage.
Was nicht passt, bleibt sichtbar offen statt still überbucht.

**Zeiterfassung** — Check-in und Check-out pro Schicht, Korrekturen nur als
neuer Eintrag. Export als Reinigungsplan (XLSX) für den Auftraggeber.

**Verträge** — Aus dem gewonnenen Angebot entsteht der Vertragsentwurf mit
den Zahlen des Angebots. Prüfung gegen Branchenmindestlohn und
Minijob-Grenze vor der Unterschrift.

CTA: Jetzt starten

---

## Für Betriebe

H1: Mehr Aufträge, weniger Verwaltung
Intro: Sie führen einen Reinigungsbetrieb — allein oder mit Team. ProFM
bringt Ihnen Anfragen aus Ihrer Region und nimmt Ihnen die Planung ab.

**Was Sie bekommen**
- Offene Reinigungsanfragen in Ihrem Einzugsgebiet und Ihren Leistungen
- Angebote in Minuten, Vertragsentwurf automatisch aus dem Angebot
- Wochenplan pro Objekt, mit Stundenbudget je Mitarbeiter
- Zeiterfassung Ihrer Reinigungskräfte, exportierbar
- Ein öffentliches Profil, das Auftraggeber finden

**Was ProFM nicht tut**
Wir weisen Ihnen keine Arbeit zu und geben keine Anweisungen an Ihr
Personal. Sie bleiben Unternehmer; ProFM vermittelt.

CTA: Betrieb registrieren

---

## Für Reinigungskräfte

H1: Stellen in Ihrer Nähe, Schichten ohne Rätselraten
Intro: Ob Minijob oder Vollzeit — hier finden Sie Reinigungsbetriebe, die
Personal suchen, und sehen Ihre Einsätze klar.

**Was Sie bekommen**
- Stellenanzeigen nach Ort und Tätigkeit, ohne Anmeldung lesbar
- Bewerbung mit einem Klick, Profil einmal anlegen
- Ihre Schichten der Woche: Objekt, Zeit, Zonen
- Check-in / Check-out — Ihre Stunden sind dokumentiert
- Vertrag mit geprüftem Stundenlohn, mindestens Branchenmindestlohn

CTA: Profil anlegen

---

## Für Auftraggeber

H1: Reinigung ausschreiben, Angebote vergleichen
Intro: Hausverwaltung, Praxis, Büro, Pflegeeinrichtung — Sie beschreiben,
was gereinigt werden soll; geprüfte Betriebe aus der Region bieten an.

**So läuft es**
1. Anfrage stellen: Objekt, Leistungen, Intervall, Zeitraum.
2. Angebote erhalten und vergleichen — Preis, Verfügbarkeit, Bewertung.
3. Beauftragen. Vertrag und Reinigungsplan kommen aus dem System.

**Ihre Sicherheit**
- Kontaktdaten der Betriebe erst nach Beauftragung — kein Adresshandel
- Reinigungsplan als XLSX, Zeiterfassung als Nachweis
- Betriebe mit Verifizierung (Gewerbe, Versicherung)

CTA: Anfrage stellen

---

## Blog

Listă standard a temei (masonry sau standard). Categorii inițiale:
Tariflohn · Minijob · Arbeitszeit · Ausschreibung. Fără articole la
lansare — pagina rămâne în meniu doar după primul articol.

---

## Kontakt

H1: Kontakt
Text: Fragen zur Plattform, zur Mitgliedschaft oder zu einem konkreten
Auftrag? Schreiben Sie uns.
Formular: Name · E-Mail · Betreff · Nachricht · Checkbox Datenschutz
(obligatoriu, link la /datenschutz/). Trimite pe emailul din
`OPERATOR_EMAIL`. Fără telefon/adresă în text — sunt în Impressum.

---

## Impressum

Același conținut ca `https://app.DOMENIU/impressum/` (valorile `OPERATOR_*`
din `.env`). Se copiază manual după ce datele sunt setate; până atunci
pagina WP e privată (draft).

## Datenschutz

Același conținut ca `https://app.DOMENIU/datenschutz/`, plus secțiunile
specifice WP: cookie-uri WordPress, formular de contact (Contact Form 7),
Google Fonts dacă tema le încarcă de la Google (de preferat: local). Se
publică odată cu Impressum.
````

- [ ] **Step 2: Verifică**

Run: `grep -c "app.DOMENIU/accounts/signup/" docs/marketing/pages.md`
Expected: `1` (linia de sus; CTA-urile din pagini folosesc doar eticheta,
ținta e definită o singură dată).

- [ ] **Step 3: Commit**

```bash
git add docs/marketing/pages.md
git commit -m "Docs: structura și textul german al paginilor WordPress"
```

---

## Verificare finală

- `.venv/bin/python -m pytest -q` — 0 failed.
- `git status --short` — doar `prompts/`, `RECOMANDARI-AUDIT.md` (ale altei sesiuni) și eventual `templates/_icons.html` (fix necomis din sesiunea anterioară).
- Pe server, după cumpărarea domeniului: `curl -I https://www.DOMENIU` → 200/302 (WP), `curl -I https://app.DOMENIU/healthz/` → 200.
