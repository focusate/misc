# Author: Silvija Butko. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Account Invoice Report Credentials",
    'version': '14.0.2.0.0-rc.1',
    'license': 'LGPL-3',
    'summary': 'Account, Invoice, Report, credentials',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Accounting/Reporting',
    'depends': [
        # odoo
        'account',
        # misc
        'report_template_credentials',
        'report_external_layout_simple',
    ],
    'data': [
        'data/ir_actions_report_data.xml',
        'reports/account_invoice_report.xml',
    ],
    'installable': True,
}
