# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Odoo Utilities",
    'version': '12.0.2.15.0',
    'summary': 'odoo, utilities, helper methods',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Extra Tools',
    'depends': [
        'web'
    ],
    'external_dependencies': {'python': ['footil', 'num2words', 'yattag']},
    'data': ['views/odootil.xml'],
    'installable': True,
}
