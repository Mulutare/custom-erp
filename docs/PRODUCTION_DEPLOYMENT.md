# PassionTech ERP production deployment

> **GO-LIVE BLOCKED PENDING PROFESSIONAL ACCOUNTING VALIDATION.** Private
> infrastructure may be staged, but public operational use requires written
> approval of VAT and withholding mappings, tax grids and filing outputs,
> invoice/tax treatment, depreciation and fixed-asset classification, retained
> earnings/current-period income, and Cash Flow classification.

## Architecture

```text
Internet
  -> TCP 443 (80 only for redirect/certificate validation)
  -> cPanel/WHM-managed Apache TLS frontend
  -> 127.0.0.1:8069 Odoo HTTP
     127.0.0.1:8072 Odoo websocket/gevent
  -> private Compose network
  -> PostgreSQL 5432 (not published)

Persistent volumes: postgres_data + odoo_data (filestore/sessions)
External protected storage: timestamped DB + matching filestore backups
```

The image contains only tracked Community/OCA/PassionTech addons. Provenance is
in `OCA_DEPENDENCIES.md`; no Enterprise tree or ignored local `oca/` checkout is
used.

## Exact controlled sequence

1. Provision a root-access cPanel/WHM VPS/dedicated server. Patch the OS and WHM.
2. Confirm CPU/RAM/disk/web topology and install Docker Engine, Compose v2, Git,
   and Python 3 using the OS vendor-supported method.
3. Create a non-login or restricted deployment operator and `/srv/passiontech`;
   clone the approved repository there and checkout the approved full SHA:

   ```sh
   git clone <APPROVED_REPOSITORY_URL> /srv/passiontech/app
   git -C /srv/passiontech/app checkout --detach <APPROVED_FULL_COMMIT_SHA>
   ```

4. Create `/srv/passiontech/backups` mode 0700. Copy the environment example,
   replace placeholders offline, and chmod the resulting file 0600.
5. Set worker/memory parameters from actual capacity, then run preflight:

   ```sh
   cd /srv/passiontech/app
   deployment/scripts/preflight.sh deployment/env/.env.production
   ```

6. Build the pinned application image. Start PostgreSQL first:

   ```sh
   docker compose --env-file deployment/env/.env.production \
     -f deployment/docker-compose.prod.yml build --pull
   docker compose --env-file deployment/env/.env.production \
     -f deployment/docker-compose.prod.yml up -d db
   ```

7. Choose exactly one database path below. Do not combine them.

   **A — fresh production bootstrap (recommended):** start Odoo with an empty
   database created using the configured `POSTGRES_DB`, install the documented
   no-demo module set, and manually configure legal/company-specific records.
   This avoids development companies, transactions, sample budgets, and the
   questionable tax-account classifications in `office-db`.

   ```sh
   docker compose --env-file deployment/env/.env.production \
     -f deployment/docker-compose.prod.yml run --rm odoo \
     odoo -c /etc/odoo/odoo.conf --without-demo=all --stop-after-init \
     -i passiontech_branding,passiontech_core,passiontech_security,passiontech_financial_reports,l10n_et,purchase_stock,stock_account,stock_landed_costs,product_expiry,stock_picking_batch,stock_dropshipping,sale_margin,sale_loyalty,sale_product_matrix,purchase_product_matrix,purchase_requisition,account_debit_note,account_check_printing,crm,delivery,account_asset_management,account_financial_report,account_reconcile_oca,account_statement_base,account_statement_import_base,account_statement_import_file,account_statement_import_file_reconcile_oca,account_statement_import_sheet_file,account_statement_import_sheet_file_xlsx
   ```

   **B — migrate tested `office-db`:** create a final matching DB/filestore backup,
   transfer both securely, restore both, then upgrade only the reviewed modules.
   This preserves established configuration but also carries development/demo
   records and accounting mappings that must be reviewed before go-live.

8. Start Odoo and run health checks:

   ```sh
   docker compose --env-file deployment/env/.env.production \
     -f deployment/docker-compose.prod.yml up -d odoo
   deployment/scripts/healthcheck.sh deployment/env/.env.production
   ```

9. In WHM, add the Apache reverse-proxy include described in
   `CPANEL_WHM_DEPLOYMENT.md`; rebuild/restart Apache through supported WHM tools.
10. Point DNS only in the approved deployment window, obtain/verify AutoSSL, enforce
    HTTPS, and validate headers/websocket routing.
11. Allow public 443 (and 80 only as needed). Confirm 5432, 8069, and 8072 are not
    externally reachable.
12. Configure SMTP in Odoo using a dedicated account. Verify sender domain SPF,
    DKIM, DMARC, TLS, delivery, bounce handling, and password-reset email.
13. Smoke-test login, company isolation, Sales, Purchase, Inventory, accounting
    posting authorization, reports, scheduled actions, email, and uploads.
14. Run a production backup, restore it into an isolated test database, verify login
    and attachments, and retain evidence.
15. Obtain written Ethiopian accountant/tax approval and business-owner sign-off.
16. Only then schedule and authorize operational go-live.

## Bootstrap responsibility

Automatically reproduced: PassionTech roles/security, financial report templates,
demo suppression, and tracked addons. Database-preserved on migration: companies,
users, sequences, journals, warehouses, taxes, reconciliation models, and balances.
Manual for a fresh database: Passion Technology legal identity, Ethiopia/ETB chart,
PT warehouse/operations, journals/banks/sequences, taxes/fiscal positions, named
role assignments, email, reconciliation, and accountant-approved mappings. Never
use numeric database IDs in automation.

## No demo data

Always use `--without-demo=all`. Local manifests also intentionally disable demo
records in `account_reconcile_oca`, `account_statement_import_file`,
`account_budget_oca`, and `report_xlsx`; this prevents sample reconciliation data,
bank accounts, budgets, and report actions even if an operator misconfigures demo
loading. Production must not contain sample users, companies, transactions, or
security-group changes.

## Email and future integrations

Do not copy development SMTP assumptions. Store production SMTP credentials only
in the ignored secret file or Odoo's protected database configuration. Future APIs
must use HTTPS, dedicated least-privilege service users/keys, audited Sales and
Inventory permissions, and normal Odoo workflows. Never issue System Administrator
keys or mutate stock quants directly.

## Operations and monitoring

Keep Odoo at INFO; do not enable global DEBUG. Compose rotates JSON logs at five
20 MB files per service. Monitor HTTP, PostgreSQL readiness, disk, RAM, CPU,
container restarts, backup age/success, and certificate expiry. Review with:

```sh
docker compose --env-file deployment/env/.env.production \
  -f deployment/docker-compose.prod.yml logs --since 1h odoo \
  | grep -E 'ERROR|CRITICAL|Traceback'
```
