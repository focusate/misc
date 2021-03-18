# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Bank Account Improvements",
    'version': '14.0.1.0.0',
    'summary': 'partner, banks, reports, reference, relation',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Tools',
    'depends': [
        # misc
        'base_is_company_partner',
    ],
    'data': [
        'views/res_partner_bank_views.xml',
        'views/ir_actions_report_views.xml',
    ],
    'installable': True,
}
