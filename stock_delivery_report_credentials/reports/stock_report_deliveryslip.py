from odoo import models, api


class ReportDeliverySlip(models.AbstractModel):
    """Redefine to add helpers for delivery slip report."""

    _name = 'report.stock.report_deliveryslip'
    _description = 'Delivery Slip Report'

    @api.model
    def _get_company_partner(self, picking):
        return picking.company_id.partner_id

    @api.model
    def _get_picking_partner(self, picking):
        # Take partner from lines if no partner is set on picking
        # (partner is not required on picking).
        return picking.partner_id or picking.move_lines[:1].partner_id

    @api.model
    def _get_sender_receiver_map(self):
        return {
            'outgoing': {
                'sender': self._get_company_partner,
                'receiver': self._get_picking_partner,
            },
            'incoming': {
                'sender': self._get_picking_partner,
                'receiver': self._get_company_partner,
            },
            'internal': {
                'sender': self._get_company_partner,
                'receiver': self._get_company_partner,
            },
        }

    @api.model
    def get_sender(self, picking):
        """Get partner that is sender for picking."""
        code = picking.picking_type_id.code
        return self._get_sender_receiver_map()[code]['sender'](picking)

    @api.model
    def get_receiver(self, picking):
        """Get partner that is receiver for picking."""
        code = picking.picking_type_id.code
        return self._get_sender_receiver_map()[code]['receiver'](picking)

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'stock.report_deliveryslip')
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(docids),
            'get_sender': self.get_sender,
            'get_receiver': self.get_receiver,
        }
