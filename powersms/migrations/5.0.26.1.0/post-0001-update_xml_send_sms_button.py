# coding=utf-8
from tools import config
from oopgrade.oopgrade import MigrationHelper


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    mh = MigrationHelper(cursor, 'powersms')
    mh.update_xml_records('wizard/wizard_send_sms_view.xml', ['powersms_send_wizard_form'])

def down(cursor, installed_version):
    if not installed_version:
        return


migrate = up
