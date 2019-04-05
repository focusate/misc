from .common import TestOdootilCommon

XML_ID = 'base.autovacuum_job'
DUMMY_XML_ID = 'base.not_existing_xml_id'
FILE_PATH = 'base/data/ir_cron_data.xml'
DUMMY_NAME = 'NEWNAME'
DUMMY_VALS = {'name': DUMMY_NAME}


class TestEnvDbHelpers(TestOdootilCommon):
    """Class to test environment and database operation helpers."""

    def test_01_update_external_ids_module(self):
        """Test external identifier's module update."""
        ext_ids = self.env['ir.model.data'].search(
            [('module', '=', 'base')], limit=2)
        module_new = 'some_existing_module_name'
        self.Odootil.update_external_ids_module(
            ext_ids.mapped('name'), 'base', module_new)
        self.assertEqual(list(set(ext_ids.mapped('module'))), [module_new])

    def test_02_update_xml_record(self):
        """Update when it exists."""
        record = self.Odootil.update_xml_record(XML_ID, dict(DUMMY_VALS))
        self.assertEqual(record.name, DUMMY_NAME)

    def test_03_update_xml_record(self):
        """Update when it does not exist, but can be recreated."""
        self.env.ref(XML_ID).unlink()
        record = self.Odootil.update_xml_record(
            XML_ID, dict(DUMMY_VALS), path=FILE_PATH)
        self.assertEqual(record.name, DUMMY_NAME)

    def test_04_update_xml_record(self):
        """Update when it does not exist."""
        with self.assertRaises(ValueError):
            self.Odootil.update_xml_record(DUMMY_XML_ID, dict(DUMMY_VALS))
        with self.assertRaises(ValueError):
            self.Odootil.update_xml_record(
                DUMMY_XML_ID, dict(DUMMY_VALS), path=FILE_PATH)
