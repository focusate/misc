from odoo import models, fields, api


class ResPartner(models.Model):
    """Extend to add is_commercial_partner field."""

    _inherit = 'res.partner'

    is_commercial_partner = fields.Boolean(
        "Is Commercial Partner",
        compute='_compute_is_commercial_partner',
        store=True)

    @api.depends('commercial_partner_id')
    def _compute_is_commercial_partner(self):
        for rec in self:
            rec.is_commercial_partner = rec == rec.commercial_partner_id
