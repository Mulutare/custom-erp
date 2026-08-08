from odoo import _, models
from odoo.exceptions import AccessError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _passiontech_check_posting_access(self):
        """Restrict accounting-document posting to Finance management."""
        if self.env.su:
            return

        user = self.env.user

        allowed = (
            user.has_group(
                "passiontech_security.group_finance_manager"
            )
            or user.has_group("base.group_system")
            or user.has_group(
                "passiontech_security.group_system_administrator"
            )
        )

        if not allowed:
            raise AccessError(
                _(
                    "Only Finance Managers, Company Owners, "
                    "or System Administrators may post "
                    "accounting documents."
                )
            )

    def action_post(self):
        self._passiontech_check_posting_access()
        return super().action_post()
