# PassionTech production-template artifacts

The production baseline is one coordinated, inseparable release set:

1. the approved Git SHA;
2. the sanitized PostgreSQL custom-format backup; and
3. the matching Odoo filestore backup.

The database and filestore archives are operational artifacts. They are ignored
by Git and must be transferred through protected storage. Never commit them.

## Local validated template

- Source database retained for validation: `passion_db`
- Sanitized template clone: `passiontech_production_template`
- Ignored local backup directory: `backups/passiontech-production-template/final-20260808/`
- Database archive: `passiontech_production_template.dump`
- Filestore archive: `passiontech_production_template-filestore.tar.gz`

## Restore and upgrade order

1. Check out the exact approved Git SHA and build/install its pinned dependencies.
2. Stop Odoo application workers; keep PostgreSQL available privately.
3. Create an empty target database owned by the configured Odoo database user.
4. Restore the custom-format PostgreSQL archive with `pg_restore`, without
   importing source ownership or privileges.
5. Extract the matching filestore directory under
   `/var/lib/odoo/filestore/<target_database>` with Odoo ownership.
6. Run Odoo once with `--stop-after-init` and upgrade `passiontech_erp`.
7. Start Odoo, confirm HTTP health, log in, and verify Sales, Purchase,
   Inventory, Invoicing/Finance, reports, role access, imports/exports, and
   branding.
8. Configure production-only SMTP, URL/proxy, backup retention, monitoring,
   legal identifiers, bank accounts, and accountant-approved statutory data.

Do not restore a database archive without its matching filestore, do not mix
artifacts from different Git SHAs, and never overwrite `passion_db` during a
restore test.

## Source-controlled configuration

- `passiontech_erp` single-module Phase-1 dependency bootstrap
- PassionTech roles, hierarchy, ACLs, record rules, menus, and server checks
- PassionTech branding and company defaults (name, Ethiopia, ETB, timezone)
- Approved financial-report templates and security
- Vendored/pinned OCA modules and no-demo safeguards
- Docker and native-Linux deployment runbooks

## Database-only configuration

- Real users and their role assignments
- Company address, legal/tax registration, bank accounts, and contact details
- Chart/journals/sequences after professional accounting approval
- Taxes, tax grids, fiscal positions, reconciliation models, opening balances,
  and opening stock
- SMTP credentials, base URL, scheduled-action ownership, and production secrets
- Real customers, vendors, products, transactions, and attachments

The template intentionally contains no Sales orders, purchase orders, stock
pickings/moves, customer/vendor invoices, payments, or budgets.
