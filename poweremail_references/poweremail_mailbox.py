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
        records_checked = context.get('records_checked', {})
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
            model_type = ref[0]
            record_id = ref[1]
            if not self.restrict_write_callback_from_previous_emails(cursor, uid, ref, func, vals, context=ctx):
                ids_cbk[model_type] = ids_cbk.get(model_type, []) + [int(record_id)]
                records_checked[model_type] = records_checked.get(model_type, []) + [int(record_id)]
                context.update({
                    'records_checked': records_checked
                })
            ctx['pe_callback_origin_ids'][int(record_id)] = i['id']
            ctx['meta'][int(record_id)] = meta
        for model in ids_cbk:
            src = self.pool.get(model)
            try:
                if vals:
                    getattr(src, self.callbacks[func])(cursor, uid, ids_cbk[model], vals, ctx)
                else:
                    getattr(src, self.callbacks[func])(cursor, uid, ids_cbk[model], ctx)
            except AttributeError:
                pass

    def restrict_write_callback_from_previous_emails(self, cursor, uid, ref, func, vals={}, context=None):
        if context is None:
            context = {}
        records_checked = context.get('records_checked', {})
        restrict = True
        model_type = ref[0]
        record_id = ref[1]
        if (not records_checked.get(model_type, [])
                or (records_checked.get(model_type, []) and int(record_id) not in records_checked[model_type])
                or func != 'write') or 'certificat_state' not in vals.keys():
            restrict = False
        return restrict

    def get_certificate_email_ids_with_same_ref(self, cursor, uid, ref, context=None):
        if context is None:
            context = {}
        email_ids = self.search(cursor, uid, [
            ('certificat', '=', True),
            ('reference', '=', ref)
        ], context=context)
        email_ids.sort(reverse=True)
        return email_ids

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
