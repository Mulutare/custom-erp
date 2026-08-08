from odoo import _, models
from odoo.exceptions import AccessError


class PassionTechMisReportAccessMixin(models.AbstractModel):
    _name = "passiontech.mis.report.access.mixin"
    _description = "PassionTech MIS financial report access control"

    def _passiontech_check_mis_report_access(self):
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


class MisReport(models.Model):
    _name = "mis.report"
    _inherit = ["mis.report", "passiontech.mis.report.access.mixin"]

    def evaluate(self, *args, **kwargs):
        self._passiontech_check_mis_report_access()
        return super().evaluate(*args, **kwargs)


class MisReportInstance(models.Model):
    _name = "mis.report.instance"
    _inherit = ["mis.report.instance", "passiontech.mis.report.access.mixin"]

    def preview(self):
        self._passiontech_check_mis_report_access()
        return super().preview()

    def print_pdf(self):
        self._passiontech_check_mis_report_access()
        return super().print_pdf()

    def export_xls(self):
        self._passiontech_check_mis_report_access()
        return super().export_xls()
