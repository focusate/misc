from odoo.exceptions import ValidationError

from .common import TestOdootilCommon
from ..models.odootil import singleton_records


class TestGetSingletonRecord(TestOdootilCommon):
    """Test class for get_singleton_record method."""

    def test_get_singleton_record_1(self):
        """Get singleton base.module.update record."""
        m = 'base.module.update'
        record1 = self.Odootil.get_singleton_record(m)
        self.assertTrue(record1)
        record2 = self.Odootil.get_singleton_record(m)
        self.assertEqual(record1, record2)
        record3 = self.Odootil.get_singleton_record((m,))
        # Even though same model is used, key is now tuple, not string.
        self.assertNotEqual(record2, record3)
        # Get singleton record with new env, so it would be closed.
        record4 = None
        with self.Odootil.get_environment() as env:
            record4 = env['odootil'].get_singleton_record((m, 2))
        record5 = self.Odootil.get_singleton_record((m, 2))
        # Expecting new record, because record4 cursor is closed.
        self.assertNotEqual(record4, record5)

    def test_get_singleton_record_2(self):
        """Get singleton res.partner record."""
        m = 'res.partner'
        record1 = self.Odootil.get_singleton_record(m, {'name': 'T1'})
        self.assertTrue(record1.exists())
        self.assertEqual(singleton_records[m], record1)
        # Check that it will still use same record, even if we try to
        # call with new values (which would only be used if creation
        # is needed).
        record2 = self.Odootil.get_singleton_record(m, {'name': 'T2'})
        self.assertTrue(record2.exists())
        self.assertEqual(record1, record2)
        self.assertEqual(record2.name, 'T1')
        self.assertEqual(singleton_records[m], record1)
        # Remove record, so it would be removed from cache.
        record2.unlink()
        record3 = self.Odootil.get_singleton_record(m, {'name': 'T3'})
        self.assertFalse(record1.exists())
        self.assertFalse(record2.exists())
        self.assertTrue(record3.exists())
        self.assertEqual(singleton_records[m], record3)
        # Specify new key, so new res.partner record would be created
        # alongside.
        record4 = self.Odootil.get_singleton_record((m, 't4'), {'name': 'T4'})
        self.assertTrue(record4.exists)
        self.assertEqual(record4._name, 'res.partner')
        self.assertEqual(record4.name, 'T4')
        self.assertEqual(singleton_records[(m, 't4')], record4)
        self.assertNotEqual(record3, record4)
        record5 = self.Odootil.get_singleton_record((m, 't4'), {'name': 'T4'})
        self.assertTrue(record5.exists())
        self.assertEqual(record4, record5)
        self.assertEqual(singleton_records[(m, 't4')], record5)
        # Remove from cache directly, to force new record.
        del singleton_records[(m, 't4')]
        record6 = self.Odootil.get_singleton_record((m, 't4'), {'name': 'T6'})
        self.assertTrue(record6.exists())
        self.assertNotEqual(record5, record6)
        self.assertEqual(record6.name, 'T6')
        self.assertEqual(singleton_records[(m, 't4')], record6)

    def test_get_singleton_record_3(self):
        """Get singleton record for not existing model."""
        with self.assertRaises(ValidationError):
            self.Odootil.get_singleton_record('some.not.existing.model')
        with self.assertRaises(ValidationError):
            self.Odootil.get_singleton_record(
                ('some.unknown.model', 'res.partner'))
        with self.assertRaises(ValidationError):
            self.Odootil.get_singleton_record(
                (555, 'res.partner'))
