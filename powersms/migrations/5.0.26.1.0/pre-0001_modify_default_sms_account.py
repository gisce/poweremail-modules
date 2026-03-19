# -*- coding: utf-8 -*-
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    cursor.execute("SELECT id, res_id from ir_model_data WHERE name = 'sms_account_som' and model = 'powersms.core_accounts'")
    row = cursor.fetchone()

    if row:
        logger.info('Updating default SMS core account...')
        ir_model_data_id = row[0]
        powersms_core_account_id = row[1]
        cursor.execute("""
            UPDATE ir_model_data SET name = 'default_sms_account' where id = %s
        """, (ir_model_data_id,))

        cursor.execute("SELECT name from res_company order by id asc limit 1")
        company_row = cursor.fetchone()
        company_name = company_row[0] if company_row else 'Companyia'
        cursor.execute("""
            UPDATE powersms_core_accounts SET name = %s where id = %s
        """, (company_name, powersms_core_account_id,))

        cursor.execute("SELECT res_id from ir_model_data WHERE name = 'sms_template_factura_impagada'")
        row = cursor.fetchone()
        if row:
            logger.info('Updating company_name from default powersms template for unpaid invoices...')
            powersms_template_id = row[0]
            cursor.execute("""
                UPDATE powersms_templates SET def_from = %s where id = %s
            """, (company_name, powersms_template_id,))

    logger.info('Migration completed!')

def down(cursor, installed_version):
    pass


migrate = up