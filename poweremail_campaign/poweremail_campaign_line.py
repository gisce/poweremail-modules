# -*- coding: utf-8 -*-

from osv import osv, fields
from osv.osv import TransactionExecute
from tools.translate import _

class PoweremailCampaignLine(osv.osv):

    _name = 'poweremail.campaign.line'

    callbacks = {'create': 'poweremail_create_callback',
                 'write': 'poweremail_write_callback',
                 'unlink': 'poweremail_unlink_callback',
                 }

    def _get_ref(self, cursor, uid, context=None):
        if context is None:
            context = {}
        obj = self.pool.get('ir.model')
        ids = obj.search(cursor, uid, [], context=context)
        res = obj.read(cursor, uid, ids, ['model', 'name'], context)
        return [(r['model'], r['name']) for r in res]

    def poweremail_callback(self, cursor, uid, ids, func, vals=None, context=None):
        """Crida el callback callbacks[func] del reference de ids
        """
        if context is None:
            context = {}
        data = self.read(cursor, uid, ids, ['ref'])
        if not isinstance(data, list):
            data = [data]
        ids_cbk = {}
        ctx = context.copy()
        ctx['pe_callback_origin_ids'] = {}
        for i in data:
            if not i['ref']:
                continue
            meta = {}
            ref = i['ref'].split(',')
            ids_cbk[ref[0]] = ids_cbk.get(ref[0], []) + [int(ref[1])]
            ctx['pe_callback_origin_ids'][int(ref[1])] = i['id']
            ctx['meta'][int(ref[1])] = meta
        for model in ids_cbk:
            src = self.pool.get(model)
            try:
                if vals:
                    getattr(src, self.callbacks[func])(cursor, uid, ids_cbk[model], vals, ctx)
                else:
                    getattr(src, self.callbacks[func])(cursor, uid, ids_cbk[model], ctx)
            except AttributeError:
                pass

    def poweremail_create_callback(self, cursor, uid, ids, vals, context=None):
        #ids -> ids de les linies
        #vals['folder'] -> si hi posa "create", marcar com a enviada la factura (cridar powermail_create_callback)
        self.poweremail_callback(cursor, uid, ids, 'create', vals, context=context)
        self.write(cursor, uid, ids, {'mail_id': context['pe_callback_origin_ids'][ids[0]]})

    def poweremail_write_callback(self, cursor, uid, ids, vals, context=None):
        # ids -> ids de les linies
        # vals['folder'] -> si hi posa "sent", marcar com a enviada la factura (cridar powermail_write_callback)
        self.poweremail_callback(cursor, uid, ids, 'write', vals, context=context)
        if vals.get('folder', False) and vals.get('folder', False) == 'sent':
            self.write(cursor, uid, ids, {'state': 'sent'})

    def poweremail_unlink_callback(self, cursor, uid, ids, context=None):
        self.poweremail_callback(cursor, uid, ids, 'unlink', context=context)
        self.write(cursor, uid, ids, {'state': 'to_send'})

    def send_mail_from_line(self, cursor, uid, line_id, template, context=None):
        pm_template_obj = TransactionExecute(cursor.dbname, uid, 'poweremail.templates')
        self_obj = TransactionExecute(cursor.dbname, uid, 'poweremail.campaign.line')
        line_v = self.read(cursor, uid, line_id, ['state', 'mail_id'])
        if line_v['state'] in ('sent', 'sending') and line_v['mail_id']:
            return
        ref_aux = self.read(cursor, uid, line_id, ['ref'])['ref']
        id_aux = int(ref_aux.split(",")[1])
        try:
            context['src_rec_id'] = line_id
            context['src_model'] = self._name
            self_obj.write(line_id, {'state': 'sending'})
            pm_template_obj.generate_mail(template, id_aux, context=context)
        except Exception as e:
            self_obj.write(line_id, {'state': 'sending_error', 'log': str(e) + "\n"})
        return True

    def generate_mail_button(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        ctx = context.copy()
        ctx['prefetch'] = False
        line_id = self.browse(cursor, uid, ids, context=ctx)
        template = line_id.campaign_id.template_id
        return self.send_mail_from_line(cursor, uid, ids, template.id, context=context)

    STATE_SELECTION = [('to_send', 'To Send'),
                       ('sending', 'Sending'),
                       ('sending_error', 'Sending Error'),
                       ('sent', 'Sent')]

    _rec_name = 'campaign_id'

    _columns = {
        'campaign_id': fields.many2one(
            'poweremail.campaign', 'Campaign', required=True
        ),
        'ref': fields.reference('Reference', selection=_get_ref, size=128, select=1),
        'mail_id': fields.many2one(
            'poweremail.mailbox', 'Mail', ondelete='set null'
        ),
        'state': fields.selection(STATE_SELECTION, 'State'),
        'log': fields.text('Line Log'),
    }

    _defaults = {
        'state': lambda *a: 'to_send',
    }


PoweremailCampaignLine()


class PoweremailCampaign(osv.osv):

    _name = 'poweremail.campaign'
    _inherit = 'poweremail.campaign'

    _columns = {
        'reference_ids': fields.one2many('poweremail.campaign.line', 'campaign_id', 'Campaign Line'),
    }


PoweremailCampaign()
