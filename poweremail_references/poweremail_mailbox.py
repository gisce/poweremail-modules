# -*- coding: utf-8 -*-
import json
from osv import osv, fields
import six
from ast import literal_eval
import netsvc

from tools.translate import _

LOGGER = netsvc.Logger()


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

    def _find_error_mails_with_later_success(self, cursor, uid, context=None):
        if context is None:
            context = {}

        res_config = self.pool.get('res.config')
        template_obj = self.pool.get('poweremail.templates')

        configured_template_ids = res_config.get(cursor, uid, 'poweremail_templates_clear_error_on_success', '[]')
        if configured_template_ids == 'all':
            template_ids = template_obj.search(cursor, uid, [], context=context)
        else:
            template_ids = literal_eval(configured_template_ids or '[]')

        if not template_ids:
            return []

        query = """
                SELECT DISTINCT ON (error_mail.id) error_mail.id AS error_mail_id, sent_mail.id  AS sent_mail_id
                FROM poweremail_mailbox AS error_mail
                    JOIN poweremail_mailbox AS sent_mail ON sent_mail.folder = 'sent'
                    AND sent_mail.template_id = error_mail.template_id
                    AND sent_mail.pem_subject = error_mail.pem_subject
                    AND sent_mail.reference = error_mail.reference
                    AND (sent_mail.create_date > error_mail.create_date
                        OR (sent_mail.create_date = error_mail.create_date AND sent_mail.id > error_mail.id)
                    )
                WHERE error_mail.folder = 'error'
                    AND error_mail.template_id IN %s
                    AND error_mail.reference IS NOT NULL
                    AND error_mail.reference != ''
                ORDER BY error_mail.id, sent_mail.create_date, sent_mail.id
                """

        cursor.execute(query, (tuple(template_ids),))
        return cursor.fetchall()

    def clear_errors_with_later_success_mails(self, cursor, uid, context=None):
        """
            Move obsolete error mails to trash when later successful mails are found
        """
        if context is None:
            context = {}

        error_mail_ids = []

        errors_ids = self._find_error_mails_with_later_success(cursor, uid, context=context)
        if errors_ids:
            error_mail_ids = [error_mail_id for error_mail_id, sent_mail_id in errors_ids]
            write_vals = {
                'state': 'na',
                'folder': 'trash',
            }
            self.write(cursor, uid, error_mail_ids, write_vals, context=context)

            for error_mail_id, sent_mail_id in errors_ids:
                message = _('Moved to Trash because a later successful send was detected from mail with ID %s.') % sent_mail_id
                self.historise(cursor, uid, [error_mail_id], message, context=context)

        return error_mail_ids

    def run_mail_scheduler(self, cursor, user, context=None):
        """
        This method is called by Open ERP Scheduler
        to periodically receive & fetch mails
        """
        if context is None:
            context = {}
        super(PoweremailMailbox, self).run_mail_scheduler(cursor, user, context)

        try:
            self.clear_errors_with_later_succcess_mails(cursor, user, context)
        except Exception as e:
            LOGGER.notifyChannel(
                _("Power Email"),
                netsvc.LOG_ERROR,
                _("Error clearing obsolete PowerEmail error mails: %s") % str(e)
            )

    _columns = {
        'reference': fields.reference('Source Object', selection=_get_models,
                                      size=128),
        'meta': fields.text('Meta information')
    }

PoweremailMailbox()
