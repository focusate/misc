from odoo import models, api


class ReportInvoice(models.AbstractModel):
    """Extend to implement some methods for custom account template."""

    # NOTE. `report.account.report_invoice_with_payments` inherits
    # from `report.account.report_invoice`, so we don't need to add
    # same methods separately.
    _inherit = 'report.account.report_invoice'

    def _get_invoice_direction(self, invoice):
        # Its now account.move, but we still call it invoice to make it
        # more clear what kind of move it is.
        if invoice.move_type in ('out_invoice', 'out_refund'):
            return 'out'
        return 'in'

    @api.model
    def _get_seller(self, invoice):
        if self._get_invoice_direction(invoice) == 'out':
            return invoice.company_id.partner_id
        return invoice.partner_id

    @api.model
    def _get_buyer(self, invoice):
        if self._get_invoice_direction(invoice) == 'in':
            return invoice.company_id.partner_id
        return invoice.partner_id

    @api.model
    def _get_bank_accounts_to_display(self, invoice):
        # Assuming report models start with `report.` prefix.
        report_name = self._name.replace('report.', '', 1)  # replace first
        reports = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name)]
        )
        extra_bank_accounts = reports.mapped('partner_bank_ref_ids').filtered(
            lambda r: r.company_id == invoice.company_id or not r.company_id
        )
        return invoice.partner_bank_id | extra_bank_accounts

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data=data)
        res.update({
            'report_type': data.get('report_type') if data else '',
            'get_seller': self._get_seller,
            'get_buyer': self._get_buyer,
            'get_invoice_direction': self._get_invoice_direction,
            'get_bank_accounts_to_display': self._get_bank_accounts_to_display
        })
        return res
