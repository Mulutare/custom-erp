# PassionTech ERP deployment manuals

Choose exactly one application runtime model. Both options retain the same
release gates, reverse-proxy controls, database/filestore integrity rules, and
accounting approval requirement.

| Option | Manual | Runtime |
|---|---|---|
| Docker Compose | [`PRODUCTION_DEPLOYMENT.md`](PRODUCTION_DEPLOYMENT.md) | Pinned Odoo image, PostgreSQL and Odoo in private Compose services |
| Native Linux | [`NATIVE_LINUX_DEPLOYMENT.md`](NATIVE_LINUX_DEPLOYMENT.md) | Pinned Odoo source in a Python venv, systemd, local PostgreSQL |

Shared supporting manuals:

- [`PRODUCTION_PRECHECK.md`](PRODUCTION_PRECHECK.md)
- [`PRODUCTION_RELEASE_GATE.md`](PRODUCTION_RELEASE_GATE.md)
- [`CPANEL_WHM_DEPLOYMENT.md`](CPANEL_WHM_DEPLOYMENT.md)
- [`BACKUP_RESTORE.md`](BACKUP_RESTORE.md) (Docker automation; native operators
  must apply the matching native backup requirements)
- [`UPDATE_ROLLBACK.md`](UPDATE_ROLLBACK.md) (Docker automation; native update
  and rollback are covered in the native manual)

Do not run both application stacks against the production database concurrently.
Do not deploy, change DNS, or expose the service until the selected manual's
private validation and the production release gate are complete.
