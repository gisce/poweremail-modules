# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML")
    record_id = "signaturit_email_request_type"
    load_data_records(
        cursor, 'poweremail_signaturit', "poweremail_mailbox_data.xml", [record_id], mode='update'
    )
    logger.info("XML succesfully updatded")


def down(cursor, installed_version):
    pass


migrate = up
