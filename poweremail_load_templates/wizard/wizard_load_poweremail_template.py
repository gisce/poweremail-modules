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
        poweremail_template_obj = self.pool.get('poweremail.templates')
        poweremail_template_source_obj = self.pool.get(
            'poweremail.templates.source'
        )
        res_lang_obj = self.pool.get('res.lang')
        # Read source ids
        source_v = poweremail_template_obj.read(
            cursor, uid, ids[0], ['source_ids'], context=context
        )
        source_ids = source_v['source_ids']
        for source_id in source_ids:
            template_source_v = poweremail_template_source_obj.read(
                cursor, uid, source_id, [
                    'template_id', 'source', 'lang'
                ],
                context=context
            )
            file_path = "{}/{}".format(
                config['addons_path'], template_source_v['source']
            )
            if os.path.exists(file_path):
                with open(file_path, "r") as mf:
                    ctx = context.copy()
                    res_lang_v = res_lang_obj.read(
                        cursor, uid, template_source_v['lang'][0], [
                            'code'
                        ],
                        context=context
                    )
                    ctx['lang'] = res_lang_v['code']
                    file_contents = mf.read()
                    poweremail_template_obj.write(
                        cursor, uid, template_source_v['template_id'][0], {
                            'def_body_text': file_contents
                        },
                        context=ctx
                    )
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
