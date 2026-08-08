#!/usr/bin/env sh
set -eu
test "$#" -ge 2 || { echo "usage: update.sh ENV APPROVED_REVISION [modules]" >&2; exit 2; }
ENV_FILE=$1
REVISION=$2
MODULES=${3:-}
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
COMPOSE="$ROOT/deployment/docker-compose.prod.yml"
ENV_REVISION=$(sed -n 's/^RELEASE_REVISION=//p' "$ENV_FILE")

test -z "$(git -C "$ROOT" status --porcelain)" || { echo "working tree is not clean" >&2; exit 1; }
test "$ENV_REVISION" = "$REVISION" || { echo "environment RELEASE_REVISION does not match approved revision" >&2; exit 1; }
git -C "$ROOT" cat-file -e "$REVISION^{commit}"
"$ROOT/deployment/scripts/backup.sh" "$ENV_FILE"
printf 'Type UPDATE %s to check out and build the approved revision: ' "$REVISION"
read -r CONFIRM
test "$CONFIRM" = "UPDATE $REVISION" || exit 1
git -C "$ROOT" checkout --detach "$REVISION"
test "$(git -C "$ROOT" rev-parse HEAD)" = "$REVISION"
python3 "$ROOT/deployment/scripts/render_config.py" "$ENV_FILE" "$ROOT/deployment/config/odoo.conf.example" "$ROOT/deployment/runtime/odoo.conf"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" build --pull
if test -n "$MODULES"; then
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE" run --rm odoo \
    odoo -c /etc/odoo/odoo.conf -d "$(sed -n 's/^POSTGRES_DB=//p' "$ENV_FILE")" -u "$MODULES" --stop-after-init
fi
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" up -d
"$ROOT/deployment/scripts/healthcheck.sh" "$ENV_FILE"
