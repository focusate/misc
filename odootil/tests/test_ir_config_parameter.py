from .common import TestOdootilCommon

from odoo.exceptions import AccessError


class TestIrConfigParameter(TestOdootilCommon):
    """Class to test getting param and converting it to other type."""

    @classmethod
    def setUpClass(cls):
        """Set up data to check param evaluation."""
        super(TestIrConfigParameter, cls).setUpClass()
        cls.param = cls.env['ir.config_parameter'].create(
            {'key': 'test.some.param.1', 'value': "{'a': 10, 'b': False}"})
        cls.user_demo = cls.env.ref('base.user_demo')

    def _custom_conversion_fun(self, value):
        # Simple conversion to return True, if value evaluates to True.
        return bool(value)

    def test_get_param_eval_1(self):
        """Get param and convert using default eval_fun."""
        res = self.IrConfigParameter.get_param_eval('test.some.param.1')
        self.assertEqual(res, {'a': 10, 'b': False})

    def test_get_param_eval_2(self):
        """Do not find param to get default value without conversion."""
        res = self.IrConfigParameter.get_param_eval('test.some.param.2')
        self.assertEqual(res, False)

    def test_get_param_eval_3(self):
        """Do find param and use custom conversion function."""
        res = self.IrConfigParameter.get_param_eval(
            'test.some.param.1', eval_fun=self._custom_conversion_fun)
        # Because custom conversion just return True/False, we expect
        # True for found param.
        self.assertEqual(res, True)

    def test_get_param_eval_4(self):
        """Test defaults when param is set to 'True'."""
        self.param.value = 'True'
        res = self.IrConfigParameter.get_param_eval('test.some.param.1')
        self.assertEqual(res, True)

    def test_get_param_eval_5(self):
        """Use get_param_eval with demo user that has no access."""
        with self.assertRaises(AccessError):
            self.IrConfigParameter.with_user(self.user_demo).get_param_eval(
                'test.some.param.1')
