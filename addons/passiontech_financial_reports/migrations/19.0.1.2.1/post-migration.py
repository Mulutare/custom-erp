from odoo import SUPERUSER_ID, api


OPERATING_EXPRESSION = (
    "-balp['|', '|', '|', '|', '|', '|', '|', '|', '|', '|', "
    "('account_type', '=', 'income'), "
    "('account_type', '=', 'income_other'), "
    "('account_type', '=', 'expense'), "
    "('account_type', '=', 'expense_direct_cost'), "
    "('account_type', '=', 'expense_depreciation'), "
    "('account_type', '=', 'asset_receivable'), "
    "('account_type', '=', 'asset_current'), "
    "('account_type', '=', 'asset_prepayments'), "
    "('account_type', '=', 'liability_payable'), "
    "('account_type', '=', 'liability_current'), "
    "('account_type', '=', 'liability_credit_card')]"
)
INVESTING_EXPRESSION = (
    "-balp['|', ('account_type', '=', 'asset_fixed'), "
    "('account_type', '=', 'asset_non_current')]"
)
FINANCING_EXPRESSION = (
    "-balp['|', '|', ('account_type', '=', 'liability_non_current'), "
    "('account_type', '=', 'equity'), "
    "('account_type', '=', 'equity_unaffected')]"
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    expressions = {
        "expr_operating_cash_flow": OPERATING_EXPRESSION,
        "expr_investing_cash_flow": INVESTING_EXPRESSION,
        "expr_financing_cash_flow": FINANCING_EXPRESSION,
    }
    for xmlid, expression in expressions.items():
        env.ref(f"passiontech_financial_reports.{xmlid}").write(
            {"name": expression}
        )

    for xmlid in (
        "kpi_operating_cash_flow",
        "kpi_investing_cash_flow",
        "kpi_financing_cash_flow",
    ):
        env.ref(f"passiontech_financial_reports.{xmlid}").write(
            {
                "auto_expand_accounts": False,
                "auto_expand_accounts_style_id": False,
            }
        )

    env.ref("passiontech_financial_reports.report_cash_flow").write(
        {
            "description": (
                "Indirect cash flow reconciled to the period movement in "
                "cash and cash-equivalent accounts."
            )
        }
    )
