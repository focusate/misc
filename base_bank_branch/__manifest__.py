# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Bank Branches",
    'version': '14.0.1.0.0',
    'summary': 'bank, branch',
    'license': 'LGPL-3',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Tools',
    'depends': [
        # odoo
        'base'
    ],
    'data': [
        'views/res_bank_views.xml',
    ],
    'installable': True,
}
