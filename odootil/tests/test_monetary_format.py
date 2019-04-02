from .common import TestOdootilCommon


class TestMonetaryFormat(TestOdootilCommon):
    """Class to test monetary formating."""

    @classmethod
    def setUpClass(cls):
        """Set up data used in test cases."""
        super(TestMonetaryFormat, cls).setUpClass()
        cls.currency = cls.env.ref('base.EUR')
        cls.language = cls.env.ref('base.lang_en')
        cls.format = cls.Odootil.get_monetary_format
        cls.env.ref('base.lang_lt').active = True

    def test_monetary_format_1(self):
        """Test currency-specific monetary formating."""
        # Default
        self.assertEqual(self.format(self.currency, 1000.0), '1,000.00')
        # Rounding
        self.currency.rounding = 0.1
        self.assertEqual(self.format(self.currency, 1000.05), '1,000.1')
        self.currency.rounding = 0.001
        self.assertEqual(self.format(self.currency, 1000.00045), '1,000.000')
        self.currency.rounding = 0.0001
        self.assertEqual(self.format(self.currency, 1000.00005), '1,000.0001')

    def test_monetary_format_2(self):
        """Test language-specific monetary formating."""
        # Default
        self.assertEqual(self.format(self.currency, 1000.0), '1,000.00')
        # Thousand separator
        self.language.thousands_sep = '@'
        self.assertEqual(self.format(self.currency, 1000.0), '1@000.00')
        # Decimal separator
        self.language.decimal_point = ','
        self.assertEqual(self.format(self.currency, 1000.0), '1@000,00')
        # Separator format
        self.assertEqual(
            self.format(self.currency, 1000.0, grouping=False), '1000.00')
        self.language.grouping = '[4,0]'
        self.assertEqual(self.format(self.currency, 10000.0), '1@0000,00')
        # Other lang
        self.assertEqual(self.format(
            self.currency, 10000.0, lang_code='lt_LT'), '10.000,00')
