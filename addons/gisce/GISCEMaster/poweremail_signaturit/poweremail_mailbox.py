# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class PoweremailMailbox(osv.osv):

    _inherit = 'poweremail.mailbox'

    def get_email_sent_state(self, cursor, uid, context=None):
        return "email_delivered"

    def get_email_opened_state(self, cursor, uid, context=None):
        return self.pool.get("res.config").get(cursor, uid, "signaturit_email_opened_state", "document_opened")

    def _get_certificat_states(self, cursor, uid, context=None):
        res = super(PoweremailMailbox, self)._get_certificat_states(cursor, uid, context=context)
        res += [
            ('email_processed', _(u"Email processat (per ser enviat)")),
            ('email_delivered', _(u"Email enviat")),
            ('email_opened', _(u"Email obert per el receptor")),
            ('email_bounced', _(u"No s'ha pogut enviar el email")),
            ('email_deferred', _(u"No s'ha pogut enviar el email, es fara un reintent")),
            ('documents_opened', _(u"Vista previa dels documents del email oberta")),
            ('document_opened', _(u"Documents del email oberts")),
            ('document_downloaded', _(u"Documents del email descarregats")),
        ]
        return res

    _columns = {
        'certificat_state': fields.selection(_get_certificat_states, 'Estat del mail certificat'),
        'certificat_signature_id': fields.char("Signatureit ID", size=64)
    }

PoweremailMailbox()
