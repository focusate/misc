
from .common import TestOdootilCommon


class TestGetSelectionLabel(TestOdootilCommon):
    """Class to test get_selection_label function."""

    def test_get_selection_label_1(self):
        """Get selection label when something is selected."""
        res = self.Odootil.get_selection_label(
            self.company, 'base_onboarding_company_state')
        self.assertEqual(res, 'Not done')
        self.company.base_onboarding_company_state = 'just_done'
        res = self.Odootil.get_selection_label(
            self.company, 'base_onboarding_company_state')
        self.assertEqual(res, 'Just done')

    def test_get_selection_label_2(self):
        """Get selection label when nothing is selected."""
        self.company.base_onboarding_company_state = False
        res = self.Odootil.get_selection_label(
            self.company, 'base_onboarding_company_state')
        self.assertEqual(res, '')
        # Do the same on empty recordset.
        res = self.Odootil.get_selection_label(
            self.env['res.company'], 'base_onboarding_company_state')
        self.assertEqual(res, '')
