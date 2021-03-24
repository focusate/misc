from odoo import models


class ResBank(models.Model):
    """Extend to inherit from address.format.mixin."""

    _name = 'res.bank'
    _inherit = ['res.bank', 'address.format.mixin']

    @property
    def address_fields_map(self):
        """Extend to change state/country mapping.

        state/country field name is different on res.bank.
        """
        res = super().address_fields_map
        res.update({
            'state_id': 'state',
            'country_id': 'country'
        })
        return res
