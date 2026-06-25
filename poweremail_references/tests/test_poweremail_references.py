# coding=utf-8
from destral import testing


class TestPoweremailReferences(testing.OOTestCaseWithCursor):

    def create_account(self):
        account_obj = self.openerp.pool.get('poweremail.core_accounts')

        return account_obj.create(self.cursor, self.uid, {
            'name': 'Test account',
            'user': self.uid,
            'email_id': 'test@example.com',
            'smtpserver': 'smtp.example.com',
            'smtpport': 587,
            'smtpuname': 'test',
            'smtppass': 'test',
            'company': 'yes',
        })

    def create_template(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        template_obj = self.openerp.pool.get('poweremail.templates')

        model_partner = imd_obj.get_object_reference(
            self.cursor, self.uid, 'base', 'model_res_partner'
        )[1]

        return template_obj.create(self.cursor, self.uid, {
            'name': 'Reference test template',
            'object_name': model_partner,
            'enforce_from_account': self.create_account(),
            'template_language': 'mako',
            'def_to': 'test@example.com',
        })

    def test_generated_mailbox_gets_reference_from_template_model(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        mailbox_obj = self.openerp.pool.get('poweremail.mailbox')
        template_obj = self.openerp.pool.get('poweremail.templates')

        partner_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'base', 'res_partner_asus'
        )[1]
        template_id = self.create_template()
        template = template_obj.browse(self.cursor, self.uid, template_id)

        mailbox_id = template_obj._generate_mailbox_item_from_template(
            self.cursor, self.uid, template, partner_id, context={}
        )

        mailbox = mailbox_obj.read(
            self.cursor, self.uid, mailbox_id, ['reference']
        )
        self.assertEqual(
            mailbox['reference'], 'res.partner,%d' % partner_id
        )
