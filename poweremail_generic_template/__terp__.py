# -*- coding: utf-8 -*-
{
    "name": "poweremail_basic_template",
    "description": """Implements a generic email template using the banners module""",
    "version": "0-dev",
    "author": "GISCE",
    "category": "GISCEMaster",
    "depends": [
        "poweremail",
        "report_banner"
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "data/banners/banner_generic_email_template_title.xml",
        "data/banners/banner_generic_email_template_header.xml",
        "data/banners/banner_generic_email_template_preheader.xml",
        "data/banners/banner_generic_email_template_body.xml",
        "data/banners/banner_generic_email_template_footer.xml",
        "data/banners/banner_generic_email_template_css.xml",
        "data/banners/banner_generic_email_template_company.xml",
        "data/banners/banner_generic_email_template_button.xml",
    ],
    "active": False,
    "installable": True
}
