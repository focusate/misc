# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "REST Client Demo",
    'version': '12.0.1.0.0',
    'summary': 'rest, client, manager, demo',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Extra Tools',
    'depends': [
        'rest_client'
    ],
    'data': [
        'security/rest_client_demo_groups.xml',
        'security/ir.model.access.csv',
        'security/test_models_security.xml',
    ],
    'installable': True,
}
