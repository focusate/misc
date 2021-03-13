from odoo.tests import common


class TestISCommercialPartner(common.SavepointCase):
    """Test is_commercial_partner field."""

    @classmethod
    def setUpClass(cls):
        """Set up data for all test cases."""
        super(TestISCommercialPartner, cls).setUpClass()
        # Agrolait
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.partner_child = cls.partner.child_ids[0]

    def test_01_is_commercial_partner(self):
        """Test partner that matches commercial partner conditions."""
        self.assertTrue(self.partner.is_commercial_partner)

    def test_02_is_commercial_partner(self):
        """Test partner child that is not comm. partner."""
        self.assertFalse(self.partner_child.is_commercial_partner)

    def test_03_is_commercial_partner(self):
        """Make non commercial partner, a commercial partner.

        Condition met by setting it to is_company=True.
        """
        self.partner_child.is_company = True
        self.assertTrue(self.partner_child.is_commercial_partner)

    def test_04_is_commercial_partner(self):
        """Make non commercial partner, a commercial partner.

        Condition met by setting parent_id=False.
        """
        self.partner_child.parent_id = False
        self.assertTrue(self.partner_child.is_commercial_partner)
