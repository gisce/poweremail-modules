# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import mock
from destral.patch import PatchNewCursors

from osv import osv
from osv.orm import ValidateException
from osv.osv import except_osv
from tools.translate import _
from datetime import date
from destral import testing
from destral.transaction import Transaction

class TestPoweremailCampaign(testing.OOTestCase):
    def test_ff_created(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            camp_obj = self.openerp.pool.get('poweremail.campaign')
            camp_line_obj = self.openerp.pool.get('poweremail.campaign.line')
            mailbox_obj = self.openerp.pool.get('poweremail.mailbox')
            imd_obj = self.openerp.pool.get('ir.model.data')

            template_id = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign',  'default_template_poweremail')[1]
            core_accounts_id = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign', 'default_core_accounts')[1]

            mailbox_id = mailbox_obj.create(cursor, uid, {'pem_account_id': core_accounts_id, 'pem_subject': "Prova"})

            #Campanya 1 amb 2/2 linies creades
            camp_id_1 = camp_obj.create(
                cursor, uid, {'template_id': template_id, 'name': "Poweremail Campaign Prova 1"})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1, 'mail_id': mailbox_id})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1, 'mail_id': mailbox_id})

            # Campanya 2 amb 1/2 linies creades
            camp_id_2 = camp_obj.create(
                cursor, uid, {'template_id': template_id, 'name': "Poweremail Campaign Prova 2"})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_2, 'mail_id': mailbox_id})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_2})

            # Campanya 3 amb 0/0 linies creades
            camp_id_3 = camp_obj.create(
                cursor, uid, {'template_id': template_id, 'name': "Poweremail Campaign Prova 3"})

            progress_created_1 = camp_obj.read(cursor, uid, camp_id_1, ['progress_created'])['progress_created']
            progress_created_2 = camp_obj.read(cursor, uid, camp_id_2, ['progress_created'])['progress_created']
            progress_created_3 = camp_obj.read(cursor, uid, camp_id_3, ['progress_created'])['progress_created']
            self.assertEqual(progress_created_1, 100.0)
            self.assertEqual(progress_created_2, 50.0)
            self.assertEqual(progress_created_3, 0)

    def test_ff_sent(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            camp_obj = self.openerp.pool.get('poweremail.campaign')
            camp_line_obj = self.openerp.pool.get('poweremail.campaign.line')
            imd_obj = self.openerp.pool.get('ir.model.data')

            template_id = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign', 'default_template_poweremail')[1]
            core_accounts_id = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign', 'default_core_accounts')[1]

            # Campanya 1 amb 2/2 linies sent
            camp_id_1 = camp_obj.create(
                cursor, uid, {'template_id': template_id, 'name': "Poweremail Campaign Prova 1"})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1, 'state': 'sent'})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1, 'state': 'sent'})

            # Campanya 2 amb 1/2 linies sent
            camp_id_2 = camp_obj.create(
                cursor, uid, {'template_id': template_id, 'name': "Poweremail Campaign Prova 2"})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_2, 'state': 'sent'})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_2, 'state': 'to_send'})

            # Campanya 3 amb 0/0 linies sent
            camp_id_3 = camp_obj.create(
                cursor, uid, {'template_id': template_id, 'name': "Poweremail Campaign Prova 3"})

            progress_sent_1 = camp_obj.read(cursor, uid, camp_id_1, ['progress_sent'])['progress_sent']
            progress_sent_2 = camp_obj.read(cursor, uid, camp_id_2, ['progress_sent'])['progress_sent']
            progress_sent_3 = camp_obj.read(cursor, uid, camp_id_3, ['progress_sent'])['progress_sent']
            self.assertEqual(progress_sent_1, 100.0)
            self.assertEqual(progress_sent_2, 50.0)
            self.assertEqual(progress_sent_3, 0)

    def test_ff_object(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            camp_obj = self.openerp.pool.get('poweremail.campaign')
            camp_line_obj = self.openerp.pool.get('poweremail.campaign.line')
            mailbox_obj = self.openerp.pool.get('poweremail.mailbox')
            imd_obj = self.openerp.pool.get('ir.model.data')
            tmp_obj = self.openerp.pool.get('poweremail.templates')

            template_id_1 = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign', 'default_template_poweremail')[1]
            template_id_2 = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign', 'default_template_poweremail_no_model')[1]
            core_accounts_id = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign', 'default_core_accounts')[1]

            mailbox_id = mailbox_obj.create(cursor, uid, {'pem_account_id': core_accounts_id, 'pem_subject': "Prova"})

            # Campanya 1 amb template_id (amb model)
            camp_id_1 = camp_obj.create(
                cursor, uid, {'template_id': template_id_1, 'name': "Poweremail Campaign Prova 1"})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1, 'mail_id': mailbox_id})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1, 'mail_id': mailbox_id})

            # Campanya 2 amb template_id (sense model)
            camp_id_2 = camp_obj.create(
                cursor, uid, {'template_id': template_id_2, 'name': "Poweremail Campaign Prova 2"})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_2, 'mail_id': mailbox_id})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_2})

            template_id_1 = camp_obj.read(cursor, uid, camp_id_1, ['template_id'])['template_id'][0]
            template_id_2 = camp_obj.read(cursor, uid, camp_id_2, ['template_id'])['template_id'][0]

            if tmp_obj.read(cursor, uid, template_id_1, ['object_name'])['object_name']:
                template_model_1 = tmp_obj.read(cursor, uid, template_id_1, ['object_name'])['object_name'][1]
            else:
                template_model_1 = ''
            if tmp_obj.read(cursor, uid, template_id_2, ['object_name'])['object_name']:
                template_model_2 = tmp_obj.read(cursor, uid, template_id_2, ['object_name'])['object_name'][1]
            else:
                template_model_2 = ''

            model_camp_1 = camp_obj.read(cursor, uid, camp_id_1, ['template_obj'])['template_obj']
            model_camp_2 = camp_obj.read(cursor, uid, camp_id_2, ['template_obj'])['template_obj']
            self.assertEqual(str(template_model_1), model_camp_1)
            self.assertEqual(template_model_2, model_camp_2)


    def test_update_linies_campanya(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            #Crear una powermail.campaign amb:
                #Domini: S'aplica al recalcular les línies
                #Model: Es buscaran objectes d'aquest model
            #Per cada registre trobat a la bdd d'aquest tipus es creara un linia (es crida el mètode amb l'objecte poweremail.campaign)
            imd_obj = self.openerp.pool.get('ir.model.data')
            camp_obj = self.openerp.pool.get('poweremail.campaign')
            camp_line_obj = self.openerp.pool.get('poweremail.campaign.line')


            template_id_1 = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign', 'default_template_poweremail')[1]

            # Campanya 1 amb 1 línia
            camp_id_1 = camp_obj.create(
                cursor, uid, {'template_id': template_id_1, 'name': "Poweremail Campaign Prova 2"})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1})

            #Linies a la campanya abans de cridar el mètode
            num_linies_pre = len(camp_obj.read(cursor, uid, camp_id_1, ['reference_ids'])['reference_ids'])

            self.assertEqual(num_linies_pre, 1)

            camp_obj.update_linies_campanya(cursor, uid, [camp_id_1])

            pm_camp_brw = camp_obj.browse(cursor, uid, camp_id_1)
            domain = eval(pm_camp_brw.domain)
            if pm_camp_brw.template_id and pm_camp_brw.template_id.model_int_name:
                model_camp_1 = str(pm_camp_brw.template_id.model_int_name)
                model_obj = self.openerp.pool.get(model_camp_1)
                novesLinies = len(model_obj.search(cursor, uid, domain))

                num_linies_post = len(camp_obj.read(cursor, uid, camp_id_1, ['reference_ids'])['reference_ids'])

                self.assertEqual(num_linies_post, novesLinies)

    def generate_mail_test(self, cursor, uid, ids, context=None):
        pm_camp_line_obj = self.openerp.pool.get('poweremail.campaign.line')
        pm_camp_obj = self.openerp.pool.get('poweremail.campaign')
        pm_mb_obj = self.openerp.pool.get('poweremail.mailbox')
        account_obj = self.openerp.pool.get('poweremail.core_accounts')
        for camp_id in ids:
            campaign_v = pm_camp_obj.read(
                cursor, uid, camp_id, ['template_id', 'batch'],
                context=context
            )
            dmn = [
                ('campaign_id', '=', camp_id),
                ('state', 'in', ('to_send', 'sending_error'))
            ]
            line_ids = pm_camp_line_obj.search(
                cursor, uid, dmn, limit=campaign_v['batch'] or None,
                context=context
            )
            for line_id in line_ids:
                line_v = pm_camp_line_obj.read(cursor, uid, line_id, ['state', 'mail_id'])
                if line_v['state'] in ('sent', 'sending') and line_v['mail_id']:
                    return
                try:
                    context['src_rec_id'] = line_id
                    context['src_model'] = pm_camp_line_obj._name
                    pm_camp_line_obj.write(cursor, uid, line_id, {'state': 'sending'}, context=context)
                    # generate_mail
                    reference = context['src_model'] + ',' + str(context['src_rec_id'])

                    # Creem el mailbox amb la linia

                    vals_mailbox = {
                        'pem_account_id': account_obj.search(cursor, uid, [])[0],
                        'pem_subject': "Lorem Ipsum",
                        'reference': reference,
                    }
                    pm_mb_obj.create(cursor, uid, vals_mailbox, context=context)

                except Exception as e:
                    pm_camp_line_obj.write(cursor, uid, line_id, {'state': 'sending_error', 'log': str(e) + "\n"}, context=context)
                return True

    @mock.patch('poweremail.poweremail_template.poweremail_templates.generate_mail')
    def test_send_email(self, mocked_function):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            pm_camp_line_obj = self.openerp.pool.get('poweremail.campaign.line')
            pm_camp_obj = self.openerp.pool.get('poweremail.campaign')
            pm_tmp_obj = self.openerp.pool.get('poweremail.templates')
            #Creem template
            vals_template = {
                'name': 'template_prova',
                'template_language': 'mako',
            }
            pm_temp_id = pm_tmp_obj.create(cursor, uid, vals_template)
            #Creem campanya
            vals_camp = {
                'template_id': pm_temp_id,
                'name': 'prova',
            }
            pm_camp_id = pm_camp_obj.create(cursor, uid, vals_camp)
            #Creem linia campanya
            vals_pm_camp_line = {
                'campaign_id': pm_camp_id,
                'ref': str('res.partner,1')
            }
            pm_camp_line_id = pm_camp_line_obj.create(cursor, uid, vals_pm_camp_line)

            mocked_function.return_value = self.generate_mail_test(cursor, uid, [pm_camp_id], context={})

            with PatchNewCursors():
                pm_camp_obj.send_emails(cursor, uid, [pm_camp_id], context={})
            dades_linia = pm_camp_line_obj.read(cursor, uid, pm_camp_line_id, ['mail_id', 'state'])
            self.assertTrue(dades_linia['mail_id'])

    def test_update_linies_campanya_distinct_email(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            imd_obj = self.openerp.pool.get('ir.model.data')
            camp_obj = self.openerp.pool.get('poweremail.campaign')
            camp_line_obj = self.openerp.pool.get('poweremail.campaign.line')
            template_obj = self.openerp.pool.get('poweremail.templates')

            template_id = imd_obj.get_object_reference(
                cursor, uid, 'poweremail_campaign', 'default_template_poweremail')[1]

            # Email
            template_obj.write(cursor, uid, template_id, {
                'def_to': 'hola@gmail.com'
            })

            # Campanya 1 amb 2 línies
            camp_id_1 = camp_obj.create(cursor, uid, {
                'template_id': template_id,
                'name': "Poweremail Campaign Prova 1",
                'distinct_mails': True,
            })
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_1})

            # Les dues línies tenen el camp state a 'to_send'
            linies_ids = camp_obj.read(cursor, uid, camp_id_1, ['reference_ids'])['reference_ids']
            self.assertEqual(len(linies_ids), 2)
            states = camp_line_obj.read(cursor, uid, linies_ids, ['state'])
            for state in states:
                self.assertEqual(state['state'], 'to_send')

            camp_obj.update_linies_campanya(cursor, uid, [camp_id_1])

            # Lines actualitzades, una d'elles ha de tenir l'state a 'avoid_duplicate'
            estats = []
            line_ids = camp_line_obj.search(cursor, uid, [('campaign_id', '=', camp_id_1)])
            self.assertEqual(len(line_ids), 2)
            for linia in line_ids:
                state = camp_line_obj.read(cursor, uid, linia, ['state'])['state']
                estats.append(state)
            self.assertEqual(estats, ['to_send', 'avoid_duplicate'])


            # Campanya 2 amb 2 linies creades sense el distinct_email a True
            camp_id_2 = camp_obj.create(cursor, uid, {
                'template_id': template_id,
                'name': "Poweremail Campaign Prova 2"
            })
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_2})
            camp_line_obj.create(cursor, uid, {'campaign_id': camp_id_2})

            camp_obj.update_linies_campanya(cursor, uid, [camp_id_2])

            # Les dues línies tenen el camp state a 'to_send'
            linies_ids = camp_obj.read(cursor, uid, camp_id_2, ['reference_ids'])['reference_ids']
            self.assertEqual(len(linies_ids), 2)
            states = camp_line_obj.read(cursor, uid, linies_ids, ['state'])
            for state in states:
                self.assertEqual(state['state'], 'to_send')