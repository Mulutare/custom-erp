#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE=${1:-"$ROOT/deployment/env/.env.production"}
COMPOSE="$ROOT/deployment/docker-compose.prod.yml"

fail() { echo "FAIL: $*" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || fail "Docker is required"
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"
test -r "$ENV_FILE" || fail "missing readable $ENV_FILE"
test -d "$ROOT/addons" || fail "missing tracked addons directory"
test -s "$ROOT/requirements-app.txt" || fail "missing requirements-app.txt"
test -s "$COMPOSE" || fail "missing production Compose file"

python3 "$ROOT/deployment/scripts/render_config.py" "$ENV_FILE" \
  "$ROOT/deployment/config/odoo.conf.example" \
  "$ROOT/deployment/runtime/odoo.conf"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" config --quiet

EXPECTED=$(sed -n 's/^RELEASE_REVISION=//p' "$ENV_FILE")
ACTUAL=$(git -C "$ROOT" rev-parse HEAD)
test "$EXPECTED" = "$ACTUAL" || fail "release revision differs: expected $EXPECTED, got $ACTUAL"

BACKUP_DIR=$(sed -n 's/^BACKUP_DIR=//p' "$ENV_FILE")
MIN_FREE_GB=$(sed -n 's/^MIN_FREE_DISK_GB=//p' "$ENV_FILE")
test -n "$BACKUP_DIR" || fail "BACKUP_DIR is required"
test -d "$BACKUP_DIR" || fail "backup directory does not exist: $BACKUP_DIR"
test -w "$BACKUP_DIR" || fail "backup directory is not writable"
FREE_KB=$(df -Pk "$BACKUP_DIR" | awk 'NR==2 {print $4}')
test "$FREE_KB" -ge "$((MIN_FREE_GB * 1024 * 1024))" \
  || fail "backup filesystem has less than $MIN_FREE_GB GiB free"

echo "CPU cores: $(getconf _NPROCESSORS_ONLN 2>/dev/null || echo unknown)"
echo "Memory: $(awk '/MemTotal/ {print $2 " kB"}' /proc/meminfo 2>/dev/null || echo unknown)"
df -h "$ROOT" "$BACKUP_DIR"
echo "Listening ports 80/443/8069/8072 (review conflicts):"
ss -ltn 2>/dev/null | grep -E ':(80|443|8069|8072)[[:space:]]' || true
echo "PASS: deployment preflight is read-only except for the ignored rendered config"
