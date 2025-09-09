# -*- coding: utf-8 -*-
{
    "name": "Poweremail OORQ",
    "description": """Poweremail using OORQ""",
    "version": "23.9.0",
    "author": "GISCE",
    "category": "GISCEMaster",
    "depends": [
        'base',
        'base_extended',
        'poweremail_certificat',
        'giscedata_signatura_documents_signaturit',
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "poweremail_mailbox_view.xml",
        "poweremail_mailbox_data.xml",
        "report/data.xml",
    ],
    "active": False,
    "installable": True
}
