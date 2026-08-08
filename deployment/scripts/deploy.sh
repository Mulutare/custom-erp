#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE=${1:-"$ROOT/deployment/env/.env.production"}
COMPOSE="$ROOT/deployment/docker-compose.prod.yml"
"$ROOT/deployment/scripts/preflight.sh" "$ENV_FILE"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" build --pull
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" up -d db
docker compose --env-file "$ENV_FILE" -f "$COMPOSE" up -d odoo
"$ROOT/deployment/scripts/healthcheck.sh" "$ENV_FILE"
