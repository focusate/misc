from odoo.tests import common


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


class TestOdootilCommon(common.SavepointCase):
    """Common class for all odootil test cases."""

    @classmethod
    def setUpClass(cls):
        """Set up common data."""
        super(TestOdootilCommon, cls).setUpClass()
        cls.Odootil = cls.env['odootil']
        cls.company = cls.env.ref('base.main_company')
        cls.user_demo = cls.env.ref('base.user_demo')
        cls.ResPartner = cls.env['res.partner']
        cls.partner_1 = cls.env.ref('base.res_partner_1')
        cls.partner_2 = cls.env.ref('base.res_partner_2')
        cls.partner_3 = cls.env.ref('base.res_partner_3')
        cls.partner_4 = cls.env.ref('base.res_partner_4')
