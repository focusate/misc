from .common import TestOdootilCommon


class TestSearchHelpers(TestOdootilCommon):
    """Test class for search helper methods."""

    def test_get_name_search_domain_1(self):
        """Get search domain without leaf conditions."""
        op = 'ilike'
        val = 'test'
        domain = self.Odootil.get_name_search_domain(
            val, ['code', 'name'])
        self.assertEqual(
            domain,
            ['|', ('code', op, val), ('name', op, val)]
        )
        op = '='
        domain = self.Odootil.get_name_search_domain(
            val, ['code', 'name'], args=[('a', '=', 'b')], operator=op)
        self.assertEqual(
            domain,
            ['&', '|', ('code', op, val), ('name', op, val), ('a', '=', 'b')]
        )

    def test_get_name_search_domain_2(self):
        """Get search domain with leaf conditions."""
        op = 'ilike'
        val = 'test'
        # First key will be included if search value is not longer than
        # 4 symbols.
        leaf_conditions = {'country_id.code': lambda val: len(val) <= 4}
        domain = self.Odootil.get_name_search_domain(
            val, ['country_id.code', 'name'], leaf_conditions=leaf_conditions)
        self.assertEqual(
            domain,
            ['|', ('country_id.code', op, val), ('name', op, val)]
        )
        op = '='
        # Make value not pass lead_condition for country_id.code.
        val = 'testing'
        domain = self.Odootil.get_name_search_domain(
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
