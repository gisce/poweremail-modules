# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_access_rules_from_model_name


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    models = [
        "wizard.resend.mails"
    ]

    for model in models:
        # Crear les diferents taules
        logger.info("Creating table: {}".format(model))
        pool.get(model)._auto_init(cursor, context={'module': 'poweremail_campaign'})
        logger.info("Table created succesfully.")

    # Indiquem les vistes que volem carregar
    views = [
        "wizard/wizard_resend_mails_view.xml"
    ]

    for view in views:
        # Crear les diferents vistes
        logger.info("Updating XML {}".format(view))
        load_data(cursor, 'poweremail_campaign', view, idref=None, mode='update')
        logger.info("XMLs succesfully updatd.")

    load_access_rules_from_model_name(
        cursor, 'poweremail_campaign', [
            'model_wizard_resend_mails_r',
            'model_wizard_resend_mails_w',
            'model_wizard_resend_mails_u'
        ], mode='init'
    )

    logger.info('Migration successful.')


def down(cursor, installed_version):
    pass


migrate = up