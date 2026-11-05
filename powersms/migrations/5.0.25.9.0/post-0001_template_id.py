# -*- coding: utf-8 -*-
from __future__ import absolute_import

from oopgrade.oopgrade import MigrationHelper
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    module = 'powersms'
    model_name = 'powersms.smsbox'
    model_xml_id = 'powersms_smsbox_form'

    helper = MigrationHelper(cursor, module)
    helper.init_model(model_name)
    helper.update_xml_records('powersms_smsbox_view.xml', [model_xml_id])


def down(cursor, installed_version):
    pass


migrate = up
