# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Sale Order Report Credentials",
    'version': '14.0.1.0.0',
    'summary': 'sale order, report, credentials',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Sales/Reporting',
    'depends': [
        # odoo
        'sale',
        # misc
        'report_template_credentials',
        'report_external_layout_simple',
    ],
    'data': [
        'data/ir_actions_report_data.xml',
        'reports/sale_order_report.xml',
    ],
    'installable': True,
}
