#!/usr/bin/env sh
set -eu
umask 077

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE=${1:-"$ROOT/deployment/env/.env.production"}
COMPOSE="$ROOT/deployment/docker-compose.prod.yml"
DB=$(sed -n 's/^POSTGRES_DB=//p' "$ENV_FILE")
DB_USER=$(sed -n 's/^POSTGRES_USER=//p' "$ENV_FILE")
BACKUP_DIR=$(sed -n 's/^BACKUP_DIR=//p' "$ENV_FILE")
RETENTION=$(sed -n 's/^BACKUP_RETENTION_DAYS=//p' "$ENV_FILE")
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
DEST="$BACKUP_DIR/$DB-$STAMP"
mkdir -p "$DEST"
ODOO_PAUSED=0

cleanup() {
  if test "$ODOO_PAUSED" -eq 1; then
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE" unpause odoo >/dev/null
  fi
  test -f "$DEST/COMPLETE" || rm -f "$DEST/database.dump" "$DEST/filestore.tar.gz"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

docker compose --env-file "$ENV_FILE" -f "$COMPOSE" pause odoo >/dev/null
ODOO_PAUSED=1
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" exec -T db \
  pg_dump -U "$DB_USER" -d "$DB" -Fc > "$DEST/database.dump"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" run --rm -T odoo \
  tar -C /var/lib/odoo/filestore -czf - "$DB" > "$DEST/filestore.tar.gz"
test -s "$DEST/database.dump"
test -s "$DEST/filestore.tar.gz"
printf '%s\n' "revision=$(git -C "$ROOT" rev-parse HEAD)" "database=$DB" "created_utc=$STAMP" > "$DEST/manifest.txt"
touch "$DEST/COMPLETE"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" unpause odoo >/dev/null
ODOO_PAUSED=0
echo "Verified complete backup: $DEST"

if test "${RETENTION:-0}" -gt 0 2>/dev/null; then
  find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -name "$DB-*" \
    -mtime "+$RETENTION" -exec test -f '{}/COMPLETE' \; -print
  echo "Retention candidates printed only; deletion requires operator review."
fi
