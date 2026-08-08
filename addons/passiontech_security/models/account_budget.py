from odoo import _, api, models
from odoo.exceptions import AccessError


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    @api.model
    def _passiontech_check_budget_access(self):
        if self.env.su:
            return
        if not (
            self.env.user.has_group(
                "passiontech_security.group_finance_officer"
            )
            or self.env.user.has_group("base.group_system")
            or self.env.user.has_group(
                "passiontech_security.group_system_administrator"
            )
        ):
            raise AccessError(
                _("Only authorized Finance users may modify budget lines.")
            )

    @api.model_create_multi
    def create(self, vals_list):
        self._passiontech_check_budget_access()
        return super().create(vals_list)

    def write(self, vals):
        self._passiontech_check_budget_access()
        return super().write(vals)

    def unlink(self):
        self._passiontech_check_budget_access()
        return super().unlink()
