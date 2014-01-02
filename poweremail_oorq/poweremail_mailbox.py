# -*- coding: utf-8 -*-
from osv import osv
from oorq.decorators import job


class PoweremailMailbox(osv.osv):
    _name = "poweremail.mailbox"
    _inherit = 'poweremail.mailbox'

    @job(queue='poweremail')
    def send_in_background(self, cursor, uid, ids, context):
        return super(PoweremailMailbox,
                     self).send_this_mail(cursor, uid, ids, context)

    def send_this_mail(self, cursor, uid, ids=None, context=None):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        for mail_id in ids:
            self.send_in_background(cursor, uid, mail_id, context)
        return True

PoweremailMailbox()
