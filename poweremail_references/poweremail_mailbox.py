# -*- coding: utf-8 -*-
import json
from osv import osv, fields
import six


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
        if context is None:
            context = {}
        data = self.read(cursor, uid, ids, ['reference', 'meta'])
        if not isinstance(data, list):
            data = [data]
        ids_cbk = {}
        ctx = context.copy()
        ctx['pe_callback_origin_ids'] = {}
        ctx['meta'] = {}
        if vals:
            init_meta = vals.get('meta', {}) or {}
            if isinstance(init_meta, six.string_types):
                init_meta = json.loads(init_meta)
        else:
            init_meta = {}
        for i in data:
            if not i['reference']:
                continue
            meta_vals = i['meta']
            if meta_vals:
                meta = json.loads(meta_vals)
                meta.update(init_meta)
            else:
                meta = {}

            ref = i['reference'].split(',')
            ids_cbk[ref[0]] = ids_cbk.get(ref[0], []) + [int(ref[1])]
            ctx['pe_callback_origin_ids'][int(ref[1])] = i['id']
            ctx['meta'][int(ref[1])] = meta
        for model in ids_cbk:
            src = self.pool.get(model)
            try:
                if vals:
                    getattr(src, self.callbacks[func])(cursor, uid,
                                                ids_cbk[model], vals, ctx)
                else:
                    getattr(src, self.callbacks[func])(cursor, uid,
                                                ids_cbk[model], ctx)
            except AttributeError:
                pass

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}
        src_id = context.get('src_rec_id', False)
        if src_id:
            upd_vals = {
                'reference': '%s,%d' % (context['src_model'], src_id)
            }
            meta = context.get('meta')
            if meta:
                upd_vals['meta'] = json.dumps(context['meta'])
            vals.update(upd_vals)
        pe_id = super(PoweremailMailbox,
                      self).create(cursor, uid, vals, context)
        self.poweremail_callback(cursor, uid, pe_id, 'create', vals, context)
        return pe_id

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}
        meta = context.get('meta')
        if meta:
            vals['meta'] = json.dumps(meta)
        self.poweremail_callback(cursor, uid, ids, 'write', vals, context)
        ret = super(PoweremailMailbox, self).write(cursor, uid, ids, vals, context)
        return ret

    def unlink(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        self.poweremail_callback(cursor, uid, ids, 'unlink', context=context)
        ret = super(PoweremailMailbox, self).unlink(cursor, uid, ids, context)
        return ret

    def _get_models(self, cursor, uid, context=None):
        if context is None:
            context = {}
        cursor.execute('select m.model, m.name from ir_model m order by m.model')
        return cursor.fetchall()

    _columns = {
        'reference': fields.reference('Source Object', selection=_get_models,
                                      size=128),
        'meta': fields.text('Meta information')
    }

PoweremailMailbox()
