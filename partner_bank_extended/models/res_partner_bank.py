from odoo import models, fields


class ResPartnerBank(models.Model):
    """Extend to add field report_ref_ids."""

    _inherit = 'res.partner.bank'

    is_company_partner = fields.Boolean(
        related='partner_id.is_company_partner',
        string="Is Our Bank Account",
    )
    report_ref_ids = fields.Many2many(
        'ir.actions.report',
        'partner_bank_report_ref_rel',
        'partner_bank_id',
        'report_id',
        string="Reports",
        help="Reports that are related with this bank account"
    )
    account_holder_name_in_report = fields.Boolean(
        "Include Account Holder Name In Reports",
        help="Will use Account Holder name from related partner if custom "
        "name not specified on account.")

    @property
    def _account_holder_name(self):
        self.ensure_one()
        # Following similar approach as in SEPA module.
        # NOTE. Technically partner name can be False (depending on type
        # ), so defaulting to empty string to make sure it won't crash.
        return (self.acc_holder_name or self.partner_id.name or '')[:71]
