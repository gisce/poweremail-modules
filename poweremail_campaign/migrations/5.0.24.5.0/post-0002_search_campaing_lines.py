# -*- encoding: utf-8 -*-
import logging

import pooler
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)
    uid = 1
    campaign_o = pool.get('poweremail.campaign')
    camp_line_o = pool.get('poweremail.campaign.line')

    logger.info("Searching for campaigns")
    campaign_ids = campaign_o.search(cursor, uid, [])

    logger.info("Searching campaign lines")

    if len(campaign_ids):
        for campaign_id in campaign_ids:
            camp_lines_id = camp_line_o.search(cursor, uid, [('campaign_id', '=', campaign_id)])
            if len(camp_lines_id):
                campaign_o.write(cursor, uid, campaign_id, {'n_registres': len(camp_lines_id)})
    else:
        logger.info("Not campaings")


def down(cursor, installed_version):
    pass


migrate = up