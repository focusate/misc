# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Odoo Utilities",
    'version': '14.0.3.0.0-rc.1',
    'summary': 'odoo, utilities, helper methods',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Technical/Tools',
    'depends': [
        'web'
    ],
    'external_dependencies': {
        'python': ['footil', 'num2words', 'yattag', 'validators']
    },
    'data': [
        'security/ir.model.access.csv',
        'views/odootil.xml'
    ],
    'installable': True,
}
