/** @odoo-module **/

import "@web/webclient/user_menu/user_menu_items";
import { registry } from "@web/core/registry";

// Keep the user menu focused on PassionTech ERP rather than Odoo's hosted account.
registry.category("user_menuitems").remove("odoo_account");
