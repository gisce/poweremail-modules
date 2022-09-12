from osv import osv, fields


class PoweremailTemplates(osv.osv):
    _name = 'poweremail.templates'
    _inherit = 'poweremail.templates'

    def _generate_mailbox_item_from_template(self, cursor, uid, template, record_id, context=None):
        robinson_obj = self.pool.get('poweremail.template.robinson')
        mailbox_obj = self.pool.get('poweremail.mailbox')

        mailbox_id = super(PoweremailTemplates, self)._generate_mailbox_item_from_template(
            cursor, uid, template, record_id, context=context
        )
        mailbox_v = mailbox_obj.read(cursor, uid, mailbox_id, ['pem_to'], context=context)
        mails = mailbox_v['pem_to'].split(',') if mailbox_v['pem_to'] else []

        mailbox_wv = {'folder': 'robinson'}
        robinson_ids = []
        for mail in mails:
            # Comprovem si existeix un registre de poweremail_template_robinson
            # amb el mateix email i la id del template (o template a null).

            dmn = [('template_id', '=', False), ('email', '=', mail)]
            robinson_ids = robinson_obj.search(cursor, uid, dmn, context=context)
            if robinson_ids:
                break
            dmn = [('template_id', '=', template.id), ('email', '=', mail)]
            robinson_ids = robinson_obj.search(cursor, uid, dmn, context=context)
            if robinson_ids:
                break

        if robinson_ids:
            mailbox_obj.write(cursor, uid, [mailbox_id], mailbox_wv, context=context)

        return mailbox_id

    def check_outbox(self, cursor, uid, mailbox_id, context=None):
        super_bool = super(PoweremailTemplates, self).check_outbox(cursor, uid, mailbox_id, context=context)
        mailbox_obj = self.pool.get('poweremail.mailbox')
        folder = mailbox_obj.read(cursor, uid, mailbox_id, ['folder'], context=context)['folder']
        if folder == 'robinson' or not super_bool:
            res = False
        else:
            res = True
        return res


PoweremailTemplates()


class PoweremailTemplatRobinson(osv.osv):

    _name = 'poweremail.template.robinson'

    _columns = {
        'template_id': fields.many2one('poweremail.templates', 'Template'),
        'email': fields.char('Email', size=128, required=True)
    }


PoweremailTemplatRobinson()