#!/usr/bin/env python3
"""Render the Odoo configuration without executing the environment file."""

from pathlib import Path
import os
import re
import sys


REQUIRED = {
    "POSTGRES_DB",
    "POSTGRES_DB_REGEX",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "ODOO_ADMIN_PASSWD",
    "ODOO_WORKERS",
    "ODOO_MAX_CRON_THREADS",
    "ODOO_LIMIT_MEMORY_SOFT",
    "ODOO_LIMIT_MEMORY_HARD",
    "ODOO_LIMIT_TIME_CPU",
    "ODOO_LIMIT_TIME_REAL",
}
PREFLIGHT_REQUIRED = REQUIRED | {
    "BACKUP_DIR",
    "BACKUP_RETENTION_DAYS",
    "DOMAIN",
    "MIN_FREE_DISK_GB",
    "ODOO_GEVENT_PORT",
    "ODOO_HTTP_PORT",
    "RELEASE_REVISION",
}


def read_env(path):
    values = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"{path}:{number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError(f"{path}:{number}: invalid variable name")
        values[key] = value.strip()
    return values


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: render_config.py ENV TEMPLATE OUTPUT")
    env_path, template_path, output_path = map(Path, sys.argv[1:])
    values = read_env(env_path)
    missing = sorted(PREFLIGHT_REQUIRED - values.keys())
    placeholders = sorted(
        key for key in PREFLIGHT_REQUIRED
        if key in values and "REPLACE_WITH" in values[key]
    )
    if missing or placeholders:
        raise SystemExit(f"missing={missing}; unresolved_placeholders={placeholders}")
    for key in (
        "BACKUP_RETENTION_DAYS",
        "MIN_FREE_DISK_GB",
        "ODOO_WORKERS",
        "ODOO_MAX_CRON_THREADS",
        "ODOO_LIMIT_MEMORY_SOFT",
        "ODOO_LIMIT_MEMORY_HARD",
        "ODOO_LIMIT_TIME_CPU",
        "ODOO_LIMIT_TIME_REAL",
        "ODOO_HTTP_PORT",
        "ODOO_GEVENT_PORT",
    ):
        if not values[key].isdigit():
            raise SystemExit(f"{key} must be a non-negative integer")
    rendered = template_path.read_text(encoding="utf-8")
    for key in REQUIRED:
        value = values[key]
        if any(char in value for char in "\r\n"):
            raise SystemExit(f"unsafe newline in {key}")
        rendered = rendered.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"{{([A-Z0-9_]+)}}", rendered)))
    if unresolved:
        raise SystemExit(f"unresolved template variables: {unresolved}")
    output_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    os.chmod(output_path, 0o600)
    print(f"Rendered {output_path} with mode 0600")


if __name__ == "__main__":
    main()
