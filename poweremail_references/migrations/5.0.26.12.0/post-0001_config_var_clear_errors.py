# coding=utf-8
from tools import config
from oopgrade.oopgrade import MigrationHelper


def up(cursor, installed_version):
    if not installed_version:
        return
    if config.updating_all:
        return

    module = 'poweremail_references'

    helper = MigrationHelper(cursor, module)
    helper.update_xml('res_config.xml', mode='init')


def down(cursor, installed_version):
    pass


migrate = up
