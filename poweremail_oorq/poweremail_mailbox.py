# -*- coding: utf-8 -*-
from osv import osv
from oorq.decorators import job
from tools import config


class PoweremailMailbox(osv.osv):
    _name = "poweremail.mailbox"
    _inherit = 'poweremail.mailbox'

    @job(queue=config.get('poweremail_sender_queue', 'poweremail'))
    def send_in_background(self, cursor, uid, ids, context):
        return super(PoweremailMailbox,
                     self).send_this_mail(cursor, uid, ids, context)

    @job(queue=config.get('poweremail_sender_queue', 'poweremail'), at_front=True)
    def send_in_background_at_front(self, cursor, uid, ids, context):
        return super(PoweremailMailbox,
                     self).send_this_mail(cursor, uid, ids, context)

    def send_this_mail(self, cursor, uid, ids=None, context=None):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        for mail in self.read(cursor, uid, ids, ['priority']):
            if mail['priority'] == '2':
                method = getattr(self, 'send_in_background_at_front')
            else:
                method = getattr(self, 'send_in_background')
            method(cursor, uid, [mail['id']], context)
        return True

PoweremailMailbox()
