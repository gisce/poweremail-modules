# -*- coding: utf-8 -*-

from osv import osv, fields
from osv.osv import TransactionExecute
from tools.translate import _


class PoweremailCampaign(osv.osv):

    _name = 'poweremail.campaign'
    _description = "Email Campaign"

    def _ff_created(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        campanyes = self.browse(cursor, uid, ids, context=context)
        res = {}
        for campanya in campanyes:
            total = []
            created = []
            for line in campanya.reference_ids:
                if line.mail_id:
                    created.append(line.id)
                total.append(line.id)
            if not total:
                res[campanya.id] = 0.0
            else:
                res[campanya.id] = (float(len(created)) / float(len(total))) * 100
        return res

    def _ff_sent(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        total = []
        sent = []
        campanyes = self.browse(cursor, uid, ids, context)
        res = {}
        for campanya in campanyes:
            for line in campanya.reference_ids:
                if line.state == 'sent':
                    sent.append(line.id)
                total.append(line.id)
            if not total:
                res[campanya.id] = 0.0
            else:
                res[campanya.id] = (float(len(sent)) / float(len(total))) * 100
        return res

    def _ff_object(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        campanyes = self.browse(cursor, uid, ids, context)
        res = {}
        for campanya in campanyes:
            if not campanya.template_id or not campanya.template_id.object_name.model:
                res[campanya.id] = ""
            else:
                res[campanya.id] = str(campanya.template_id.object_name.model)
        return res

    def update_linies_campanya(self, cursor, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        pm_camp_obj = self.pool.get('poweremail.campaign')
        pm_camp_line_obj = self.pool.get('poweremail.campaign.line')
        for camp_id in ids:
            pm_camp_brw = pm_camp_obj.browse(cursor, uid, camp_id)
            #Borra línies existents de la campanya
            for line_id in pm_camp_brw.reference_ids:
                pm_camp_line_obj.unlink(cursor, uid, line_id.id)
            #Recalcula linies aplicant el domain al model de dades
            domain = eval(pm_camp_brw.domain)
            if pm_camp_brw.template_id and pm_camp_brw.template_id.model_int_name:
                model = str(pm_camp_brw.template_id.model_int_name)
                model_obj = self.pool.get(model)
                res_ids = model_obj.search(cursor, uid, domain)
                #Crear campaign line per cada registre trobat
                for id in res_ids:
                    ref = model+','+str(id)
                    params = {
                        'campaign_id': camp_id,
                        'ref': ref,
                        'state': 'to_send',
                    }
                    pm_camp_line_obj.create(cursor, uid, params)

    def send_emails(self, cursor, uid, ids, context):
        if not isinstance(ids, list):
            ids = [ids]
        pm_camp_line_obj = self.pool.get('poweremail.campaign.line')
        pm_camp_obj = self.pool.get('poweremail.campaign')
        for camp_id in ids:
            pm_camp_brw = pm_camp_obj.browse(cursor, uid, camp_id)
            references_ids = pm_camp_brw.reference_ids
            template = pm_camp_brw.template_id.id
            for id_brw in references_ids:
                pm_camp_line_obj.send_mail_from_line(cursor, uid, id_brw.id, template, context=context)

    _columns = {
        'template_id': fields.many2one('poweremail.templates', 'Template E-mail', required=True),
        'name': fields.char('Name', size=64, required=True),
        'domain': fields.text('Filter Objects', size=256, required=True),
        'progress_created': fields.function(_ff_created, string='Progress Created', type='float', method=True),
        'progress_sent': fields.function(_ff_sent, string='Progress Sent', type='float', method=True),
        'create_date': fields.datetime('Create Date', readonly=1),
        'template_obj': fields.function(_ff_object, string='Object', type='char', size=64, method=True, readonly=1),
    }

    _defaults = {
        'domain': lambda *a: '[]',
    }

PoweremailCampaign()