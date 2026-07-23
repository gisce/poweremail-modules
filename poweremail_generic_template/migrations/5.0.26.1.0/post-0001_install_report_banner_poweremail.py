# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import install_modules
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    cursor.execute(
        'SELECT * FROM ir_module_module WHERE name=%s AND state=%s',
        ('report_banner_poweremail', 'uninstalled')
    )
    if cursor.fetchone():
        logger.info('Instal·lem el modul de report_banner_poweremail')
        install_modules(cursor, 'report_banner_poweremail')
        logger.info('Instal·lació completada!')
    else:
        logger.info(
            "El mòdul report_banner_poweremail ja està instal·lat o "
            "no existeix"
        )


def down(cursor, installed_version):
    pass

migrate = up