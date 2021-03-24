from . import common


class TestAddressFormat(common.TestAddressFormatCommon):
    """Class to test address formatting for res.partner, base.bank."""

    @classmethod
    def setUpClass(cls):
        """Set up data for address formatting tests."""
        super().setUpClass()
        cls.partner_azure = cls.env.ref('base.res_partner_12')
        cls.bank_pnb = cls.env.ref('base.bank_bnp')
        cls.company_main = cls.env.ref('base.main_company')
        # Set same address as partner, for more convenient testing.
        cls.bank_pnb.write({
            'zip': cls.partner_azure.zip,
            'street': cls.partner_azure.street,
            'city': cls.partner_azure.city,
            'state': cls.partner_azure.state_id.id,
            'country': cls.partner_azure.country_id.id,
        })
        cls.company_main.write({
            'zip': cls.partner_azure.zip,
            'street': cls.partner_azure.street,
            'city': cls.partner_azure.city,
            'state_id': cls.partner_azure.state_id.id,
            'country_id': cls.partner_azure.country_id.id,
        })

    def _test_address_interpolate(self, objects, address_str, **kw):
        for obj in objects:
            self.assertEqual(obj.address_interpolate(**kw), address_str)

    def test_01_address_interpolate(self):
        """Interpolate country address with strip_falsy=True."""
        address_us = (
            '4557 De Silva St\n'
            'Fremont CA 94538\n'
            'United States'
        )
        self._test_address_interpolate(
            [self.partner_azure, self.company_main, self.bank_pnb],
            address_us
        )

    def test_02_address_interpolate(self):
        """Interpolate country address with strip_falsy=False."""
        address_us = (
            # Extra newline should be left from street2, which is falsy.
            '4557 De Silva St\n\n'
            'Fremont CA 94538\n'
            'United States'
        )
        self._test_address_interpolate(
            [self.partner_azure, self.company_main, self.bank_pnb],
            address_us,
            strip_falsy=False,
        )

    def test_03_address_interpolate(self):
        """Interpolate default address, when no country address."""
        self.country_us.address_format = False
        address_default = (
            '4557 De Silva St, 94538, Fremont, CA, United States')
        self._test_address_interpolate(
            [self.partner_azure, self.company_main, self.bank_pnb],
            address_default,
        )

    def test_04_address_interpolate(self):
        """Interpolate default address, when country one disabled."""
        self.company_main.use_country_address_format = False
        address_default = (
            '4557 De Silva St, 94538, Fremont, CA, United States')
        self._test_address_interpolate(
            [self.partner_azure, self.company_main, self.bank_pnb],
            address_default,
        )
