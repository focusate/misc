# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "Unified Address Format Mixin",
    'version': '14.0.1.0.0',
    'summary': 'address format, partner, mixin',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Tools',
    'depends': [
        # odoo
        'base_setup'
    ],
    'external_dependencies': {'python': ['footil']},
    'data': [
        'views/assets.xml',
        'views/address_format_templates.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
}
