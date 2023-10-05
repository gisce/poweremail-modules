import logging
import pooler
from oopgrade.oopgrade import load_data_records
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info('Adding poweremail templates source to module')
    pool.get("poweremail.templates.source")._auto_init(cursor, context={
        'module': 'poweremail_load_templates'
    })

    logger.info('Adding poweremail templates to module')
    pool.get("poweremail.templates")._auto_init(cursor, context={
        'module': 'poweremail_load_templates'
    })

    logger.info('Adding wizard to module')
    pool.get("wizard.load.poweremail.template")._auto_init(cursor, context={
        'module': 'poweremail_load_templates'
    })

    logger.info('Adding poweremail templates source view')
    load = [
        'poweremail_templates_source_tree',
        'poweremail_templates_source_form'
    ]
    load_data_records(
        cursor, 'poweremail_load_templates',
        'poweremail_templates_source_view.xml', load
    )

    logger.info('Adding poweremail templates view')
    load = [
        'view_poweremail_source_form'
    ]
    load_data_records(
        cursor, 'poweremail_load_templates',
        'poweremail_template_view.xml', load
    )

    logger.info('Adding poweremail templates source view')
    load = [
        'view_wizard_load_poweremail_template',
        'action_wizard_load_poweremail_template',
        'values_wizard_load_poweremail_template'
    ]
    load_data_records(
        cursor, 'poweremail_load_templates',
        'wizard/wizard_load_poweremail_template.xml', load
    )

    logger.info('XML refreshed for poweremail_templates_source.')

    logger.info("Updating access CSV")
    load_data(
        cursor, 'poweremail_load_templates',
        'security/ir.model.access.csv', idref=None,
        mode='update'
    )
    logger.info("CSV succesfully updated.")

def down(cursor, installed_version):
    pass


migrate = up
