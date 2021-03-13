# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Is Partner Commercial Entity",
    'version': '14.0.3.0.0-rc.1',
    'summary': 'Identify if partner is commercial entity',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Tools',
    'depends': [
        # odoo
        'base'
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
}
