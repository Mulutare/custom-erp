#!/usr/bin/env sh
set -eu

test "$#" -eq 3 || { echo "usage: restore.sh ENV BACKUP_DIR TARGET_DB" >&2; exit 2; }
ENV_FILE=$1
SOURCE=$2
TARGET_DB=$3
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
COMPOSE="$ROOT/deployment/docker-compose.prod.yml"
DB_USER=$(sed -n 's/^POSTGRES_USER=//p' "$ENV_FILE")
SOURCE_DB=$(sed -n 's/^database=//p' "$SOURCE/manifest.txt")

test -f "$SOURCE/COMPLETE" && test -s "$SOURCE/database.dump" && test -s "$SOURCE/filestore.tar.gz" && test -n "$SOURCE_DB"
case "$SOURCE_DB" in *[!A-Za-z0-9_-]*) echo "invalid source database name in manifest" >&2; exit 2;; esac
case "$TARGET_DB" in *[!A-Za-z0-9_]*) echo "invalid target database name" >&2; exit 2;; esac
printf 'Type RESTORE %s to continue: ' "$TARGET_DB"
read -r CONFIRM
test "$CONFIRM" = "RESTORE $TARGET_DB" || { echo "Cancelled"; exit 1; }

test -z "$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE" exec -T db psql -U "$DB_USER" -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='$TARGET_DB'")" \
  || { echo "target database already exists; refusing overwrite" >&2; exit 1; }
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" stop odoo
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" exec -T db createdb -U "$DB_USER" "$TARGET_DB"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" exec -T db pg_restore -U "$DB_USER" -d "$TARGET_DB" --no-owner < "$SOURCE/database.dump"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" run --rm -T --user root \
  -e RESTORE_SOURCE_DB="$SOURCE_DB" -e RESTORE_TARGET_DB="$TARGET_DB" odoo sh -c '
    set -eu
    stage="/var/lib/odoo/restore-staging-$RESTORE_TARGET_DB"
    target="/var/lib/odoo/filestore/$RESTORE_TARGET_DB"
    test ! -e "$stage" && test ! -e "$target"
    mkdir -p "$stage"
    tar -C "$stage" -xzf -
    test -d "$stage/$RESTORE_SOURCE_DB"
    mv "$stage/$RESTORE_SOURCE_DB" "$target"
    rmdir "$stage"
    chown -R odoo:odoo "$target"
  ' < "$SOURCE/filestore.tar.gz"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" up -d odoo
echo "Restore completed into $TARGET_DB; run healthcheck and login verification."
