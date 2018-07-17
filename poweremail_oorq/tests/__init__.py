# coding=utf-8
from destral import testing
from rq import Queue
from oorq.oorq import setup_redis_connection
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
