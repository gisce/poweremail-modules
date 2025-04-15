from report.interface import report_int
from osv import osv
from base64 import b64decode


class SignatureReport(report_int):
    _name = 'report.signature.email.download.audit.trail'

    def create(self, cr, uid, ids, datas, context=None):
        if context is None:
            context = {}
        document = b64decode(datas.get('pdf', None))
        return document, 'pdf'


SignatureReport('report.signature.email.download.audit.trail')