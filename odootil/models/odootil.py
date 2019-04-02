from contextlib import contextmanager
import collections
from ast import literal_eval

from odoo import models, api, _
from odoo import registry

from odoo.addons.base.models.ir_sequence import IrSequence

# Common constants.
PRIORITY = [(1, 'Low'), (2, 'Normal'), (3, 'High')]
DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'


class Interpolation(object):
    """Interpolate string using datetime variables.

    Attaching already existing implementation from ir.sequence model.
    """

    def __init__(self, prefix='', suffix='', _name='', _context=None):
        """Initialize Interpolation class for string rendering."""
        self.prefix = prefix
        self.suffix = suffix
        self._name = _name
        self._context = _context or {}

    # Need to implement this method, because _get_prefix_suffix expects
    # it, so we mimic that.
    def get(self, name):
        """Implement odoo model's 'get' method interface."""
        # name argument is ignored here actually, we only pass it,
        # because of attached method requirement.
        return self._name

    get_prefix_suffix = IrSequence._get_prefix_suffix


class Odootil(models.AbstractModel):
    """Model to add some common functionality patterns for modules.

    Provided methods can be used as helpers for better re-usability.
    """

    _name = 'odootil'
    _description = 'Odoo Utilities'

    # String manipulation helpers.

    @api.model
    def get_monetary_format(
            self, currency, value,
            lang_code=False, grouping=True, monetary=True):
        """Return monetary form of float value.

        Args:
            currency (recordset): res.currency record
            value (float): float value to be formated
            lang_code (str): code of language (locale code), e.g. 'en_US'
            grouping (bool): decimal and thousand separators
            monetary (bool): monetary separator (used if grouping enabled)

        Returns:
            str: monetary form of float value.

        """
        lang_code = lang_code or self.env.user.lang or self._context.get(
            'lang', 'en_US')
        lang = self.env['res.lang']._lang_get(lang_code)
        fmt = '%.{0}f'.format(currency.decimal_places)
        # Currency and language specific output
        return lang.format(
            fmt, currency.round(value), grouping=grouping, monetary=monetary)

    def get_prefix_suffix(
            self, prefix='', suffix='', _name='', _context=None):
        """Return interpolated prefix/suffix using specified pattern.

        This is a wrapper for Interpolation class get_prefix_suffix
        method, for convenience.
        """
        if not _context:
            _context = {}
        interpolation = Interpolation(
            prefix=prefix,
            suffix=suffix,
            _name=_name,
            _context=_context)
        return interpolation.get_prefix_suffix()

    # Sequence number wrapper.

    @api.model
    def get_sequence_number(
            self, code=False, sequence=False, company_id=False):
        """Get sequence number by code or by sequence record.

        company_id is ignored if sequence number is retrieved by
        sequence record.

        Args:
            code (str): sequence record code (default: {False})
            sequence (recordset): sequence record (default: {False})
            company_id (int): company ID to use in search with sequence
                code (default: {False})

        Returns:
            str: next sequence number by sequence record.

        """
        if code:
            ctx = dict(self._context)
            if company_id:
                ctx['force_company'] = company_id
            return self.env['ir.sequence'].with_context(ctx).next_by_code(code)
        if sequence:
            return sequence.next_by_id()

    @api.model
    def set_sequence_number(
        self,
        vals,
        key,
        code=False,
        sequence=False,
        company_id=False,
            default=None):
        """Set sequence number on specified dictionary key.

        sequence number getter uses method get_sequence_number.

        Args:
            vals (dict): dictionary to have sequence set on.
            key (str): vals key to set sequence number on.
            code (str): sequence record code to use in search
                (default: {False})
            sequence (recordset): sequence record to use
                (default: {False})
            company_id (int): company ID to use in seq search
                (default: {False})
            default (str): default sequence number value if sequence
                can't be found (default: {False}).

        Returns:
            None

        """
        if not vals.get(key):
            if default is None:
                default = _('New')
            seq_number = self.get_sequence_number(
                code=code, sequence=sequence, company_id=company_id)
            vals[key] = seq_number or default

    # Selection field helpers.

    @api.model
    def get_selection_map(self, record, field_key):
        """Return OrderedDict selection mapping for record field.

        Args:
            record (recordset): record selection field is called on.
            field_key (str): selection field name
        Returns:
            OrderedDict: selection mapping in OrderedDict form.
        """
        return collections.OrderedDict(record._fields[field_key].selection)

    @api.model
    def get_selection_label(self, record, field_key):
        """Return Label of current selection field value.

        If selection value is falsy, returns empty string. This might
        return unexpected results if one of the selection field values
        is falsy value. It is good practice to specify only truthy
        values for selection values.

        Args:
            record (recordset): record selection field is called on
            field_key (str): selection field name

        Returns:
            str: label of current selection field value.

        """
        val = record[field_key]
        if not val:
            return ''
        selection_map = self.get_selection_map(record, field_key)
        return selection_map[val]

    # ir.config_parameter helpers.

    @api.model
    def get_param_eval(self, key, default=False, eval_fun=literal_eval):
        """Retrieve the value for a given key and convert it.

        Value is retrieved using `get_param` method. If eval_fun is
        provided, value is then converted using that function. Otherwise
        no conversion is done.
        Args:
            key (str): The key of the parameter value to retrieve.
            default: default value if parameter is missing (
                default: {False}).
            eval_fun: function to convert retrieved value (default:
                {literal_eval}).

        Returns:
            type converted using eval_fun or str if no conversion done,
            or default value if nothing was found (last option works
            the same as `get_param` method).

        """
        value = self.env['ir.config_parameter'].get_param(key, default=default)
        # Check if we actually got param. If value matches with default,
        # it means we did not found param and it returned default value.
        if value == default:
            return default
        return eval_fun(value)

    # Environment and database operations helpers.

    @contextmanager
    def get_environment(self):
        """Return new env, transaction is committed on closing env."""
        Registry = registry(self.env.cr.dbname)
        with Registry.cursor() as cr:
            yield api.Environment(cr, self.env.uid, self._context)
            cr.commit()

    @api.model
    def update_external_ids_module(self, names, module, module_new):
        """Update module name of external identifiers.

        This might be reused as hook or in .yml file, when some elements
        (which have external identifiers) were moved from one module to
        another and external identifiers have left unchanged.

        Args:
            names (list): list of full names of external identifiers,
                excluding module name, e.g. 'field_res_partner_name'.
            module (str): module name set on external identifier,
                e.g. 'sale_order'.
            module_new (str): name of module to set on external identifier,
                e.g. 'sale_order_extended'.
        """
        # We expect to get a single record for each name, because there
        # is an unique constraint (module, name).
        identifiers = self.env['ir.model.data'].search([
            ('name', 'in', names),
            ('module', '=', module)
        ])
        if identifiers:
            identifiers.write({'module': module_new})
