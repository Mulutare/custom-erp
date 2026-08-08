from odoo import _, models
from odoo.exceptions import AccessError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        if not self.env.su and not (
            self.env.user.has_group(
                "passiontech_security.group_inventory_officer"
            )
            or self.env.user.has_group(
                "passiontech_security.group_system_administrator"
            )
        ):
            raise AccessError(
                _("Only authorized Inventory users may validate transfers.")
            )
        return super().button_validate()
