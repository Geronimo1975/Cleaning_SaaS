# Punere în producție

Există două variante de stack:

| Fișier | Când |
|---|---|
| `docker-compose.traefik.yml` | **Serverul 85.215.69.83** (`ssh macbook-air`), unde Traefik deține deja 80/443 și emite certificatele. Fără Nginx expus, fără certbot. |
| `docker-compose.prod.yml` | Un server gol, unde stack-ul aduce propriul Nginx + Let's Encrypt. |

## Varianta Traefik (serverul actual)

Serverul rulează deja Traefik v2.11 pe portul 80/443, cu resolver-ul
`letsencrypt` și rețeaua `gethub_gethub-network`. Aplicația se atașează la ele
prin etichete — exact ca `rotocon-web` și celelalte.

```bash
ssh macbook-air
mkdir -p /opt/cleaning && cd /opt/cleaning
# copiază codul (rsync din laptop sau git clone)

cp .env.example .env    # completează SECRET_KEY, APP_HOST, ALLOWED_HOSTS, DB_PASSWORD, SMTP
docker compose -f docker-compose.traefik.yml up -d --build
docker compose -f docker-compose.traefik.yml exec web python manage.py migrate
docker compose -f docker-compose.traefik.yml exec web python manage.py createsuperuser
```

`APP_HOST` trebuie să aibă deja un A record spre 85.215.69.83 înainte de
pornire — Traefik cere certificatul la prima cerere pe acea gazdă.

Copiere din laptop, fără git:

```bash
rsync -az --delete \
  --exclude .venv --exclude __pycache__ --exclude db.sqlite3 \
  --exclude media --exclude private --exclude staticfiles --exclude .env \
  ./ macbook-air:/opt/cleaning/
```

---

## Varianta cu Nginx propriu (server gol)

Stack: Django 5.2 + HTMX, Postgres 16, Nginx, Let's Encrypt. Fără Celery și fără
Redis — nimic din aplicație nu are nevoie de o coadă de task-uri; cele două
comenzi programate rulează într-un container `cron` simplu.

## 1. Server

Minim realist pentru început: 2 vCPU, 4 GB RAM, 40 GB disc. Debian 12 sau
Ubuntu 24.04. Instalează Docker Engine + plugin-ul `compose`.

```bash
sudo mkdir -p /opt/cleaning && sudo chown "$USER" /opt/cleaning
cd /opt/cleaning
# copiază codul aici (git clone sau rsync)
```

## 2. Configurare

```bash
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'   # SECRET_KEY
sed -i 's/DOMAIN/curatenie.example.de/g' deploy/nginx.conf
```

Completează în `.env`: `SECRET_KEY`, `ALLOWED_HOSTS`, `DB_PASSWORD`,
`DATABASE_URL` (aceeași parolă), datele SMTP.

## 3. Certificat TLS

Nginx nu pornește fără certificat, iar certbot are nevoie de Nginx. Se rupe
bucla cerând certificatul înainte, cu un server temporar:

```bash
docker compose -f docker-compose.prod.yml up -d db web
docker run --rm -p 80:80 \
  -v cleaning_certbot_conf:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d curatenie.example.de -m tu@example.de --agree-tos --no-eff-email
docker compose -f docker-compose.prod.yml up -d
```

Reînnoirea rulează singură în containerul `certbot`, la 12 ore.

## 4. Prima pornire

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Migrările de date aduc singure taxonomia germană (4 categorii, 24 de frunze),
cele 30 de localități din nordul Hamburgului, pragurile salariale datate, cele
patru șabloane de contract și politica de repartizare fondatoare.

## 5. Backup

```bash
sudo mkdir -p /opt/backups/cleaning
crontab -e
# 0 3 * * * /opt/cleaning/deploy/backup-db.sh >> /var/log/cleaning-backup.log 2>&1
```

Salvează **și** volumul `private_files`. Documentele de verificare nu sunt în
baza de date, iar la un control FKS trebuie să le poți produce.

Restaurare:

```bash
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U "$DB_USER" -d "$DB_NAME" --clean < /opt/backups/cleaning/db_TIMESTAMP.dump
```

## 6. Actualizare

```bash
cd /opt/cleaning && git pull
docker compose -f docker-compose.prod.yml build web
docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml up -d
```

Fă backup înainte de migrare, nu după.

## Ce trebuie știut înainte de primul utilizator real

- **Datele personale.** Documentele de verificare stau în volumul `private_files`,
  care NU e montat în containerul Nginx și se servesc doar prin
  `/cont/documente/<pk>/`, cu verificare de proprietar. Nu muta nimic din ele în
  `media/`.
- **DSGVO.** Politica de confidențialitate, Termenii și Impressum-ul (§5 TMG)
  trebuie publicate înainte de primul cont real. Nu există încă în aplicație.
- **Valorile de tarif** semănate în migrări sunt marcate `DE CONFIRMAT`. Verifică-le
  cu un Steuerberater înainte de primul contract semnat.
- **Șabloanele de contract** sunt schelete corecte structural, nu documente gata
  de semnat. Un Fachanwalt für Arbeitsrecht trebuie să le treacă o dată.
