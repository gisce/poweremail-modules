from osv import osv
from tools import config
from oorq.decorators import job


class PoweremailTemplates(osv.osv):
    _name = 'poweremail.templates'
    _inherit = 'poweremail.templates'

    @job(queue=config.get('poweremail_render_queue', 'poweremail'), on_commit=True, at_front=True)
    def generate_mail_in_background_at_front(self, cursor, uid, template_id, ids, context=None):
        return super(PoweremailTemplates, self).generate_mail(
            cursor, uid, template_id, ids, context
        )

    @job(queue=config.get('poweremail_render_queue', 'poweremail'), on_commit=True)
    def generate_mail_in_background(self, cursor, uid, template_id, ids, context=None):
        return super(PoweremailTemplates, self).generate_mail(
            cursor, uid, template_id, ids, context
        )

    def generate_mail(self, cursor, uid, template_id, ids, context=None):
        priority = self.read(cursor, uid, template_id, ['def_priority'])['def_priority']
        if priority == '2':
            method = getattr(self, 'generate_mail_in_background_at_front')
        else:
            method = getattr(self, 'generate_mail_in_background')
        return method(cursor, uid, template_id, ids, context)


PoweremailTemplates()
