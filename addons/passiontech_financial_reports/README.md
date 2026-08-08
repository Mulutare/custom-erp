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

The Cash Flow statement uses the explicit Operating Activities, Investing &
Extraordinary Activities, and Financing Activities tags supplied by the
Ethiopian chart of accounts. Accounts must retain one of these classifications
to appear in the corresponding section. The report deliberately avoids
account-code and account-type guesses, which keeps the classification visible
and maintainable by Finance.
