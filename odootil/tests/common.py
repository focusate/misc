from odoo.tests import common


class Dummy(object):
    """Dummy class to create object with various attributes."""

    def __init__(self, **kwargs):
        """Set up attributes."""
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestOdootilCommon(common.SavepointCase):
    """Common class for all odootil test cases."""

    @classmethod
    def setUpClass(cls):
        """Set up common data."""
        super(TestOdootilCommon, cls).setUpClass()
        cls.Odootil = cls.env['odootil']
        cls.company = cls.env.ref('base.main_company')
