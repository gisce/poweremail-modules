# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import add_columns, column_exists


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info('Increasing size of powersms.templates name from 100 to 200')
    cursor.execute('ALTER TABLE powersms_templates ALTER COLUMN name type varchar(200)')
    logger.info('Migration successfully completed')



def down(cursor, installed_version):
    pass


migrate = up