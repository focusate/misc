# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "REST Client",
    'version': '12.0.1.0.0',
    'summary': 'rest, client, manager',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Extra Tools',
    'depends': [
        'odootil'
    ],
    'data': [
        'views/rest_client_auth_views.xml',
    ],
    'external_dependencies': {'python': ['footil', 'mergedeep']},
    'installable': True,
}
