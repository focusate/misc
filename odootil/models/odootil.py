import os
from contextlib import contextmanager
import collections
import six
from ast import literal_eval
from num2words import num2words
import operator
import itertools

from odoo import models, api, fields, _, registry, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools.convert import convert_file
from odoo.exceptions import ValidationError, UserError, AccessError
# Might be better to give new name on import to avoid clashes?
from odoo.tests.common import Form

from odoo.addons.base.models.ir_sequence import IrSequence

NON_WRITABLE_KEYS = ['id']
PSQL_DESC = 'desc'
# Common constants.
PRIORITY = [(1, 'Low'), (2, 'Normal'), (3, 'High')]
DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

# Cache for singleton records.
singleton_records = {}


# TODO: move this to footil.
class ItemDummy(object):
    """Dummy class to create object with various attributes."""

    def __init__(self, **kwargs):
        """Set up attributes."""
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        """Return attribute using key."""
        return self.__dict__[key]

    def __repr__(self):
        """Return string with attributes map."""
        return '%s(**%s)' % (self.__class__.__name__, self.__dict__)


# TODO: might be better to have it on footil.
class ReverseComparator:
    """Class to allow reverse comparison for initialized object."""

    def __init__(self, obj):
        """Init object to be compared in reverse order."""
        self.obj = obj

    def __eq__(self, other):
        """Check equality in reverse."""
        return other.obj == self.obj

    def __lt__(self, other):
        """Check less than in reverse."""
        return other.obj < self.obj


class SortedNewId(models.NewId):
    """Subclass for NewId to make it sortable with real record.

    Comparing is done in three ways:
        - Both have db_id. Comparing db_id.
        - Only one has db_id. Less than is the one with db_id.
        - None have db_id. Comparing with pos (position).
    """

    id_iter = itertools.count()
    __slots__ = ('pos', 'db_id', '_pseudo_id')

    def __init__(self, ref=None, pos=0, db_id=0):
        """Override to include original position in recordset."""
        super().__init__(ref=ref)
        self.pos = pos
        self.db_id = db_id
        self._pseudo_id = next(self.id_iter)

    def __lt__(self, other):
        """Compare int or other SortedNewId object."""
        if self.db_id and other.db_id:
            return self.db_id < other.db_id
        # The one with db_id is less than without db_id.
        if not self.db_id and other.db_id:
            return False
        if self.db_id and not other.db_id:
            return True
        # None have db_id. Comparing with position.
        return self.pos < other.pos

    def __repr__(self):
        """Return reproducible object in string."""
        class_name = self.__class__.__name__
        return '%s(db_id=%s, pos=%s)' % (class_name, self.db_id, self.pos)


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

    # Search/check helpers.

    @api.model
    def get_name_search_domain(
        self,
        name,
        keys,
        leaf_conditions=None,
        args=None,
            operator='ilike'):
        """Prepare domain to be used for name_search with custom keys.

        keys (path to field in object) argument is used to create
        domain leafs separated by OR operator.

        Args:
            name (str): search value.
            keys (list): list of string keys specifying left operand.
            leaf_conditions (dict): specify condition for name argument
                for specific key. key is key from keys arg and value is
                check function that takes search value as argument.
                (default: {None})
            args (list): Optional argument to append to domain after
                domain is created (default: {None})
            operator (str): operator that will be used in all domain
                leafs. (default: {'ilike'})

        Returns:
            name_search
            list

        """
        def check_key(key):
            condition = leaf_conditions.get(key)
            # Can pass if there is no condition, or condition is
            # specified.
            return not condition or condition(name)

        args = list(args or [])
        if not leaf_conditions:
            leaf_conditions = {}
        domains = [[(k, operator, name)] for k in keys if check_key(k)]
        # Convert little domains into full domain separating
        # it with OR.
        domain = expression.OR(domains)
        # Add extra args.
        return expression.AND([domain, args])

    def name_search_multi_leaf(
        self,
        model_name,
        name,
        keys,
        leaf_conditions=None,
        args=None,
        operator='ilike',
        limit=100,
            name_get_uid=None):
        """Search name with multiple leafs separated by OR operator.

        This is wrapper for get_name_search_domain with native
        _name_search method implementation.

        For arguments related with get_name_search_domain, see its
        docstring.
        """
        domain = self.env['odootil'].get_name_search_domain(
            name,
            keys,
            leaf_conditions=leaf_conditions,
            args=args,
            operator=operator
        )
        uid = name_get_uid or self._uid
        Model = self.env[model_name]
        ids = Model._search(domain, limit=limit, access_rights_uid=uid)
        recs = Model.browse(ids)
        return models.lazy_name_get(recs.sudo(uid))

    def check_field_unique(
        self,
        Model,
        field_name,
        val,
        count=False,
            options=None):
        """Check if field value is unique.

        Intended to be used for fields where value uniqueness must be
        preserved.

        Uniqueness checked globally if objects are shared across
        multiple companies, otherwise current object company is used.

        Args:
            obj (models.Model): object to use as a base for uniqueness
                check.
            field_name (str): field that is checked.
            val (any): value of field to be build search domain.
            count (bool): whether to just count duplicates or return
                found records. Optional (default: {False}).
            options (dict): extra options to modify search. Dict can
                    have such keys. (default: {None}):
                args (list): additional domain to be extended on top of
                    main one. Optional (default: {None})
                case_insensitive (bool): flag if case insensitive search
                    should be done. Optional (default: {False}).
                multi_comp_rule_xml_id (str): multi company ir.rule
                    XMLID that is used to identify if multi-company is
                    used for that object. Optional (default: {None}).
                company_id (int): company ID that is used for multi
                    company domain. If multi_company_rule_xml_id is not
                    used and company_id is specified, it will be force
                    used in domain. Optional (default: {False}).

        Returns:
            Number of records found.
            int

        """
        def is_multi_comp_used(multi_comp_rule_xml_id, company_id):
            # Multi company is used, if there is explicit rule to
            # enable/disable it or if company_id was passed as argument.
            # Multi company rule takes priority.
            if multi_comp_rule_xml_id:
                # Rule that defines if multi-company rule is enabled (
                # shared globally or per company)
                return self.sudo().env.ref(multi_comp_rule_xml_id).active
            return bool(company_id)

        def get_company_domain_leaf(multi_comp_rule_xml_id, company_id):
            if is_multi_comp_used(multi_comp_rule_xml_id, company_id):
                return ('company_id', 'in', [company_id, False])
            return []

        def get_domain(options):
            op = '=ilike' if options.get('case_insensitive') else '='
            domain = [(field_name, op, val)] + options.get('args', [])
            company_domain_leaf = get_company_domain_leaf(
                options.get('multi_comp_rule_xml_id'),
                options.get('company_id', False))
            if company_domain_leaf:
                domain.append(company_domain_leaf)
            return domain

        if not options:
            options = {}
        domain = get_domain(options)
        # Using sudo() because regular user might not have access to
        # all objects. Searching among archived objects too.
        return Model.with_context(active_test=False).sudo().search(
            domain, count=count)

    # String manipulation helpers.

    @api.model
    def get_monetary_format(
            self, currency, value, lang_code=False, use_symbol=False):
        """Return monetary form of float value.

        Args:
            currency (recordset): res.currency record
            value (float): float value to be formated
            lang_code (str): code of language (locale code),
                e.g. 'en_US'
            use_symbol (bool): whether to include currency symbol or not
                (default: {False}).

        Returns:
            str: monetary form of float value.

        """
        lang_code = lang_code or self.env.user.lang or self._context.get(
            'lang', 'en_US')
        lang = self.env['res.lang']._lang_get(lang_code)
        fmt = '%.{0}f'.format(currency.decimal_places)
        # Currency and language specific output.
        # `format` with `grouping` and `monetary` enabled returns
        # monetary format for float values.
        value = lang.format(
            fmt, currency.round(value), grouping=True, monetary=True)
        if use_symbol:
            if currency.position == 'before':
                args = (currency.symbol, value)
            else:
                args = (value, currency.symbol)
            return '%s %s' % args
        else:
            return value

    @api.model
    def get_num2words(
            self, number, options=None):
        """Check if valid to use num2words, get number in words."""
        if not options:
            options = {}
        ordinal = options.get('ordinal', False)
        lang = options.get('lang') or self.env.user.lang or self._context.get(
            'lang', 'en_US')
        to = options.get('to', 'cardinal')
        kwargs = options.get('kwargs', {})
        try:
            return num2words(
                number, ordinal=ordinal, lang=lang, to=to, **kwargs)
        except NotImplementedError:
            fallback_words = options.get('fallback_words')
            if fallback_words is not None:
                return fallback_words
            raise

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
            self, code=None, sequence=None, company_id=None):
        """Get sequence number by code or by sequence record.

        company_id is ignored if sequence number is retrieved by
        sequence record.

        Args:
            code (str): sequence record code (default: {None})
            sequence (recordset): sequence record (default: {None})
            company_id (int): company ID to use in search with sequence
                code (default: {None})

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

    # Environment and database operation helpers.

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

    @api.model
    def update_xml_record(self, xml_id, vals, path=None):
        """Update record that can be referenced via xml_id using vals.

        Args:
            xml_id (str): XML ID to reference record.
            vals (dict): values to update record with.
            path (str): record's definition file path. If specified,
                will try to load it in case XML ID does not exist.
                (default: {None})

        Returns:
            updated record.
            record

        """
        def update():
            record = self.env.ref(xml_id)
            record.write(vals)
            return record

        def get_module_and_filename():
            # Assuming valid relative odoo path to module.
            module = path.split('/')[0]
            filename = os.path.basename(path)
            return module, filename

        try:
            return update()
        except ValueError:
            if path:
                module, filename = get_module_and_filename()
                # Load record's file.
                convert_file(
                    self._cr,
                    module,
                    filename,
                    {},
                    mode='init',
                    pathname=path)
                # Try again.
                return update()
            else:
                raise

    # orderby transformation helpers.

    def to_writable_keys(self, keys):
        """Filter keys, leaving only those that could be writable.

        We currently exclude ID key, because that one is not writable.
        """
        return [k for k in keys if k not in NON_WRITABLE_KEYS]

    @api.model
    def orderby_to_list(self, Model):
        """Transform Model's _order value into list."""
        return Model._order.replace(' ', '').split(',')

    @api.model
    def _orderby_to_items(self, _order):
        for item in _order.split(','):
            # Remove leading white space that might be hanging after
            # splitting.
            item = item.lstrip()
            # E.g. 'name asc NULLS FIRST' -> ('name', 'asc NULLS FIRST')
            key, *options = item.split(' ', 1)
            options = options[0] if options else ''
            yield (key.replace(' ', ''), options)

    @api.model
    def orderby_to_keys(self, _order):
        """Transorm Model's _order to list keys only.

        Strips all options, like asc, desc, NULLS {FIRST | LAST}.
        """
        return [item[0] for item in self._orderby_to_items(_order)]

    def orderby_to_writable_keys(self, _order):
        """Transorm Model's _order to list with writable keys."""
        return self.to_writable_keys(self.orderby_to_keys(_order))

    @api.model
    def orderby_to_sort_keys(self, _order):
        """Transform Model's _order to list of tuple keys.

        First item in tuple is key, second boolean value, indicating if
        key order must be reversed (usually descending).
        """
        def is_reversed(options):
            return PSQL_DESC in options.lower()
        return [
            (i[0], is_reversed(i[1])) for i in self._orderby_to_items(_order)
        ]

    @api.model
    def get_sort_key_function(self, sort_keys):
        """Return function that uses sort_keys for sort function.

        Takes into account reverse option, so comparison is done in
        reverse using ReverseComparator class.
        """
        return lambda x: tuple(
            ReverseComparator(x[k]) if rev else x[k] for (k, rev) in sort_keys
        )

    # recordset helpers.

    @api.model
    def get_record_index(
        self,
        recordset,
        record,
        start=0,
        end=None,
            raise_if_not_found=True):
        """Get lowest zero-based index as record value in recordset.

        Can specify optional range.

        Args:
            recordset (recordset): recordset to check
            record (recordset): single record to find its index position
                in recordset.
            start (int): start index for recordset (default: {0})
            end (int): end index for recordset (default: {None})
            raise_if_not_found (bool): raise ValidationError if record
                is not in recordset (default: {True})

        Returns:
            record index position in recordset or raise if not found, or
            -1 if not raising.
            int

        """
        if not end:
            end = len(recordset)
        if start > end:
            raise ValidationError(_("end index must be greater than start."))
        for i in range(start, end):
            if recordset[i] == record:
                return i
        if raise_if_not_found:
            raise ValidationError(_("%s is not in recordset") % record)
        return -1

    @api.model
    def sorted_with_newid(self, recordset, _order='id', reverse=False):
        """Return sorted recordset. Records can have pseudo NewId.

        If there are no records with NewId, it uses recordset `sorted`
        method. With NewId, recordset gets sortable dummy records which
        attributes are sorted like recordset, except for 'id' attribute.

        'id' attribute is sorted using SortedNewId class. Read
        SortedNewId docstring about 'id' attribute sorting.

        Args:
            recordset (recordset): recordset to be sorted.
            _order (str): sorting spec as used by attribute _order.
            reverse (bool): if sorted recordset is to be reversed.

        Returns:
            recordset: sorted recordset.

        """
        def create_dummy_record(record, pos, keys):
            # new object will be used for id.
            vals = {}
            for key in keys:
                vals[key] = record[key]
            # False is NewId record that can have ref.
            ref = record.id.ref if not record.id else None
            vals['id'] = SortedNewId(
                ref=ref, pos=pos, db_id=record.id)
            return ItemDummy(**vals)

        def to_sortable_with_map(recordset, keys):
            records_map = {}
            to_sort = []
            for pos, record in enumerate(recordset):
                dummy = create_dummy_record(record, pos, keys)
                records_map[dummy.id._pseudo_id] = record
                to_sort.append(dummy)
            return to_sort, records_map  # map is to convert back.

        def to_real_records(sorted_dummies, records_map, model_name):
            sorted_recordset = self.env[model_name]
            for dummy in sorted_dummies:
                sorted_recordset |= records_map[dummy.id._pseudo_id]
            return sorted_recordset
        order_keys = self.orderby_to_keys(_order)
        sort_keys = self.orderby_to_sort_keys(_order)
        key_func = self.get_sort_key_function(sort_keys)
        # only need to hack, if order contains 'id'
        if 'id' in _order:
            to_sort, records_map = to_sortable_with_map(
                recordset, self.to_writable_keys(order_keys))
            sorted_dummies = sorted(to_sort, key=key_func, reverse=reverse)
            return to_real_records(
                sorted_dummies, records_map, recordset._name)
        return recordset.sorted(key=key_func, reverse=reverse)

    # Context helpers

    @api.model
    def get_active_data(self, single=False, msg=None):
        """Validate context and return active data.

        Args:
            single (bool): check if active_ids can have only one element
                 in it (default: {False})
            msg (str): custom exception message if there is more than
                one active_id, when single=True used (default: {None})

        Returns:
            {'res_id': int, 'res_ids': list, 'model': str}

        """
        ctx = self._context
        try:
            model = ctx['active_model']
        except KeyError:
            raise ValidationError(
                _("Programming error: 'active_model' is missing in context"))
        res_id = ctx.get('active_id', False)
        res_ids = ctx.get('active_ids', [])
        if not res_id:
            try:
                res_id = res_ids[0]
            except IndexError:
                raise ValidationError(
                    _("Programming error: at least 'active_id' or "
                        "'active_ids' key must be present in context"))
        elif not res_ids:
            res_ids = [res_id]
        if single and len(res_ids) > 1:
            exc_msg = msg or _("Only single active_id is allowed")
            raise ValidationError(exc_msg)
        return {
            'res_id': res_id,
            'res_ids': res_ids,
            'model': model
        }

    @api.model
    def get_active_records(self, single=False, msg=None):
        """Return browsed records from active context.

        Args:
            single (bool): if record have to be singleton (
                default: {False}).
            msg (str): custom exception message if there is more than
                one active_id, when single=True used (default: {None})

        Returns:
            recordset

        """
        data = self.get_active_data(single=single, msg=msg)
        try:
            return self.env[data['model']].browse(data['res_ids'])
        except KeyError as e:
            raise ValidationError(_("Model '%s' not found.") % e)

    def force_with_context(self, obj, **kwargs):
        """Build context with custom arguments and force context update.

        Context is updated for argument `obj`.

        Usual context update `self = self.with_context(...)` doesn't
        work in onchange method, therefore we use a solution, suggested
        here: https://github.com/odoo/odoo/issues/7472
        """
        obj.env.context = obj.with_context(**kwargs).env.context

    @api.multi
    def prepare_message_compose_act(
            self, template_xml_id, composer_form_xml_id=None, target='new',
            attachments_data=None):
        """Prepare message composer.

        Args:
            template_xml_id (str): full xml id of `mail.template` to be used.
            composer_form_xml_id (str): full xml id of `mail.compose.message`
                form view.
            target (str): defines where new composer window should be
                opened (default - open in new window). Available values:
                'current', 'new', 'inline', 'fullscreen', 'main'.
            attachments_data (list): list of dictionaries with valid
                values for `ir.attachment` records to be created.
        """
        # `context` might contain extra defaults for
        # `mail.compose.message` or `mail.message`, such as `res_id`,
        # `model`, `composition_mode` and etc.
        template = self.env.ref(template_xml_id)
        context = dict(
            self._context,
            default_use_template=bool(template),
            default_template_id=template.id,
        )
        composer_form_view = composer_form_xml_id or self.env.ref(
            'mail.email_compose_message_wizard_form')
        attachments = Attachment = self.env['ir.attachment']
        for values in attachments_data:
            attachments |= Attachment.create(values)
        if attachments:
            context['default_attachment_ids'] = [(6, 0, attachments.ids)]
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(composer_form_view.id, 'form')],
            'view_id': composer_form_view.id,
            'target': target,
            'context': context,
        }

    @api.model
    def get_singleton_record(self, key, vals=None):
        """Get singleton record per uniquely specified key.

        If key does not exist, it will create new record. On consequent
        calls, it will return same record from cache - different vals
        will be ignored if key is already in cached dict.

        This method is intended for TransientModel records, to reference
        same short lived record as much as possible (till it will
        be vacuum cleaned by Odoo).

        Args:
            key (str, tuple): if string, must be model's name, if tuple
                first item must be model's name.
            vals (dict): values to use when creating record.
                (default: {None})

        Returns:
            record

        """
        if not vals:
            vals = {}
        record = singleton_records.get(key)
        # Comparing with None, to distinguish from missing key. Also
        # check if cursor is not closed, to be able to check record
        # existence.
        if record is not None and not record._cr._closed and record.exists():
            return record
        # key can be string.
        if isinstance(key, six.string_types):
            model = key
        else:  # Otherwise, we expect that it is tuple.
            model = key[0]
        try:
            Model = self.env[model]
        except KeyError as e:
            raise ValidationError(e)
        record = Model.create(vals)
        singleton_records[key] = record
        return record

    # ir.actions helpers.

    @api.model
    def _get_default_act_window_vals(self, Model):
        return {
            'name': Model._description,
            'type': 'ir.actions.act_window',
            'res_model': Model._name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
        }

    @api.model
    def _update_act_window_views(self, views, view_xml_ids_map):
        def get_view_id(xml_id):
            if not xml_id:
                return False
            return self.env.ref(xml_id)
        # Use enumerate to know which view tuple to replace.
        for i, item in enumerate(views):
            view_type, view_id = item
            if view_type in view_xml_ids_map:
                xml_id = view_xml_ids_map[view_type]
                views[i] = (get_view_id(xml_id), view_type)

    @api.model
    def prepare_action_view_records(
            self,
            records,
            act_xml_id=None,
            options=None):
        """Prepare act_window dict to open its record or records.

        If records are passed only, default act_window dict will be used
        with tree and form views.

        Default condition for using all views: need to be more than one
        record.
        Default condition for form view: need to be exactly one record.

        Args:
            records (recordset): recordset to generate act_window for.
            act_xml_id (str): XML ID for act_window to use its values
                from. (default: {None})
            options (dict): custom options to tailor how act_window dict
                is to be generated. Currently such keys are supported:
                    - custom_vals (dict): can specify any vals to
                        overwrite generated by default (e.g change
                        name).
                    - view_xml_ids_map (dict): XML IDs mapping for
                        views per view type. Key should be view type and
                        value that view's XML ID. Will overwrite XML ID
                        even if one is already set from act_window dict.
                    - conditions (dict): can specify custom conditions
                        when checking if use all views or form only.
                        Value is filter function which argument is
                        recordset. For all views, need to use key
                        'views_all', for form, 'views_form'.
                        (default: {None})

        Returns:
            Generated act_window dict
            dict

        """
        def filter_views(views, types_to_keep):
            return [
                (vid, vtype) for vid, vtype in views if vtype in types_to_keep
            ]

        def get_conditions(conditions):
            def condi_views_all(records):
                return len(records) > 1

            def condi_views_form(records):
                return len(records) == 1

            condi_all = condi_views_all
            condi_form = condi_views_form
            if conditions.get('views_all'):
                condi_all = conditions['views_all']
            if conditions.get('views_form'):
                condi_form = conditions['views_form']
            return condi_all, condi_form

        if not options:
            options = {}
        if act_xml_id:
            act_dict = self.env.ref(act_xml_id).read()[0]
        else:
            # Pass records to act as a Model.
            act_dict = self._get_default_act_window_vals(records)
        # Set custom vals on act_dict.
        act_dict.update(options.get('custom_vals', {}))
        condi_all, condi_form = get_conditions(options.get('conditions', {}))
        if condi_all(records):
            act_dict['domain'] = [('id', 'in', records.ids)]
        elif condi_form(records):
            views = filter_views(act_dict['views'], ['form'])
            act_dict.update(
                res_id=records.id,
                view_mode='form',
                views=views
            )
        else:
            act_dict['type'] = 'ir.actions.act_window_close'
            # Return here, to avoid any other updates that might come
            # at the end of method.
            return act_dict
        if options.get('view_xml_ids_map'):
            view_xml_ids_map = options['view_xml_ids_map']
            self._update_act_window_views(act_dict['views'], view_xml_ids_map)
        return act_dict

    # Date helpers.

    @api.model
    def check_dates_range(
            self, date_earlier, date_later, allow_equal=True, msg=None):
        """Validate two dates and raise if condition is not satisfied.

        Args:
            date_earlier (str, date, datetime): date which should be
                earlier.
            date_later (str, date, datetime): date which should be
                later.
            allow_equal (bool): defines if dates are allowed to be
                equal (default: {True}).
            msg (str): custom exception message (default: {None}).
        """
        _operator = operator.gt if allow_equal else operator.ge
        if _operator(date_earlier, date_later):
            msg = msg or _("Date From must be earlier than %sDate To.") % (
                _("or equal to ") if allow_equal else "")
            raise UserError(msg)

    @api.model
    def get_iso_timestamp(self, dt=fields.Datetime.now()):
        """Get datetime in ISO format.

        Args:
            dt (str, date, datetime): date/datetime string or object
                (default: {now}).

        Returns:
            datetime in ISO format, e.g. '2018-01-22T08:19:54+01:00'.
            str

        """
        return fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(dt)).isoformat()

    # Compute amount helpers.

    @api.model
    def get_cost(self, product, uom, options=None):
        """Return unconverted cost for product.

        It will return price's original currency alongside.
        Possible one of four cases:
          - if order is 'standard' and standard_price is not False, will
                return it.
          - if order is 'supplier', will return seller/vendor price if
                it's set.
          - if order is 'bom', will return cost calculated from bom if
                product has one.
          - if none of the above is set, will default to 0.

        Args:
            product (recordset): product.product object for which cost
                should be calculated.
            uom (recordset): uom.uom recordset.
            options (dict): custom options to get cost price. Supported
                keys:
                - quantity (float): quantity for which cost should be
                    get (default {0.0}).
                - date (datetime.date): date to get cost.
                - cost_methods (tuple): defines in what order cost will
                    be calculated (which type of cost method must be
                    checked first). Default: {('standard', 'supplier')}.

        Returns:
            cost, res.currency recordset, cost method
            float, recordset, str

        """
        if not options:
            options = {}
        company_currency = self.env.user.company_id.currency_id

        def get_standard_cost():
            if product.standard_price:
                return product.standard_price, company_currency

        def get_supplier_cost():
            if product.seller_ids:
                seller = product._select_seller(
                    quantity=options.get('quantity', 0.0),
                    date=options.get('date', None), uom_id=uom)
                # because might not match and return empty rec.
                if seller:
                    return seller.price, seller.currency_id

        def get_bom_cost():
            bom = self.env['mrp.bom'].sudo()._bom_find(product=product)
            if bom:
                uom_ratio = bom.product_uom_id._compute_quantity(
                    1.0, uom, round=False)
                if bom.product_qty and uom_ratio:
                    factor = bom.product_qty / uom_ratio
                    # Dividing by factor, because need unit price,
                    # not whole price of BOM (it would be different
                    # if quantity on BOM is different than one)
                    price = self.env[
                        'report.mrp.report_bom_structure']._get_price(
                            bom, factor, product) / factor
                    # Its a dilemma here, because get_cost is
                    # supposed to return unconverted price, though
                    # to get correct price, need to specify
                    # converted quantity for BOM. To workaround
                    # that, converting back to product UOM.
                    price = uom._compute_price(price, product.uom_id)
                    return price, self.env.user.company_id.currency_id

        for cost_method in options.get(
                'cost_methods', ('standard', 'supplier')):
            cost_tuple = locals()['get_%s_cost' % cost_method]()
            if cost_tuple:
                return cost_tuple + (cost_method,)

        return 0.0, company_currency, False

    @api.model
    def convert_order_float_to_other_curr(self, order, amount, to_currency):
        """Convert some order amount to another currency if needed."""
        date = order.date_order or fields.Date.today()
        from_currency = order.pricelist_id.currency_id
        if from_currency != to_currency:
            amount = from_currency._convert(
                amount, to_currency, order.company_id, date)
        return amount

    @api.model
    def get_o2m_field_for_inverse(self, Model, inverse_name):
        """Return related o2m field using inverse_name (m2o).

        Returns first found o2m field for inverse field.

        Args:
            Model (object): Model that has m2o field with name from
                rel_field_name.
            inverse_name (str): m2o field that is inverse field for
                target o2m field.

        Returns:
            fields.One2Many: o2m field object.

        """
        parent_model_name = Model._fields[inverse_name].comodel_name
        ParentModel = self.env[parent_model_name]
        for field in ParentModel._fields.values():
            if field.type == 'one2many' and field.inverse_name == inverse_name:
                return field
        raise ValueError(
            "No one2many field found for inverse field '%s' with model '%s'" %
            (inverse_name, parent_model_name)
        )

    # Access Management Helpers.
    # TODO: better make system wide change module that would implement
    # such access management without a need to override for every
    # model/fields pair.
    @api.model
    def check_access_set_fields(self, fields, vals, groups, model=''):
        """Check if user has access to set value on fields.

        Current user is checked for specified fields. If fields are
        in vals and user has no specified access groups, AccessError is
        raised.

        Args:
            fields (list): field names to check.
            vals (dict): dictionary used in create/write methods.
            groups (str): comma-separated list of fully-qualified group
                external IDs, e.g., `base.group_user,base.group_system`,
                optionally preceded by `!`.
            model (str): model name to show on access error message.
                (default: {''})

        Raises:
            AccessError

        """
        if self._uid != SUPERUSER_ID:
            for field in fields:
                if field in vals:
                    if not self.user_has_groups(groups):
                        raise AccessError(
                            _("You have no access to set value on '%s' "
                                "field. Model: '%s'") % (field, model))
                    break  # its enough to match one field with vals.

    # View Manipulation Helpers

    def validate_form_required_fields(self, record):
        """Validate record required fields as it was saved on form.

        Args:
            record (recordset): singleton recordset to validate required
                fields.

        Returns:
            True if valid
            bool

        Raises:
            ValidationError

        """
        def check_required(form):
            fields = form._view['fields']
            for fname in fields:
                descr = fields[fname]
                value = form._values[fname]
                # Reusing same approach as in odoo.tests.common.Form.
                required = (
                    form._get_modifier(fname, 'required') and not
                    descr['type'] == 'boolean'
                )
                yield (required, value, fname)

        def is_required_missing(required, value):
            return required and value is False

        with Form(record) as form:
            field_labels = []
            IrTranslation = self.env['ir.translation']
            model_name = record._name
            for required, value, fname in check_required(form):
                if is_required_missing(required, value):
                    # This one is supposed to be cached.
                    label = IrTranslation.get_field_string(model_name)[fname]
                    field_labels.append(label)
            if field_labels:
                raise ValidationError(
                    _("These fields are required: %s") %
                    ', '.join(field_labels))
        return True
