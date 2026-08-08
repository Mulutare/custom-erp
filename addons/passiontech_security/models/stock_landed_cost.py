from odoo import _, models
from odoo.exceptions import AccessError


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    def button_validate(self):
        if not self.env.su and not (
            self.env.user.has_group(
                "passiontech_security.group_inventory_manager"
            )
            or self.env.user.has_group(
                "passiontech_security.group_finance_manager"
            )
            or self.env.user.has_group(
                "passiontech_security.group_system_administrator"
            )
        ):
            raise AccessError(
                _(
                    "Only Inventory Managers, Finance Managers, Company "
                    "Owners, or System Administrators may validate landed "
                    "costs."
                )
            )
        return super().button_validate()
