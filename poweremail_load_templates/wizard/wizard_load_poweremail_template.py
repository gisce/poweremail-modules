# -*- coding: utf-8 -*-
from osv import fields, osv
from tools import config
import os

class WizardLoadPoweremailTemplate(osv.osv_memory):

    _name = "wizard.load.poweremail.template"

    def load_poweremail_template(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        wiz = self.browse(cursor, uid, ids[0], context=context)
        for source in wiz.template_id.source_ids:
            file_path = "{}/{}".format(
                config['addons_path'], source.source
            )
            if os.path.exists(file_path):
                with open(file_path, "r") as mf:
                    ctx = context.copy()
                    ctx['lang'] = source.lang.code
                    file_contents = mf.read()
                    wiz.template_id.write({'def_body_text': file_contents}, context=ctx)
            else:
                path_split = file_path.split('/')
                raise osv.except_osv(
                    'Error',
                    'The entered file: {} does not exist'.format(path_split[-1])
                )
        return {}

    _columns = {
        'template_id': fields.many2one(
            'poweremail.templates', 'Template', select=1, required=True,
        )
    }


WizardLoadPoweremailTemplate()
