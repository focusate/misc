from odoo import models, fields


class ResPartner(models.Model):
    """Extend to add field is_company_partner."""

    _inherit = 'res.partner'

    is_company_partner = fields.Boolean(
        compute='_compute_is_company_partner',
        search='_search_is_company_partner'
    )

    def _compute_is_company_partner(self):
        _find_partner_company_id = self.env[
            'res.company'
        ]._find_partner_company_id
        for partner in self:
            partner.is_company_partner = bool(
                _find_partner_company_id(partner.id)
            )

    def _search_is_company_partner(self, op, value):
        # We always find company partners, because there will be much
        # less such partners than not company partners. This way we can
        # reverse search if needed.
        # Must use sudo to search for all companies (for non admin
        # users).
        companies = self.env['res.company'].sudo().search([])
        partner_company_ids = companies.mapped('partner_id.id')
        bool_val = bool(value)
        # Searching for company partners.
        if op == '=' and bool_val or op == '!=' and not bool_val:
            return [('id', 'in', partner_company_ids)]
        # Otherwise reverse result to find not company partners.
        return [('id', 'not in', partner_company_ids)]
