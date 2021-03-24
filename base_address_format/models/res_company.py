from odoo import models, fields, api


class ResCompany(models.Model):
    """Extend to inherit from address.format.mixin."""

    _name = 'res.company'
    _inherit = ['res.company', 'address.format.mixin']

    @api.model
    def _get_default_address_format(self):
        return (
            '%(street)s, %(street2)s, %(zip)s,'
            ' %(city)s, %(state_code)s, %(country_name)s'
        )

    use_country_address_format = fields.Boolean(default=True)
    default_address_format = fields.Text(default=_get_default_address_format)
