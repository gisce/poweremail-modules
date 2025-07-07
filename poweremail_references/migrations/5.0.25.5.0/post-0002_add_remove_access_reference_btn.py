# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data_records
from tools import config


def up(cursor, installed_version):
    if not installed_version:
        return

    load_data_records(
        cursor,
        'poweremail_references',
        'poweremail_template_view.xml',
        ['poweremail_template_access_form'],
        mode='update'
    )


def down(cursor, installed_version):
    pass


migrate = up
