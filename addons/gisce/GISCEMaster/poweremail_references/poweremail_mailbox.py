# -*- coding: utf-8 -*-

from osv import osv, fields

class PoweremailMailbox(osv.osv):
    _name = "poweremail.mailbox"
    _inherit = "poweremail.mailbox"

    def create(self, cursor, uid, vals, context=None):
        import pdb; pdb.set_trace()
        return super(GiscedataFacturacioFacturaLinia,
                     self).create(cursor, uid, values, context)

    def _get_models(self, cursor, uid, context={}):
        cursor.execute('select m.model, m.name from ir_model order by m.model')
        return cursor.fetchall()

    _columns = {
        'reference': fields.reference('Source Object', selection=_get_models, size=128),
    }

PoweremailMailbox()
