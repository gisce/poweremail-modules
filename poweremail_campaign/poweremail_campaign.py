# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv, fields
from osv.osv import except_osv
from poweremail.poweremail_template import get_value
from tools import config
from tools.translate import _


class PoweremailCampaign(osv.osv):

    _name = 'poweremail.campaign'
    _description = "Email Campaign"

    def _ff_created_sent_object(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        campanyes = self.browse(cursor, uid, ids, context=context)
        res = {}
        for campanya in campanyes:
            lines_obj = self.pool.get('poweremail.campaign.line')
            lines_q = lines_obj.q(cursor, uid)
            created_data = lines_q.read(
                ['id'],
                only_active=False
            ).where(
                [('mail_id', '!=', False), ('campaign_id', '=', campanya.id)]
            )
            sent_data = lines_q.read(
                ['id'],
                only_active=False
            ).where(
                [('state', '=', 'sent'), ('campaign_id', '=', campanya.id)]
            )
            total_data = lines_q.read(
                ['id'],
                only_active=False
            ).where(
                [('state', '!=', 'avoid_duplicate'), ('campaign_id', '=', campanya.id)]
            )
            tempval = str(campanya.template_id.object_name.model)
            if not total_data:
                prog_created = 0.0
                prog_sent = 0.0
            else:
                prog_created = (float(len(created_data)) / float(len(total_data))) * 100
                prog_sent = (float(len(sent_data)) / float(len(total_data))) * 100

            if not campanya.template_id or not campanya.template_id.object_name.model:
                tempval = ""

            
            res[campanya.id] = {
                'progress_created': prog_created,
                'progress_sent': prog_sent,
                'template_obj': tempval
            }
        return res

    def update_linies_campanya(self, cursor, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        template_o = self.pool.get('poweremail.templates')
        pm_camp_obj = self.pool.get('poweremail.campaign')
        pm_camp_q = pm_camp_obj.q(cursor, uid)
        pm_camp_line_obj = self.pool.get('poweremail.campaign.line')
        pm_camp_line_q = pm_camp_line_obj.q(cursor, uid)
        mails_unics = set()
        for camp_id in ids:
            pm_camp_vs = pm_camp_q.read(['domain', 'template_id', 'distinct_mails', 'campaign_mode']).where([('id', '=', camp_id)])[0]
            if pm_camp_vs['campaign_mode'] == 'csv':
                raise except_osv(
                    _('Error'),
                    _('CSV campaigns must create lines from the CSV import.')
                )
            line_vs = pm_camp_line_q.read(['id']).where([('campaign_id', '=', camp_id)])
            # Borra línies existents de la campanya
            for line_v in line_vs:
                pm_camp_line_obj.unlink(cursor, uid, line_v['id'], context=context)
            # Recalcula linies aplicant el domain al model de dades
            domain = eval(pm_camp_vs['domain'])
            template_id = pm_camp_vs['template_id']
            if not template_id:
                continue
            template = template_o.browse(cursor, uid, template_id, context=context)
            if template.model_int_name:
                model = str(template.model_int_name)
                model_obj = self.pool.get(model)
                res_ids = model_obj.search(cursor, uid, domain, context=context)

                # Crear campaign line per cada registre trobat
                from tqdm import tqdm
                for record_id in tqdm(res_ids):
                    ref = '{},{}'.format(model, record_id)
                    lang = get_value(
                        cursor, uid, record_id, template.lang, template,
                        context=context
                    )
                    state = 'to_send'
                    if pm_camp_vs['distinct_mails']:
                        email = get_value(
                            cursor, uid, record_id, template.def_to, template,
                            context=context
                        )
                        if email in mails_unics:
                            state = 'avoid_duplicate'
                        else:
                            mails_unics.add(email)

                    params = {
                        'campaign_id': camp_id,
                        'ref': ref,
                        'state': state,
                        'lang': lang != 'False' and lang or config.get('lang', 'en_US')
                    }
                    pm_camp_line_obj.create(cursor, uid, params)
        return True

    def _check_csv_template(self, cursor, uid, campaign, context=None):
        if campaign.campaign_mode != 'csv':
            raise except_osv(
                _('Error'),
                _('CSV import is only available in CSV campaign mode.')
            )
        if not campaign.template_id:
            raise except_osv(_('Error'), _('A template is required.'))
        model = str(campaign.template_id.model_int_name or '')
        if model != 'poweremail.campaign.recipient':
            raise except_osv(
                _('Error'),
                _('CSV campaigns require a template over poweremail.campaign.recipient.')
            )

    def action_preview_csv_import(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        recipient_obj = self.pool.get('poweremail.campaign.recipient')
        for campaign in self.browse(cursor, uid, ids, context=context):
            self._check_csv_template(cursor, uid, campaign, context=context)
            recipients, summary = recipient_obj.parse_csv_data(
                cursor, uid, campaign.id, campaign.csv_file, context=context
            )
            self.write(cursor, uid, campaign.id, {
                'csv_import_summary': recipient_obj.format_import_summary(summary)
            }, context=context)
        return True

    def action_import_csv_recipients(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        recipient_obj = self.pool.get('poweremail.campaign.recipient')
        line_obj = self.pool.get('poweremail.campaign.line')
        for campaign in self.browse(cursor, uid, ids, context=context):
            self._check_csv_template(cursor, uid, campaign, context=context)
            recipients, summary = recipient_obj.parse_csv_data(
                cursor, uid, campaign.id, campaign.csv_file, context=context,
                check_existing=False
            )
            old_line_ids = line_obj.search(
                cursor, uid, [('campaign_id', '=', campaign.id)], context=context
            )
            if old_line_ids:
                line_obj.unlink(cursor, uid, old_line_ids, context=context)
            old_recipient_ids = recipient_obj.search(
                cursor, uid, [('campaign_id', '=', campaign.id)], context=context
            )
            if old_recipient_ids:
                recipient_obj.unlink(
                    cursor, uid, old_recipient_ids, context=context
                )

            source_filename = campaign.csv_filename or ''
            for recipient in recipients:
                recipient['source_filename'] = source_filename
                recipient_id = recipient_obj.create(
                    cursor, uid, recipient, context=context
                )
                if recipient['state'] not in ('valid', 'duplicate'):
                    continue
                line_state = 'to_send'
                if recipient['state'] == 'duplicate' and campaign.distinct_mails:
                    line_state = 'avoid_duplicate'
                line_id = line_obj.create(cursor, uid, {
                    'campaign_id': campaign.id,
                    'ref': 'poweremail.campaign.recipient,%s' % recipient_id,
                    'state': line_state,
                    'lang': recipient['language'] or config.get('lang', 'en_US'),
                    'log': recipient['log'],
                }, context=context)
                recipient_obj.write(cursor, uid, recipient_id, {
                    'campaign_line_id': line_id,
                    'state': recipient['state'] == 'valid' and 'line_created' or 'duplicate',
                }, context=context)
            self.write(cursor, uid, campaign.id, {
                'csv_import_summary': recipient_obj.format_import_summary(summary)
            }, context=context)
        return True

    def send_emails(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        pm_camp_line_obj = self.pool.get('poweremail.campaign.line')
        pm_camp_obj = self.pool.get('poweremail.campaign')
        for camp_id in ids:
            campaign_v = pm_camp_obj.read(
                cursor, uid, camp_id, ['template_id', 'batch'],
                context=context
            )
            dmn = [
                ('campaign_id', '=', camp_id),
                ('state', 'in', ('to_send', 'sending_error'))
            ]
            line_ids = pm_camp_line_obj.search(
                cursor, uid, dmn, limit=campaign_v['batch'] or None,
                context=context
            )
            for line_id in line_ids:
                pm_camp_line_obj.send_mail_from_line(
                    cursor, uid, line_id, campaign_v['template_id'][0],
                    context=context
                )

    _columns = {
        'template_id': fields.many2one('poweremail.templates', 'Template E-mail', required=True),
        'name': fields.char('Name', size=64, required=True),
        'campaign_mode': fields.selection([
            ('objects', 'Objects / Domain'),
            ('csv', 'CSV Recipients'),
        ], 'Campaign Mode', required=True),
        'domain': fields.text('Filter Objects', size=256, required=True),
        'csv_file': fields.binary('CSV File'),
        'csv_filename': fields.char('CSV Filename', size=256),
        'csv_import_summary': fields.text('CSV Import Summary', readonly=True),
        'progress_created': fields.function(_ff_created_sent_object, multi='barra_progres', string='Progress Created', type='float', method=True),
        'progress_sent': fields.function(_ff_created_sent_object, multi='barra_progres', string='Progress Sent', type='float', method=True),
        'create_date': fields.datetime('Create Date', readonly=1),
        'template_obj': fields.function(_ff_created_sent_object, multi='barra_progres', string='Object', type='char', size=64, method=True, readonly=1),
        'batch': fields.integer('Batch', help='Sends the indicated quantity of emails each time the "Send Emails" button is pressed. 0 to send all.'),
        'distinct_mails': fields.boolean('Avoid same email', help='Check to avoid send repeated campaigns to the same email')
    }

    _defaults = {
        'campaign_mode': lambda *a: 'objects',
        'domain': lambda *a: '[]',
        'distinct_mails': lambda *a: False,
    }

PoweremailCampaign()
