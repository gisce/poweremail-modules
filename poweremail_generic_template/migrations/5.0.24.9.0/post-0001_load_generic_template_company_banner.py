# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return
    load_data(cursor, 'poweremail_generic_template', 'data/banners/banner_generic_email_template_company.xml')


def down(cursor, installed_version):
    pass

migrate = up