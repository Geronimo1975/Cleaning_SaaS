#!/bin/bash
# Backup zilnic al bazei. Cron pe gazdă:
#   0 3 * * * /opt/cleaning/deploy/backup-db.sh >> /var/log/cleaning-backup.log 2>&1
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/cleaning}"
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/cleaning}"
KEEP_DAYS="${KEEP_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

cd "$APP_DIR"

# NU `source .env`: valorile pot conține spații (ex. OPERATOR_NAME=George
# Sebastian Cucuiet), iar shell-ul le-ar interpreta ca argumente sau comenzi.
# Docker Compose citește același fișier fără shell, deci nu are problema asta.
env_value() {
    grep -E "^$1=" .env | head -1 | cut -d= -f2-
}
DB_USER=$(env_value DB_USER)
DB_NAME=$(env_value DB_NAME)
: "${DB_USER:?DB_USER lipsește din .env}"
: "${DB_NAME:?DB_NAME lipsește din .env}"

mkdir -p "$BACKUP_DIR"

docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_DIR/db_$TIMESTAMP.dump"

# Documentele de verificare nu sunt în baza de date. Un backup fără ele
# pierde exact partea pe care legea cere să o poți produce la control.
docker run --rm \
    -v cleaning_private_files:/data:ro \
    -v "$BACKUP_DIR":/backup \
    alpine tar czf "/backup/private_$TIMESTAMP.tar.gz" -C /data .

# WordPress — doar dacă stack-ul rulează pe această mașină. Site-ul de
# marketing nu are date legale, dar are conținut pe care nimeni nu-l rescrie
# de plăcere.
if docker compose -f docker-compose.wp.yml ps --status running wpdb 2>/dev/null | grep -q wpdb; then
    WP_DB_USER=$(env_value WP_DB_USER)
    WP_DB_PASSWORD=$(env_value WP_DB_PASSWORD)
    WP_DB_NAME=$(env_value WP_DB_NAME)
    # Parola prin variabilă de mediu, nu în argv — altfel apare în `ps`.
    docker compose -f docker-compose.wp.yml exec -T -e MYSQL_PWD="$WP_DB_PASSWORD" wpdb \
        mariadb-dump -u "$WP_DB_USER" "$WP_DB_NAME" \
        | gzip > "$BACKUP_DIR/wp_db_$TIMESTAMP.sql.gz"
    docker run --rm \
        -v cleaning-wp_wp_data:/data:ro \
        -v "$BACKUP_DIR":/backup \
        alpine tar czf "/backup/wp_files_$TIMESTAMP.tar.gz" -C /data .
fi

find "$BACKUP_DIR" -name 'db_*.dump' -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name 'private_*.tar.gz' -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name 'wp_*' -mtime +"$KEEP_DAYS" -delete

echo "Backup complet: db_$TIMESTAMP.dump + private_$TIMESTAMP.tar.gz"
