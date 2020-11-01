from .common import TestOdootilCommon
from ..models.base import get_name_search_domain


class TestSearchHelpers(TestOdootilCommon):
    """Test class for search helper methods."""

    @classmethod
    def setUpClass(cls):
        """Set up data for partner name_get search."""
        super().setUpClass()
        cls.partner_1_name = cls.partner_1.name
        cls.partner_1_search_args = [('id', '=', cls.partner_1.id)]

    def test_01_get_name_search_domain(self):
        """Get search domain without leaf conditions."""
        op = 'ilike'
        val = 'test'
        domain = get_name_search_domain(
            val, ['code', 'name'])
        self.assertEqual(
            domain,
            ['|', ('code', op, val), ('name', op, val)]
        )
        op = '='
        domain = get_name_search_domain(
            val, ['code', 'name'], args=[('a', '=', 'b')], operator=op)
        self.assertEqual(
            domain,
            ['&', '|', ('code', op, val), ('name', op, val), ('a', '=', 'b')]
        )

    def test_02_get_name_search_domain(self):
        """Get search domain with leaf conditions."""
        op = 'ilike'
        val = 'test'
        # First key will be included if search value is not longer than
        # 4 symbols.
        leaf_conditions = {'country_id.code': lambda val: len(val) <= 4}
        domain = get_name_search_domain(
            val, ['country_id.code', 'name'], leaf_conditions=leaf_conditions)
        self.assertEqual(
            domain,
            ['|', ('country_id.code', op, val), ('name', op, val)]
        )
        op = '='
        # Make value not pass lead_condition for country_id.code.
        val = 'testing'
        domain = get_name_search_domain(
            val,
            ['country_id.code', 'name'],
            args=[('a', '=', 'b')],
            leaf_conditions=leaf_conditions,
            operator=op)
        self.assertEqual(
            domain,
            [
                '&',
                ('name', op, val),
                ('a', '=', 'b')
            ]
        )

    def test_03_name_search_multi_leaf(self):
        """Search partners using name_search_multi_leaf."""
        res = self.ResPartner.name_search_multi_leaf(
            self.partner_1_name,
            ['name'],
            args=self.partner_1_search_args,
            operator='=')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][0], self.partner_1.id)
