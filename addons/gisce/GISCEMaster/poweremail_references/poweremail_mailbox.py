# -*- coding: utf-8 -*-

from osv import osv, fields

class PoweremailMailbox(osv.osv):
    _name = "poweremail.mailbox"
    _inherit = "poweremail.mailbox"

    callbacks = {'create': 'poweremail_create_callback',
                 'write': 'poweremail_write_callback',
                 'unlink': 'poweremail_unlink_callback',
                }

    def poweremail_callback(self, cursor, uid, ids, func, vals=None, context=None):
        """Crida el callback callbacks[func] del reference de ids
        """
        data = self.read(cursor, uid, ids, ['reference'])
        if not isinstance(data, list):
            data = [data]
        ids_cbk = {}
        for i in data:
            if not i['reference']:
                continue
            ref = i['reference'].split(',')
            ids_cbk[ref[0]] = ids_cbk.get(ref[0], []) + [int(ref[1])]
        for model in ids_cbk:
            src = self.pool.get(model)
            try:
                if vals:
                    getattr(src, self.callbacks[func])(cursor, uid,
                                                ids_cbk[model], vals, context)
                else:
                    getattr(src, self.callbacks[func])(cursor, uid,
                                                ids_cbk[model], context)
            except:
                pass

    def create(self, cursor, uid, vals, context=None):
        pe_id = super(PoweremailMailbox,
                     self).create(cursor, uid, vals, context)
        src_id = context.get('src_rec_id', False)
        if src_id:
            self.write(cursor, uid, pe_id,
                    {'reference': '%s,%d' % (context['src_model'], src_id)})
            self.poweremail_callback(cursor, uid, pe_id, 'create', vals,
                                     context)
        return pe_id

    def write(self, cursor, uid, ids, vals, context=None):
        self.poweremail_callback(cursor, uid, ids, 'write', vals, context)
        ret = super(PoweremailMailbox,
                     self).write(cursor, uid, ids, vals, context)
        return ret

    def unlink(self, cursor, uid, ids, context=None):
        self.poweremail_callback(cursor, uid, ids, 'unlink', context)
        ret = super(PoweremailMailbox,
                     self).unlink(cursor, uid, ids, context)
        return ret

    def _get_models(self, cursor, uid, context={}):
        cursor.execute('select m.model, m.name from ir_model m order by m.model')
        return cursor.fetchall()

    _columns = {
        'reference': fields.reference('Source Object', selection=_get_models,
                                      size=128),
    }

PoweremailMailbox()
