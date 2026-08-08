from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import common, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestPassionTechFinancialReports(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].search(
            [("name", "=", "Passion Technology")], limit=1
        )
        if not cls.company:
            raise AssertionError("Passion Technology company is not configured")
        cls.finance_officer = new_test_user(
            cls.env,
            login="pt_finance_officer_reports_test",
            groups="passiontech_security.group_finance_officer",
            company_id=cls.company.id,
        )
        cls.finance_manager = new_test_user(
            cls.env,
            login="pt_finance_manager_reports_test",
            groups="passiontech_security.group_finance_manager",
            company_id=cls.company.id,
        )

    def test_templates_are_complete_and_evaluable(self):
        expected = {
            "passiontech_financial_reports.report_profit_and_loss": "net_profit",
            "passiontech_financial_reports.report_balance_sheet": "balance_check",
            "passiontech_financial_reports.report_cash_flow": "net_cash_flow",
        }
        for xmlid, final_kpi in expected.items():
            report = self.env.ref(xmlid)
            self.assertIn(final_kpi, report.kpi_ids.mapped("name"))
            aep = report._prepare_aep(self.env.company)
            result = report.evaluate(
                aep,
                date_from="2026-01-01",
                date_to="2026-12-31",
            )
            self.assertTrue(result)

    def test_instances_default_to_posted_entries(self):
        for xmlid in (
            "passiontech_financial_reports.instance_profit_and_loss",
            "passiontech_financial_reports.instance_balance_sheet",
            "passiontech_financial_reports.instance_cash_flow",
        ):
            instance = self.env.ref(xmlid)
            self.assertEqual(instance.target_move, "posted")
            self.assertEqual(len(instance.period_ids), 2)

    def test_financial_statement_pdf_and_xlsx_actions(self):
        pdf_report = self.env.ref("mis_builder.qweb_pdf_export")
        xlsx_report = self.env.ref("mis_builder.xls_export")
        self.assertEqual(pdf_report.report_type, "qweb-pdf")
        self.assertEqual(xlsx_report.report_type, "xlsx")
        for xmlid in (
            "passiontech_financial_reports.instance_profit_and_loss",
            "passiontech_financial_reports.instance_balance_sheet",
            "passiontech_financial_reports.instance_cash_flow",
        ):
            instance = self.env.ref(xmlid)
            instance.print_pdf()
            instance.export_xls()
            html, html_format = self.env["ir.actions.report"]._render_qweb_html(
                "mis_builder.report_mis_report_instance",
                instance.ids,
                data={"dummy": True},
            )
            xlsx, xlsx_format = self.env["ir.actions.report"]._render(
                "mis_builder.mis_report_instance_xlsx",
                instance.ids,
                data={"dummy": True},
            )
            self.assertEqual(html_format, "html")
            self.assertIn(b"mis_table", html)
            self.assertEqual(xlsx_format, "xlsx")
            self.assertTrue(xlsx.startswith(b"PK"))

    def test_cash_flow_reconciles_to_cash_accounts(self):
        report = self.env.ref("passiontech_financial_reports.report_cash_flow")
        self.assertIn("cash_account_movement", report.kpi_ids.mapped("name"))
        self.assertIn("cash_flow_reconciliation", report.kpi_ids.mapped("name"))

    def test_controlled_financial_statement_values(self):
        manager = self.finance_manager
        accounts = {}
        for account_type in (
            "asset_cash",
            "asset_receivable",
            "asset_fixed",
            "income",
            "equity",
        ):
            accounts[account_type] = self.env["account.account"].search(
                [
                    ("company_ids", "in", self.company.id),
                    ("account_type", "=", account_type),
                ],
                limit=1,
            )
            self.assertTrue(accounts[account_type], account_type)

        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")],
            limit=1,
        )

        def post(debit_type, credit_type, amount, label):
            move = (
                self.env["account.move"]
                .with_user(manager)
                .with_company(self.company)
                .create(
                    {
                        "date": fields.Date.from_string("2099-06-30"),
                        "journal_id": journal.id,
                        "ref": label,
                        "line_ids": [
                            Command.create(
                                {
                                    "account_id": accounts[debit_type].id,
                                    "debit": amount,
                                    "name": label,
                                }
                            ),
                            Command.create(
                                {
                                    "account_id": accounts[credit_type].id,
                                    "credit": amount,
                                    "name": label,
                                }
                            ),
                        ],
                    }
                )
            )
            move.action_post()

        post("asset_receivable", "income", 100.0, "Controlled invoice")
        post("asset_cash", "asset_receivable", 100.0, "Controlled receipt")
        post("asset_fixed", "asset_cash", 40.0, "Controlled asset purchase")
        post("asset_cash", "equity", 25.0, "Controlled capital injection")

        def evaluate(xmlid):
            report = self.env.ref(xmlid)
            return report.evaluate(
                report._prepare_aep(self.company),
                date_from="2099-01-01",
                date_to="2099-12-31",
            )

        def value(result, key):
            raw_value = result[key]
            return raw_value[1] if isinstance(raw_value, tuple) else raw_value

        profit_and_loss = evaluate(
            "passiontech_financial_reports.report_profit_and_loss"
        )
        self.assertAlmostEqual(value(profit_and_loss, "revenue"), 100.0)
        self.assertAlmostEqual(value(profit_and_loss, "net_profit"), 100.0)

        cash_flow = evaluate("passiontech_financial_reports.report_cash_flow")
        self.assertAlmostEqual(value(cash_flow, "operating_cash_flow"), 100.0)
        self.assertAlmostEqual(value(cash_flow, "investing_cash_flow"), -40.0)
        self.assertAlmostEqual(value(cash_flow, "financing_cash_flow"), 25.0)
        self.assertAlmostEqual(value(cash_flow, "net_cash_flow"), 85.0)
        self.assertAlmostEqual(value(cash_flow, "cash_account_movement"), 85.0)
        self.assertAlmostEqual(value(cash_flow, "cash_flow_reconciliation"), 0.0)

        balance_sheet = evaluate(
            "passiontech_financial_reports.report_balance_sheet"
        )
        self.assertAlmostEqual(value(balance_sheet, "balance_check"), 0.0)

    def test_finance_officer_can_open_partner_statement(self):
        self.assertTrue(
            self.finance_officer.has_group(
                "partner_statement.group_outstanding_statement"
            )
        )
        partner = self.env.ref("base.res_partner_2")
        wizard = (
            self.env["outstanding.statement.wizard"]
            .with_user(self.finance_officer)
            .with_company(self.company)
            .with_context(active_model="res.partner", active_ids=partner.ids)
            .create({"company_id": self.company.id})
        )
        action = wizard.button_export_html()
        self.assertEqual(action["type"], "ir.actions.report")

    def test_journal_lock_and_posting_roles(self):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")],
            limit=1,
        )
        accounts = self.env["account.account"].search(
            [
                ("company_ids", "in", self.company.id),
                ("account_type", "in", ["income", "expense"]),
            ],
            limit=2,
        )
        self.assertEqual(len(accounts), 2)
        values = {
            "date": fields.Date.today(),
            "journal_id": journal.id,
            "line_ids": [
                Command.create(
                    {"account_id": accounts[0].id, "debit": 10.0, "name": "Debit"}
                ),
                Command.create(
                    {"account_id": accounts[1].id, "credit": 10.0, "name": "Credit"}
                ),
            ],
        }
        manager_move = (
            self.env["account.move"]
            .with_user(self.finance_manager)
            .with_company(self.company)
            .create(values)
        )
        officer_move = (
            self.env["account.move"]
            .with_user(self.finance_manager)
            .with_company(self.company)
            .create(values)
        )
        manager_move.action_post()
        journal.with_user(self.finance_manager).fiscalyear_lock_date = manager_move.date
        with self.assertRaises(UserError):
            manager_move.button_cancel()
        with self.assertRaises(AccessError):
            officer_move.with_user(self.finance_officer).action_post()
