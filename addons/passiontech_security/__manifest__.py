{
    "name": "PassionTech Security",
    "version": "19.0.1.26.0",
    "summary": "Passion Technology company roles and access control",
    "category": "PassionTech",
    "author": "Passion Technology",
    "license": "LGPL-3",
    "depends": [
        "passiontech_core",
        "auth_signup",
        "hr_expense",
        "account_budget_oca",
        "account_financial_report",
        "purchase_stock",
        "stock_landed_costs",
        "web"
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/finance_menu_views.xml",
        "data/default_user_policy.xml",
        "data/menu_restrictions.xml",
        "data/security_settings.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
