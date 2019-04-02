from .common import TestOdootilCommon


class TestUpdateExtIdModule(TestOdootilCommon):
    """Class to test external identifier's module update."""

    def test_update_external_ids_module(self):
        """Test external identifier's module update."""
        ext_ids = self.env['ir.model.data'].search(
            [('module', '=', 'base')], limit=2)
        module_new = 'some_existing_module_name'
        self.Odootil.update_external_ids_module(
            ext_ids.mapped('name'), 'base', module_new)
        self.assertEqual(list(set(ext_ids.mapped('module'))), [module_new])
