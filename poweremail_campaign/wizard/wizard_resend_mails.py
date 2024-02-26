# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardResendMails(osv.osv_memory):

    _name = 'wizard.resend.mails'

    def send_mails(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        # Aquest mètode el que fa és posar els correus un altre cop
        # a la carpeta de outbox, d'aquesta forma els correus ja es
        # tornaran a enviar automàticament.
        pw_mail_obj = self.pool.get('poweremail.mailbox')
        pw_line_obj = self.pool.get('poweremail.campaign.line')

        lines_ids = self.read(cursor, uid, ids, ['lines_ids'])[0]['lines_ids']
        mail_ids = [x['mail_id'][0] for x in pw_line_obj.read(cursor, uid, lines_ids, ['mail_id'])]
        pw_mail_obj.write(cursor, uid, mail_ids, {'folder': 'outbox'})

        return {}

    def onchange_domain(self, cursor, uid, ids, line_ids, context=None):
        if context is None:
            context = {}

        pw_line_obj = self.pool.get('poweremail.campaign.line')

        res = {'domain': {}}
        pw_camp_ids = context.get('active_ids', [])
        pw_line_ids = pw_line_obj.search(cursor, uid, [
            ('campaign_id', 'in', pw_camp_ids),
            ('state', '=', 'sent')
        ])

        res['domain'].update(
            {'lines_ids': [('id', 'in', pw_line_ids)]}
        )

        return res

    _columns = {
        'state': fields.char('State', size=10),
        'lines_ids': fields.many2many(
            'poweremail.campaign.line',
            'poweremail_lines_on_campaign',
            'wizard_id', 'line_id',
            'Poweremails Campaign Lines'
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }


WizardResendMails()
