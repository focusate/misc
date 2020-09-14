from odoo.addons.odootil.tests.common import SavepointCaseAccess

DUMMY_URL = 'http://dummy-url.com'
DUMMY_ENDPOINT = "%s/my_path" % DUMMY_URL
REST_CLIENT_MODULE_PATH = 'odoo.addons.rest_client.models.rest_client'


class TestRestClientCommon(SavepointCaseAccess):
    """Common class for REST client tests."""

    @classmethod
    def setUpClass(cls):
        """Set up common data."""
        super().setUpClass()
        cls.RestClientController = cls.env['rest.client.controller']
        # Country.
        cls.country_usa = cls.env.ref('base.us')
        # Company.
        cls.main_company = cls.env.ref('base.main_company')
        # Partner.
        cls.ResPartner = cls.env['res.partner']
        cls.partner_azure = cls.env.ref('base.res_partner_12')

    @classmethod
    def _get_auth_model(cls):
        raise NotImplementedError()

    @classmethod
    def _create_auth(cls, vals=None):
        if not vals:
            vals = {}
        vals.setdefault('url', DUMMY_URL)
        return cls._get_auth_model().create(vals)

    def _get_mock_args(self, endpoint, response_body=None):
        if not response_body:
            response_body = {}
        return ([endpoint], response_body)

    def _mock_method(self, method, mock, endpoint, response_body=None):
        """Mock requests METHOD for specific case.

        Args:
            method: HTTP verb.
            mock (requests_mock.Mocker): mock object to use in post.
            endpoint (str): endpoint for request.
            response_body (dict): options to build response body.
                (default: {None}).

        Returns:
            None

        """
        args, kwargs = self._get_mock_args(
            endpoint, response_body=response_body)
        getattr(mock, method)(*args, **kwargs)

    def mock_post(self, mock, endpoint, response_body=None):
        """Mock post method."""
        self._mock_method('post', mock, endpoint, response_body=response_body)

    def mock_put(self, mock, endpoint, response_body=None):
        """Mock put method."""
        self._mock_method('put', mock, endpoint, response_body=response_body)

    def mock_get(self, mock, endpoint, response_body=None):
        """Mock get method."""
        self._mock_method('get', mock, endpoint, response_body=response_body)
