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

        # Finance-only, multi-role, and standard users return to the
        # normal web client, which resolves their permitted applications.
        return "/odoo"

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
        """Restrict the Apps catalog to PassionTech system administrators."""
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

        if not request.env.user.has_group(
            "passiontech_security."
            "group_system_administrator"
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