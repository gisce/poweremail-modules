# -*- coding: utf-8 -*-
import logging
from tools import config
from oopgrade.oopgrade import load_data_records, column_exists, add_columns

logger = logging.getLogger('openerp.migration.' + __name__)


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    # afegim columna nova
    if column_exists(cursor, 'poweremail_campaign', 'progress_generate_mails'):
        logger.info('Column progress_generate_mails already exists in poweremail_campaign. Passing...')
    else:
        add_columns(cursor, {
            'poweremail_campaign': [('progress_generate_mails', 'float')]
        })

    # Crear les diferents vistes
    load_data_records(
        cursor, 'poweremail_campaign',
        'poweremail_campaign_view.xml',
        ['poweremail_campaign_form', 'poweremail_campaign_tree'],
        mode='update'
    )


def down(cursor, installed_version):
    pass


migrate = up
