from odoo import _, api, models
from odoo.exceptions import AccessError


class AccountFinancialReportAbstractWizard(models.AbstractModel):
    _inherit = "account_financial_report_abstract_wizard"

    def _passiontech_check_financial_report_access(self):
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
                _("Only authorized Finance users may access financial reports.")
            )

    @api.model_create_multi
    def create(self, vals_list):
        self._passiontech_check_financial_report_access()
        return super().create(vals_list)

    def button_export_html(self):
        self._passiontech_check_financial_report_access()
        return super().button_export_html()

    def button_export_pdf(self):
        self._passiontech_check_financial_report_access()
        return super().button_export_pdf()

    def button_export_xlsx(self):
        self._passiontech_check_financial_report_access()
        return super().button_export_xlsx()


class AccountAgeReportConfiguration(models.Model):
    _inherit = "account.age.report.configuration"

    def _passiontech_check_configuration_access(self):
        if self.env.su:
            return
        if not (
            self.env.user.has_group("passiontech_security.group_finance_manager")
            or self.env.user.has_group("base.group_system")
            or self.env.user.has_group(
                "passiontech_security.group_system_administrator"
            )
        ):
            raise AccessError(
                _("Only Finance Managers may change aged report configuration.")
            )

    @api.model_create_multi
    def create(self, vals_list):
        self._passiontech_check_configuration_access()
        return super().create(vals_list)

    def write(self, vals):
        self._passiontech_check_configuration_access()
        return super().write(vals)

    def unlink(self):
        self._passiontech_check_configuration_access()
        return super().unlink()


class AccountAgeReportConfigurationLine(models.Model):
    _inherit = "account.age.report.configuration.line"

    @api.model_create_multi
    def create(self, vals_list):
        self.env["account.age.report.configuration"]._passiontech_check_configuration_access()
        return super().create(vals_list)

    def write(self, vals):
        self.env["account.age.report.configuration"]._passiontech_check_configuration_access()
        return super().write(vals)

    def unlink(self):
        self.env["account.age.report.configuration"]._passiontech_check_configuration_access()
        return super().unlink()
