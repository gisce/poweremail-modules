# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields
from tools.translate import _
from datetime import datetime


class PoweremailMailbox(osv.osv):

    _inherit = 'poweremail.mailbox'

    def update_poweremail_certificat_state(self, cursor, uid, ids, context=None):
        res = super(PoweremailMailbox, self).update_poweremail_certificat_state(cursor, uid, ids, context=context)
        from poweremail_signaturit.poweremail_core import get_signaturit_client
        client = get_signaturit_client()
        # Actualitzarem l'estat de tots els mails que el seu certificat_state no sigui l'estat "get_email_opened_state"
        # ni que siguin erronis (estat "email_bounced"). Si l'email ja l'ha obert el client la resta de la info no ens
        # interessa i si el email esta en error tampoc ens interesa perque no es moura d'alla
        final_certificat_state = self.get_email_opened_state(cursor, uid)
        pwids = self.search(cursor, uid, [
            ('certificat', '=', True), ('certificat_state', 'not in', [final_certificat_state, 'email_bounced'])
        ])
        self.write(cursor, uid, pwids, {'certificat_update_datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        for poweremail_info in self.read(cursor, uid, pwids, ['certificat_signature_id']):
            res = client.get_email(poweremail_info['certificat_signature_id'])
            if "id" not in res:
                continue
            email_events = []
            for certificate in res.get("certificates", []):  # Hauria de ser nomes 1 pero bueno
                for event in certificate.get("events", []):  # Ens guardem tots els events que ha tingut el email
                    email_events.append((event['created_at'], event["type"]))
            # Si un dels events es que s'ha arrivat al estat get_email_opened_state, ja en tenim prou amb aixo
            if final_certificat_state in [x[1] for x in email_events]:
                certificat_state_to_write = final_certificat_state
            # Si no tenim lestat final, l'estat mes recent
            else:
                certificat_state_to_write = max(email_events, key=lambda x: x[0])[1]
            self.write(cursor, uid, poweremail_info['id'], {'certificat_state': certificat_state_to_write})
        return res

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
