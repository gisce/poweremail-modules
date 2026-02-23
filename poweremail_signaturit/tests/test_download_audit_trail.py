# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from email.utils import make_msgid
import six
if six.PY2:
    import mock
else:
    from unittest import mock
from addons import get_module_resource
import os
from base64 import b64decode

class TestDownloadAuditTrail(testing.OOTestCaseWithCursor):
    # Set up global var.
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    # Tanca transacció bd.
    def tearDown(self):
        self.txn.stop()

    def test_download_email_audit_trail(self):
        file_path = get_module_resource(
            'poweremail_signaturit', 'tests', 'fixtures', 'test_certified_email_audit_trail.pdf'
        )
        fake_certificate = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        with mock.patch('poweremail_signaturit.poweremail_core.PoweremailCore.get_signaturit_client') as mock_client:
            mock_client.return_value = mock.MagicMock()
            with open(file_path, 'rb') as f:
                mock_client.return_value.download_email_audit_trail.return_value = final_expected_file = f.read()
            mock_client.return_value.get_email.return_value = {'certificates': [{'id': fake_certificate}]}

            context = {}
            pem_mailbox_obj = self.pool.get('poweremail.mailbox')
            pem_core_account_obj = self.pool.get('poweremail.core_accounts')

            pem_account_id = pem_core_account_obj.create(self.cursor, self.uid, {
                'email_id': "algunmail@gisce.net",
                'company': "yes",
                'smtpport': 1,
                'smtpserver': ""
            })

            pem_mailbox_id = pem_mailbox_obj.create(self.cursor, self.uid, {
                'pem_account_id': pem_account_id,
                'state': 'na',
                'folder': 'inbox',
                'pem_message_id': make_msgid('poweremail'),
                'pem_subject': 'anything',
                'certificat_signature_id': fake_certificate,
                'certificat_state': "init",
                'certificat': True,
            }, context=context)

            pdf = pem_mailbox_obj.download_signaturit_email_audit_trail_document(self.cursor, self.uid, pem_mailbox_id, context=context)
            pdf_contents = pdf.get('datas', {}).get('pdf', False)
            self.assertTrue(pdf_contents)
            self.assertEqual(b64decode(pdf_contents), final_expected_file)
