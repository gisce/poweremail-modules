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
        records_checked = context.get('records_checked', [])
        if vals:
            init_meta = vals.get('meta', {}) or {}
            if isinstance(init_meta, basestring):
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
        use_callback = True
        for model in ids_cbk:
            src = self.pool.get(model)
            try:
                if not records_checked or (records_checked and ids_cbk not in records_checked):
                    # Si la llista de records comprovats es buida, agafem tots els emails de la factura relacionada
                    # per poder tenir una visió global, ja que si es crida el mètode amb un sol email, pot ser que tingui
                    # mes emails posteriors i que no s'hagi de cridar el callback
                    if not records_checked:
                        certificate_email_ids = self.get_certificate_email_ids_with_same_ref(cursor, uid, data['reference'], context=context)
                        # Si l'id de l'email que estem processant es més petit que el major referent al mateix objecte
                        # Vol dir que hi ha un email posterior, per tant no cridem el callback per un email anterior.
                        if ids[0] < certificate_email_ids[0]:
                            use_callback = False
                    if use_callback:
                        if vals:
                            getattr(src, self.callbacks[func])(cursor, uid, ids_cbk[model], vals, ctx)
                        else:
                            getattr(src, self.callbacks[func])(cursor, uid, ids_cbk[model], ctx)
                        records_checked.append(ids_cbk)
                        context.update({
                            'records_checked': records_checked,
                        })
            except AttributeError:
                pass

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

    def validate_referenced_object_exists(self, cursor, uid, id, vals, context=None):
        ret = True
        fields = ['reference']
        result = self._read_flat(cursor, uid, id, fields, context, '_classic_read')
        for r in result:
            if 'reference' in r.keys():
                v = r['reference']
                if v:
                    model, ref_id = v.split(',')
                    ref_obj = self.pool.get(model)

                    if ref_id != '0':
                        id_exist = ref_obj.search(cursor, 1, [
                            ('id', '=', ref_id)
                        ], context={'active_test': False})
                        if not id_exist:
                            ret = False
        return ret

    def read(self, cursor, uid, ids, fields=None, context=None, load='_classic_read'):
        if context is None:
            context = {}
        select = ids
        if isinstance(ids, six.integer_types):
            select = [ids]
        valid_select = []
        for id in select:
            res = self.validate_referenced_object_exists(cursor, uid, [id], fields, context=None)
            if res:
                valid_select.append(id)
            else:
                super(PoweremailMailbox,
                        self).unlink(cursor, uid, [id], context)
        ret = []
        if valid_select:
            ret = super(PoweremailMailbox,
                        self).read(cursor, uid, valid_select, fields, context, load)
        if isinstance(ids, six.integer_types) and ret:
            return ret[0]
        return ret

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}
        meta = context.get('meta')
        if meta:
            vals['meta'] = json.dumps(meta)
        self.poweremail_callback(cursor, uid, ids, 'write', vals, context)
        ret = super(PoweremailMailbox,
                     self).write(cursor, uid, ids, vals, context)
        return ret

    def unlink(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        self.poweremail_callback(cursor, uid, ids, 'unlink', context=context)
        ret = super(PoweremailMailbox,
                     self).unlink(cursor, uid, ids, context)
        return ret

    def _get_models(self, cursor, uid, context={}):
        cursor.execute('select m.model, m.name from ir_model m order by m.model')
        return cursor.fetchall()

    _columns = {
        'reference': fields.reference('Source Object', selection=_get_models,
                                      size=128),
        'meta': fields.text('Meta information')
    }

PoweremailMailbox()
