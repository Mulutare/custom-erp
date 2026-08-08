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

Cash Flow is intentionally not defined yet. Reliable operating, investing,
and financing sections require explicit account tags or groups in the
Ethiopian chart. A generic account-type-only template could silently
misclassify movements, so this remains a documented configuration gap.
