# -*- coding: utf-8 -*-
import pooler
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    pool = pooler.get_pool(cursor.dbname)

    # Crear les diferents taules
    pool.get('poweremail.campaign')._auto_init(cursor, context={'module': 'poweremail_campaign'})
    # Indiquem les vistes que volem carregar

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