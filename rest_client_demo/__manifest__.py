# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "REST Client Demo",
    'version': '15.0.2.0.0-rc.1',
    'summary': 'rest, client, manager, demo',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Technical/Demo',
    'depends': [
        'rest_client'
    ],
    'data': [
        'security/rest_client_demo_groups.xml',
        'security/ir.model.access.csv',
        'security/test_models_security.xml',
    ],
    'installable': False,
}
