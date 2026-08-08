from odoo import _, models
from odoo.exceptions import AccessError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def action_apply_inventory(self, date=None):
        if not self.env.su and not (
            self.env.user.has_group(
                "passiontech_security.group_inventory_manager"
            )
            or self.env.user.has_group("base.group_system")
            or self.env.user.has_group(
                "passiontech_security.group_system_administrator"
            )
        ):
            raise AccessError(
                _(
                    "Only Inventory Managers, Company Owners, or System "
                    "Administrators may apply inventory adjustments."
                )
            )
        return super().action_apply_inventory(date=date)
