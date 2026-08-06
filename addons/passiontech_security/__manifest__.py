{
    "name": "PassionTech Security",
    "version": "19.0.1.4.0",
    "summary": "Passion Technology company roles and access control",
    "category": "PassionTech",
    "author": "Passion Technology",
    "license": "LGPL-3",
    "depends": [
        "passiontech_core",
        "auth_signup",
        "web"
    ],
    "data": [
        "security/groups.xml",
        "data/default_user_policy.xml",
        "data/menu_restrictions.xml",
        "data/security_settings.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}