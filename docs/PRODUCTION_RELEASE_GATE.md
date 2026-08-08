# PassionTech ERP production release gate

This repository packages Odoo Community addons only. It contains no Odoo
Enterprise dependency. Install the Python packages in `requirements-app.txt`
before starting Odoo.

## Reproducible installation

Install this single bootstrap module from the tracked `addons/` directory:

```text
passiontech_erp
```

Odoo resolves the complete approved PassionTech, Community, and vendored OCA
dependency stack below. For a production database, disable demo data explicitly
(`--without-demo=True`) even though known vendored demo declarations are also
disabled.

The bootstrap installs this approved business application set:

```text
l10n_et, purchase_stock, stock_account, stock_landed_costs,
product_expiry, stock_picking_batch, stock_dropshipping,
sale_margin, sale_loyalty, sale_product_matrix, purchase_product_matrix,
purchase_requisition, account_debit_note, account_check_printing, crm,
delivery, account_asset_management, account_financial_report,
account_reconcile_oca, account_statement_base, account_statement_import_base,
account_statement_import_file, account_statement_import_file_reconcile_oca,
account_statement_import_sheet_file, account_statement_import_sheet_file_xlsx
```

This exact no-demo set was installed successfully in the release-gate fresh
database using only the tracked `addons/` mount and standard Odoo Community.

## Automatically reproducible

- PassionTech roles, hierarchy, menu restrictions, and server-side controls.
- P&L, Balance Sheet, and Cash Flow MIS templates and comparison periods.
- Report security and default posted-entry filtering.
- Password-reset/security defaults defined by `passiontech_security`.
- Vendored OCA code and its exact source revisions.

## Manual production configuration

- Create the legal company and choose ETB, Ethiopia, and the `l10n_et` chart.
- Validate company identity, fiscal year, invoice sequences, journals, bank
  accounts, taxes, tax grids, fiscal positions, and reconciliation models.
- Create warehouses, locations, operation types, routes, and reordering rules.
- Assign named users to PassionTech roles; never reuse test/demo users.
- Configure outgoing email, base URL, proxy/TLS, backup retention, monitoring,
  workers, memory/time limits, and scheduled-action ownership.
- Decide credit limits, sales approvals, and negative-stock policy before
  enabling any related restriction.

## Professional confirmation required

- The current `office-db` Ethiopian chart has a presentation-risk mapping:
  accounts named VAT/Withholding Payable are typed `asset_current`, while
  VAT/Withholding Receivable accounts are typed `liability_current`. Do not
  migrate that mapping into production until an Ethiopian accountant confirms
  and, where necessary, corrects the account types.
- An Ethiopian accountant must validate VAT, withholding, tax grids, invoice
  treatment, fiscal-year closing, statutory reports, and filing outputs.
- Finance must confirm every chart account's Odoo account type, especially
  retained earnings, current-year earnings, cash equivalents, depreciation,
  fixed/non-current assets, and financing balances.
- Cash Flow classifications are account-type based. The report reconciles
  opening cash plus net movement to closing cash, but non-cash fixed-asset
  movements such as depreciation require finance review of classification.

## Existing development database

`office-db` contains multiple demonstration/reference companies. It is not a
production database template. Before deployment, use a new no-demo database
or have authorized owners review and remove demo companies and the two sample
OCA budgets. Never delete them automatically because users may have reused
those records.

## Backup and restore

Every release backup must include both:

1. a PostgreSQL custom-format dump; and
2. `/var/lib/odoo/filestore/<database>`.

Test restoration under a different database name and matching filestore
directory. Never validate a restore by overwriting the live database.
