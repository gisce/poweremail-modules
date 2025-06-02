# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class PoweremailTemplateReference(osv.osv):

    _name = 'poweremail.templates'
    _inherit = 'poweremail.templates'

    def create_access_reference(self, cursor, uid, ids, context=None):
        '''create action and value to access mails generated
        directly from referenced objects'''

        action_obj = self.pool.get('ir.actions.act_window')
        value_obj = self.pool.get('ir.values')

        for id in ids:
            tmpl = self.browse(cursor, uid, id)
            src_model = tmpl.object_name.model
            # Action vals
            action_vals = {
                'name': _("%s Mail Access") % tmpl.name,
                'type': 'ir.actions.act_window',
                'res_model': 'poweremail.mailbox',
                'src_model': src_model,
                'view_type': 'form',
                'domain': ("[('reference','=','" +
                           src_model + ",%d'%active_id)]"),
                'view_mode': 'tree,form',
            }
            # If already exists, update action, else create it
            if tmpl.ref_ir_act_window_access:
                action = tmpl.ref_ir_act_window_access
                action.write(action_vals)
                action_id = action.id
            else:
                action_id = action_obj.create(cursor, uid, action_vals)

            #Value vals
            value_vals = {
                'name': _("%s Mail Access") % tmpl.name,
                'model': src_model,
                'key': 'action',
                'key2': 'client_action_relate',
                'value': "ir.actions.act_window,%s" % action_id,
                'object': True,
            }
            # If already exists, update action, else create it
            if tmpl.ref_ir_value_access:
                value = tmpl.ref_ir_value_access
                value.write(value_vals)
                value_id = value.id
            else:
                value_id = value_obj.create(cursor, uid, value_vals)

            tmpl.write({'ref_ir_act_window_access': action_id,
                        'ref_ir_value_access': value_id})

        return True

    def remove_access_reference(self, cursor, uid, ids, context):
        action_obj = self.pool.get('ir.actions.act_window')
        value_obj = self.pool.get('ir.values')

        template_brw = self.pool.get('poweremail.templates').browse(cursor, uid, ids[0])

        if template_brw.ref_ir_act_window_access:
            action_id = template_brw.ref_ir_act_window_access.id
            template_brw.write({'ref_ir_act_window_access': False})
            action_obj.unlink(cursor, uid, action_id)

        if template_brw.ref_ir_value_access:
            value_id = template_brw.ref_ir_value_access.id
            template_brw.write({'ref_ir_value_access': False})
            value_obj.unlink(cursor, uid, value_id)


    _columns = {
        'ref_ir_act_window_access': fields.many2one(
                                        'ir.actions.act_window',
                                        'Access Window Action',
                                        readonly=True),
        'ref_ir_value_access': fields.many2one(
                                        'ir.values',
                                        'Access Button',
                                        readonly=True),
    }

PoweremailTemplateReference()
