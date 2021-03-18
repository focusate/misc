from odoo.addons.odootil.tests.common import TestBaseCommon


class TestIsCompanyPartner(TestBaseCommon):
    """Test class to check if company refers to partner."""

    @classmethod
    def setUpClass(cls):
        """Set up data."""
        super().setUpClass()
        cls.ResCompany = cls.env['res.company']
        cls.ResPartner = cls.env['res.partner']
        cls.company_main = cls.env.ref('base.main_company')
        cls.partner_main = cls.env.ref('base.main_partner')
        cls.partner_azure = cls.env.ref('base.res_partner_12')

    def _test_is_company_partner_search(
            self, partner_companies, not_partner_company):
        # Search using demo user to mimic real usage.
        ResPartnerDemo = self.ResPartner.with_user(self.user_demo)
        # Find cases when searching for company partners.
        domain_partner_company_ids = [('id', 'in', partner_companies.ids)]
        partners = ResPartnerDemo.search(
            [('is_company_partner', '=', True)] + domain_partner_company_ids
        )
        self.assertCountEqual(partners, partner_companies)
        partners = ResPartnerDemo.search(
            [('is_company_partner', '!=', False)] + domain_partner_company_ids
        )
        self.assertCountEqual(partners, partner_companies)
        # Find cases when searching for not company partners. Filtering
        # with one ID, to prevent from many results.
        domain_one_partner = [('id', '=', not_partner_company.id)]
        partner = ResPartnerDemo.search(
            [('is_company_partner', '=', False)] + domain_one_partner
        )
        self.assertCountEqual(partner, not_partner_company)
        partners = ResPartnerDemo.search(
            [('is_company_partner', '!=', True)] + domain_one_partner
        )
        self.assertCountEqual(partner, not_partner_company)

    def test_01_is_company_partner(self):
        """Check when company referring to partner.

        Case 1: company refers to partner.
        Case 2: company is made to not refer to partner.
        """
        self.assertTrue(
            self.partner_main.with_user(self.user_demo).is_company_partner
        )
        company_2 = self.ResCompany.create({'name': 'NewCompany2'})
        self.assertTrue(
            company_2.partner_id.with_user(self.user_demo).is_company_partner
        )
        self._test_is_company_partner_search(
            self.partner_main | company_2.partner_id,
            self.partner_azure
        )
        # Case 2.
        partner = company_2.partner_id
        company_2.partner_id = self.partner_azure.id
        partner.invalidate_cache()
        self.assertFalse(partner.with_user(self.user_demo).is_company_partner)
        self.assertTrue(
            self.partner_azure.with_user(self.user_demo).is_company_partner
        )

    def test_02_is_company_partner(self):
        """Check when company referring to partner.

        Case 1: company does not refer to partner.
        Case 2: company is made to refer to partner.
        """
        # Case 1.
        self.assertFalse(
            self.partner_azure.with_user(self.user_demo).is_company_partner
        )
        partner_2 = self.ResPartner.create({'name': 'NewPartner2'})
        self.assertFalse(
            partner_2.with_user(self.user_demo).is_company_partner
        )
        self.assertFalse(
            self.ResCompany._find_partner_company_id(partner_2.id)
        )
        self._test_is_company_partner_search(
            self.partner_main,
            self.partner_azure
        )
        # Case 2.
        self.company_main.partner_id = partner_2.id
        self.assertTrue(self.ResCompany._find_partner_company_id(partner_2.id))
        partner_2.invalidate_cache()
        self.assertTrue(partner_2.with_user(self.user_demo).is_company_partner)
