# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data_records
from tools import config
from tools.translate import trans_load


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

    trans_load(cursor, '{}/{}/i18n/es_ES.po'.format(config['addons_path'], module), 'es_ES')


def down(cursor, installed_version):
    pass


migrate = up
