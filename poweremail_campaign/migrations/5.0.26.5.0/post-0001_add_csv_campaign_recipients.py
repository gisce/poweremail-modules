# -*- coding: utf-8 -*-
import logging

import pooler
from oopgrade.oopgrade import load_access_rules_from_model_name, load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info('Adding CSV recipients support to poweremail_campaign')

    pool = pooler.get_pool(cursor.dbname)
    models = [
        'poweremail.campaign',
        'poweremail.campaign.recipient',
    ]

    for model in models:
        logger.info('Creating or updating table: {}'.format(model))
        pool.get(model)._auto_init(
            cursor, context={'module': 'poweremail_campaign'}
        )

    data_files = [
        'poweremail_campaign_view.xml',
        'poweremail_campaign_recipient_view.xml',
    ]
    for data_file in data_files:
        logger.info('Updating XML: {}'.format(data_file))
        load_data(
            cursor, 'poweremail_campaign', data_file, idref=None, mode='update'
        )

    load_access_rules_from_model_name(
        cursor, 'poweremail_campaign', [
            'model_poweremail_campaign_recipient',
        ], mode='init'
    )

    logger.info('CSV recipients migration successful.')


def down(cursor, installed_version):
    pass


migrate = up
