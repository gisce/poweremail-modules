# -*- coding: utf-8 -*-

from osv import osv, fields

class PoweremailMailbox(osv.osv):
    _name = "poweremail.mailbox"
    _inherit = "poweremail.mailbox"

    def create(self, cursor, uid, vals, context=None):
        pe_id = super(PoweremailMailbox,
                     self).create(cursor, uid, vals, context)
        src_id = context.get('src_rec_id', False)
        if src_id:
           self.write(cursor, uid, pe_id, 
                    {'reference': '%s,%d' % (context['src_model'], src_id)})
        return pe_id

    def _get_models(self, cursor, uid, context={}):
        cursor.execute('select m.model, m.name from ir_model m order by m.model')
        return cursor.fetchall()

    _columns = {
        'reference': fields.reference('Source Object', selection=_get_models,
                                      size=128),
    }

PoweremailMailbox()
