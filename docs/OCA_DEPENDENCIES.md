# Vendored OCA dependencies

The addons below are copied into `addons/` so production does not depend on
the ignored `oca/` working directories. Sources are pinned to the tested OCA
19.0 commits shown here.

| Upstream repository | Commit | Vendored addons | License |
|---|---|---|---|
| OCA/account-budgeting | `d811072d8e57f61f887e70e321fb8d2c640c6689` | `account_budget_oca` | LGPL-3 |
| OCA/account-financial-reporting | `6d61ff77504e3929791feeb33c57c1f0dbbcbc97` | `account_financial_report`, `partner_statement` | AGPL-3 |
| OCA/account-financial-tools | `b5077a22762cf6d2606eca53067be7ebdf0b7a49` | `account_asset_management`, `account_journal_lock_date` | AGPL-3 |
| OCA/account-reconcile | `a9bbab67e42f3b762e9c34b30b6c1a77f9c373fb` | `account_reconcile_oca` | AGPL-3 |
| OCA/bank-statement-import | `f91a33c4b68a564be0c9ac06e54568b808e31725` | `account_statement_base`, `account_statement_import_base`, `account_statement_import_file`, `account_statement_import_file_reconcile_oca`, `account_statement_import_sheet_file`, `account_statement_import_sheet_file_xlsx` | AGPL-3 or LGPL-3 per manifest |
| OCA/mis-builder | `58a237a5dc85c06a911b87ea4cfca8175ad4a78a` | `mis_builder` | AGPL-3 |
| OCA/reporting-engine | `8fdd67600c032f4b208213ef2200fabc4010314e` | `report_xlsx`, `report_xlsx_helper` | AGPL-3 |
| OCA/server-ux | `1372e6489daa3a639d7542f3dcd60af640fb294b` | `date_range` | LGPL-3 |

Upstream URLs follow `https://github.com/OCA/<repository>.git` and every
source checkout used branch `19.0`.

## Intentional local differences

Only demo declarations differ from the pinned upstream source:

- `account_reconcile_oca`: reconciliation demo records are disabled.
- `account_statement_import_file`: demo partner bank accounts are disabled.
- `account_budget_oca`: sample optimistic/pessimistic budgets are disabled.
- `report_xlsx`: the sample partner XLSX report action is disabled.

These changes prevent production installations or upgrades from creating
sample business/configuration records when the database has demo loading
enabled. Do not overwrite these manifests during an upstream refresh.
