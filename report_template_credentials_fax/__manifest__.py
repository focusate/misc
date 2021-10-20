# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Partner Credentials - Fax",
    'version': '15.0.1.0.0',
    'summary': 'Credentials, Report, Template, fax',
    'license': 'LGPL-3',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Reporting',
    'depends': [
        # misc
        'report_template_credentials',
        # oca-partner-contact
        'partner_fax',
    ],
    'data': [
        'views/report_layouts.xml',
    ],
    'installable': False,
}
