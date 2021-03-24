from odoo import models


class ResPartner(models.Model):
    """Extend to inherit address.format.mixin."""

    _name = 'res.partner'
    _inherit = ['res.partner', 'address.format.mixin']
