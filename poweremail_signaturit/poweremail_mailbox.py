# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

import pooler
from psycopg2.errors import LockNotAvailable
from sql import For
from osv import osv, fields
from tools.translate import _
from datetime import datetime

from poweremail_signaturit.poweremail_core import get_signaturit_client
from base64 import b64encode

SIGNATURIT_STATES_ORDER = {
    'email_processed': 10,
    'email_delivered': 20,
    'email_bounced': 30,
    'email_deferred': 40,
    'reminder_email_processed': 50,
    'reminder_email_delivered': 60,
    'sms_processed': 70,
    'sms_delivered': 80,
    'password_sms_processed': 90,
    'password_sms_delivered': 100,
    'document_opened': 110,
    'document_signed': 120,
    'document_completed': 130,
    'audit_trail_completed': 140,
    'document_declined': 150,
    'document_expired': 160,
    'document_canceled': 170,
    'photo_added': 180,
    'voice_added': 190,
    'file_added': 200,
    'photo_id_added': 210,
}


class PoweremailMailbox(osv.osv):

    _inherit = 'poweremail.mailbox'

    def get_signaturit_client(self, cursor, uid, pw_id, context=None):
        if isinstance(pw_id, (list, tuple)):
            pw_id = pw_id[0]
        pem_account_id = self.read(cursor, uid, pw_id, ['pem_account_id'], context=context)['pem_account_id'][0]
        return self.pool.get("poweremail.core_accounts").get_signaturit_client(cursor, uid, pem_account_id, context=context)

    def update_poweremail_certificate(
            self, cursor, uid, pe_id, final_certificat_state,  context=None):
        if context is None:
            context = {}
        self_q = self.q(cursor, uid)
        try:
            q_sql = self_q.select(
                ['id', 'certificat_signature_id', 'certificat_state'], for_=For('UPDATE', nowait=True)
            ).where([('id', '=', pe_id)])
            cursor.execute(*q_sql)
            poweremail_info = cursor.dictfetchone()
        except LockNotAvailable:
            return False
        client = self.get_signaturit_client(cursor, uid, pe_id, context=context)
        res = client.get_email(poweremail_info['certificat_signature_id'])
        if "id" not in res:
            return False
        email_events = []
        for certificate in res.get("certificates", []):  # Hauria de ser nomes 1 pero bueno
            for event in certificate.get("events", []):  # Ens guardem tots els events que ha tingut el email
                email_events.append((event['created_at'], event["type"]))
        if not email_events:
            return False
        # Si un dels events es que s'ha arrivat al estat get_email_opened_state, ja en tenim prou amb aixo
        if final_certificat_state in [x[1] for x in email_events]:
            certificat_state_to_write = final_certificat_state
        # Si no tenim lestat final, l'estat mes recent
        else:
            # Ordenem per datetime, i si es igual, per prioritats d'estats
            certificat_state_to_write = max(email_events, key=lambda x: (x[0], SIGNATURIT_STATES_ORDER.get(x[1], -1)))[1]
        if poweremail_info['certificat_state'] != certificat_state_to_write:
            self.write(cursor, uid, poweremail_info['id'],{'certificat_state': certificat_state_to_write})
        return True

    def update_poweremail_certificat_state(self, cursor, uid, ids, context=None):
        res = super(PoweremailMailbox, self).update_poweremail_certificat_state(cursor, uid, ids, context=context)
        # Actualitzarem l'estat de tots els mails que el seu certificat_state no sigui l'estat "get_email_opened_state"
        # ni que siguin erronis (estat "email_bounced"). Si l'email ja l'ha obert el client la resta de la info no ens
        # interessa i si el email esta en error tampoc ens interesa perque no es moura d'alla
        final_certificat_state = self.get_email_opened_state(cursor, uid)
        db = pooler.get_db(cursor.dbname)
        tmp_cursor = db.cursor()
        try:
            query = """
               SELECT id from poweremail_mailbox where certificat is True  
               AND certificat_state not in %(cert_state)s 
               FOR UPDATE skip locked"""
            tmp_cursor.execute(
                query,
                {'cert_state': tuple([final_certificat_state, 'email_bounced'])}
            )
            all_data = tmp_cursor.fetchall()
            pwids = [x[0] for x in all_data]
            self.write(tmp_cursor, uid, pwids, {'certificat_update_datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            tmp_cursor.commit()
        except LockNotAvailable:
            return False
        finally:
            tmp_cursor.close()
        pet_obj = osv.TransactionExecute(
            cursor.dbname, uid, 'poweremail.mailbox'
        )
        for poweremail_id in pwids:
            try:
                pet_obj.update_poweremail_certificate(
                    [poweremail_id], final_certificat_state, context=context
                )
            except Exception as e:
                sentry = self.pool.get('sentry.setup')
                if sentry:
                    sentry.client.captureException()
        return True

    def get_email_sent_state(self, cursor, uid, context=None):
        return "email_delivered"

    def get_email_opened_state(self, cursor, uid, context=None):
        return self.pool.get("res.config").get(cursor, uid, "signaturit_email_opened_state", "document_opened")

    def download_signaturit_email_audit_trail_document(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        pem_core_obj = self.pool.get('poweremail.core_accounts')

        signature_id = self.read(cursor, uid, ids, ['certificat_signature_id'], context=context)['certificat_signature_id']
        if not signature_id:
            raise osv.except_osv(_(u"Error"), _(u"No hi ha el Signatureit ID"))

        pdf = pem_core_obj.get_mail_audit_trail(cursor, uid, ids, signature_id, context=context)

        datas = {
            'pdf': b64encode(pdf),
        }
        return {
            'type': 'ir.actions.report.xml',
            'model': 'poweremail.mailbox',
            'report_name': 'signature.email.download.audit.trail',
            'datas': datas,
            'context': context
        }

    def _get_certificat_states(self, cursor, uid, context=None):
        res = super(PoweremailMailbox, self)._get_certificat_states(cursor, uid, context=context)
        res += [
            ('email_processed', _(u"Email processat (per ser enviat)")),
            ('email_delivered', _(u"Email enviat")),
            ('email_opened', _(u"Email obert per el receptor")),
            ('email_bounced', _(u"No s'ha pogut enviar el email")),
            ('bounce', _(u"No s'ha pogut enviar el email")),
            ('certification_completed', 'certification_completed'), # Posem el mateix fins que a la documentació hi hagi alguna cosa
            ('email_deferred', _(u"No s'ha pogut enviar el email, es fara un reintent")),
            ('documents_opened', _(u"Vista previa dels documents del email oberta")),
            ('document_opened', _(u"Documents del email oberts")),
            ('document_downloaded', _(u"Documents del email descarregats")),
        ]
        return res

    _columns = {
        'certificat_state': fields.selection(_get_certificat_states, 'Estat del mail certificat', size=50),
        'certificat_signature_id': fields.char("Signatureit ID", size=64)
    }

PoweremailMailbox()
