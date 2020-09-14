from odoo import models, api

GROUP_CONTROLLER_XMLID = 'rest_client_demo.controller_group_use'


class RestClientTestAuth(models.Model):
    """Model to handle test auth."""

    _name = 'rest.client.test.auth'
    _inherit = 'rest.client.auth'
    _description = "REST Client Test Authentication"


class RestClientTestController(models.AbstractModel):
    """Test controller model."""

    _name = 'rest.client.test.controller'
    _inherit = 'rest.client.controller'
    _description = "Rest Client Controller"
    _response_type = 'json'
    _auth_model = 'rest.client.test.auth'

    @api.model
    def is_controller_enabled(self):
        """Override to implement enabler."""
        group_user = self.env.ref('base.group_user')
        group_controller = self.env.ref(GROUP_CONTROLLER_XMLID)
        return group_controller in group_user.implied_ids
