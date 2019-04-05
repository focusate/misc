import os

from odoo.exceptions import ValidationError
from odoo.tools.convert import convert_file

from .common import TestOdootilCommon

MODULE = 'odootil'
PATH = 'tests'
FILE = 'test_res_partner_views.xml'


def _load_test_partner_view(cr):
    return convert_file(
        cr,
        MODULE,
        FILE,
        {},
        mode='init',
        pathname=os.path.join(MODULE, PATH, FILE))


class TestViewHelpers(TestOdootilCommon):
    """Test class for view manipulation helpers."""

    @classmethod
    def setUpClass(cls):
        """Set up data for required fields validation."""
        super().setUpClass()
        cls.test_partner = cls.ResPartner.create(
            {'name': 'test', 'is_company': True})

    def test_01_validate_form_required_fields(self):
        """Validate record with no required fields on form."""
        self.assertTrue(self.Odootil.validate_form_required_fields(
            self.test_partner))

    def test_02_validate_form_required_fields(self):
        """Validate record with required field on form."""
        # Enable required field on form, by loading test view.
        _load_test_partner_view(self.env.cr)
        with self.assertRaises(ValidationError):
            self.Odootil.validate_form_required_fields(self.test_partner)
        # Make it non company to make sure required condition is not
        # applied anymore.
        self.test_partner.is_company = False
        self.assertTrue(self.Odootil.validate_form_required_fields(
            self.test_partner))
