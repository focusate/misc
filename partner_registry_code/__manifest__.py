# Author: Eimantas Nėjus. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Partners Company Registry Code',
    'version': '14.0.4.0.0-rc.1',
    'summary': 'partner, company, code, registry',
    'license': 'LGPL-3',
    'author': 'Focusate',
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Tools',
    'depends': [
        # odoo
        'base_setup',
        # misc
        'base_is_commercial_partner',
        'odootil',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
