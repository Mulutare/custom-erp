{
    "name": "PassionTech Branding",
    "version": "19.0.2.0.1",
    "summary": "PassionTech ERP white-label web branding",
    "category": "Technical",
    "author": "Passion Technology",
    "license": "LGPL-3",
    "depends": [
        "web"
    ],
    "data": [
        "data/company_data.xml",
        "views/templates.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "passiontech_branding/static/src/js/title_service.js",
            "passiontech_branding/static/src/js/user_menu.js",
            "passiontech_branding/static/src/scss/branding.scss",
            "passiontech_branding/static/src/xml/webclient.xml"
        ]
    },
    "installable": True,
    "application": False
}
