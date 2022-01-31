# -*- coding: utf-8 -*-

from osv import osv


class WizardPoweremailCampaign(osv.osv_memory):

    _name = 'wizard.poweremail.campaign'

    def action_get_registres_campaign(self, cursor, uid, ids, context=None):
        active_id = context['active_id']
        pm_camp_obj = self.pool.get('poweremail.campaign')
        pm_camp_brw = pm_camp_obj.browse(cursor, uid, active_id)
        nom = ""
        if pm_camp_brw.name:
            nom = pm_camp_brw.name
        model = pm_camp_brw.template_id.model_int_name
        pm_camp_lines_ids = []
        for line_brw in pm_camp_brw.reference_ids:
            id = int(line_brw.ref.split(",")[1])
            pm_camp_lines_ids.append(id)

        return {
            'name': 'Poweremail Campaign Lines %s' % str(nom),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': str(model),
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': "[('id', 'in', %s)]" % str(tuple(pm_camp_lines_ids)),
        }

WizardPoweremailCampaign()
