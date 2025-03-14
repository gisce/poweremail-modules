# -*- encoding: utf-8 -*-
from osv import osv, fields
from service.security import Sudo
from tools import config
import base64

class PoweremailCoreAccounts(osv.osv):
    """
    Object to store email account settings
    """
    _name = 'poweremail.core_accounts'
    _inherit = 'poweremail.core_accounts'

    # Optenir el login IMAP
    def login_imap(self, cursor, uid, core_account, imap_connection, context=None):
        if context is None:
            context = {}

        with Sudo(uid=uid, gid='giscemisc_api.group_api_user'):
            auth_login_obj = self.pool.get('poweremail.auth.login')

            if core_account.imap_auth_login_id:
                token = auth_login_obj.get_auth_token_from_api(cursor, uid, core_account.imap_auth_login_id.id, context=context)
                auth_str = self.generate_oauth_2_string(core_account.isuser, token, base64_encode=False)
                if core_account.imap_auth_login_id.auth_type == 'office365':
                    self.imap_authentication_office365(imap_connection, auth_str)
                else:
                    raise Exception("not implemented authentication")
            else:
                super(PoweremailCoreAccounts, self).login_imap(cursor, uid, core_account, imap_connection, context=context)

    def imap_authentication_office365(self, imap_conn, auth_string):
        if config.get('debug_enabled', False):
            imap_conn.debug = 4
        imap_conn.authenticate('XOAUTH2', lambda x: auth_string)

    # Optenir el login SMTP
    def login_smtp(self, cursor, uid, core_account, smtp_conn, context=None):
        if context is None:
            context = {}

        with Sudo(uid=uid, gid='giscemisc_api.group_api_user'):
            auth_login_obj = self.pool.get('poweremail.auth.login')

            if core_account.smtp_auth_login_id:
                token = auth_login_obj.get_auth_token_from_api(cursor, uid, core_account.smtp_auth_login_id.id, context=context)
                auth_str = self.generate_oauth_2_string(core_account.email_id, token, base64_encode=False)
                self.smtp_authentication(smtp_conn, auth_str)
            else:
                super(PoweremailCoreAccounts, self).login_smtp(cursor, uid, core_account, smtp_conn, context=context)

    def smtp_authentication(self, smtp_conn, auth_string):
        if config.get('debug_enabled', False):
            smtp_conn.set_debuglevel(True)
        smtp_conn.docmd('AUTH', 'XOAUTH2 {}'.format(auth_string))

    # Mètodes comuns
    def generate_oauth_2_string(self, username, access_token, base64_encode=True):
        auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
        if base64_encode:
            auth_string = base64.b64encode(auth_string)
        return auth_string

    def get_not_debug_sender(self, account):
        if account.microsoft_graph_login_id:
            from qreu.sendcontext import MicrosoftGraphSender
            return MicrosoftGraphSender(
                client_id=account.microsoft_graph_login_id.auth_api_id.client_id,
                client_secret=account.microsoft_graph_login_id.auth_api_id.client_secret,
                tenant_id=account.microsoft_graph_login_id.auth_api_id.acces_token_url.split('/')[-1],
                email_address=account.email_id
            )
        return super(PoweremailCoreAccounts, self).get_not_debug_sender(account)

    _columns = {
        'smtp_auth_login_id': fields.many2one('poweremail.auth.login', 'Auth SMTP login ID'),
        'imap_auth_login_id': fields.many2one('poweremail.auth.login', 'Auth IMAP login ID'),
        'microsoft_graph_login_id': fields.many2one('poweremail.auth.login', 'Auth with graph.microsoft.com')
    }


PoweremailCoreAccounts()
