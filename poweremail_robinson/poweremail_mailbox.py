from __future__ import absolute_import
from osv import osv, fields

class PoweremailMailbox(osv.osv):

    _name = "poweremail.mailbox"
    _inherit = "poweremail.mailbox"

    def _folder_selection(self, cursor, uid, context=None):
        folders = super(PoweremailMailbox, self)._folder_selection(cursor, uid, context=context)
        folder_robinson = [('robinson', 'Robinson')]
        return folders + folder_robinson

    _columns = {
        'folder': fields.selection(_folder_selection, 'Folder', required=True),
    }


PoweremailMailbox()