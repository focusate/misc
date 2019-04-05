from odoo.exceptions import ValidationError

from . import common


class TestRecordSetHelpers(common.TestOdootilCommon):
    """Class to test recordset helper methods."""

    @classmethod
    def setUpClass(cls):
        """Set up data for recordset helper methods."""
        super(TestRecordSetHelpers, cls).setUpClass()
        cls.partners = cls.partner_1 | cls.partner_2 | cls.partner_3
        cls.partners_to_sort = cls.partner_1 | cls.partner_3 | cls.partner_2
        # color to be used as ordering key.
        cls.partner_1.color = 1
        cls.partner_2.color = 2
        cls.partner_3.color = 3
        cls._order = 'color, id'
        cls._order_2 = 'color desc, id'

    def test_01_get_recordset_index_1(self):
        """Get index for partner_1."""
        idx = self.Odootil.get_record_index(self.partners, self.partner_1)
        self.assertEqual(idx, 0)
        # Use custom range.
        with self.assertRaises(ValidationError):
            self.Odootil.get_record_index(
                self.partners, self.partner_1, start=1)

    def test_02_get_recordset_index_2(self):
        """Get index for partner_3."""
        idx = self.Odootil.get_record_index(self.partners, self.partner_3)
        self.assertEqual(idx, 2)
        # Use custom range to not fit in.
        with self.assertRaises(ValidationError):
            self.Odootil.get_record_index(
                self.partners, self.partner_3, start=1, end=2)
        # use custom range to fit in.
        idx = self.Odootil.get_record_index(
            self.partners, self.partner_3, start=2, end=3)
        self.assertEqual(idx, 2)
        # Make start greater than end.
        with self.assertRaises(ValidationError):
            self.Odootil.get_record_index(
                self.partners, self.partner_3, start=4)
        # Use not existing index in recordset.
        with self.assertRaises(IndexError):
            self.Odootil.get_record_index(
                self.partners, self.partner_3, start=4, end=5)

    def test_03_get_recordset_index_3(self):
        """Get index for partner_4."""
        with self.assertRaises(ValidationError):
            self.Odootil.get_record_index(self.partners, self.partner_4)
        idx = self.Odootil.get_record_index(
            self.partners, self.partner_4, raise_if_not_found=False)
        self.assertEqual(idx, -1)

    def test_04_sorted_with_newid(self):
        """Sort only normal recordset."""
        sorted_partners = self.Odootil.sorted_with_newid(
            self.partners_to_sort, _order=self._order)
        self.assertEqual(sorted_partners, self.partners)

    def test_05_sorted_with_newid(self):
        """Sort only NewId recordset."""
        # For some reason, record with NewId (using new method), lose
        # their attribute values, if those are defined on setUpClass. So
        # we define locally inside test method.
        partner_new_4 = self.ResPartner.new({'name': 'new4', 'color': 4})
        partner_new_5 = self.ResPartner.new({'name': 'new5', 'color': 5})
        sorted_partners = self.Odootil.sorted_with_newid(
            partner_new_5 | partner_new_4, _order=self._order)
        self.assertEqual(sorted_partners[0], partner_new_4)
        self.assertEqual(sorted_partners[1], partner_new_5)
        # Make color number the same, so only order records are
        # originally added is used.
        partner_new_5.color = 4
        sorted_partners = self.Odootil.sorted_with_newid(
            partner_new_5 | partner_new_4, _order=self._order)
        self.assertEqual(sorted_partners[0], partner_new_5)
        self.assertEqual(sorted_partners[1], partner_new_4)

    def test_06_sorted_with_newid(self):
        """Sort normal records with NewId records."""
        partner_new_4 = self.ResPartner.new({'name': 'new4', 'color': 4})
        partner_new_5 = self.ResPartner.new({'name': 'new5', 'color': 5})
        partners_to_sort = (
            partner_new_5 | partner_new_4 | self.partners_to_sort)
        # Sort by color, id.
        sorted_partners = self.Odootil.sorted_with_newid(
            partners_to_sort,
            _order=self._order)
        # First three must be normal records.
        self.assertEqual(sorted_partners[:3], self.partners)
        self.assertEqual(sorted_partners[3], partner_new_4)
        self.assertEqual(sorted_partners[4], partner_new_5)
        # Make partner_new_4 color number same as partner_2. It must go
        # after partner_2, because NewId records go after normal
        # records.
        partner_new_4.color = 2
        sorted_partners = self.Odootil.sorted_with_newid(
            partners_to_sort, _order=self._order)
        self.assertEqual(sorted_partners[:2], self.partner_1 | self.partner_2)
        self.assertEqual(sorted_partners[2], partner_new_4)
        self.assertEqual(sorted_partners[3], self.partner_3)
        self.assertEqual(sorted_partners[4], partner_new_5)
        # Sort only by id.
        sorted_partners = self.Odootil.sorted_with_newid(
            partners_to_sort)
        partners_reversed_by_id = self.partners.sorted(key='id')
        self.assertEqual(sorted_partners[0], partners_reversed_by_id[0])
        self.assertEqual(sorted_partners[1], partners_reversed_by_id[1])
        self.assertEqual(sorted_partners[2], partners_reversed_by_id[2])
        # When sorted by ID, SortedNewId is sorted by position, meaning
        # it will be kept at same position as it was (when comparing two
        # SortedNewId), thus partner_new_5 has index 3 as was
        # originally.
        self.assertEqual(sorted_partners[3], partner_new_5)
        self.assertEqual(sorted_partners[4], partner_new_4)

    def test_07_sorted_with_newid(self):
        """Sort normal records with NewId records, with desc option."""
        partner_new_4 = self.ResPartner.new({'name': 'new4', 'color': 4})
        partner_new_5 = self.ResPartner.new({'name': 'new5', 'color': 5})
        partners_reversed = (self.partner_3 | self.partner_2 | self.partner_1)
        partners_to_sort = (
            partner_new_5 | partner_new_4 | self.partners_to_sort)
        # Sort by color, id.
        sorted_partners = self.Odootil.sorted_with_newid(
            partners_to_sort,
            _order=self._order_2)
        self.assertEqual(sorted_partners[0], partner_new_5)
        self.assertEqual(sorted_partners[1], partner_new_4)
        self.assertEqual(sorted_partners[2:], partners_reversed)
        # Make partner_new_4 color number same as partner_2. It must
        # before partner_2, because NewId records go after normal
        # records (id is still sorted in ascending order).
        partner_new_4.color = 2
        sorted_partners = self.Odootil.sorted_with_newid(
            partners_to_sort, _order=self._order_2)
        self.assertEqual(sorted_partners[0], partner_new_5)
        self.assertEqual(sorted_partners[1], self.partner_3)
        self.assertEqual(sorted_partners[2], self.partner_2)
        self.assertEqual(sorted_partners[3], partner_new_4)
        self.assertEqual(sorted_partners[4], self.partner_1)
        # Sort only by id, but in descending order.
        sorted_partners = self.Odootil.sorted_with_newid(
            partners_to_sort, _order='id DESC')
        self.assertEqual(sorted_partners[0], partner_new_4)
        self.assertEqual(sorted_partners[1], partner_new_5)
        partners_reversed_by_id_desc = self.partners.sorted(
            key='id', reverse=True)
        self.assertEqual(sorted_partners[2], partners_reversed_by_id_desc[0])
        self.assertEqual(sorted_partners[3], partners_reversed_by_id_desc[1])
        self.assertEqual(sorted_partners[4], partners_reversed_by_id_desc[2])
