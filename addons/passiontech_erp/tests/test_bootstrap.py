from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPassionTechBootstrap(TransactionCase):
    def test_required_modules_are_installed(self):
        required = {
            "passiontech_branding",
            "passiontech_core",
            "passiontech_security",
            "passiontech_financial_reports",
            "sale_management",
            "stock",
            "purchase_stock",
            "account",
            "account_budget_oca",
            "account_financial_report",
            "account_reconcile_oca",
            "account_statement_import_file",
            "account_statement_import_file_reconcile_oca",
            "account_statement_import_sheet_file_xlsx",
            "mis_builder",
            "partner_statement",
            "report_xlsx",
        }
        modules = self.env["ir.module.module"].search([("name", "in", list(required))])
        self.assertEqual(set(modules.mapped("name")), required)
        self.assertEqual(set(modules.mapped("state")), {"installed"})

    def test_all_business_roles_exist(self):
        role_xmlids = (
            "passiontech_security.group_sales_officer",
            "passiontech_security.group_sales_manager",
            "passiontech_security.group_inventory_officer",
            "passiontech_security.group_inventory_manager",
            "passiontech_security.group_finance_officer",
            "passiontech_security.group_finance_manager",
            "passiontech_security.group_company_owner",
            "passiontech_security.group_access_administrator",
            "passiontech_security.group_system_administrator",
        )
        for xmlid in role_xmlids:
            self.assertTrue(self.env.ref(xmlid).exists(), xmlid)

    def test_reproducible_company_identity(self):
        company = self.env.ref("base.main_company")
        self.assertEqual(company.name, "Passion Technology")
        self.assertEqual(company.country_id.code, "ET")
        self.assertEqual(company.currency_id.name, "ETB")
        self.assertEqual(company.partner_id.tz, "Africa/Addis_Ababa")

    def test_fresh_install_has_no_business_transactions(self):
        transaction_models = (
            "sale.order",
            "purchase.order",
            "stock.picking",
            "account.payment",
            "crossovered.budget",
        )
        for model_name in transaction_models:
            self.assertFalse(self.env[model_name].search([], limit=1), model_name)
        self.assertFalse(
            self.env["account.move"].search(
                [("move_type", "!=", "entry")], limit=1
            ),
            "account.move",
        )
