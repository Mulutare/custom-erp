# PassionTech Financial Reports

Production-ready MIS Builder templates for Profit & Loss and Balance Sheet.

The templates use Odoo account types instead of account IDs or account-code
prefixes. They therefore remain multi-company safe and work with the active
company's chart of accounts. Report instances default to posted entries and
provide current-year/prior-year comparison columns. MIS Builder supplies
drill-down, PDF, and XLSX output.

OCA Partner Statement supplies activity, detailed activity, and outstanding
statements in HTML/PDF/XLSX. The PassionTech Finance Officer role receives
only the two statement-use groups; its existing invoice-level ACL supplies
wizard access without granting Accounting Manager privileges.

The Cash Flow statement uses a reconciled indirect method. Net profit is
adjusted for movements in non-cash operating assets and liabilities, investing
assets, and financing balances. A separate cash-account movement line and a
zero-required reconciliation line make classification or chart gaps visible
instead of silently presenting an incorrect cash total. The formulas use Odoo
account types rather than database IDs or account-code prefixes, preserving
multi-company and Ethiopian chart compatibility.
