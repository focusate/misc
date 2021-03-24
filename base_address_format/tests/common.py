from odoo.addons.odootil.tests.common import TestBaseCommon


class TestAddressFormatCommon(TestBaseCommon):
    """Common class for address format tests."""

    @classmethod
    def setUpClass(cls):
        """Set up common data for address format tests."""
        super().setUpClass()
        # US country address format.
        # %(street)s
        # %(street2)s
        # %(city)s %(state_code)s %(zip)s
        # %(country_name)s
        cls.country_us = cls.env.ref('base.us')
        cls.country_lt = cls.env.ref('base.lt')
