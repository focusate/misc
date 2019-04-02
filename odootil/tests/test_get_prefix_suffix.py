from . import common
from datetime import datetime


class TestGetPrefixSuffix(common.TestOdootilCommon):
    """Test get_prefix_suffix odootil method."""

    @classmethod
    def setUpClass(cls):
        """Set up data for get_prefix_suffix tests."""
        super(TestGetPrefixSuffix, cls).setUpClass()
        cls.year = datetime.now().year

    def test_get_preffix_suffix_1(self):
        """Get prefix."""
        prefix, suffix = self.Odootil.get_prefix_suffix(
            prefix='test-%(year)s')
        self.assertEqual(prefix, 'test-%s' % self.year)
        self.assertEqual(suffix, '')

    def test_get_preffix_suffix_2(self):
        """Get suffix."""
        prefix, suffix = self.Odootil.get_prefix_suffix(
            suffix='test-%(year)s')
        self.assertEqual(prefix, '')
        self.assertEqual(suffix, 'test-%s' % self.year)

    def test_get_preffix_suffix_3(self):
        """Get prefix and suffix."""
        prefix, suffix = self.Odootil.get_prefix_suffix(
            prefix='something', suffix='test-%(year)s')
        self.assertEqual(prefix, 'something')
        self.assertEqual(suffix, 'test-%s' % self.year)
