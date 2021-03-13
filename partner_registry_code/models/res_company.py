from odoo import models, api

from . res_partner import REGISTRY_KEY


class ResCompany(models.Model):
    """Extend to sync company registry field from company to partner."""

    _inherit = 'res.company'

    def _set_company_registry_on_partner(self):
        self.ensure_one()
        if not self._context.get('company_registry_set'):
            self.partner_id.with_context(company_registry_set=True).write(
                {REGISTRY_KEY: self.company_registry})

    @api.model
    def create(self, vals):
        """Extend to set company registry on partner."""
        rec = super(ResCompany, self).create(vals)
        if REGISTRY_KEY in vals:
            rec._set_company_registry_on_partner()
        return rec

    def write(self, vals):
        """Extend to set company registry on partner."""
        res = super(ResCompany, self).write(vals)
        if REGISTRY_KEY in vals:
            for company in self:
                company._set_company_registry_on_partner()
        return res
