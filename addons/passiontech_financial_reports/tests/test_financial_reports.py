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
        ):
            instance = self.env.ref(xmlid)
            self.assertEqual(instance.target_move, "posted")
            self.assertEqual(len(instance.period_ids), 2)

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
