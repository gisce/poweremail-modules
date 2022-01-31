# coding=utf-8
from destral import testing
from rq import Queue
from oorq.oorq import setup_redis_connection
from signals import DB_CURSOR_COMMIT
import os


def enqueue_dummy_method(name):
    return 'Hello world {}!'.format(name)


class TestEnqueue(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestEnqueue, self).setUp()
        self.redis = setup_redis_connection()
        self.q = Queue('poweremail')
        self.old_oorq_async = os.environ.get('OORQ_ASYNC')
        os.environ['OORQ_ASYNC'] = 'True'

    def tearDown(self):
        super(TestEnqueue, self).tearDown()
        self.q.empty()
        if self.old_oorq_async:
           os.environ['OORQ_ASYNC'] = self.old_oorq_async

    def create_account(self):
        acc_obj = self.openerp.pool.get('poweremail.core_accounts')
        cursor = self.cursor
        uid = self.uid

        acc_id = acc_obj.create(cursor, uid, {
            'name': 'Test account',
            'user': self.uid,
            'email_id': 'test@example.com',
            'smtpserver': 'smtp.example.com',
            'smtpport': 587,
            'smtpuname': 'test',
            'smtppass': 'test',
            'company': 'yes'
        })
        return acc_id

    def create_template(self):

        imd_obj = self.openerp.pool.get('ir.model.data')
        tmpl_obj = self.openerp.pool.get('poweremail.templates')
        cursor = self.cursor
        uid = self.uid
        acc_id = self.create_account()

        model_partner = imd_obj.get_object_reference(
            cursor, uid, 'base', 'model_res_partner'
        )[1]

        tmpl_id = tmpl_obj.create(cursor, uid, {
            'name': 'Test template',
            'object_name': model_partner,
            'enforce_from_account': acc_id,
            'template_language': 'mako',
            'def_priority': '2'
        })
        return tmpl_id

    def test_enqueue_normal_low_priority_mail_goes_last_position_of_queue(self):

        mail_obj = self.openerp.pool.get('poweremail.mailbox')
        cursor = self.cursor
        uid = self.uid
        acc_id = self.create_account()

        mail_id = mail_obj.create(cursor, uid, {
            'pem_subject': 'High priority email',
            'pem_account_id': acc_id,
            'priority': '0'
        })

        job = self.q.enqueue(enqueue_dummy_method)
        self.assertEqual(len(self.q), 1)
        self.assertEqual(self.q.jobs[0], job)

        mail_obj.send_this_mail(cursor, uid, [mail_id])
        self.assertEqual(len(self.q), 2)
        last_job = self.q.jobs[-1]
        self.assertEqual(
            last_job.args[3:6],
            ('poweremail.mailbox', 'send_in_background', [mail_id])
        )

        mail_id = mail_obj.create(cursor, uid, {
            'pem_subject': 'High priority email',
            'pem_account_id': acc_id,
            'priority': '1'
        })
        mail_obj.send_this_mail(cursor, uid, [mail_id])
        self.assertEqual(len(self.q), 3)
        last_job = self.q.jobs[-1]
        self.assertEqual(
            last_job.args[3:6],
            ('poweremail.mailbox', 'send_in_background', [mail_id])
        )

    def test_enqueue_high_priority_mail_goes_first_position_of_queue(self):

        mail_obj = self.openerp.pool.get('poweremail.mailbox')
        cursor = self.cursor
        uid = self.uid
        acc_id = self.create_account()

        priority_id = mail_obj.create(cursor, uid, {
            'pem_subject': 'High priority email',
            'pem_account_id': acc_id,
            'priority': '2'
        })

        job = self.q.enqueue(enqueue_dummy_method)
        self.assertEqual(len(self.q), 1)
        self.assertEqual(self.q.jobs[0], job)

        mail_obj.send_this_mail(cursor, uid, [priority_id])
        self.assertEqual(len(self.q), 2)
        first_job = self.q.jobs[0]
        self.assertEqual(
            first_job.args[3:6],
            ('poweremail.mailbox', 'send_in_background_at_front', [priority_id])
        )

        normal_id = mail_obj.create(cursor, uid, {
            'pem_subject': 'High priority email',
            'pem_account_id': acc_id,
            'priority': '1'
        })
        mail_obj.send_this_mail(cursor, uid, [normal_id])
        self.assertEqual(len(self.q), 3)
        first_job = self.q.jobs[0]
        self.assertEqual(
            first_job.args[3:6],
            ('poweremail.mailbox', 'send_in_background_at_front', [priority_id])
        )
        last_job = self.q.jobs[-1]
        self.assertEqual(
            last_job.args[3:6],
            ('poweremail.mailbox', 'send_in_background', [normal_id])
        )

    def test_enqueue_high_priority_mail_goes_first_position_of_render_queue(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        send_obj = self.openerp.pool.get('poweremail.send.wizard')

        job = self.q.enqueue(enqueue_dummy_method)
        self.assertEqual(len(self.q), 1)
        self.assertEqual(self.q.jobs[0], job)

        cursor = self.cursor
        uid = self.uid
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_asus'
        )[1]

        tmpl_id = self.create_template()

        ctx = {
            'active_id': partner_id,
            'active_ids': [partner_id],
            'src_rec_ids': [partner_id],
            'src_model': 'res.partner',
            'template_id': tmpl_id
        }

        wiz_id = send_obj.create(cursor, uid, {}, context=ctx)
        wiz = send_obj.browse(cursor, uid, wiz_id)
        self.assertEqual(wiz.priority, '2')

        ctx2 = ctx.copy()
        ctx2['save_async'] = True
        wiz.save_to_mailbox(context=ctx2)
        self.assertEqual(len(self.q), 2)
        first_job = self.q.jobs[0]
        self.assertEqual(
            first_job.args[3:5],
            ('poweremail.send.wizard', 'save_to_mailbox_in_background_at_front')
        )

        wiz_id = send_obj.create(cursor, uid, {}, context=ctx)
        send_obj.write(cursor, uid, [wiz_id], {'priority': '1'})
        wiz = send_obj.browse(cursor, uid, wiz_id)
        self.assertEqual(wiz.priority, '1')

        ctx2 = ctx.copy()
        ctx2['save_async'] = True
        wiz.save_to_mailbox(context=ctx2)
        self.assertEqual(len(self.q), 3)

        last_job = self.q.jobs[-1]
        self.assertEqual(
            last_job.args[3:5],
            ('poweremail.send.wizard', 'save_to_mailbox_in_background')
        )

        first_job = self.q.jobs[0]
        self.assertEqual(
            first_job.args[3:5],
            ('poweremail.send.wizard', 'save_to_mailbox_in_background_at_front')
        )

    def test_generate_mail_in_background_high_priority(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        tmpl_obj = self.openerp.pool.get('poweremail.templates')
        cursor = self.cursor
        uid = self.uid
        tmpl_id = self.create_template()
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_asus'
        )[1]

        # Add something to the queue to check if other job is putted first
        job = self.q.enqueue(enqueue_dummy_method)
        self.assertEqual(len(self.q), 1)
        self.assertEqual(self.q.jobs[0], job)

        tmpl_obj.generate_mail(cursor, uid, tmpl_id, [partner_id])
        # Hack to put the job in to the queue without commiting
        DB_CURSOR_COMMIT.send(cursor)

        self.assertEqual(len(self.q), 2)
        first_job = self.q.jobs[0]
        self.assertEqual(
            first_job.args[3:6],
            ('poweremail.templates', 'generate_mail_in_background_at_front', tmpl_id)
        )

    def test_generate_mail_in_background_low_priority(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        tmpl_obj = self.openerp.pool.get('poweremail.templates')
        cursor = self.cursor
        uid = self.uid
        tmpl_id = self.create_template()
        tmpl_obj.write(cursor, uid, [tmpl_id], {'def_priority': '1'})
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_asus'
        )[1]

        # Add something to the queue to check if other job is putted first
        job = self.q.enqueue(enqueue_dummy_method)
        self.assertEqual(len(self.q), 1)
        self.assertEqual(self.q.jobs[0], job)

        tmpl_obj.generate_mail(cursor, uid, tmpl_id, [partner_id])
        # Hack to put the job in to the queue without commiting
        DB_CURSOR_COMMIT.send(cursor)

        self.assertEqual(len(self.q), 2)
        first_job = self.q.jobs[-1]
        self.assertEqual(
            first_job.args[3:6],
            ('poweremail.templates', 'generate_mail_in_background', tmpl_id)
        )
