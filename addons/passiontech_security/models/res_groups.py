from odoo import api, models
from odoo.fields import Command


class ResGroups(models.Model):
    _inherit = "res.groups"

    @api.model
    def apply_passiontech_default_user_policy(self):
        """Remove automatic manager access from newly created users."""
        default_group = self.env.ref("base.default_user_group")

        manager_group_xml_ids = [
            "account.group_account_manager",
            "hr.group_hr_manager",
            "hr_attendance.group_hr_attendance_manager",
            "product.group_product_manager",
            "project.group_project_manager",
            "purchase.group_purchase_manager",
            "sales_team.group_sale_manager",
            "stock.group_stock_manager",
        ]

        manager_groups = self.env["res.groups"].browse([
            self.env.ref(xml_id).id
            for xml_id in manager_group_xml_ids
        ])

        default_group.sudo().write({
            "implied_ids": [
                Command.unlink(group.id)
                for group in manager_groups
            ]
        })

        return True

    @api.model
    def apply_passiontech_menu_policy(self):
        """Expose only role-approved application roots."""
        system_administrator = self.env.ref(
            "passiontech_security.group_system_administrator"
        )
        sales_manager = self.env.ref(
            "passiontech_security.group_sales_manager"
        )

        menu_policy = {
            # Administration
            "base.menu_management": [system_administrator.id],
            "base.menu_apps": [system_administrator.id],

            # CRM is available to Sales Managers, Company Owners through
            # inheritance, and System Administrators—but not Sales Officers.
            "crm.crm_menu_root": [
                sales_manager.id,
                system_administrator.id,
            ],

            # Extra applications remain hidden from operational roles.
            "mail.menu_root_discuss": [system_administrator.id],
            "project_todo.menu_todo_todos": [system_administrator.id],
            "calendar.mail_menu_calendar": [system_administrator.id],
            "contacts.menu_contacts": [system_administrator.id],
            "spreadsheet_dashboard.spreadsheet_dashboard_menu_root": [
                system_administrator.id
            ],
            "hr.menu_hr_root": [system_administrator.id],
        }

        for menu_xml_id, allowed_group_ids in menu_policy.items():
            menu = self.env.ref(
                menu_xml_id,
                raise_if_not_found=False,
            )

            if menu:
                menu.sudo().write({
                    "group_ids": [
                        Command.set(allowed_group_ids)
                    ]
                })

        return True