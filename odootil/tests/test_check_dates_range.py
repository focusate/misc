from datetime import datetime

from .common import TestOdootilCommon
from odoo.exceptions import UserError


class TestDatesValidate(TestOdootilCommon):
    """Class to test validation of two dates."""

    def test_check_dates_range_1(self):
        """Test when dates are equal and it is allowed to be equal."""
        try:
            self.Odootil.check_dates_range('2018-01-01', '2018-01-01')
        except UserError:
            self.fail(
                "Should not raise, because dates are allowed to be equal.")

    def test_check_dates_range_2(self):
        """Test when dates are equal and it is not allowed to be equal."""
        with self.assertRaises(UserError):
            self.Odootil.check_dates_range(
                '2018-01-01', '2018-01-01', allow_equal=False)

    def test_check_dates_range_3(self):
        """Test when first date is earlier and it is allowed to be equal."""
        try:
            self.Odootil.check_dates_range('2018-01-01', '2018-01-02')
        except UserError:
            self.fail(
                "Should not raise, because first date is earlier.")

    def test_check_dates_range_4(self):
        """Test when first date is earlier, is not allowed to be equal."""
        try:
            self.Odootil.check_dates_range(
                '2018-01-01', '2018-01-02', allow_equal=False)
        except UserError:
            self.fail(
                "Should not raise, because first date is earlier.")

    def test_check_dates_range_5(self):
        """Test when second date is earlier and it is allowed to be equal."""
        with self.assertRaises(UserError):
            self.Odootil.check_dates_range('2018-01-02', '2018-01-01')

    def test_check_dates_range_6(self):
        """Test when second date is earlier, is not allowed to be equal."""
        with self.assertRaises(UserError):
            self.Odootil.check_dates_range(
                '2018-01-02', '2018-01-01', allow_equal=False)

    def test_check_dates_range_7(self):
        """Test when second date is earlier, date and datetime objects."""
        date_earlier = datetime.strptime('2018.01.02', '%Y.%m.%d')
        date_later = datetime.strptime('2018.01.01', '%Y.%m.%d')
        with self.assertRaises(UserError):
            self.Odootil.check_dates_range(date_earlier, date_later)
        with self.assertRaises(UserError):
            self.Odootil.check_dates_range(
                date_earlier.date(), date_later.date())
        try:
            self.Odootil.check_dates_range(date_later, date_earlier)
        except UserError:
            self.fail("Should not raise")
