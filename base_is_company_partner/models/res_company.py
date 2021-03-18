from odoo import models, tools


class ResCompany(models.Model):
    """Extend to add _is_company_partner method."""

    _inherit = 'res.company'

    @tools.ormcache('partner_id')
    def _find_partner_company_id(self, partner_id):
        return self.sudo().search(
            [('partner_id', '=', partner_id)], limit=1
        ).id

    # NOTE. cache is always cleared on write in standard Odoo already,
    # so we don't need to extend write.

    def unlink(self):
        """Extend to clear _is_company_partner cache."""
        res = super().unlink()
        self._find_partner_company_id.clear_cache(self.env[self._name])
        return res
