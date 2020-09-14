import requests_mock

from odoo.tools import mute_logger
from odoo.exceptions import ValidationError

from . import common


class TestRestClientController(common.TestRestClientCommon):
    """Class to test REST client controller."""

    def test_01_get_endpoint(self):
        """Get endpoint without args."""
        endpoint = self.RestClientController.get_endpoint(
            'https://abc.com', 'my_pattern/a')
        self.assertEqual(endpoint, 'https://abc.com/my_pattern/a')

    def test_02_get_endpoint(self):
        """Get endpoint with args."""
        endpoint = self.RestClientController.get_endpoint(
            'https://abc.com', 'my_pattern/%s/test/%s', args=('a', 'b'))
        self.assertEqual(endpoint, 'https://abc.com/my_pattern/a/test/b')

    @requests_mock.Mocker()
    def test_03_call_rest_method(self, mock):
        """Call REST when response is 'ok'."""
        endpoint = common.DUMMY_ENDPOINT
        self.mock_get(
            mock, endpoint, response_body={'status_code': 200, 'json': {}}
        )
        response = self.RestClientController.call_rest_method(
            'get', options={'endpoint': endpoint})
        self.assertEqual(response.status_code, 200)

    @requests_mock.Mocker()
    @mute_logger(common.REST_CLIENT_MODULE_PATH)
    def test_04_call_rest_method(self, mock):
        """Call REST when response is 'bad_data'."""
        endpoint = common.DUMMY_ENDPOINT
        self.mock_post(
            mock, endpoint, response_body={'status_code': 400, 'json': {}})
        response = self.RestClientController.call_rest_method(
            'post',
            options={
                'endpoint': endpoint,
                'kwargs': {
                    'data': {'my_bad_data': 123},
                    'auth': ('user', 'passwd')
                }
            }
        )
        self.assertEqual(response.status_code, 400)

    @requests_mock.Mocker()
    @mute_logger(common.REST_CLIENT_MODULE_PATH)
    def test_05_call_rest_method(self, mock):
        """Call REST when response is 'bad_auth'."""
        endpoint = common.DUMMY_ENDPOINT
        self.mock_put(
            mock, endpoint, response_body={'status_code': 401, 'json': {}})
        response = self.RestClientController.call_rest_method(
            'put',
            options={
                'endpoint': endpoint,
                'kwargs': {
                    'data': {'my_good_data': 123},
                    'auth': ('user', 'bad_passwd'),
                }
            }
        )
        self.assertEqual(response.status_code, 401)

    @requests_mock.Mocker()
    @mute_logger(common.REST_CLIENT_MODULE_PATH)
    def test_06_call_rest_method(self, mock):
        """Call REST when response is 'bad_page'."""
        endpoint = common.DUMMY_ENDPOINT
        self.mock_get(
            mock, endpoint, response_body={'status_code': 404, 'json': {}})
        response = self.RestClientController.call_rest_method(
            'get',
            options={'endpoint': endpoint},
        )
        self.assertEqual(response.status_code, 404)

    @requests_mock.Mocker()
    @mute_logger(common.REST_CLIENT_MODULE_PATH)
    def test_07_call_rest_method(self, mock):
        """Call REST when response invalid endpoint is passed."""
        endpoint = 'invalid_endpoint'
        self.mock_get(mock, endpoint=endpoint)
        with self.assertRaises(ValidationError):
            self.RestClientController.call_rest_method(
                'get', options={'endpoint': endpoint})

    def test_08_call_rest_method(self):
        """Call REST when endpoint/uri_pattern is not XOR.

        Case 1: both endpoint and uri_item is used.
        Case 2: no endpoint nor uri_item is used.
        """
        # Case 1.
        endpoint = 'my_endpoint'
        uri_item = ('my_uri_pattern', False)
        with self.assertRaises(ValidationError):
            self.RestClientController.call_rest_method(
                'get', options={'endpoint': endpoint, 'uri_item': uri_item})
        # Case 2.
        with self.assertRaises(ValidationError):
            self.RestClientController.call_rest_method(
                'get', options={'endpoint': False, 'uri_item': False})
