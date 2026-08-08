#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE=${1:-"$ROOT/deployment/env/.env.production"}
COMPOSE="$ROOT/deployment/docker-compose.prod.yml"
BACKUP_DIR=$(sed -n 's/^BACKUP_DIR=//p' "$ENV_FILE")

docker compose --env-file "$ENV_FILE" -f "$COMPOSE" ps
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" exec -T db \
  pg_isready -U "$(sed -n 's/^POSTGRES_USER=//p' "$ENV_FILE")" \
  -d "$(sed -n 's/^POSTGRES_DB=//p' "$ENV_FILE")"
python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$(sed -n 's/^ODOO_HTTP_PORT=//p' "$ENV_FILE")/web/login', timeout=10)"
df -h "$ROOT" "$BACKUP_DIR"
find "$BACKUP_DIR" -mindepth 2 -maxdepth 2 -type f -name COMPLETE -mtime -2 -print | grep -q . \
  || echo "WARNING: no backup artifact newer than 48 hours"
echo "PASS: service health checks completed"
