{
    "name": "PassionTech Financial Reports",
    "summary": "Production financial statement templates for PassionTech ERP",
    "version": "19.0.1.0.0",
    "category": "Accounting/Accounting",
    "author": "Passion Technology",
    "website": "https://github.com/Mulutare/custom-erp",
    "license": "AGPL-3",
    "depends": [
        "account_journal_lock_date",
        "mis_builder",
        "partner_statement",
        "passiontech_security",
    ],
    "data": [
        "security/groups.xml",
        "data/report_styles.xml",
        "data/profit_and_loss.xml",
        "data/balance_sheet.xml",
    ],
    "installable": True,
    "application": False,
}
