from odoo.tools import mute_logger
from odoo.exceptions import AccessError, ValidationError

from odoo.addons.odootil.tests.common import MODELS_PATH

from . import common


class TestRestClientDemoAuth(common.TestRestClientDemoCommon):
    """Class to test demo authentication."""

    def test_01_get_auth(self):
        """Get current auth when no auth is confirmed.

        Case 1: main company.
        Case 2: second company.
        """
        # Case 1.
        (
            self.test_auth_1 | self.test_auth_2 | self.test_auth_3
        ).action_to_draft()
        self.assertEqual(self.test_auth_1.state, 'draft')
        auth = self.RestClientTestAuth.get_auth(
            company_id=self.main_company.id)
        self.assertEqual(auth, self.RestClientTestAuth)
        # Case 2.
        auth = self.RestClientTestAuth.get_auth(
            company_id=self.company_2.id)
        self.assertEqual(auth, self.RestClientTestAuth)

    def test_02_get_auth(self):
        """Get current auth per company.

        Case 1: main company.
        Case 2: second company.
        Case 3: no company (global).
        """
        # Case 1.
        auth = self.RestClientTestAuth.get_auth(
            company_id=self.main_company.id)
        self.assertEqual(auth, self.test_auth_1)
        # Case 2.
        auth = self.RestClientTestAuth.get_auth(
            company_id=self.company_2.id)
        self.assertEqual(auth, self.test_auth_2)
        # Case 3.
        # Disable company specific auth record, so it would default
        # to global one.
        self.test_auth_1.action_to_draft()
        auth = self.RestClientTestAuth.get_auth(
            company_id=self.main_company.id)
        self.assertEqual(auth, self.test_auth_3)
        # Sanity check, to make sure, global defaults to only those
        # auth that have no specific company.
        auth = self.RestClientTestAuth.get_auth(
            company_id=self.company_2.id)
        self.assertEqual(auth, self.test_auth_2)

    def test_03_auth_access_rights(self):
        """Check access rights for auth object.

        Case 1: for non admin user.
        Case 2: for admin user.
        """
        # Case 1.
        self._test_access_rights_fail(self.RestClientTestAuth)
        # Case 2.
        self._test_access_rights_pass(
            self.RestClientTestAuth, user=self.user_admin)

    def test_04_auth_access_rules(self):
        """Check auth object access rules.

        Case 1: auth company matches user company.
        Case 2: auth company does not match user company.
        Case 3: auth does not have company set.
        """
        # Case 1.
        self._test_access_rule_pass(self.test_auth_1)
        # Case 2.
        self._test_access_rule_fail(self.test_auth_2)
        # Case 3.
        self._test_access_rule_pass(self.test_auth_3)

    def test_05_get_auth_data(self):
        """Try to get auth data from model that has no auth model."""
        data = self.env['rest.client.controller']._get_auth_data(
            self.main_company.id)
        self.assertEqual(data, None)

    def test_06_get_auth_data(self):
        """Try to get auth data with user that has no access."""
        with self.assertRaises(AccessError), mute_logger(MODELS_PATH):
            self.RestClientTestController.sudo(
                self.user_demo)._get_auth_data(self.main_company.id)

    def test_07_get_auth_data(self):
        """Get auth data with None auth method."""
        data = self.RestClientTestController._get_auth_data(
            self.main_company.id)
        self.assertEqual(data, {'url': self.test_auth_1.url, 'auth': None})

    def test_08_get_auth_data(self):
        """Get auth data with Password auth method."""
        data = self.RestClientTestController._get_auth_data(
            self.company_2.id)
        auth = self.test_auth_2
        self.assertEqual(
            data,
            {
                'url': auth.url,
                'auth': {'auth': (auth.username, auth.password)}
            })

    def test_09_check_auth_unique(self):
        """Enable auth records, when uniqueness is not satisfied.

        Case 1: dupe company.
        Case 2: dupe global auth.
        """
        # Case 1.
        auth = self._create_auth()
        with self.assertRaises(ValidationError):
            auth.action_confirm()
        # Case 2.
        auth = self._create_auth({'company_id': False})
        with self.assertRaises(ValidationError):
            auth.action_confirm()
