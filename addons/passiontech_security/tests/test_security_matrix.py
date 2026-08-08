from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestPassionTechSecurityMatrix(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].search(
            [("name", "=", "Passion Technology")], limit=1
        )
        if not cls.company:
            raise AssertionError("Passion Technology company is not configured")

        roles = {
            "sales_officer": "passiontech_security.group_sales_officer",
            "sales_manager": "passiontech_security.group_sales_manager",
            "inventory_officer": "passiontech_security.group_inventory_officer",
            "inventory_manager": "passiontech_security.group_inventory_manager",
            "finance_officer": "passiontech_security.group_finance_officer",
            "finance_manager": "passiontech_security.group_finance_manager",
            "company_owner": "passiontech_security.group_company_owner",
            "access_admin": "passiontech_security.group_access_administrator",
            "system_admin": "passiontech_security.group_system_administrator",
        }
        cls.users = {
            role: new_test_user(
                cls.env,
                login=f"pt_{role}_security_test",
                groups=group,
                company_id=cls.company.id,
            )
            for role, group in roles.items()
        }

    def test_role_hierarchy_and_separation(self):
        expected = {
            "sales_manager": "passiontech_security.group_sales_officer",
            "inventory_manager": "passiontech_security.group_inventory_officer",
            "finance_manager": "passiontech_security.group_finance_officer",
            "company_owner": "passiontech_security.group_sales_manager",
            "system_admin": "passiontech_security.group_company_owner",
        }
        for role, inherited_group in expected.items():
            self.assertTrue(self.users[role].has_group(inherited_group))

        for role in ("sales_manager", "inventory_manager", "finance_manager"):
            self.assertFalse(self.users[role].has_group("base.group_system"))
            self.assertFalse(
                self.users[role].has_group(
                    "passiontech_security.group_access_administrator"
                )
            )

        self.assertFalse(
            self.users["company_owner"].has_group("base.group_system")
        )
        for group in (
            "passiontech_security.group_sales_officer",
            "passiontech_security.group_inventory_officer",
            "passiontech_security.group_finance_officer",
        ):
            self.assertFalse(self.users["access_admin"].has_group(group))

    def test_application_menu_matrix(self):
        menu_roles = {
            "sale.sale_menu_root": {
                "sales_officer", "sales_manager", "company_owner", "system_admin"
            },
            "stock.menu_stock_root": {
                "inventory_officer",
                "inventory_manager",
                "company_owner",
                "system_admin",
            },
            "account.menu_finance": {
                "finance_officer", "finance_manager", "company_owner", "system_admin"
            },
        }
        for menu_xmlid, allowed_roles in menu_roles.items():
            menu = self.env.ref(menu_xmlid)
            for role, user in self.users.items():
                visible = menu.id in self.env["ir.ui.menu"].with_user(
                    user
                )._visible_menu_ids()
                self.assertEqual(visible, role in allowed_roles)

        for role in self.users:
            if role != "system_admin":
                visible = self.env.ref("base.menu_apps").id in self.env[
                    "ir.ui.menu"
                ].with_user(self.users[role])._visible_menu_ids()
                self.assertFalse(visible)

    def test_cross_department_model_access(self):
        self.assertTrue(
            self.env["sale.order"]
            .with_user(self.users["sales_officer"])
            .has_access("create")
        )
        self.assertFalse(
            self.env["account.payment"]
            .with_user(self.users["sales_officer"])
            .has_access("create")
        )
        self.assertTrue(
            self.env["stock.picking"]
            .with_user(self.users["inventory_officer"])
            .has_access("write")
        )
        self.assertFalse(
            self.env["account.move"]
            .with_user(self.users["inventory_officer"])
            .has_access("create")
        )
        self.assertTrue(
            self.env["account.move"]
            .with_user(self.users["finance_officer"])
            .has_access("create")
        )
        self.assertFalse(
            self.env["sale.order"]
            .with_user(self.users["finance_officer"])
            .has_access("create")
        )

    def test_sensitive_stock_methods_are_server_side_protected(self):
        picking = self.env["stock.picking"]
        for role in (
            "sales_officer", "sales_manager", "finance_officer", "access_admin"
        ):
            with self.assertRaises(AccessError):
                picking.with_user(self.users[role]).button_validate()
        picking.with_user(self.users["inventory_officer"]).button_validate()

        quant = self.env["stock.quant"]
        with self.assertRaises(AccessError):
            quant.with_user(self.users["inventory_officer"]).action_apply_inventory()
        with self.assertRaises(AccessError):
            quant.with_user(self.users["sales_manager"]).action_apply_inventory()
        quant.with_user(self.users["inventory_manager"]).action_apply_inventory()

        landed_cost = self.env["stock.landed.cost"]
        for role in (
            "sales_manager", "inventory_officer", "finance_officer", "access_admin"
        ):
            with self.assertRaises(AccessError):
                landed_cost.with_user(self.users[role]).button_validate()
        landed_cost.with_user(self.users["inventory_manager"]).button_validate()
        landed_cost.with_user(self.users["finance_manager"]).button_validate()

    def test_budget_write_leak_is_blocked(self):
        budget_lines = self.env["crossovered.budget.lines"]
        for role in (
            "sales_officer",
            "sales_manager",
            "inventory_officer",
            "inventory_manager",
            "access_admin",
        ):
            with self.assertRaises(AccessError):
                budget_lines.with_user(
                    self.users[role]
                )._passiontech_check_budget_access()

        for role in (
            "finance_officer", "finance_manager", "company_owner", "system_admin"
        ):
            budget_lines.with_user(
                self.users[role]
            )._passiontech_check_budget_access()

    def test_finance_posting_and_operational_accounting(self):
        officer = self.users["finance_officer"]
        manager = self.users["finance_manager"]
        self.assertTrue(officer.has_group("account.group_account_user"))
        self.assertFalse(officer.has_group("account.group_account_manager"))
        self.assertTrue(
            self.env["account.bank.statement.line"]
            .with_user(officer)
            .has_access("write")
        )
        self.assertTrue(
            self.env["crossovered.budget"].with_user(officer).has_access("create")
        )

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
        values = {
            "date": fields.Date.today(),
            "journal_id": journal.id,
            "line_ids": [
                Command.create({"account_id": accounts[0].id, "debit": 10.0}),
                Command.create({"account_id": accounts[1].id, "credit": 10.0}),
            ],
        }
        move = self.env["account.move"].with_user(manager).create(values)
        with self.assertRaises(AccessError):
            move.with_user(officer).action_post()
        move.with_user(manager).action_post()
        self.assertEqual(move.state, "posted")

    def test_only_access_admins_manage_users(self):
        for role in (
            "sales_manager", "inventory_manager", "finance_manager", "company_owner"
        ):
            users_model = self.env["res.users"].with_user(self.users[role])
            self.assertFalse(users_model.has_access("write"))
            self.assertFalse(users_model.has_access("create"))
        for role in ("access_admin", "system_admin"):
            users_model = self.env["res.users"].with_user(self.users[role])
            self.assertTrue(users_model.has_access("write"))
            self.assertTrue(users_model.has_access("create"))

    def test_sales_delivery_invoice_payment_reconciliation_workflow(self):
        sales = self.users["sales_officer"]
        inventory = self.users["inventory_officer"]
        finance = self.users["finance_officer"]
        finance_manager = self.users["finance_manager"]

        partner = self.env["res.partner"].create(
            {"name": "PassionTech Controlled Workflow Customer"}
        )
        product = self.env["product.product"].create(
            {
                "name": "PassionTech Controlled Workflow Product",
                "is_storable": True,
                "invoice_policy": "delivery",
                "list_price": 100.0,
                "standard_price": 60.0,
                "taxes_id": [Command.clear()],
            }
        )
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.env["stock.quant"]._update_available_quantity(
            product,
            warehouse.lot_stock_id,
            5.0,
        )

        order = (
            self.env["sale.order"]
            .with_user(sales)
            .with_company(self.company)
            .create(
                {
                    "partner_id": partner.id,
                    "warehouse_id": warehouse.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": product.id,
                                "product_uom_qty": 1.0,
                            }
                        )
                    ],
                }
            )
        )
        order.action_confirm()
        self.assertEqual(order.state, "sale")

        picking = order.picking_ids.with_user(inventory)
        picking.action_assign()
        picking.move_ids.quantity = 1.0
        picking.with_context(
            picking_ids_not_to_backorder=picking.ids
        ).button_validate()
        self.assertEqual(picking.state, "done")

        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_user(finance)
            .with_company(self.company)
            .with_context(
                active_model="sale.order",
                active_ids=order.ids,
            )
            .create({"advance_payment_method": "delivered"})
        )
        wizard.create_invoices()
        invoice = order.invoice_ids
        self.assertEqual(len(invoice), 1)
        with self.assertRaises(AccessError):
            invoice.with_user(finance).action_post()
        invoice.with_user(finance_manager).action_post()

        bank_journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "bank")],
            limit=1,
        )
        payment = (
            self.env["account.payment"]
            .with_user(finance)
            .with_company(self.company)
            .create(
                {
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": partner.id,
                    "amount": invoice.amount_total,
                    "date": fields.Date.today(),
                    "journal_id": bank_journal.id,
                }
            )
        )
        with self.assertRaises(AccessError):
            payment.with_user(finance).action_post()
        payment.with_user(finance_manager).action_post()

        receivable_lines = (
            invoice.line_ids + payment.move_id.line_ids
        ).filtered(lambda line: line.account_id.account_type == "asset_receivable")
        receivable_lines.with_user(finance).reconcile()
        self.assertEqual(invoice.payment_state, "paid")

        statement_values = {
            "journal_id": bank_journal.id,
            "date": fields.Date.today(),
            "payment_ref": "Controlled bank receipt",
            "amount": invoice.amount_total,
        }
        with self.assertRaises(AccessError):
            self.env["account.bank.statement.line"].with_user(
                finance
            ).with_company(self.company).create(statement_values)
        statement_line = self.env["account.bank.statement.line"].with_user(
            finance_manager
        ).with_company(self.company).create(statement_values)
        self.assertTrue(statement_line.move_id)
