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
