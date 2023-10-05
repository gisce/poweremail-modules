# -*- coding: utf-8 -*-The entered file does not exist
from osv import osv, fields


class poweremail_templates(osv.osv):

    _name = "poweremail.templates"
    _inherit = "poweremail.templates"
    _columns = {
        'source_ids': fields.one2many(
            'poweremail.templates.source', 'template_id', 'Sources'
        )
    }


poweremail_templates()
