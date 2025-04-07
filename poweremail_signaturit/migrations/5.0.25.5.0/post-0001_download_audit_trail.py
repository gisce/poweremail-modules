# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data_records
from tools import config

def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    module = "poweremail_signaturit"
    view = "poweremail_mailbox_view.xml"
    record_list = [
        "poweremail_mailbox_certificat_form"
    ]
    load_data_records(
        cursor, module, view, record_list, mode='update'
    )

    view = "report/data.xml"
    record_list = [
        "report_email_certificate"
    ]
    load_data_records(
        cursor, module, view, record_list, mode='update'
    )

def down(cursor, installed_version):
    pass


migrate = up
