from odoo.addons.odootil.tests.common import TestBaseCommon


class TestDeliverySlipHelpers(TestBaseCommon):
    """Class to test delivery slip report helpers."""

    @classmethod
    def setUpClass(cls):
        """Set up pickings for testing."""
        super(TestDeliverySlipHelpers, cls).setUpClass()
        cls.ReportDeliverySlip = cls.env['report.stock.report_deliveryslip']
        cls.ResPartner = cls.env['res.partner']
        cls.picking_out = cls.env.ref(
            'stock.outgoing_shipment_main_warehouse6')
        cls.picking_in = cls.env.ref('stock.incomming_shipment1')
        cls.partner_main = cls.env.ref('base.main_partner')
        cls.partner_wood_corner = cls.env.ref('base.res_partner_1')
        cls.partner_azure = cls.env.ref('base.res_partner_12')

    def test_01_sender_receiver(self):
        """Get sender/receiver from outgoing shipment.

        Case 1: picking partner taken from picking.
        Case 2: picking partner taken from its move lines.
        Case 3: picking partner is not set.
        """
        # Set different partner_id on picking and it's first line
        self.picking_out.move_lines[0].partner_id = self.partner_azure
        # Sanity check
        self.assertEqual(self.picking_out.partner_id, self.partner_wood_corner)
        self.assertEqual(
            self.picking_out.move_lines[0].partner_id, self.partner_azure)
        # Case 1.
        sender = self.ReportDeliverySlip.get_sender(self.picking_out)
        self.assertEqual(sender, self.partner_main)
        receiver = self.ReportDeliverySlip.get_receiver(self.picking_out)
        self.assertEqual(receiver, self.partner_wood_corner)
        # Case 2.
        self.picking_out.partner_id = False
        sender = self.ReportDeliverySlip.get_sender(self.picking_out)
        self.assertEqual(sender, self.partner_main)
        receiver = self.ReportDeliverySlip.get_receiver(self.picking_out)
        self.assertEqual(receiver, self.partner_azure)
        # Case 3
        self.picking_out.move_lines = False
        receiver = self.ReportDeliverySlip.get_receiver(self.picking_out)
        self.assertEqual(receiver, self.ResPartner)

    def test_02_sender_receiver(self):
        """Get sender/receiver from incoming shipment.

        Case 1: picking partner taken from picking.
        Case 2: picking partner taken from its move lines.
        Case 3: picking partner is not set.
        """
        # Set different partner_id on picking and it's first line
        self.picking_in.move_lines[0].partner_id = self.partner_azure
        # Sanity check
        self.assertEqual(self.picking_in.partner_id, self.partner_wood_corner)
        self.assertEqual(
            self.picking_in.move_lines[0].partner_id, self.partner_azure)
        # Case 1.
        sender = self.ReportDeliverySlip.get_sender(self.picking_in)
        self.assertEqual(sender, self.partner_wood_corner)
        receiver = self.ReportDeliverySlip.get_receiver(self.picking_in)
        self.assertEqual(receiver, self.partner_main)
        # Case 2.
        self.picking_in.partner_id = False
        sender = self.ReportDeliverySlip.get_sender(self.picking_in)
        self.assertEqual(sender, self.partner_azure)
        receiver = self.ReportDeliverySlip.get_receiver(self.picking_in)
        self.assertEqual(receiver, self.partner_main)
        # Case 3
        self.picking_in.move_lines = False
        sender = self.ReportDeliverySlip.get_sender(self.picking_in)
        self.assertEqual(sender, self.ResPartner)

    def test_03_sender_receiver(self):
        """Get sender/receiver from internal shipment."""
        # TODO: is it correct that for internal - sender and receiver is
        # main partner?
        self.picking_in.picking_type_id.code = 'internal'
        sender = self.ReportDeliverySlip.get_sender(self.picking_in)
        self.assertEqual(sender, self.partner_main)
        receiver = self.ReportDeliverySlip.get_receiver(self.picking_in)
        self.assertEqual(receiver, self.partner_main)
