from .common import TestOdootilCommon
from odoo.exceptions import AccessError


class TestAccessHelpers(TestOdootilCommon):
    """Test class for access management helper methods."""

    def setUp(self):
        """Set up check_access_set_fields reusable args."""
        super().setUp()
        self.res_groups_xmlids = 'base.group_system'
        self.vals = {'a': 10, 'b': 20, 'c': 30}

    def test_01_check_access_set_fields(self):
        """Check access when tracked field is not set."""
        try:
            self.Odootil.sudo(self.user_demo).check_access_set_fields(
                ['d'], self.vals, self.res_groups_xmlids)
        except AccessError:
            self.fail("d key was not being set.")

    def test_02_check_access_set_fields(self):
        """Check access when user has access to set fields."""
        self.res_groups_xmlids += ',base.group_user'
        try:
            self.Odootil.sudo(self.user_demo).check_access_set_fields(
                ['d', 'a'], self.vals, self.res_groups_xmlids)
        except AccessError:
            self.fail("Demo user has access to set fields.")

    def test_03_check_access_set_fields(self):
        """Check access for SUPERUSER when it does not have group."""
        try:
            self.Odootil.check_access_set_fields(
                ['a'], self.vals, 'base.group_portal')
        except AccessError:
            self.fail("SUPERUSER must always have access.")

    def test_04_check_access_set_fields(self):
        """Checks when tracked field is set and user has no access."""
        with self.assertRaises(AccessError):
            self.Odootil.sudo(self.user_demo).check_access_set_fields(
                ['b'], self.vals, self.res_groups_xmlids, model='res.partner')
