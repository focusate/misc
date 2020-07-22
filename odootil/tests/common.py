from odoo.tests import common
from odoo.exceptions import AccessError
from odoo.tools.misc import mute_logger

MODELS_PATH = 'odoo.models'
BASE_MODELS_PATH = 'odoo.addons.base.models.ir_model'
# Note. This path exists only if module base_fields_access is installed.
BASE_FIELDS_MODELS_PATH = 'odoo.addons.base_fields_access.models.base_model'
SQL_DB_PATH = 'odoo.sql_db'
# TODO: update all modules to use these paths.
ACCESS_METHOD_PREFIX = 'check_access_'
TEST_ACCESS_METHOD_PREFIX = '_%s' % ACCESS_METHOD_PREFIX


def switch_record_currency(
        self, record, mode='over_limit', currency_fld='currency_id'):
    """Change record (or related one) currency to other than company's.

    Depending on modules installed, main company currency could be
    different.
    """
    def set_rate(curr, rate):
        # Remove currency rate with dynamic date to avoid errors in
        # tests. Tests are based on the 'base.rateUSD' currency
        # rate.
        try:
            self.env.ref('base.rateUSDbis').unlink()
        except ValueError:
            pass
        curr.rate_ids.rate = rate

    # Though, because on default EUR currency has rate of 1, we base
    # our computation from this currency.
    eur = self.browse_ref('base.EUR')
    company_currency = self.env.user.company_id.currency_id
    if company_currency == eur:
        usd = self.browse_ref('base.USD')
        if mode == 'over_limit':
            set_rate(usd, 0.01)
        else:
            set_rate(usd, 100)
        record[currency_fld] = usd.id
    else:
        if mode == 'over_limit':
            set_rate(company_currency, 100)
        else:
            set_rate(company_currency, 0.01)
        record[currency_fld] = eur.id


# TODO: replace Dummy with ItemDummy (ItemDummy should be moved
# to footil first).
class Dummy(object):
    """Dummy class to create object with various attributes."""

    def __init__(self, **kwargs):
        """Set up attributes."""
        for k, v in kwargs.items():
            setattr(self, k, v)


class SavepointCaseAccess(common.SavepointCase):
    """Extend SavePointCase with access rights helpers."""

    # TODO: list all possible modes
    ALL_MODES = frozenset({'read', 'write', 'create', 'unlink'})
    READ_MODES = frozenset({'read'})
    CHANGE_MODES = ALL_MODES - READ_MODES

    @classmethod
    def _get_modes(cls, no_modes=None):
        if not no_modes:
            no_modes = set({})
        return cls.ALL_MODES - no_modes

    @classmethod
    def setUpClass(cls):
        """Set up common data for access rights checks."""
        super().setUpClass()
        cls.user_demo = cls.env.ref('base.user_demo')
        cls.user_admin = cls.env.ref('base.user_admin')

    def _get_check_access_method(self, obj, access_type, user):
        obj = obj.sudo(user)
        return getattr(obj, '%s%s' % (ACCESS_METHOD_PREFIX, access_type))

    def _check_access(
        self,
        obj,
        access_type,
        modes,
            user=None):
        if not user:
            user = self.user_demo
        # Get check_access_rights or check_access_rule method.
        access_method = self._get_check_access_method(obj, access_type, user)
        for mode in modes:
            access_method(mode)

    def _check_access_rights(
        self,
        Model,
        modes,
            user=None):
        self._check_access(
            Model,
            'rights',
            modes,
            user=user
        )

    def _check_access_rule(
        self,
        record,
        modes,
            user=None):
        self._check_access(
            record,
            'rule',
            modes,
            user=user
        )

    def _get_test_check_access_method(self, access_type):
        return getattr(self, '%s%s' % (TEST_ACCESS_METHOD_PREFIX, access_type))

    def _test_access_fail(
            self, objects, access_type, user=None, no_modes=None):
        check_access_method = self._get_test_check_access_method(access_type)
        modes = self._get_modes(no_modes=no_modes)
        for obj in objects:
            for mode in modes:
                # Each time set different mode per check to fail.
                with self.assertRaises(AccessError):
                    check_access_method(
                        obj,
                        user=user,
                        modes={mode},
                    )
                    self.fail(
                        "AccessError not raised for obj: %s, mode: %s" %
                        (obj, mode))

    def _test_access_pass(
            self, objects, access_type, user=None, no_modes=None):
        check_access_method = self._get_test_check_access_method(access_type)
        modes = self._get_modes(no_modes=no_modes)
        for obj in objects:
            try:
                check_access_method(
                    obj,
                    modes,
                    user=user,
                )
            except AccessError as e:
                self.fail("%s obj was expected to pass. (%s)" % (obj, e))

    @mute_logger(BASE_MODELS_PATH)
    def _test_access_rights_fail(self, models, user=None, no_modes=None):
        self._test_access_fail(models, 'rights', user=user, no_modes=no_modes)

    @mute_logger(MODELS_PATH)
    def _test_access_rule_fail(self, records, user=None, no_modes=None):
        self._test_access_fail(records, 'rule', user=user, no_modes=no_modes)

    def _test_access_rights_pass(self, models, user=None, no_modes=None):
        self._test_access_pass(models, 'rights', user=user, no_modes=no_modes)

    def _test_access_rule_pass(self, records, user=None, no_modes=None):
        self._test_access_pass(records, 'rule', user=user, no_modes=no_modes)

    def _test_access_rights_spec(self, spec, user=None):
        """Test access for specified models for wanted user.

        Spec key acts as identifier where user is expected to have
        access and missing modes in a key act as missing access and is
        expected that user wont have that access. If key is empty, it
        means no access is given for specified models.

        Args:
            spec (dict): Expected structure:
                {
                    frozenset({'read', 'write'}): ['model1', 'model2'],
                    frozenset({'read'}): ['model3', 'model4'],
                    frozenset(): ['model5'],
                    ...
                    ...
                }
            user (res.users): [description] (default: {None})

        Returns:
            None

        Raises:
            AccessError

        """
        def get_models(model_names):
            return [self.env[model_name] for model_name in model_names]

        for modes_pass, model_names in spec.items():
            if not model_names:
                continue
            models = get_models(model_names)
            modes_fail = self.ALL_MODES - modes_pass
            self._test_access_rights_pass(
                models, user=user, no_modes=modes_fail)
            self._test_access_rights_fail(
                models, user=user, no_modes=modes_pass)


class TestOdootilCommon(common.SavepointCase):
    """Common class for all odootil test cases."""

    @classmethod
    def setUpClass(cls):
        """Set up common data."""
        super().setUpClass()
        cls.Odootil = cls.env['odootil']
        cls.company = cls.env.ref('base.main_company')
        cls.user_demo = cls.env.ref('base.user_demo')
        cls.ResPartner = cls.env['res.partner']
        cls.partner_1 = cls.env.ref('base.res_partner_1')
        cls.partner_2 = cls.env.ref('base.res_partner_2')
        cls.partner_3 = cls.env.ref('base.res_partner_3')
        cls.partner_4 = cls.env.ref('base.res_partner_4')
