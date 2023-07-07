# -*- coding: utf-8 -*-
from osv import osv, fields


class PoweremailTemplatesSource(osv.osv):

    _name = "poweremail.templates.source"
    _description = "Poweremail templates source"
    _columns = {
        'template_id': fields.many2one(
            'poweremail.templates', 'Template', select=1, required=True
        ),
        'source': fields.char('Source', size=64, required=True),
        'lang': fields.many2one(
            'res.lang', 'Language', select=1, required=True
        ),
    }


PoweremailTemplatesSource()
