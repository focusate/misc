from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    """Extend to add address format options."""

    _inherit = 'res.config.settings'

    use_country_address_format = fields.Boolean(
        related='company_id.use_country_address_format',
        readonly=False,
    )
    # Adding related because field starting with `default_` is special.
    related_default_address_format = fields.Text(
        related='company_id.default_address_format',
        readonly=False,
    )
