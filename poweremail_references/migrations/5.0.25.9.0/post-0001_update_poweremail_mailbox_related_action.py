# -*- coding: utf-8 -*-
import pooler
from tqdm import tqdm


def up(cursor, installed_version):
    if not installed_version:
        return

    pool = pooler.get_pool(cursor.dbname)
    uid = 1
    active_id = 0

    template_o = pool.get('poweremail.templates')
    template_ids = template_o.search(cursor, uid, [('ref_ir_act_window_access', '!=', False)])
    for template_id in tqdm(template_ids):
        template = template_o.simple_browse(cursor, uid, template_id)
        domain = eval(template.ref_ir_act_window_access.domain)
        domain.append(('template_id', '=', template.id))
        domain = str(domain)
        domain = domain.replace("0'", """%d' % active_id""")
        sql = """UPDATE ir_act_window SET domain = %s WHERE id = %d"""
        cursor.execute(sql, (domain, template.ref_ir_act_window_access.id))


def down(cursor, installed_version):
    pass


migrate = up
