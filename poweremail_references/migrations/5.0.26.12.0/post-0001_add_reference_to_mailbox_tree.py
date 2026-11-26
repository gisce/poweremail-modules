# -*- coding: utf-8 -*-
from __future__ import absolute_import
from oopgrade.oopgrade import MigrationHelper
from tools.config import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    module = 'poweremail_references'
    mh = MigrationHelper(cursor, module)
    file = 'poweremail_mailbox_view.xml'
    views = [
        'poweremail_reference_all_emails_tree',
        'poweremail_reference_inbox_tree',
        'poweremail_reference_drafts_tree',
        'poweremail_reference_outbox_tree',
        'poweremail_reference_sentbox_tree',
        'poweremail_reference_followbox_tree',
        'poweremail_reference_trashbox_tree',
        'poweremail_reference_errorbox_tree'
    ]
    mh.update_xml_records(xml_path=file, update_record_ids=views)


def down(cursor, installed_version):
    pass


migrate = up
