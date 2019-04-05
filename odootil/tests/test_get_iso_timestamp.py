from datetime import datetime

from .common import TestOdootilCommon


class TestGetIsoDatetime(TestOdootilCommon):
    """Class to test validation of two dates."""

    def test_get_iso_timestamp_1(self):
        """Test with datetime as string."""
        dt = self.Odootil.with_context(
            tz='Lithuania/Vilnius').get_iso_timestamp('2018-01-31 10:15:20')
        self.assertEqual(dt, '2018-01-31T10:15:20+00:00',
                         "Incorrect datetime ISO format returned.")

    def test_get_iso_timestamp_2(self):
        """Test with date as string."""
        dt = self.Odootil.with_context(
            tz='Lithuania/Vilnius').get_iso_timestamp('2018-01-31')
        self.assertEqual(dt, '2018-01-31T00:00:00+00:00',
                         "Incorrect datetime ISO format returned.")

    def test_get_iso_timestamp_3(self):
        """Test with datetime object."""
        dt = datetime.strptime('2018.01.31 10:15:20', '%Y.%m.%d %H:%M:%S')
        dt = self.Odootil.with_context(
            tz='Lithuania/Vilnius').get_iso_timestamp(dt)
        self.assertEqual(dt, '2018-01-31T10:15:20+00:00',
                         "Incorrect datetime ISO format returned.")

    def test_get_iso_timestamp_4(self):
        """Test with date object."""
        dt = datetime.strptime(
            '2018.01.31 10:15:20', '%Y.%m.%d %H:%M:%S').date()
        dt = self.Odootil.with_context(
            tz='Lithuania/Vilnius').get_iso_timestamp(dt)
        self.assertEqual(dt, '2018-01-31T00:00:00+00:00',
                         "Incorrect datetime ISO format returned.")
