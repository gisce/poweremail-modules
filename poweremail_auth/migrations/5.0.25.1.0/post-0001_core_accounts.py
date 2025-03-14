# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    models = ["poweremail.core_accounts"]

    for model in models:
        logger.info("Creating table: {}".format(model))
        pool.get(model)._auto_init(cursor, context={'module': 'poweremail_auth'})
        logger.info("Table created succesfully.")


def down(cursor, installed_version):
    pass


migrate = up