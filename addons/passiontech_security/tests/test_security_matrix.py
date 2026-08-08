from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, common, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestPassionTechSecurityMatrix(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].search(
            [("name", "=", "Passion Technology")], limit=1
        )
        if not cls.company:
            cls.company = cls.env.company
            cls.company.name = "Passion Technology"

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

    def test_oca_financial_report_rpc_is_finance_only(self):
        wizard_model = self.env["general.ledger.report.wizard"]
        for role in (
            "sales_officer",
            "sales_manager",
            "inventory_officer",
            "inventory_manager",
            "access_admin",
        ):
            with self.assertRaises(AccessError):
                wizard_model.with_user(self.users[role]).create({})

        wizard = wizard_model.with_user(self.users["finance_officer"]).create({})
        self.assertTrue(wizard)

    def test_aged_report_configuration_is_finance_manager_only(self):
        values = {
            "name": "Audit ageing intervals",
            "line_ids": [
                Command.create({"name": "30 days", "inferior_limit": 30})
            ],
        }
        for role in ("sales_manager", "inventory_manager", "finance_officer"):
            with self.assertRaises(AccessError):
                self.env["account.age.report.configuration"].with_user(
                    self.users[role]
                ).create(values)

        configuration = self.env["account.age.report.configuration"].with_user(
            self.users["finance_manager"]
        ).create(values)
        self.assertTrue(configuration)

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

    def test_builtin_technical_admin_has_full_server_authority(self):
        self.assertTrue(self.env.user.has_group("base.group_system"))
        self.env["account.move"]._passiontech_check_posting_access()
        self.env[
            "sale.advance.payment.inv"
        ]._passiontech_check_invoice_creation_access()
        self.env[
            "crossovered.budget.lines"
        ]._passiontech_check_budget_access()
        self.env[
            "general.ledger.report.wizard"
        ]._passiontech_check_financial_report_access()

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

    def test_partial_delivery_backorder_and_duplicate_actions(self):
        sales = self.users["sales_officer"]
        inventory = self.users["inventory_officer"]
        finance = self.users["finance_officer"]
        partner = self.env["res.partner"].create(
            {"name": "PassionTech Backorder Test Customer"}
        )
        product = self.env["product.product"].create(
            {
                "name": "PassionTech Backorder Test Product",
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
            product, warehouse.lot_stock_id, 10.0
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
                            {"product_id": product.id, "product_uom_qty": 10.0}
                        )
                    ],
                }
            )
        )
        order.action_confirm()
        picking_count = len(order.picking_ids)
        with self.assertRaises(UserError):
            order.action_confirm()
        self.assertEqual(len(order.picking_ids), picking_count)

        delivery = order.picking_ids.with_user(inventory)
        delivery.action_assign()
        delivery.move_ids.quantity = 6.0
        backorder_action = delivery.button_validate()
        self.assertEqual(
            backorder_action["res_model"], "stock.backorder.confirmation"
        )
        with Form(
            self.env["stock.backorder.confirmation"]
            .with_user(inventory)
            .with_context(backorder_action["context"])
        ) as backorder_form:
            backorder_wizard = backorder_form.save()
        backorder_wizard.process()
        self.assertEqual(delivery.state, "done")
        self.assertAlmostEqual(sum(delivery.move_ids.mapped("quantity")), 6.0)

        backorder = self.env["stock.picking"].search(
            [("backorder_id", "=", delivery.id)]
        )
        self.assertEqual(len(backorder), 1)
        self.assertAlmostEqual(sum(backorder.move_ids.mapped("product_uom_qty")), 4.0)
        self.assertAlmostEqual(order.order_line.qty_delivered, 6.0)
        self.assertEqual(order.invoice_status, "to invoice")

        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_user(finance)
            .with_company(self.company)
            .with_context(active_model="sale.order", active_ids=order.ids)
            .create({"advance_payment_method": "delivered"})
        )
        wizard.create_invoices()
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertAlmostEqual(order.invoice_ids.invoice_line_ids.quantity, 6.0)

        backorder = backorder.with_user(inventory)
        backorder.action_assign()
        backorder.move_ids.quantity = 4.0
        backorder.button_validate()
        backorder.button_validate()
        self.assertEqual(backorder.state, "done")
        self.assertAlmostEqual(order.order_line.qty_delivered, 10.0)
        self.assertFalse(
            self.env["stock.picking"].search_count(
                [("backorder_id", "=", backorder.id)]
            )
        )
        self.assertAlmostEqual(
            self.env["stock.quant"]._get_available_quantity(
                product, warehouse.lot_stock_id
            ),
            0.0,
        )

    def test_cross_company_operational_records_are_isolated(self):
        other_company = self.env["res.company"].create(
            {"name": "PassionTech Isolated Test Company"}
        )
        other_partner = self.env["res.partner"].create(
            {
                "name": "PassionTech Isolated Customer",
                "company_id": other_company.id,
            }
        )
        other_warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", other_company.id)], limit=1
        )
        self.assertTrue(other_warehouse)
        other_order = self.env["sale.order"].with_company(other_company).create(
            {
                "partner_id": other_partner.id,
                "company_id": other_company.id,
                "warehouse_id": other_warehouse.id,
            }
        )
        other_budget = self.env["crossovered.budget"].with_company(
            other_company
        ).create(
            {
                "name": "Isolated budget",
                "date_from": fields.Date.today().replace(month=1, day=1),
                "date_to": fields.Date.today().replace(month=12, day=31),
                "company_id": other_company.id,
            }
        )

        for role in ("sales_officer", "inventory_officer", "finance_officer"):
            user = self.users[role]
            self.assertNotIn(other_company, user.company_ids)
            self.assertFalse(
                self.env["sale.order"].with_user(user).search_count(
                    [("id", "=", other_order.id)]
                )
            )
            self.assertFalse(
                self.env["stock.warehouse"].with_user(user).search_count(
                    [("id", "=", other_warehouse.id)]
                )
            )
            if role == "finance_officer":
                self.assertFalse(
                    self.env["crossovered.budget"].with_user(user).search_count(
                        [("id", "=", other_budget.id)]
                    )
                )
            else:
                with self.assertRaises(AccessError):
                    self.env["crossovered.budget"].with_user(user).search_count(
                        [("id", "=", other_budget.id)]
                    )

    def test_purchase_receipt_bill_payment_and_valuation_workflow(self):
        owner = self.users["company_owner"]
        inventory = self.users["inventory_officer"]
        finance = self.users["finance_officer"]
        finance_manager = self.users["finance_manager"]
        self.assertTrue(owner.has_group("purchase.group_purchase_manager"))

        vendor = self.env["res.partner"].create(
            {"name": "PassionTech Controlled Workflow Vendor"}
        )
        product = self.env["product.product"].create(
            {
                "name": "PassionTech Controlled Purchased Product",
                "is_storable": True,
                "standard_price": 60.0,
                "supplier_taxes_id": [Command.clear()],
            }
        )
        purchase = (
            self.env["purchase.order"]
            .with_user(owner)
            .with_company(self.company)
            .create(
                {
                    "partner_id": vendor.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": product.id,
                                "product_qty": 2.0,
                                "price_unit": 60.0,
                            }
                        )
                    ],
                }
            )
        )
        purchase.button_confirm()
        receipt = purchase.picking_ids.with_user(inventory)
        receipt.action_assign()
        receipt.move_ids.quantity = 2.0
        receipt.with_context(
            picking_ids_not_to_backorder=receipt.ids
        ).button_validate()
        self.assertEqual(receipt.state, "done")
        self.assertTrue(all(receipt.move_ids.mapped("is_valued")))
        self.assertAlmostEqual(sum(receipt.move_ids.mapped("value")), 120.0)

        bill = (
            self.env["account.move"]
            .with_user(finance)
            .with_company(self.company)
            .create(
                {
                    "move_type": "in_invoice",
                    "partner_id": vendor.id,
                    "invoice_date": fields.Date.today(),
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": product.id,
                                "quantity": 2.0,
                                "price_unit": 60.0,
                                "tax_ids": [Command.clear()],
                            }
                        )
                    ],
                }
            )
        )
        with self.assertRaises(AccessError):
            bill.with_user(finance).action_post()
        bill.with_user(finance_manager).action_post()

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
                    "payment_type": "outbound",
                    "partner_type": "supplier",
                    "partner_id": vendor.id,
                    "amount": bill.amount_total,
                    "date": fields.Date.today(),
                    "journal_id": bank_journal.id,
                }
            )
        )
        payment.with_user(finance_manager).action_post()
        payable_lines = (bill.line_ids + payment.move_id.line_ids).filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        payable_lines.with_user(finance).reconcile()
        self.assertEqual(bill.payment_state, "paid")

    def test_return_credit_note_stock_and_accounting_correction(self):
        sales = self.users["sales_officer"]
        inventory = self.users["inventory_officer"]
        finance = self.users["finance_officer"]
        finance_manager = self.users["finance_manager"]
        partner = self.env["res.partner"].create(
            {"name": "PassionTech Controlled Return Customer"}
        )
        product = self.env["product.product"].create(
            {
                "name": "PassionTech Controlled Return Product",
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
            product, warehouse.lot_stock_id, 1.0
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
                            {"product_id": product.id, "product_uom_qty": 1.0}
                        )
                    ],
                }
            )
        )
        order.action_confirm()
        delivery = order.picking_ids.with_user(inventory)
        delivery.action_assign()
        delivery.move_ids.quantity = 1.0
        delivery.with_context(
            picking_ids_not_to_backorder=delivery.ids
        ).button_validate()

        invoice_wizard = (
            self.env["sale.advance.payment.inv"]
            .with_user(finance)
            .with_company(self.company)
            .with_context(active_model="sale.order", active_ids=order.ids)
            .create({"advance_payment_method": "delivered"})
        )
        invoice_wizard.create_invoices()
        invoice = order.invoice_ids
        invoice.with_user(finance_manager).action_post()

        return_form = Form(
            self.env["stock.return.picking"]
            .with_user(inventory)
            .with_context(
                active_ids=delivery.ids,
                active_id=delivery.id,
                active_model="stock.picking",
            )
        )
        return_wizard = return_form.save()
        return_wizard.product_return_moves.quantity = 1.0
        return_action = return_wizard.action_create_returns()
        return_picking = self.env["stock.picking"].browse(return_action["res_id"])
        return_picking = return_picking.with_user(inventory)
        return_picking.action_assign()
        return_picking.move_ids.quantity = 1.0
        return_picking.with_context(
            picking_ids_not_to_backorder=return_picking.ids
        ).button_validate()
        self.assertEqual(return_picking.state, "done")
        self.assertEqual(
            product.with_company(self.company).qty_available,
            1.0,
        )

        reversal = (
            self.env["account.move.reversal"]
            .with_user(finance_manager)
            .with_company(self.company)
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "date": fields.Date.today(),
                    "journal_id": invoice.journal_id.id,
                    "reason": "Controlled product return",
                }
            )
        )
        action = reversal.refund_moves()
        credit_note = self.env["account.move"].browse(action["res_id"])
        credit_note.with_user(finance_manager).action_post()
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(credit_note.state, "posted")
        self.assertEqual(credit_note.amount_total, invoice.amount_total)
