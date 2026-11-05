# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64
import csv
import re

from six import PY2
if PY2:
    from six.moves import cStringIO as StringIO
else:
    from io import StringIO

from osv import osv, fields
from osv.osv import except_osv
from tools.translate import _


EMAIL_RE = re.compile(r'^[^@\s;]+@[^@\s;]+\.[^@\s;]+$')


class PoweremailCampaignRecipient(osv.osv):

    _name = 'poweremail.campaign.recipient'
    _description = 'Poweremail Campaign Recipient'
    _rec_name = 'email'

    def normalize_email(self, email):
        return (email or '').strip().lower()

    def _decode_csv_data(self, csv_data):
        if not csv_data:
            raise except_osv(
                _('Error'),
                _('You must upload a CSV file before importing recipients.')
            )
        decoded = base64.b64decode(csv_data)
        if PY2:
            return decoded
        return decoded.decode('utf-8-sig')

    def _get_existing_emails(self, cursor, uid, campaign_id, context=None):
        ids = self.search(
            cursor, uid, [('campaign_id', '=', campaign_id)],
            context=context
        )
        if not ids:
            return set()
        values = self.read(cursor, uid, ids, ['normalized_email'], context=context)
        return set([v['normalized_email'] for v in values if v['normalized_email']])

    def _validate_language(self, cursor, uid, language, context=None):
        if not language:
            return True
        lang_obj = self.pool.get('res.lang')
        return bool(lang_obj.search(
            cursor, uid, [('code', '=', language)], context=context
        ))

    def parse_csv_data(self, cursor, uid, campaign_id, csv_data, context=None,
                       check_existing=True):
        if context is None:
            context = {}
        content = self._decode_csv_data(csv_data)
        reader = csv.reader(StringIO(content), delimiter=';')
        rows = list(reader)
        if not rows:
            raise except_osv(_('Error'), _('The CSV file is empty.'))
        header = [col.strip().lower() for col in rows[0]]
        if header != ['email', 'language']:
            raise except_osv(
                _('Error'),
                _('Invalid CSV header. Expected exactly: email;language')
            )

        seen = set()
        existing = set()
        if check_existing:
            existing = self._get_existing_emails(
                cursor, uid, campaign_id, context=context
            )
        recipients = []
        summary = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'duplicate': 0,
            'empty': 0,
            'languages': {},
        }
        for row_number, row in enumerate(rows[1:], 2):
            if not row or not ''.join([c.strip() for c in row]):
                summary['empty'] += 1
                continue
            summary['total'] += 1
            log = ''
            state = 'valid'
            email = ''
            language = ''
            normalized_email = ''
            if len(row) != 2:
                state = 'invalid'
                log = _('Expected 2 columns: email;language')
            else:
                email = row[0].strip()
                language = row[1].strip()
                normalized_email = self.normalize_email(email)
                if not normalized_email or not EMAIL_RE.match(normalized_email):
                    state = 'invalid'
                    log = _('Invalid email')
                elif language and not self._validate_language(
                        cursor, uid, language, context=context):
                    state = 'invalid'
                    log = _('Invalid language')
                elif normalized_email in seen or normalized_email in existing:
                    state = 'duplicate'
                    log = _('Duplicated email')
                else:
                    seen.add(normalized_email)

            if state == 'valid':
                summary['valid'] += 1
                if language:
                    summary['languages'][language] = (
                        summary['languages'].get(language, 0) + 1
                    )
            elif state == 'duplicate':
                summary['duplicate'] += 1
            else:
                summary['invalid'] += 1

            recipients.append({
                'campaign_id': campaign_id,
                'email': email,
                'normalized_email': normalized_email,
                'language': language,
                'csv_line_number': row_number,
                'state': state,
                'log': log,
            })
        return recipients, summary

    def format_import_summary(self, summary):
        language_lines = []
        for lang in sorted(summary['languages']):
            language_lines.append('%s: %s' % (lang, summary['languages'][lang]))
        if not language_lines:
            language_lines.append(_('No valid language data.'))
        return '\n'.join([
            _('Rows read: %s') % summary['total'],
            _('Valid rows: %s') % summary['valid'],
            _('Invalid rows: %s') % summary['invalid'],
            _('Duplicate rows: %s') % summary['duplicate'],
            _('Empty rows ignored: %s') % summary['empty'],
            _('Languages:'),
        ] + language_lines)

    STATE_SELECTION = [
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('duplicate', 'Duplicate'),
        ('line_created', 'Line Created'),
    ]

    _columns = {
        'campaign_id': fields.many2one(
            'poweremail.campaign', 'Campaign', required=True,
            ondelete='cascade'
        ),
        'campaign_line_id': fields.many2one(
            'poweremail.campaign.line', 'Campaign Line', ondelete='set null'
        ),
        'email': fields.char('Email', size=256),
        'normalized_email': fields.char('Normalized Email', size=256),
        'language': fields.char('Language', size=5),
        'csv_line_number': fields.integer('CSV Line'),
        'state': fields.selection(STATE_SELECTION, 'State', required=True),
        'log': fields.text('Log'),
        'source_filename': fields.char('Source Filename', size=256),
    }

    _defaults = {
        'state': lambda *a: 'valid',
    }


PoweremailCampaignRecipient()
