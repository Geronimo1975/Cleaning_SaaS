# Site de marketing pe WordPress, aplicația pe Django

Data: 2026-09-12. Decizie luată în sesiune, după evaluarea temei Wilmer.

## Decizia

Două site-uri pe același VPS (`85.215.69.83`, Traefik pe 80/443), legate
**doar prin linkuri**:

| Gazdă | Stack | Conținut |
|---|---|---|
| `www.DOMENIU` | WordPress + tema Wilmer (WPBakery) | Homepage, Leistungen, landing per rol, Blog, Kontakt, Impressum, Datenschutz |
| `app.DOMENIU` | Django (repo-ul acesta) | Signup/login, dashboard-uri, `/jobs/`, `/reinigungskraft/<oraș>/`, profiluri, sitemap, Impressum/Datenschutz/AGB proprii |

`DOMENIU` e placeholder până la cumpărare. Ambele gazde sunt A records spre
`85.215.69.83`; Traefik emite certificatele.

Fără SSO, fără API între ele, fără cookie partajat, fără header/footer
livrat de WP către Django. Un cont există doar în Django.

## De ce nu altfel

- **Tema Wilmer nu poate deveni frontendul Django.** Nu conține HTML static;
  toate paginile sunt shortcode-uri PHP (`wilmer-core`, `js_composer`,
  `revslider`). CSS-ul de 1 MB e legat de clasele `mkdf-*` generate de ele.
- **Dashboard-urile rămân în Django.** Sunt asamblate din `apps/dashboard/panels.py`
  pe capabilități și conțin contracte, pontaj, planificare — logică fără
  echivalent în WP.
- **Un singur domeniu cu rutare pe path** a fost respins: cookie-uri partajate
  între WP și Django, iar `ReservedSlug` (namespace global de URL-uri) s-ar
  bate cu slug-urile WP.
- **WP ca „shell" HTML inclus de Django** a fost respins: Django ar depinde de
  WP la runtime.

## Componente

### 1. `docker-compose.wp.yml` (nou, în rădăcina repo-ului)

- `wordpress:6-php8.3-apache` + `mariadb:11`, ambele `restart: unless-stopped`.
- Volume: `wp_data` (`/var/www/html`), `wp_db`.
- Rețele: `internal` proprie + `gethub_gethub-network` (external), ca în
  `docker-compose.traefik.yml`.
- Etichete Traefik identice ca tipar cu `proxy` din stack-ul Django, cu
  prefixul `wp-` pentru routere/middleware și `Host(\`${WP_HOST}\`)`.
- Variabile în `.env`: `WP_HOST`, `WP_DB_NAME`, `WP_DB_USER`, `WP_DB_PASSWORD`.
- `upload_max_filesize`/`post_max_size` ridicate la 64M printr-un
  `deploy/wp-uploads.ini` montat în container — `revslider.zip` are 10,7 MB.
- Stack separat de cel Django: se pornește/oprește/actualizează independent.

### 2. Backup

`deploy/backup-db.sh` primește o a doua ramură: `mariadb-dump` din containerul
WP, în același director de backup, cu același prefix de dată. Volumul
`wp_data` (upload-uri + temă) intră în același `tar`.

### 3. Django

- `MARKETING_SITE_URL` în `config/settings.py`, citit din env, gol implicit.
  Expus în template-uri printr-un al doilea context processor de o linie,
  `marketing`, în `apps/dashboard/context_processors.py` — `navigation()`
  iese devreme fără cont activ, iar link-ul e necesar și pe paginile publice.
- `templates/base.html` și `templates/app.html`: logo-ul duce la
  `MARKETING_SITE_URL` dacă e setat, altfel la `/jobs/` (nu există rută `/`).
- Paginile legale rămân în Django (`apps/legal`) — `app.DOMENIU` e site
  propriu și are nevoie de Impressum-ul lui (§5 TMG). WP are copiile lui.
  Nu se dublează textul în două repo-uri: WP-ul e sursa editabilă, Django
  ține textul din `templates/legal/` cum e acum.
- `.env.example`: `ALLOWED_HOSTS=app.DOMENIU`, `APP_HOST=app.DOMENIU`,
  `MARKETING_SITE_URL=https://www.DOMENIU`, plus variabilele `WP_*`.
- `deploy/README.md`: secțiune nouă „Site de marketing (WordPress)".

### 4. WordPress (operat manual, nu în git)

- Tema Wilmer + `wilmer-core`, `js_composer`, `revslider` se instalează din
  admin. Zip-ul ThemeForest **nu intră în git** — licența e personală;
  `themeforest-*.zip` intră în `.gitignore`.
- Pagini (germană): Start, Leistungen, Für Betriebe, Für Reinigungskräfte,
  Für Auftraggeber, Blog, Kontakt, Impressum, Datenschutz.
- Toate CTA-urile → `https://app.DOMENIU/accounts/signup/`. Link de login în
  header → `https://app.DOMENIU/accounts/login/`.
- Formularul de contact trimite email (plugin-ul temei / Contact Form 7);
  nu scrie în Django.
- Livrabil din repo: `docs/marketing/pages.md` — structura și textul german
  al fiecărei pagini, ca să fie construite în WPBakery. Imaginile de demo
  (construcții) se înlocuiesc integral.

## Ce nu face acest spec

- Nu stilizează paginile Django publice și allauth — rămâne un task
  separat (`base.html`).
- Nu introduce SSO, API, webhook-uri sau sincronizare de conținut.
- Nu mută `apps/legal` în WP.

## Testare

- `docker compose -f docker-compose.wp.yml config` validează fișierul.
- Test Django: `MARKETING_SITE_URL` setat ⇒ logo-ul din `base.html` duce
  acolo; nesetat ⇒ duce la `/jobs/`. Un singur test, în `tests/test_legal.py`
  (deja acoperă paginile publice).
- Manual pe server: `curl -I https://www.DOMENIU` → 200 de la WP;
  `curl -I https://app.DOMENIU/healthz/` → 200 de la Django.
