# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Delivery Slip Report Credentials",
    'version': '14.0.1.0.0',
    'license': 'LGPL-3',
    'summary': 'stock, delivery, slip, report, credentials',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Inventory/Reporting',
    'depends': [
        # odoo
        'sale_stock',
        # misc
        'report_template_credentials',
        'report_external_layout_simple',
    ],
    'data': [
        'data/ir_actions_report_data.xml',
        'reports/stock_report_deliveryslip.xml',
    ],
    'installable': True,
}
