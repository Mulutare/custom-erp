from odoo import _, models
from odoo.exceptions import AccessError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _passiontech_check_invoice_creation_access(self):
        """Allow manual sales-order invoicing only to Finance."""
        if self.env.su:
            return

        user = self.env.user

        allowed = (
            user.has_group(
                "passiontech_security.group_finance_officer"
            )
            or user.has_group("base.group_system")
            or user.has_group(
                "passiontech_security.group_system_administrator"
            )
        )

        if not allowed:
            raise AccessError(
                _(
                    "Only Finance Officers, Finance Managers, "
                    "Company Owners, or System Administrators "
                    "may create customer invoices from sales orders."
                )
            )

    def create_invoices(self):
        self._passiontech_check_invoice_creation_access()
        return super().create_invoices()
