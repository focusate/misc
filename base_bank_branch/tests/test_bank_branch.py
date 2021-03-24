from odoo.exceptions import ValidationError

from odoo.addons.odootil.tests.common import TestBaseCommon


class TestBankBranch(TestBaseCommon):
    """Class to test bank and branches relationship."""

    @classmethod
    def setUpClass(cls):
        """Set up data."""
        super().setUpClass()
        cls.ResBank = cls.env['res.bank']
        cls.bank_pnb = cls.env.ref('base.bank_bnp')
        cls.bank_ing = cls.env.ref('base.bank_ing')
        cls.country_lt = cls.env.ref('base.lt')
        cls.bank_pnb.write({
            'zip': 'z123',
            'street': 'street1',
            'street2': 'street2',
            'city': 'Vilnius',
            'state': cls.env.ref('base.state_lt_vl').id,
            'country': cls.country_lt.id
        })

    def test_01_bank_name_get_name_search(self):
        """Check name_get/name_search on bank marked as branch.

        Case 1: Check bank display name
        Case 2: search using branch name
        Case 3: search using branch display name.
        Case 4: search using main bank name.
        """
        # Case 1.
        branch_1 = self.ResBank.create({
            'is_branch': True, 'parent_id': self.bank_pnb.id, 'name': 'Branch1'
        })
        # Sanity check (to make sure bank address not synced).
        self.assertFalse(branch_1.street)
        self.assertEqual(
            branch_1.display_name, f'{self.bank_pnb.name} / {branch_1.name}'
        )
        # Case 2.
        res = self.ResBank.name_search(
            'Branch1', args=[('id', '=', branch_1.id)]
        )
        self.assertEqual(res[0][0], branch_1.id)
        # Case 3.
        res = self.ResBank.name_search(
            f'{self.bank_pnb.name} / {branch_1.name}',
            args=[('id', '=', branch_1.id)]
        )
        self.assertEqual(res[0][0], branch_1.id)
        # Case 4.
        banks = self.bank_pnb | branch_1
        res = self.ResBank.name_search(
            self.bank_pnb.name,
            args=[('id', 'in', banks.ids)]
        )
        self.assertCountEqual([i[0] for i in res], banks.ids)

    def test_02_check_parent_id(self):
        """Check if recursion is not allowed."""
        with self.assertRaises(ValidationError):
            self.bank_pnb.parent_id = self.bank_pnb.id

    def test_03_check_parent_id(self):
        """Check if parent_id is only allowed with is_branch=True."""
        with self.assertRaises(ValidationError):
            self.bank_pnb.parent_id = self.bank_ing.id

    def _test_bank_address_match(self, bank, branch):
        self.assertEqual(bank.zip, branch.zip)
        self.assertEqual(bank.street, branch.street)
        self.assertEqual(bank.street2, branch.street2)
        self.assertEqual(bank.city, branch.city)
        self.assertEqual(bank.state, branch.state)
        self.assertEqual(bank.country, branch.country)

    def test_04_sync_bank_address(self):
        """Sync bank address with branches.

        Case 1: on branch create.
        Case 2: on main bank write.
        Case 3: one branch has use_bank_address=False.
        """
        # Case 1.
        bank_vals = {
            'name': 'Some Branch',
            'is_branch': True,
            'parent_id': self.bank_pnb.id,
            'use_bank_address': True,
        }
        branch_1, branch_2 = self.ResBank.create([bank_vals, bank_vals])
        self._test_bank_address_match(self.bank_pnb, branch_1)
        self._test_bank_address_match(self.bank_pnb, branch_2)
        # Case 2.
        street = 'new_street1'
        self.bank_pnb.street = street
        self.assertEqual(branch_1.street, street)
        self.assertEqual(branch_2.street, street)
        # Case 3.
        branch_2.use_bank_address = False
        old_street_2 = self.bank_pnb.street2
        street2 = 'new_street2'
        self.bank_pnb.street2 = street2
        self.assertEqual(branch_1.street2, street2)
        self.assertEqual(branch_2.street2, old_street_2)

    def test_05_sync_bank_address(self):
        """Change bank on branch to sync address."""
        bank_vals = {
            'name': 'Some Branch',
            'is_branch': True,
            # Bank without address.
            'parent_id': self.bank_ing.id,
            'use_bank_address': True,
        }
        branch_1 = self.ResBank.create(bank_vals)
        self.assertFalse(branch_1.street)
        branch_1.parent_id = self.bank_pnb.id
        self._test_bank_address_match(self.bank_pnb, branch_1)
