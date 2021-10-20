# Author: Silvija Butko. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Report External Layout Simple",
    'version': '15.0.3.0.0-rc.1',
    'license': 'LGPL-3',
    'summary': 'Report, External, Layout, Simple, Simplified',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Reporting',
    'depends': [
        # odoo
        'web',
    ],
    'data': [
        'views/assets.xml',
        'views/report_templates.xml',
        'data/report_paperformat_data.xml',
        'data/report_layout_data.xml',
    ],
    'installable': False,
}
