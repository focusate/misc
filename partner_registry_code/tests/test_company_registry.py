from odoo.exceptions import ValidationError

from odoo.addons.odootil.tests.common import TestBaseCommon


class TestCompanyRegistry(TestBaseCommon):
    """Test partner registry code."""

    @classmethod
    def setUpClass(cls):
        """Set up data for all test cases."""
        super().setUpClass()
        cls.ResPartner = cls.env['res.partner']
        cls.ResCompany = cls.env['res.company']
        cls.company = cls.env.ref('base.main_company')
        cls.other_company = cls.env['res.company'].create({
            'name': 'Other Company'})
        # Wood Corner.
        cls.partner_1 = cls.env.ref('base.res_partner_1')
        # Deco Addict.
        cls.partner_2 = cls.env.ref('base.res_partner_2')
        # Deco Addict, Floyd Steward
        cls.partner_4 = cls.env.ref('base.res_partner_address_4')
        cls.share_partner_rule = cls.env.ref('base.res_partner_rule')
        # Disable rule, because more test cases use it when its
        # disabled.
        cls.share_partner_rule.active = False

    def test_01_code_unique(self):
        """Diff. codes, no company, non multi-company environment."""
        try:
            self.partner_1.company_registry = '123'
            self.partner_2.company_registry = '124'
        except ValidationError:
            self.fail("Unique code must have been set on partners.")

    def test_02_code_unique(self):
        """Diff. codes, no company, multi-company env, sharing contacts."""
        try:
            self.partner_1.company_registry = '123'
            self.partner_2.company_registry = '124'
        except ValidationError:
            self.fail("Unique code must have been set on partners.")

    def test_03_code_unique(self):
        """Diff. codes, diff comp., multi-company env, sharing contacts."""
        try:
            self.partner_1.write({
                'company_registry': '123',
                'company_id': self.company.id,
            })
            self.partner_2.write({
                'company_registry': '124',
                'company_id': self.other_company.id,
            })
        except ValidationError:
            self.fail("Unique code must have been set on partners.")

    def test_04_code_unique(self):
        """Diff. codes, same comp., multi-company env, sharing contacts."""
        (self.partner_1 | self.partner_2).write({
            'company_id': self.company.id})
        try:
            self.partner_1.company_registry = '123'
            self.partner_2.company_registry = '124'
        except ValidationError:
            self.fail("Unique code must have been set on partners.")

    def test_05_code_unique(self):
        """Same. codes, same comp., multi-company, not sharing contacts."""
        self.share_partner_rule.active = True
        with self.assertRaises(ValidationError):
            (self.partner_1 | self.partner_2).write({
                'company_id': self.company.id,
                'company_registry': '123',
            })

    def test_06_code_unique(self):
        """Same. codes, diff comp., multi-company, not sharing contacts."""
        self.share_partner_rule.active = True
        self.partner_1.write({
            'company_registry': '123',
            'company_id': self.company.id,
        })
        try:
            self.partner_2.write({
                'company_registry': '123',
                'company_id': self.other_company.id,
            })
        # Should not raise, because different companies and contact
        # sharing is disabled.
        except ValidationError:
            self.fail("Should not raised ValidationError.")

    def test_07_code_unique(self):
        """Same. codes, diff comp., multi-company, not sharing."""
        self.share_partner_rule.active = True
        self.partner_1.write({
            'company_registry': '123',
            'company_id': self.other_company.id,
        })
        # Should raise an error, because partner has the same code and
        # company is not set.
        self.partner_2.with_user(self.user_demo).company_id = False
        with self.assertRaises(ValidationError):
            # Make sure it raises for non superuser too.
            self.partner_2.with_user(self.user_demo).company_registry = '123'

    def test_08_code_unique(self):
        """Same. codes, diff comp., multi-company, sharing contacts."""
        self.partner_1.write({
            'company_registry': '123',
            'company_id': self.company.id,
        })
        # Should raise an error, because contact sharing is enabled,
        # partner has the same code and partners belongs to different
        # companies.
        self.partner_2.company_id = self.other_company.id
        with self.assertRaises(ValidationError):
            self.partner_2.company_registry = '123'

    def test_09_code_unique(self):
        """Same code on partner and its child (multi-comp, not sharing)."""
        self.share_partner_rule.active = True
        try:
            (self.partner_2 | self.partner_4).write(
                {'company_registry': '123'})
        except ValidationError:
            self.fail(
                "Non commercial partner should not be included in uniqueness"
                " check.")

    def test_10_code_unique(self):
        """Same code on partner and its child (multi-comp, sharing)."""
        try:
            (self.partner_2 | self.partner_4).write(
                {'company_registry': '123'})
        except ValidationError:
            self.fail(
                "Non commercial partner should not be included in uniqueness"
                " check.")

    def test_11_code_unique(self):
        """Set same code on partner company and individual."""
        # Make individual.
        self.partner_4.write({'parent_id': False})
        with self.assertRaises(ValidationError):
            (self.partner_2 | self.partner_4).write(
                {'company_registry': '123'})

    def test_12_code_unique(self):
        """Same code on partner company and individual (multi, no share)."""
        self.share_partner_rule.active = True
        # Make individual.
        self.partner_4.write({'parent_id': False})
        with self.assertRaises(ValidationError):
            (self.partner_2 | self.partner_4).write(
                {'company_registry': '123'})

    def test_13_code_unique(self):
        """Same code on partner company and individual (multi, share)."""
        # Test when one partner has company set, and another one - not.
        # Make individual.
        self.partner_4.write({
            'parent_id': False, 'company_id': self.company.id})
        # Should raise because companies are different (one is False)
        # and sharing is enabled
        with self.assertRaises(ValidationError):
            (self.partner_2 | self.partner_4).write(
                {'company_registry': '123'})

    def test_14_code_unique(self):
        """Same. codes, diff comp., sharing contacts, archived partner."""
        self.partner_1.write({
            'company_registry': '123',
            'company_id': self.company.id,
            'active': False,
        })
        # Should raise an error, because contact sharing is enabled,
        # partner has the same code and partners belongs to different
        # companies.
        self.partner_2.company_id = self.other_company.id
        with self.assertRaises(ValidationError):
            self.partner_2.company_registry = '123'

    def test_15_code_unique(self):
        """Same. codes, same comp., no sharing, archived partner."""
        self.share_partner_rule.active = True
        self.partner_1.write({
            'company_registry': '123',
            'company_id': self.company.id,
            'active': False,
        })
        # Should raise an error, because partner has the same code and
        # partners belongs to the same company.
        self.partner_2.company_id = self.company.id
        with self.assertRaises(ValidationError):
            self.partner_2.company_registry = '123'

    def test_16_code_unique(self):
        """Set not unique partner company registry with spaces.

        Case 1: write on partner.
        Case 2: write on company.
        Case 3: create partner.
        Case 4: create company.
        """
        self.partner_2.company_registry = 'CR123'
        code_with_spaces = 'CR 123'
        # Case 1.
        with self.assertRaises(ValidationError):
            self.company.partner_id.company_registry = code_with_spaces
        # Case 2.
        with self.assertRaises(ValidationError):
            self.company.partner_id.company_registry = code_with_spaces
        # Case 3.
        with self.assertRaises(ValidationError):
            self.ResPartner.create({
                'name': 'partner', 'company_registry': code_with_spaces
            })
        # Case 4.
        with self.assertRaises(ValidationError):
            self.ResCompany.create({
                'name': 'company', 'company_registry': code_with_spaces
            })

    def test_17_company_registry_from_company(self):
        """Set company registry on company to fill on its partner."""
        self.company.company_registry = '123'
        self.assertEqual(self.company.partner_id.company_registry, '123')

    def test_18_company_registry_from_company(self):
        """Update company with other values than `company_registry`.

        We expect that if `company_registry` was not changed, it should
        not be updated on related partner too.
        """
        self.company.company_registry = '123'
        self.assertEqual(self.company.partner_id.company_registry, '123')
        # Ensure registry codes are not the same on company and it's
        # partner (force context to allow setting different code).
        self.company.partner_id.with_context(
            company_registry_set=True).company_registry = False
        self.assertEqual(self.company.company_registry, '123')
        self.assertEqual(self.company.partner_id.company_registry, False)
        # Update company with any other values and expect
        # `company_registry` not to be changed on partner.
        self.company.phone = '1234'
        self.assertEqual(self.company.company_registry, '123')
        self.assertEqual(self.company.partner_id.company_registry, False)

    def test_19_company_registry_from_company(self):
        """Create company with registry to fill on its partner."""
        temp_company = self.company.create(
            {'name': 'Temp', 'company_registry': '123'})
        self.assertEqual(temp_company.partner_id.company_registry, '123')

    def test_20_company_registry_from_company(self):
        """Create company without registry."""
        temp_company = self.company.create({'name': 'Temp'})
        self.assertEqual(temp_company.company_registry,
                         temp_company.partner_id.company_registry)
        self.assertEqual(temp_company.partner_id.company_registry, False)

    def test_21_company_registry_from_partner(self):
        """Set registry code on partner unrelated with company."""
        self.partner_1.company_registry = '123'
        self.assertFalse(self.company.company_registry)

    def test_22_company_registry_from_partner(self):
        """Set registry code on partner with related company."""
        self.company.partner_id.company_registry = '123'
        self.assertEqual(self.company.company_registry, '123')
