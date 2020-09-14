import requests_mock

from odoo.addons.rest_client.exceptions import AuthDataError
from odoo.addons.rest_client.tests.common import DUMMY_URL, DUMMY_ENDPOINT

from . import common


class TestRestClientDemoController(common.TestRestClientDemoCommon):
    """Class to test demo controller."""

    @requests_mock.Mocker()
    def test_01_call_rest_method(self, mock):
        """Call REST method when uri_item is passed, but no auth obj."""
        # Make sure no auth obj can be found.
        (
            self.test_auth_1 | self.test_auth_2 | self.test_auth_3
        ).action_to_draft()
        endpoint = DUMMY_ENDPOINT
        self.mock_get(
            mock, endpoint, response_body={'status_code': 200, 'json': {}}
        )
        with self.assertRaises(AuthDataError):
            self.RestClientTestController.call_rest_method(
                'get',
                options={
                    'uri_item': ('my_uri/%s', ['a']),
                    'company_id': self.main_company.id,
                }
            )

    @requests_mock.Mocker()
    def test_02_call_rest_method(self, mock):
        """Call REST method when uri_item is passed and is auth obj.

        Auth obj method is None.
        """
        endpoint = DUMMY_URL + '/my_uri/a'
        self.mock_get(
            mock, endpoint, response_body={'status_code': 200, 'json': {}}
        )
        response = self.RestClientTestController.call_rest_method(
            'get',
            options={
                'uri_item': ('my_uri/%s', ('a',)),
                'company_id': self.main_company.id,
            }
        )
        self.assertEqual(response.status_code, 200)

    @requests_mock.Mocker()
    def test_03_call_rest_method(self, mock):
        """Call REST method when uri_item is passed and is auth obj.

        Auth obj method is Password.
        """
        endpoint = DUMMY_URL + '/my_uri'
        self.mock_get(
            mock, endpoint, response_body={'status_code': 200, 'json': {}}
        )
        response = self.RestClientTestController.call_rest_method(
            'get',
            options={
                'uri_item': ('my_uri', False),
                'company_id': self.company_2.id,
                'kwargs': {'headers': {'my_header': '123'}}
            }
        )
        self.assertEqual(response.status_code, 200)
