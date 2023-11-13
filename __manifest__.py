# -*- coding: utf-8 -*-
{
    'name': 'mail_automation',
    'version': '1.0',
    'category': 'Custom',
    'sequence': 15,
    'summary': 'Odoo v15 module with custom features for roc project',
    'description': "",
    'website': '',
    'depends': [
        'base',
        'crm',
        'mail',
    ],
    'data': [
        'data/ir_cron_data.xml',
        'views/mail_automation_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
