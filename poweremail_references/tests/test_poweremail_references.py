# coding=utf-8
from destral import testing


class TestPoweremailReferences(testing.OOTestCaseWithCursor):

    def get_demo_template(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        template_obj = self.openerp.pool.get('poweremail.templates')

        template_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'poweremail',
            'default_template_poweremail'
        )[1]
        account_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'poweremail',
            'info_energia_from_email'
        )[1]
        template_obj.write(
            self.cursor, self.uid, template_id,
            {'enforce_from_account': account_id}
        )

        return template_obj.browse(self.cursor, self.uid, template_id)

    def test_generated_mailbox_gets_reference_from_template_model(self):
        mailbox_obj = self.openerp.pool.get('poweremail.mailbox')
        template_obj = self.openerp.pool.get('poweremail.templates')

        template = self.get_demo_template()

        mailbox_id = template_obj._generate_mailbox_item_from_template(
            self.cursor, self.uid, template, self.uid, context={}
        )

        mailbox = mailbox_obj.read(
            self.cursor, self.uid, mailbox_id, ['reference']
        )
        self.assertEqual(
            mailbox['reference'], 'res.users,%d' % self.uid
        )
