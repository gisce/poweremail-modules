# -*- encoding: utf-8 -*-
from osv import osv, fields
import msal


class PoweremailAuthLogin(osv.osv):
    _name = 'poweremail.auth.login'
    _description = 'Auth login for poweremail'
    _rec_name = 'auth_type'

    _columns = {
        'auth_type': fields.selection([
            ('office365', 'MS Office 365')
        ], 'Server type'),
        'auth_api_id': fields.many2one('giscemisc.api.auth', 'Auth API', required=True, ondelete='cascade', help=''),
    }

    def get_auth_token_from_api(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        auth_obj = self.pool.get('giscemisc.api.auth')

        auth_id = self.read(cursor, uid, ids, ['auth_api_id'], context=context)['auth_api_id'][0]
        conf = auth_obj.read(cursor, uid, auth_id, [], context=context)

        app = msal.ConfidentialClientApplication(
            conf['client_id'], authority=conf['acces_token_url'],
            client_credential=conf['client_secret']
        )

        conf['scopes'] = [conf['scopes']]
        result = app.acquire_token_silent(conf['scopes'], account=None)
        if not result:
            print("No suitable token in cache.  Get new one.")
            result = app.acquire_token_for_client(scopes=conf['scopes'])

        return result['access_token']

    # def get_auth_token_from_api(self, cursor, uid, poweremail_account_id, server_type, context=None):
    #     if context is None:
    #         context = {}
    #
    #     pwe_obj = self.pool.get('poweremail.core_accounts')
    #     auth_obj = self.pool.get('giscemisc.api.auth')
    #
    #     # pwe_email = pwe_obj.read(cursor, uid, poweremail_account_id, ['email_id'], context=context)['email_id']
    #
    #     auth_id = self.pool.get('ir.model.data').get_object_reference(
    #         cursor, uid, 'poweremail_auth', 'office360_ecasa_auth'
    #     )[1]
    #     Aquí provava de posar el valor de scopes en un llista ja que és l'única diferència que veia.
    #     info = auth_obj.read(cursor, uid, auth_id, ['scopes'], context=context)['scopes']
    #     info = [info]
    #     auth_obj.write(cursor, uid, auth_id, {'scopes': info}, context=context)
    #
    #     auth_session = auth_obj._generate_auth(cursor, uid, auth_id, context=context)
    #     token = auth_session.token
    #     print(token)
    #
    # def get_token_imap(self, cursor, uid, token, context=None):
    #     if context is None:
    #         context = {}


PoweremailAuthLogin()
