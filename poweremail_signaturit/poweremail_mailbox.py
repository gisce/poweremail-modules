# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

import pooler
from psycopg2.errors import LockNotAvailable
from sql import For
from osv import osv, fields
from tools.translate import _
from datetime import datetime

from signaturit_sdk.signaturit_client import SignaturitClient
from poweremail_signaturit.poweremail_core import get_signaturit_client
from tools import config


class PoweremailMailbox(osv.osv):

    _inherit = 'poweremail.mailbox'

    def get_company_signaturit_id(self, cursor, uid, poweremail_id, context=None):
        """
        S'intenta calcular el company_id de un email a partir de la referencia vinculada al emailñ.
        Si no hi ha referencia, s'agafa del context (si n'hi ha)
        """
        if isinstance(poweremail_id, list):
            poweremail_id = poweremail_id[0]
        if context is None:
            context = {}
        company_o = self.pool.get("res.company")

        # Si no tenim el modul signaturit_multicompany instalat no fem res
        if "signaturit_id" not in company_o._columns:
            return False

        # Si no tenim registre vinculat desde el que calcular la company ni tenim context, no fem res
        reference = self.read(cursor, uid, poweremail_id, ['reference'])['reference']
        if not reference:
            if context.get("company_id"):
                signaturit_id = company_o.read(cursor, uid, context.get("company_id"), ['signaturit_id'])['signaturit_id']
                return signaturit_id
            return False

        # Si el registre que tenim vinculat no existeix i no tenim context, no fem res
        ref_o_str, ref_id = reference.split(",")
        ref_o = self.pool.get(ref_o_str)
        ref_id = int(ref_id)
        if not ref_id:
            if context.get("company_id"):
                signaturit_id = company_o.read(cursor, uid, context.get("company_id"), ['signaturit_id'])['signaturit_id']
                return signaturit_id
            return False

        # Finalment, si el registre vinculat te el camp "company_id" el fem servir. Sino l'agafem del context
        company_id = False
        if "company_id" in ref_o:
            company_id = ref_o.read(cursor, uid, ref_id, ['company_id'])
            if company_id['company_id']:
                company_id = company_id['company_id'][0]
        if not company_id and context.get("company_id"):
            company_id = context.get("company_id")
        else:
            return False
        signaturit_id = company_o.read(cursor, uid, company_id, ['signaturit_id'])['signaturit_id']
        return signaturit_id

    def get_signaturit_client(self, cursor, uid, poweremail_id, context=None):
        client = get_signaturit_client()
        if not poweremail_id:
            return client
        token = self.get_company_signaturit_id(cursor, uid, poweremail_id, context=context)
        if token:
            client = SignaturitClient(token, config.get('signaturit_production', False))
        return client

    def update_poweremail_certificate(
            self, cursor, uid, pe_id, final_certificat_state,  context=None):
        if context is None:
            context = {}
        self_q = self.q(cursor, uid)
        try:
            q_sql = self_q.select(
                ['id', 'certificat_signature_id'], for_=For('UPDATE', nowait=True)
            ).where([('id', '=', pe_id)])
            cursor.execute(*q_sql)
            poweremail_info = cursor.dictfetchone()
        except LockNotAvailable:
            return False
        client = self.pool.get("poweremail.mailbox").get_signaturit_client(cursor, uid, context.get("poweremail_id"), context=context)
        res = client.get_email(poweremail_info['certificat_signature_id'])
        if "id" not in res:
            return False
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
        self.write(cursor, uid, poweremail_info['id'],
                   {'certificat_state': certificat_state_to_write})

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
