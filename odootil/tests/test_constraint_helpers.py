from odoo.exceptions import ValidationError

from .common import TestOdootilCommon


class TestEnvDbHelpers(TestOdootilCommon):
    """Class to test various constraint helper methods."""

    def test_01_check_url(self):
        """Check valid url."""
        try:
            self.Odootil.check_url('http://www.focusate.eu')
            self.Odootil.check_url('https://www.focusate.eu')
            self.Odootil.check_url('ftp://www.focusate.eu')
        except ValidationError:
            self.fail("Valid URL must pass")

    def test_02_check_url(self):
        """Check invalid url."""
        with self.assertRaises(ValidationError):
            self.Odootil.check_url('httpxx://www.focusate')
        with self.assertRaises(ValidationError):
            self.Odootil.check_url('')
        with self.assertRaises(ValidationError):
            self.Odootil.check_url(False)
        with self.assertRaises(ValidationError):
            self.Odootil.check_url('www.focusate')
