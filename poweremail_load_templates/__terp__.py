# -*- coding: utf-8 -*-
{
  "name": "PowerEmail Campaign",
  "description": """PowerEmail Sync Templates""",
  "version": "23.6.0",
  "author": "GISCE",
  "category": "GISCEMaster",
  "depends": [
      "poweremail",
  ],
  "init_xml": [],
  "demo_xml": [],
  "update_xml": [
      "poweremail_template_view.xml",
      "poweremail_templates_source_view.xml",
      "wizard/wizard_load_poweremail_template.xml",
      "security/ir.model.access.csv",
  ],
  "active": False,
  "installable": True
}