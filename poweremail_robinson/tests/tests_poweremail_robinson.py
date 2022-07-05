# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from destral import testing
from destral.transaction import Transaction

class TestPoweremailRobinson(testing.OOTestCase):

    def test_ff_created(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            mailbox_obj = self.openerp.pool.get('poweremail.mailbox')
            template_obj = self.openerp.pool.get('poweremail.templates')
            robinson_obj = self.openerp.pool.get('poweremail.template.robinson')

            imd_obj = self.openerp.pool.get('ir.model.data')

            template_id = imd_obj.get_object_reference(cursor, uid, 'poweremail_robinson', 'default_template_poweremail')[1]
            account_id = imd_obj.get_object_reference(cursor, uid, 'poweremail_robinson', 'info_energia_from_email')[1]
            #Escrivim un email a 'def_to' del template que és el que se li passara al mailbox a crear
            template_obj.write(cursor, uid, template_id, {'def_to': 'email@prova.com', 'enforce_from_account': account_id})

            #Crear objecte poweremail_robinson amb el correu de prova que li poso + el template que faig servir
            robinson_id = robinson_obj.create(cursor, uid, {'template_id': template_id, 'email': 'email@prova.com'})

            template_bwr = template_obj.browse(cursor, uid, template_id)

            record_id = imd_obj.get_object_reference(cursor, uid, 'poweremail_robinson', 'user_user')[1]

            # Cridar el _generate_mailbox_item_from_template i com que he creat el robinson, el mailbox_id que retorna
            # hauria de tenir com a folder el robinson
            mailbox_id = template_obj._generate_mailbox_item_from_template(cursor, uid, template_bwr, record_id)

            folder = mailbox_obj.read(cursor, uid, mailbox_id, ['folder'])['folder']
            self.assertEqual(folder, 'robinson')

            robinson_obj.unlink(cursor, uid, robinson_id)
            template_bwr = template_obj.browse(cursor, uid, template_id)
            # Cridar el _generate_mailbox_item_from_template i com que he creat el robinson, el mailbox_id que retorna
            # hauria de tenir com a folder el robinson
            mailbox_id = template_obj._generate_mailbox_item_from_template(cursor, uid, template_bwr, record_id)
            folder = mailbox_obj.read(cursor, uid, mailbox_id, ['folder'])['folder']
            self.assertEqual(folder, 'drafts')


