from odoo import models, fields


class IrActionsReport(models.Model):
    """Extend to add field partner_bank_ref_ids."""

    _inherit = 'ir.actions.report'

    partner_bank_ref_ids = fields.Many2many(
        'res.partner.bank',
        'partner_bank_report_ref_rel',
        'report_id',
        'partner_bank_id',
        string="Bank Accounts",
        domain=[('partner_id.is_company_partner', '=', True)],
        help="Bank accounts that are related with this report"
    )
