# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return
    load_data(cursor, 'poweremail_generic_template', 'data/banners/banner_generic_email_template_button.xml')

def down(cursor, installed_version):
    pass

migrate = up