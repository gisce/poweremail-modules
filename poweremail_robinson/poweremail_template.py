from osv import osv, fields


class PoweremailTemplates(osv.osv):
    _name = 'poweremail.templates'
    _inherit = 'poweremail.templates'

    def _generate_mailbox_item_from_template(self, cursor, uid, template, record_id, context=None):
        mailbox_obj = self.pool.get('poweremail.mailbox')
        mailbox_id = super(PoweremailTemplates, self)._generate_mailbox_item_from_template(
                                                        cursor, uid, template, record_id, context=context)
        mailbox_email = mailbox_obj.read(cursor, uid, mailbox_id, ['pem_to'], context=context)['pem_to']
        # Comprovem si existeix un registre de poweremail_template_robinson amb el mateix email i la id del template
        # (o template a null).
        robinson_obj = self.pool.get('poweremail.template.robinson')
        search_params = [('template_id', '=', template.id), ('email', '=', mailbox_email)]
        robinson_ids_1 = robinson_obj.search(cursor, uid, search_params, context=context)
        search_params = [('template_id', '=', False), ('email', '=', mailbox_email)]
        robinson_ids_2 = robinson_obj.search(cursor, uid, search_params, context=context)
        robinson_ids = robinson_ids_1 + robinson_ids_2
        if robinson_ids:
            mailbox_obj.write(cursor, uid, [mailbox_id], {'folder': 'robinson'}, context=context)

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
        'email': fields.text('Email', required = True)
    }


PoweremailTemplatRobinson()