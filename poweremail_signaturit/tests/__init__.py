# -*- coding: utf-8 -*-
from test_download_audit_trail import *

from addons import get_module_resource
from destral import testing
from destral.patch import PatchNewCursors
from signaturit_sdk.signaturit_client import SignaturitClient
from destral.transaction import Transaction
from osv.orm import except_orm
import mock
from addons import get_module_resource
from tools import config


class TestPoweremailSignaturit(testing.OOTestCaseWithCursor):

    signaturit_sandbox_token = "JhsVikrzRcskvRRYnKkfaLltWBKHbNbzlGBpmgdQTQjHZQFhbmnjApUGKVVIZYxVBqtktRfeDebMPfLZGEwIYj"

    def get_sandbox_client(self):
        client = SignaturitClient(self.signaturit_sandbox_token, False)
        return client

    def test_POST_email_simple(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        client = self.get_sandbox_client()

        # He comentat el test per no fer una crida sempre que es facin els tests, pero ho deixo per veure com es pot cridar la api

        # res = client.create_email(
        #     files=[],
        #     recipients=[{'name': 'Eduard', 'email': 'eberloso@gisce.net'}],
        #     subject="Email Certificat Simple",
        #     body="Aixo es un email <b>certificat</b>",
        #     params={'type': "open_email"}
        # )
        # self.assertTrue(res['id'])
        # self.assertEqual(res['certificates'][0]['status'], u'in_queue')
        # self.assertEqual(res['certificates'][0]['name'], u'Eduard')
        # self.assertEqual(res['certificates'][0]['email'], u'eberloso@gisce.net')

    @mock.patch("signaturit_sdk.signaturit_client.SignaturitClient.get_email")
    @mock.patch("poweremail_signaturit.poweremail_core.get_signaturit_client")
    def test_update_poweremail_certificat_state(self, mocked_get_signaturit_client, mocked):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        client = self.get_sandbox_client()
        config['signaturit_token'] = 'RANDOM_RANDOM'
        mocked_get_signaturit_client.return_value = client

        poweracc_o = pool.get("poweremail.core_accounts")
        poweremail_o = pool.get("poweremail.mailbox")

        paid = poweracc_o.create(cursor, uid, {
            'email_id': "algunmail@gisce.net",
            'company': "yes",
            'smtpport': 1,
            'smtpserver': ""
        })
        pwid = poweremail_o.create(cursor, uid, {
            'pem_subject': "Test Mail",
            'pem_account_id': paid,
            'certificat_signature_id': "123456789",
            'certificat_state': "init",
            'certificat': True
        })
        with PatchNewCursors():
            # Primer provem que s'actualitza be quan li diguem que s'ha enviat el email
            resource = get_module_resource('poweremail_signaturit', 'tests', 'fixtures', 'email_sent_res.json')
            with open(resource, 'r') as demo_file:
                response = demo_file.read()
            mocked.return_value = eval(response)
            self.assertEqual(poweremail_o.read(cursor, uid, pwid, ['certificat_state'])['certificat_state'], "init")
            poweremail_o.update_poweremail_certificat_state(cursor, uid, [])
            self.assertEqual(poweremail_o.read(cursor, uid, pwid, ['certificat_state'])['certificat_state'], "email_delivered")

            # Ara procem provem que s'actualitza be quan li diguem que s'ha obert el email
            resource = get_module_resource('poweremail_signaturit', 'tests', 'fixtures', 'email_opened_res.json')
            with open(resource, 'r') as demo_file:
                response = demo_file.read()
            mocked.return_value = eval(response)
            poweremail_o.write(cursor, uid, pwid, {'certificat_state': 'init'})
            self.assertEqual(poweremail_o.read(cursor, uid, pwid, ['certificat_state'])['certificat_state'], "init")
            poweremail_o.update_poweremail_certificat_state(cursor, uid, [])
            self.assertEqual(poweremail_o.read(cursor, uid, pwid, ['certificat_state'])['certificat_state'], "email_opened")

            # Ara procem provem que s'actualitza be quan li diguem que s'ha obert el document
            resource = get_module_resource('poweremail_signaturit', 'tests', 'fixtures', 'document_opened_res.json')
            with open(resource, 'r') as demo_file:
                response = demo_file.read()
            mocked.return_value = eval(response)
            self.assertEqual(poweremail_o.read(cursor, uid, pwid, ['certificat_state'])['certificat_state'], "email_opened")
            poweremail_o.update_poweremail_certificat_state(cursor, uid, [])
            self.assertEqual(poweremail_o.read(cursor, uid, pwid, ['certificat_state'])['certificat_state'], "document_opened")

            # Ara procem provem que s'actualitza be quan li diguem que s'ha descarregat el document. Encara que s'hagi
            # descarregat, com que l'estat final es "document obert", no ens actualitzara a document_descarregat i es
            # quedara amb el document_obert
            resource = get_module_resource('poweremail_signaturit', 'tests', 'fixtures', 'document_downloaded_res.json')
            with open(resource, 'r') as demo_file:
                response = demo_file.read()
            mocked.return_value = eval(response)
            poweremail_o.write(cursor, uid, pwid, {'certificat_state': 'init'})
            self.assertEqual(poweremail_o.read(cursor, uid, pwid, ['certificat_state'])['certificat_state'], "init")
            poweremail_o.update_poweremail_certificat_state(cursor, uid, [])
            self.assertEqual(poweremail_o.read(cursor, uid, pwid, ['certificat_state'])['certificat_state'], "document_opened")

    @mock.patch("poweremail_signaturit.poweremail_core.get_signaturit_client")
    def test_send_mail_certificat_fails_and_returns_false(self, mocked_get_signaturit_client):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        poweracc_o = pool.get("poweremail.core_accounts")
        poweremail_o = pool.get("poweremail.mailbox")

        client = self.get_sandbox_client()
        mocked_get_signaturit_client.return_value = client

        ids = [
            poweracc_o.create(cursor, uid, {
                'email_id': "algunmail@gisce.net",
                'company': "yes",
                'smtpport': 1,
                'smtpserver': ""
            })
        ]
        # EMAIL INCORRECTE PERQUE DONGUI ERROR al fer la crida. Com que donara error no s'enviara cap mail,
        # per tant no fa falta que fem un mock
        addresses = {
            'To': "algunmailgisce.net",
            'FROM': "algunmailgisce.net"
        }
        subject = u"Email Certificat de Test"
        body = {'html': u"""Aixo es un email <b>certificat (test_send_mail_certificat)</b>"""}
        payload = {}
        pwid = poweremail_o.create(cursor, uid, {
            'pem_subject': subject,
            'pem_account_id': ids[0],
        })
        context = {
            'poweremail_id': pwid,
        }
        res = poweracc_o.send_mail_certificat(
            cursor, uid, ids, addresses, subject=subject, body=body, payload=payload, context=context
        )
        self.assertFalse(res)

    @mock.patch("poweremail_signaturit.poweremail_core.get_signaturit_client")
    @mock.patch("signaturit_sdk.signaturit_client.SignaturitClient.create_email")
    def test_send_mail_certificat_ok_and_returns_true(self, mocked_create_email, mocked_get_signaturit_client):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        poweracc_o = pool.get("poweremail.core_accounts")
        poweremail_o = pool.get("poweremail.mailbox")

        client = self.get_sandbox_client()
        mocked_get_signaturit_client.return_value = client
        # Per evitar anar enviant emails, fem un mock id espres validem que es crida com esperem
        mocked_create_email.return_value = {'id': "123456789"}

        ids = [
            poweracc_o.create(cursor, uid, {
                'email_id': "algunmail@gisce.net",
                'company': "yes",
                'smtpport': 1,
                'smtpserver': ""
            })
        ]
        addresses = {
            'To': "eberloso@gisce.net",
            'FROM': "algunmail@gisce.net"
        }
        subject = u"Email Certificat de Test"
        body = {'html': u"""Aixo es un email <b>certificat (test_send_mail_certificat)</b>"""}
        payload = {}
        pwid = poweremail_o.create(cursor, uid, {
            'pem_subject': subject,
            'pem_account_id': ids[0],
        })
        context = {
            'poweremail_id': pwid,
        }
        res = poweracc_o.send_mail_certificat(
            cursor, uid, ids, addresses, subject=subject, body=body, payload=payload, context=context
        )
        self.assertTrue(res)
        mocked_create_email.assert_called_with(
            files=[],
            recipients=[{'name': 'eberloso@gisce.net', 'email': 'eberloso@gisce.net'}],
            subject=subject,
            body=body['html'],
            params={'type': "open_document", "recipients": {}}
        )
