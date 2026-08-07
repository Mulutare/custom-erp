from odoo import http
from odoo.http import request
from odoo.service import security

from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.utils import (
    ensure_db,
    is_user_internal,
)


class PassionTechHome(Home):

    def _passiontech_landing_url(self):
        user = request.env.user

        has_sales = user.has_group(
            "passiontech_security.group_sales_officer"
        )
        has_inventory = user.has_group(
            "passiontech_security.group_inventory_officer"
        )
        has_finance = user.has_group(
            "passiontech_security.group_finance_officer"
        )

        if has_sales and not has_inventory and not has_finance:
            return "/odoo/sales"

        if has_inventory and not has_sales and not has_finance:
            return "/odoo/inventory"

        if has_finance and not has_sales and not has_inventory:
            return "/odoo/customer-invoices"

        return "/odoo"

    def _passiontech_prepare_user(self):
        ensure_db()

        if not request.session.uid:
            return request.redirect_query(
                "/web/login",
                query={
                    "redirect": request.httprequest.full_path,
                },
                code=303,
            )

        if not security.check_session(
            request.session,
            request.env,
            request,
        ):
            raise http.SessionExpiredException(
                "Session expired"
            )

        if not is_user_internal(request.session.uid):
            return request.redirect(
                "/web/login_successful",
                303,
            )

        request.update_env(user=request.session.uid)
        return None

    def _passiontech_is_system_administrator(self):
        return request.env.user.has_group(
            "passiontech_security."
            "group_system_administrator"
        )

    @http.route(
        "/odoo",
        type="http",
        auth="none",
        readonly=Home._web_client_readonly,
    )
    def passiontech_root(
        self,
        s_action=None,
        **kw,
    ):
        response = self._passiontech_prepare_user()

        if response:
            return response

        landing_url = self._passiontech_landing_url()

        if landing_url != "/odoo":
            return request.redirect(
                landing_url,
                303,
            )

        return super().web_client(
            s_action=s_action,
            **kw,
        )

    @http.route(
        [
            "/odoo/apps",
            "/odoo/apps/<path:subpath>",
        ],
        type="http",
        auth="none",
        readonly=Home._web_client_readonly,
    )
    def passiontech_apps(
        self,
        subpath=None,
        s_action=None,
        **kw,
    ):
        response = self._passiontech_prepare_user()

        if response:
            return response

        if not self._passiontech_is_system_administrator():
            return request.redirect(
                self._passiontech_landing_url(),
                303,
            )

        return super().web_client(
            s_action=s_action,
            subpath=subpath,
            **kw,
        )

    @http.route(
        [
            "/odoo/sales",
            "/odoo/sales/<path:subpath>",
        ],
        type="http",
        auth="none",
        readonly=Home._web_client_readonly,
    )
    def passiontech_sales(
        self,
        subpath=None,
        s_action=None,
        **kw,
    ):
        response = self._passiontech_prepare_user()

        if response:
            return response

        has_sales_access = request.env.user.has_group(
            "passiontech_security.group_sales_officer"
        )

        if (
            not has_sales_access
            and not self._passiontech_is_system_administrator()
        ):
            return request.redirect(
                self._passiontech_landing_url(),
                303,
            )

        return super().web_client(
            s_action=s_action,
            subpath=subpath,
            **kw,
        )

    @http.route(
        [
            "/odoo/customer-invoices",
            "/odoo/customer-invoices/<path:subpath>",
        ],
        type="http",
        auth="none",
        readonly=Home._web_client_readonly,
    )
    def passiontech_finance(
        self,
        subpath=None,
        s_action=None,
        **kw,
    ):
        response = self._passiontech_prepare_user()

        if response:
            return response

        has_finance_access = request.env.user.has_group(
            "passiontech_security.group_finance_officer"
        )

        if (
            not has_finance_access
            and not self._passiontech_is_system_administrator()
        ):
            return request.redirect(
                self._passiontech_landing_url(),
                303,
            )

        return super().web_client(
            s_action=s_action,
            subpath=subpath,
            **kw,
        )

    @http.route(
        [
            "/odoo/inventory",
            "/odoo/inventory/<path:subpath>",
        ],
        type="http",
        auth="none",
        readonly=Home._web_client_readonly,
    )
    def passiontech_inventory(
        self,
        subpath=None,
        s_action=None,
        **kw,
    ):
        response = self._passiontech_prepare_user()

        if response:
            return response

        has_inventory_access = request.env.user.has_group(
            "passiontech_security.group_inventory_officer"
        )

        if (
            not has_inventory_access
            and not self._passiontech_is_system_administrator()
        ):
            return request.redirect(
                self._passiontech_landing_url(),
                303,
            )

        return super().web_client(
            s_action=s_action,
            subpath=subpath,
            **kw,
        )
