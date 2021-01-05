# Author: Andrius Laukavičius. Copyright: JSC Focusate.
# See LICENSE file for full copyright and licensing details.
{
    'name': "REST Client",
    'version': '14.0.2.0.0-rc.1',
    'summary': 'rest, client, manager',
    'license': 'OEEL-1',
    'author': "Focusate",
    'website': "http://www.focusate.eu",
    'category': 'Hidden/Tools',
    'depends': [
        'odootil'
    ],
    'data': [
        'views/rest_client_auth_views.xml',
    ],
    'external_dependencies': {'python': ['footil', 'mergedeep']},
    'installable': True,
}
