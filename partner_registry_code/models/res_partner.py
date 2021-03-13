from footil.formatting import strip_space

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

REGISTRY_KEY = 'company_registry'


class ResPartner(models.Model):
    """Extend model to add field for storing company registry code."""

    _inherit = 'res.partner'

    company_registry = fields.Char(
        help="Registry code",
        index=True,
        copy=False,
    )

    @api.constrains(REGISTRY_KEY, 'is_commercial_partner', 'company_id')
    def _check_company_registry(self):
        for rec in self:
            company_registry = rec.company_registry
            if rec.company_registry and rec.is_commercial_partner:
                matches = rec.sudo().search_multicompany_count(
                    [
                        (REGISTRY_KEY, '=ilike', company_registry),
                        ('is_commercial_partner', '=', True),
                    ],
                    options={
                        'multi_comp_rule_xml_id': 'base.res_partner_rule',
                        'company_id': rec.company_id.id,
                    }
                )
                if matches > 1:
                    raise ValidationError(
                        _("Company Registry code must be unique per "
                            "commercial partner.\nThere might be a partner "
                            "which belongs to another company or an archived "
                            "partner with the same code too. Company "
                            "Registry: %s") % company_registry
                    )

    def _set_company_registry_on_company(self, company_registry):
        """Set company registry value from partner on company.

        Related company is company that is related with partner via
        `res.company -> partner_id` field.
        """
        if not self._context.get('company_registry_set'):
            # Find companies that are related with partner.
            Company = companies = self.env['res.company']
            for rec in self:
                # There can only be o2o relation between partner and company,
                # because there is a constraint which does not allow to relate
                # the same partner with different companies.
                companies |= Company.search([('partner_id', '=', rec.id)])
            if companies:
                companies.with_context(
                    company_registry_set=True).write(
                    {REGISTRY_KEY: company_registry})

    def _commercial_fields(self):
        """Extend to add company_registry field."""
        res = super()._commercial_fields()
        res.append(REGISTRY_KEY)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Extend to format company_registry without any spaces."""
        for vals in vals_list:
            if vals.get(REGISTRY_KEY):
                vals[REGISTRY_KEY] = strip_space(vals[REGISTRY_KEY])
        return super().create(vals_list)

    def write(self, vals):
        """Extend to update related company with company registry.

        Also formats company_registry value.
        """
        if vals.get(REGISTRY_KEY):
            vals[REGISTRY_KEY] = strip_space(vals[REGISTRY_KEY])
        res = super().write(vals)
        # Note this is only valid for write, because on create, we know
        # there won't be any related company (this is different than
        # `company_id` relation).
        if REGISTRY_KEY in vals:
            # Value to set for related company.
            self._set_company_registry_on_company(vals[REGISTRY_KEY])
        return res
