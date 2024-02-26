# -*- coding: utf-8 -*-
{
  "name": "PowerEmail Campaign",
  "description": """PowerEmail Campaign Manager""",
  "version": "23.9.0",
  "author": "GISCE",
  "category": "GISCEMaster",
  "depends": [
      "poweremail",
      "poweremail_references",
  ],
  "init_xml": [],
  "demo_xml": [
    "poweremail_campaign_demo.xml",
  ],
  "update_xml": [
      "wizard/wizard_poweremail_campaign.xml",
      "wizard/wizard_resend_mails_view.xml",
      "poweremail_campaign_view.xml",
      "poweremail_campaign_line_view.xml",
      "security/ir.model.access.csv",
  ],
  "active": False,
  "installable": True
}
