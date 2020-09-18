import os
import requests
import logging
import mergedeep

from footil.formatting import get_formatted_exception

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from .. exceptions import AuthDataError

_logger = logging.getLogger(__name__)

CODE_OK = 200


class RestClientAuth(models.AbstractModel):
    """Base Authentication model to connect with REST calls."""

    _name = 'rest.client.auth'
    _description = "REST Client Authentication"

    url = fields.Char("URL", required=True, help="Base URL for endpoints")
    auth_method = fields.Selection(
        [
            ('none', 'None'),
            ('password', 'Password'),
        ],
        required=True,
        default='none',
        copy=False)
    username = fields.Char(copy=False)
    password = fields.Char(copy=False)
    company_id = fields.Many2one(
        'res.company', default=lambda s: s.env.user.company_id)
    state = fields.Selection(
        [('draft', 'Not Confirmed'), ('confirmed', 'Confirmed')],
        default='draft',
        copy=False,
        readonly=True,
        required=True)

    @api.model
    def _get_domain(self, company_id=False):
        return [
            ('state', '=', 'confirmed'), ('company_id', '=', company_id)
        ]

    @api.one
    @api.constrains('url')
    def _check_url(self):
        self.env['odootil'].check_url(self.url)

    @api.one
    @api.constrains('state', 'company_id')
    def _check_auth_unique(self):
        if self.state == 'confirmed':
            domain = self._get_domain(company_id=self.company_id.id)
            if self.search_count(domain) > 1:
                raise ValidationError(
                    _("Authentication record must be unique per company or "
                        "can have one global authentication record."))

    @api.model
    def get_auth(self, company_id):
        """Return auth object for specific company.

        If no auth can be found for specific company, defaults to global
        auth if there is one.

        Args:
            company_id (int): Company ID related with auth object.

        Returns:
            rest.client.auth

        """
        auth = self.search(self._get_domain(company_id=company_id))
        if not auth:
            # Search without company specified.
            auth = self.search(self._get_domain())
        return auth

    def get_data(self):
        """Return base URL and auth data in expected requests format."""
        self.ensure_one()
        data = {'url': self.url, 'auth': None}
        if self.auth_method == 'password':
            data['auth'] = {'auth': (self.username, self.password)}
        return data

    def action_confirm(self):
        """Confirm Authentication records to be used."""
        self.write({'state': 'confirmed'})

    def action_to_draft(self):
        """Set Authentication records back to draft state."""
        self.write({'state': 'draft'})


class RestClientController(models.AbstractModel):
    """Base model as a client side controller with remote system.

    This model must be inherited when implementing specific controller.
    """

    _name = 'rest.client.controller'
    _description = "REST Client Controller"
    _response_type = 'json'
    _auth_model = None

    def _get_auth_data(self, company_id):
        if self._auth_model:
            auth = self.env[self._auth_model].get_auth(company_id)
            if auth:
                return auth.get_data()

    @api.model
    def get_endpoint(self, base_url, uri_expression, args=None):
        """Return endpoint using base URL and URI pattern.

        Args:
            base_url (str): base URL for endpoint.
            uri_expression (str): URI expression that is appended to
                base URL to form endpoint.
            args (tuple): extra arguments to render variables in
                endpoint if there are any (default: {None}).

        Returns:
            str: generated endpoint.

        """
        endpoint = os.path.join(base_url, uri_expression)
        if args:
            return endpoint % args
        return endpoint

    @api.model
    def is_controller_enabled(self):
        """Return True if controller is enabled, False otherwise.

        Override to implement enabler logic.
        """
        return True

    @api.model
    def _extract_response_body(self, response):
        # TODO: implement body types: content, body, raw, exc.
        if self._response_type == 'json':
            return response.json()
        return response.text

    @api.model
    def _check_response(self, response, method_name, endpoint):
        if response.status_code != CODE_OK:
            body = self._extract_response_body(response)
            _logger.error(
                "Endpoint '%s' call failed. Method: %s Error Code: %s, "
                "Response: %s", endpoint, method_name, response.status_code,
                body)
            return False
        return True

    def _validate_endpoint_with_uri_item(self, endpoint, uri_item):
        if not (bool(endpoint) ^ bool(uri_item)):
            raise ValidationError(
                _("Programming error: endpoint and uri_item must satisfy"
                    " XOR condition."))

    @api.model
    def call_rest_method(self, method_name, options=None):
        """Call specified REST method.

        Args:
            method_name: HTTP verb to use (e.g GET).
            options (dict): options for REST method calls:
                endpoint (str): endpoint path to use in REST call
                    (default: {None}).
                uri_item (tuple): two pair tuple, where first item is
                    uri_expression and second, optional tuple of
                    endpoint arguments. endpoint and uri_item have
                    exclusive OR condition (default: {None}).
                company_id (int): company ID to use in finding related
                    auth object if there is any (default: {None}).
                kwargs (dict): extra keyword arguments for call, like
                    payload, auth headers etc. (default: {None}).

        Returns:
            response obj

        Raises:
            ValidationError

        """
        def get_endpoint_from_uri_item(uri_item, auth_data):
            uri_expression, endpoint_args = uri_item
            try:
                url = auth_data['url']
            except TypeError:
                raise AuthDataError(
                    _("No Authentication object found to get base URL. "
                        "Check Authentication objects configuration."))
            return self.get_endpoint(
                url, uri_expression, args=endpoint_args)

        def merge_kwargs(kwargs, auth_data):
            if auth_data and auth_data['auth']:
                mergedeep.merge(kwargs, auth_data['auth'])

        if not options:
            options = {}
        endpoint, uri_item = options.get('endpoint'), options.get('uri_item')
        self._validate_endpoint_with_uri_item(endpoint, uri_item)
        company_id = options.get('company_id', False)
        auth_data = self._get_auth_data(company_id)
        kwargs = options.get('kwargs', {})
        merge_kwargs(kwargs, auth_data)
        if uri_item:
            endpoint = get_endpoint_from_uri_item(uri_item, auth_data)
        method = getattr(requests, method_name)
        try:
            response = method(endpoint, **kwargs)
            self._check_response(response, method_name, endpoint)
            return response
        # We raise on unexpected exceptions.
        except Exception:
            raise ValidationError(get_formatted_exception())
