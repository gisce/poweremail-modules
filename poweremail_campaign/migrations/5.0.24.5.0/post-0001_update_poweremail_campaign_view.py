# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info('** STARTING THE UPDATE OF XML VIEW **')
    logger.info('* Module poweremail_campaign')
    logger.info('*      View poweremail_campaign_view.xml with id poweremail_campaign_form')

    load_data_records(cursor, 'poweremail_campaign', 'poweremail_campaign_view.xml',
                      ['poweremail_campaign_form'], )
    logger.info('** XML VIEW UPDATED SUCCESSFULLY **')


def down(cursor, installed_version):
    pass


migrate = up
