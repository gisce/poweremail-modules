# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    ##UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA##
    logger.info("Creating table: poweremail.campaign")
    pool.get("poweremail.campaign")._auto_init(cursor, context={'module': 'poweremail_campaign'})
    logger.info("Table created succesfully.")

def down(cursor, installed_version):
    pass


migrate = up
