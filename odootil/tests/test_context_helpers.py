from odoo.exceptions import ValidationError

from . import common


class TestContextHelpers(common.TestOdootilCommon):
    """Class to test context helpers."""

    @classmethod
    def setUpClass(cls):
        """Set up data for context helper tests."""
        super(TestContextHelpers, cls).setUpClass()
        cls.partner_1 = cls.env.ref('base.res_partner_1')
        cls.partner_2 = cls.env.ref('base.res_partner_2')

    def test_01_get_active_data_1(self):
        """Get active data from context with needed keys."""
        data = {
            'res_id': self.partner_1.id,
            'res_ids': [self.partner_1.id],
            'model': 'res.partner'
        }
        res = self.ResPartner.with_context(
            active_id=self.partner_1.id,
            active_model='res.partner').get_active_data()
        self.assertEqual(res, data)
        res = self.ResPartner.with_context(
            active_ids=[self.partner_1.id, 555],
            active_model='res.partner').get_active_data()
        data['res_ids'].append(555)
        self.assertEqual(res, data)
        res = self.ResPartner.with_context(
            active_id=self.partner_1.id,
            active_ids=[self.partner_1.id, 555],
            active_model='res.partner').get_active_data()
        self.assertEqual(res, data)

    def test_02_get_active_data_2(self):
        """Get active data from ctx with forced single active_id."""
        with self.assertRaises(ValidationError):
            self.ResPartner.with_context(
                active_ids=[self.partner_1.id, 555],
                active_model='res.partner').get_active_data(single=True)

    def test_03_get_active_data_3(self):
        """Get active data from ctx without active_model."""
        with self.assertRaises(ValidationError):
            self.ResPartner.with_context(
                active_ids=[self.partner_1.id, 555]).get_active_data()

    def test_04_get_active_data_4(self):
        """Get active data from ctx without active_id, active_ids."""
        with self.assertRaises(ValidationError):
            self.ResPartner.with_context(
                active_model='res.partner').get_active_data()

    def test_05_get_active_records_1(self):
        """Get active record from active context."""
        record = self.ResPartner.with_context(
            active_id=self.partner_1.id,
            active_model='res.partner').get_active_records()
        self.assertEqual(record, self.partner_1)

    def test_06_get_active_records_2(self):
        """Get two active records from active context."""
        ctx = {
            'active_id': self.partner_1.id,
            'active_ids': [self.partner_1.id, self.partner_2.id],
            'active_model': 'res.partner',
        }
        records = self.ResPartner.with_context(**ctx).get_active_records()
        self.assertEqual(
            set(records.ids), set((self.partner_1 | self.partner_2).ids))
        # Force only single record.
        with self.assertRaises(ValidationError):
            self.ResPartner.with_context(**ctx).get_active_records(single=True)
        # Pass custom message for single=True exception.
        try:
            self.ResPartner.with_context(**ctx).get_active_records(
                single=True, msg='my_custom_message')
        except ValidationError as e:
            self.assertEqual(e.args[0], 'my_custom_message')

    def test_07_get_active_records_3(self):
        """Get active record for non existing model."""
        with self.assertRaises(ValidationError):
            self.ResPartner.with_context(
                active_id=10,
                active_model='some.not.existing.model').get_active_records()

    def test_08_with_context_force(self):
        """Force update partner object context."""
        Partner = self.env['res.partner']
        self.assertEqual(Partner._context, {})
        Partner = Partner.with_context(t1=True)
        self.assertEqual(Partner._context, {'t1': True})
        # Passing no context, so nothing updated.
        Partner.with_context_force()
        self.assertEqual(Partner._context, {'t1': True})
        # Passing new key for context.
        Partner.with_context_force(t2=True)
        self.assertEqual(Partner._context, {'t1': True, 't2': True})
        # Update existing key.
        Partner.with_context_force(t1=False)
        self.assertEqual(Partner._context, {'t1': False, 't2': True})
