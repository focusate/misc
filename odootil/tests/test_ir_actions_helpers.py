from . import common


class TestIrActionsHelpers(common.TestOdootilCommon):
    """Test class for ir.action helpers."""

    @classmethod
    def setUpClass(cls):
        """Set up ir.actions helpers data."""
        super(TestIrActionsHelpers, cls).setUpClass()
        cls.act_partner_xml_id = 'base.action_partner_form'
        cls.act_partner = cls.env.ref(cls.act_partner_xml_id)
        cls.view_partner_tree_xml_id = 'base.view_partner_tree'
        cls.view_partner_form_xml_id = 'base.view_partner_simple_form'
        cls.view_partner_tree = cls.env.ref(cls.view_partner_tree_xml_id)
        cls.view_partner_form = cls.env.ref(cls.view_partner_form_xml_id)
        cls.partners = cls.partner_1 | cls.partner_2

    def setUp(self):
        """Set up reusable dict."""
        super(TestIrActionsHelpers, self).setUp()
        self.base_act_vals = {
            'name': self.ResPartner._description,
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
        }

    def test_01_prepare_act_window_data(self):
        """Get action dict, when records is empty recordset."""
        res = self.ResPartner.prepare_act_window_data()
        self.base_act_vals['type'] = 'ir.actions.act_window_close'
        self.assertEqual(res, self.base_act_vals)

    def test_02_prepare_act_window_data(self):
        """Get action dict with default arguments."""
        res = self.partners.prepare_act_window_data()
        dest_vals = dict(
            self.base_act_vals,
            domain=[('id', 'in', self.partners.ids)],
        )
        self.assertEqual(
            res,
            dest_vals
        )
        res = self.partner_1.prepare_act_window_data()
        del dest_vals['domain']
        dest_vals.update(
            res_id=self.partner_1.id,
            view_mode='form',
            views=[(False, 'form')])
        self.assertEqual(
            res,
            dest_vals
        )

    def _compare_with_action(self, act_dict, act_rec, custom_vals=None):
        dest_act_dict = act_rec.read()[0]
        if not custom_vals:
            custom_vals = {}
        for k, v in custom_vals.items():
            self.assertEqual(act_dict.pop(k), v, k)
            dest_act_dict.pop(k, None)  # Might not exist if new key.
        for k, v in act_dict.items():
            self.assertEqual(dest_act_dict[k], v, k)

    def test_03_prepare_act_window_data(self):
        """Get action dict with custom action."""
        res = self.partners.prepare_act_window_data(
            act_xml_id=self.act_partner_xml_id)
        views = self.act_partner.read()[0]['views']
        self._compare_with_action(
            res,
            self.act_partner,
            custom_vals={
                'domain': [('id', 'in', self.partners.ids)],
            }
        )
        res = self.partner_1.prepare_act_window_data(
            act_xml_id=self.act_partner_xml_id)
        self._compare_with_action(
            res,
            self.act_partner,
            custom_vals={
                'view_mode': 'form',
                # Views are filtered to only have form type.
                'views': [views[2]],
                'res_id': self.partner_1.id
            }
        )

    def test_04_prepare_act_window_data(self):
        """Get action dict with custom action and other custom args."""
        # Dict to change views if such views are used when opening
        # records.
        view_xml_ids_map = {
            'kanban': False,
            'tree': self.view_partner_tree_xml_id,
            'form': self.view_partner_form_xml_id,
        }
        views = self.act_partner.read()[0]['views']
        # Need to replace only kanban and form view, because tree view
        # is the same when using that partner action.
        views[0] = (False, 'kanban')
        views[2] = (self.view_partner_form.id, 'form')
        res = self.partners.prepare_act_window_data(
            act_xml_id=self.act_partner_xml_id,
            options={
                'view_xml_ids_map': view_xml_ids_map,
                'custom_vals': {'name': 'TEST'}
            }
        )
        self._compare_with_action(
            res,
            self.act_partner,
            custom_vals={
                'domain': [('id', 'in', self.partners.ids)],
                'views': views,
                'name': 'TEST',
            }
        )
        res = self.partner_1.prepare_act_window_data(
            act_xml_id=self.act_partner_xml_id,
            options={'view_xml_ids_map': view_xml_ids_map}
        )
        self._compare_with_action(
            res,
            self.act_partner,
            custom_vals={
                'view_mode': 'form',
                'views': [(self.view_partner_form.id, 'form')],
                'res_id': self.partner_1.id
            }
        )

    def test_05_prepare_act_window_data(self):
        """Get action dict with custom views conditions."""
        # Custom condition for all views (when no views are filtered).
        res = self.ResPartner.prepare_act_window_data(
            options={
                'conditions': {
                    'views_all': lambda recs: not recs or len(recs) > 1
                }
            }
        )
        dest_vals = dict(
            self.base_act_vals,
            domain=[('id', 'in', self.ResPartner.ids)],
        )
        # Custom condition for form view (when all views are filtered
        # out, except form).
        self.assertEqual(res, dest_vals)
        res = self.ResPartner.prepare_act_window_data(
            options={
                'conditions': {
                    # Same condition as for views_all, just shorter:)
                    'views_form': lambda recs: len(recs) in (0, 1)
                }
            }
        )
        del dest_vals['domain']
        dest_vals.update(
            view_mode='form',
            res_id=False,
            views=[(False, 'form')]
        )
        self.assertEqual(res, dest_vals)

    def test_06_prepare_act_window_data(self):
        """Get action dict with manual option."""
        # To Check if domain is not auto generated by conditions check.
        domain = [(1, '=', 1)]
        res = self.partners.prepare_act_window_data(
            options={
                'manual': True,
                'custom_vals': {'domain': domain}
            }
        )
        self.base_act_vals['domain'] = domain
        self.assertEqual(res, self.base_act_vals)
