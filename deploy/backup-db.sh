#!/bin/bash
# Backup zilnic al bazei. Cron pe gazdă:
#   0 3 * * * /opt/cleaning/deploy/backup-db.sh >> /var/log/cleaning-backup.log 2>&1
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/cleaning}"
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/cleaning}"
KEEP_DAYS="${KEEP_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

cd "$APP_DIR"
# shellcheck disable=SC1091
set -a; source .env; set +a

mkdir -p "$BACKUP_DIR"

docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_DIR/db_$TIMESTAMP.dump"

# Documentele de verificare nu sunt în baza de date. Un backup fără ele
# pierde exact partea pe care legea cere să o poți produce la control.
docker run --rm \
    -v cleaning_private_files:/data:ro \
    -v "$BACKUP_DIR":/backup \
    alpine tar czf "/backup/private_$TIMESTAMP.tar.gz" -C /data .

find "$BACKUP_DIR" -name 'db_*.dump' -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name 'private_*.tar.gz' -mtime +"$KEEP_DAYS" -delete

echo "Backup complet: db_$TIMESTAMP.dump + private_$TIMESTAMP.tar.gz"
