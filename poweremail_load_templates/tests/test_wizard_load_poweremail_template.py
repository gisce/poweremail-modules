
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from dateutil.relativedelta import relativedelta
from destral import testing
from destral.transaction import Transaction
from datetime import datetime
import calendar
from osv import osv


class TestLoadTemplate(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool

    def test_load_poweremail_template(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            context = {}

            # Objects
            imd_obj = self.pool.get('ir.model.data')
            poweremail_template_obj = self.pool.get('poweremail.templates')
            poweremail_template_source_obj = self.pool.get(
                'poweremail.templates.source'
            )
            wiz = self.openerp.pool.get('wizard.load.poweremail.template')

            # Get initial body text
            poweremail_template_id = imd_obj.get_object_reference(
                cursor, uid, 'poweremail', 'default_template_poweremail'
            )[1]

            poweremail_template_v = poweremail_template_obj.read(
                cursor, uid, poweremail_template_id, [
                    'def_body_text'
                ],
                context=context
            )

            initial_body_text = poweremail_template_v['def_body_text']

            # Create Template Source
            poweremail_template_source_obj.create(
                cursor, uid, {
                    'template_id': poweremail_template_id,
                    'source': 'poweremail_load_templates/tests/test_files/test_file_1.mako',
                    'lang': 1,
                },
                context=context
            )

            # Call wizard function
            wiz.load_poweremail_template(
                cursor, uid, [poweremail_template_id], context=context
            )

            # Get new body text
            poweremail_template_v = poweremail_template_obj.read(
                cursor, uid, poweremail_template_id, [
                    'def_body_text'
                ],
                context=context
            )

            new_body_text = poweremail_template_v['def_body_text']

            # Check if new and intial are different
            self.assertNotEqual(initial_body_text, new_body_text)
