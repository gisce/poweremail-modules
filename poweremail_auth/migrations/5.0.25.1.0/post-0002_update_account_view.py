# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    load_data_records(
        cursor, 'poweremail_auth',
        'poweremail_core_view.xml', ['view_poweremail_core_api_info_form'])
    logger.info('** XML VIEW UPDATED SUCCESSFULLY **')


def down(cursor, installed_version):
    pass


migrate = up
