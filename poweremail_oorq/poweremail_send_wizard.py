# -*- coding: utf-8 -*-
from itertools import chain
from osv import osv
from rq import get_current_job
from oorq.decorators import job
from oorq.oorq import JobsPool, AsyncMode
from tools import config


class PoweremailSendWizard(osv.osv_memory):
    _name = 'poweremail.send.wizard'
    _inherit = 'poweremail.send.wizard'

    def save_to_mailbox(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if get_current_job() or not AsyncMode.is_async():
            return super(PoweremailSendWizard,
                         self).save_to_mailbox(cursor, uid, ids,
                                               context=context)

        fields = self.fields_get(cursor, uid, context=context).keys()
        wiz = self.read(cursor, uid, ids, [], context)[0]
        def_fields = self.fields_get(cursor, uid, context=context)
        for k in wiz.keys():
            if k in def_fields and def_fields[k]['type'].endswith('2many'):
                wiz[k] = [[6, 0, wiz[k]]]
            if k not in fields:
                del wiz[k]
        res = []
        ctx = context.copy()
        j_pool = JobsPool()
        if wiz['single_email'] and len(context['src_rec_ids']) > 1:
            # We send a single email for several records
            context['src_rec_ids'] = context['src_rec_ids'][:1]
        # Copy the original list
        src_rec_ids = context.get('src_rec_ids', [])[:]
        len_src_rec_ids = len(src_rec_ids)
        new_rec_ids = []
        
        # Due the original method only parse the templates if the len of
        # src_rec_ids is greater than 1 but we want to minimize the mails to
        # generate we make groups of two. [(1,2), (3,4), (5,6)]
        # We check if the len is mod of 2 if not we make a fisrt group of 3
        if len(src_rec_ids) % 2:
            new_rec_ids.append(tuple(src_rec_ids[:3]))
            src_rec_ids = src_rec_ids[3:]
        # Make the group of 2 for the rest
        new_rec_ids.extend(zip(*(iter(src_rec_ids),) * 2))
        len_new_rec_ids = len(list(chain.from_iterable(new_rec_ids)))
        if len_src_rec_ids != len_new_rec_ids:
            raise Exception(
                "Original list is different %s != %s" % (
                    len_src_rec_ids, len_new_rec_ids
                )
            )
        for rec_id in new_rec_ids:
            ctx['screen_vals'] = wiz
            ctx['src_rec_ids'] = rec_id
            if wiz['priority'] == '2':
                job = self.save_to_mailbox_in_background_at_front(cursor, uid, ctx)
            else:
                job = self.save_to_mailbox_in_background(cursor, uid, ctx)
            j_pool.add_job(job)
            if 'screen_vals' in ctx:
                del ctx['screen_vals']
        # When using `save_async`, it won't join the jobs, so they'll be
        #    done on background.
        # The background rendered emails will be added to the folder on
        #    context and won't be forced into the 'outbox' folder
        if not(context.get('save_async', False)):
            j_pool.join()
            for res_job in j_pool.results.values():
                res += res_job
            # Put the rendered mails on outbox
            mailbox_obj = self.pool.get('poweremail.mailbox')
            to_write = res
            if res:
                # Per si algun dels emails que volem moure no existeix. Aixi avitem AccesError i que falli tot el proces
                to_write = mailbox_obj.search(cursor, uid, [('id', 'in', res)])
            mailbox_obj.write(cursor, uid, to_write, {'folder': 'outbox'}, ctx)
        return res

    @job(queue=config.get('poweremail_render_queue', 'poweremail'), at_front=True)
    def save_to_mailbox_in_background_at_front(self, cursor, uid, context):
        mailbox_obj = self.pool.get('poweremail.mailbox')
        if not context:
            context = {}
        screen_vals = context.get('screen_vals', {})
        ctx = context.copy()
        del ctx['screen_vals']
        if not screen_vals:
            raise Exception("No screen_vals found in the context!")

        wiz_id = self.create(cursor, uid, screen_vals, ctx)
        mail_ids = super(PoweremailSendWizard,
                         self).save_to_mailbox(cursor, uid, [wiz_id], ctx)
        # When using `save_async`, we leave the folder as it should be
        if not(context.get('save_async', False)):
            mailbox_obj.write(cursor, uid, mail_ids, {'folder': 'drafts'}, ctx)
        return mail_ids

    @job(queue=config.get('poweremail_render_queue', 'poweremail'))
    def save_to_mailbox_in_background(self, cursor, uid, context):
        mailbox_obj = self.pool.get('poweremail.mailbox')
        if not context:
            context = {}
        screen_vals = context.get('screen_vals', {})
        ctx = context.copy()
        del ctx['screen_vals']
        if not screen_vals:
            raise Exception("No screen_vals found in the context!")

        wiz_id = self.create(cursor, uid, screen_vals, ctx)
        mail_ids = super(PoweremailSendWizard,
                         self).save_to_mailbox(cursor, uid, [wiz_id], ctx)
        # When using `save_async`, we leave the folder as it should be
        if not(context.get('save_async', False)):
            mailbox_obj.write(cursor, uid, mail_ids, {'folder': 'drafts'}, ctx)
        return mail_ids

PoweremailSendWizard()
