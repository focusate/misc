# Author: Silvija Butko. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Credentials for Report Template",
    'version': '15.0.3.0.0-rc.1',
    'summary': 'Credentials, Report, Template, Buyer, Seller',
    'license': 'LGPL-3',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Reporting',
    'depends': [
        # misc
        'partner_registry_code',
    ],
    'data': [
        'views/report_layouts.xml',
    ],
    'installable': False,
}
