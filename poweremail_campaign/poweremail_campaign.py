# -*- coding: utf-8 -*-

from osv import osv, fields
from poweremail.poweremail_template import get_value
from tools import config


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
            pm_camp_vs = pm_camp_q.read(['domain', 'template_id', 'distinct_mails']).where([('id', '=', camp_id)])[0]
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
        'domain': fields.text('Filter Objects', size=256, required=True),
        'progress_created': fields.function(_ff_created_sent_object, multi='barra_progres', string='Progress Created', type='float', method=True),
        'progress_sent': fields.function(_ff_created_sent_object, multi='barra_progres', string='Progress Sent', type='float', method=True),
        'create_date': fields.datetime('Create Date', readonly=1),
        'template_obj': fields.function(_ff_created_sent_object, multi='barra_progres', string='Object', type='char', size=64, method=True, readonly=1),
        'batch': fields.integer('Batch', help='Sends the indicated quantity of emails each time the "Send Emails" button is pressed. 0 to send all.'),
        'distinct_mails': fields.boolean('Avoid same email', help='Check to avoid send repeated campaigns to the same email')
    }

    _defaults = {
        'domain': lambda *a: '[]',
        'distinct_mails': lambda *a: False,
    }

PoweremailCampaign()
