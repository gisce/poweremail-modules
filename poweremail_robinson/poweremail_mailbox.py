from __future__ import absolute_import
from osv import osv, fields

class PoweremailMailbox(osv.osv):
    _name = "poweremail.mailbox"
    _inherits = "poweremail.mailbox"

    def _folder_selection(self, cursor, uid, context=None):
        folders = super(PoweremailMailbox, self)._folder_selection
        folder_robinson = [('robinson', 'Robinson')]
        return folders + folder_robinson

PoweremailMailbox()