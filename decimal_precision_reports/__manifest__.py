# Author: Silvija Butko. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Decimal Precision for Reports",
    'version': '14.0.2.0.0-rc.1',
    'license': 'LGPL-3',
    'summary': 'decimal precision',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Tools',
    'depends': [
        # odoo
        'base',
    ],
    'data': [
        'data/decimal_precision_data.xml',
    ],
    'installable': True,
}
