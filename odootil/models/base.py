import itertools
import collections
from footil.sorting import ReverseComparator

from odoo import models, api, _
from odoo.exceptions import ValidationError
from odoo.tests.common import Form

from ..tools.search import get_name_search_domain

PSQL_DESC = 'desc'


class NewIdSorted(models.NewId):
    """Subclass for NewId to make it sortable with real record.

    Comparing is done in three ways:
        - Both have origin. Comparing origin.
        - Only one has origin. Less than is the one with origin.
        - None have origin. Comparing with pos (position).
    """

    id_iter = itertools.count()
    __slots__ = ('pos', '_pseudo_id')

    def __init__(self, origin=None, ref=None, pos=0):
        """Override to include original position in recordset."""
        super().__init__(origin=origin, ref=ref)
        self.pos = pos
        self._pseudo_id = next(self.id_iter)

    def __lt__(self, other):
        """Compare int or other NewIdSorted object."""
        if self.origin and other.origin:
            return self.origin < other.origin
        # The one with origin is less than without origin.
        if not self.origin and other.origin:
            return False
        if self.origin and not other.origin:
            return True
        # None have origin. Comparing with position.
        return self.pos < other.pos

    def __repr__(self):
        """Return reproducible object in string."""
        class_name = self.__class__.__name__
        return '%s(origin=%s, pos=%s)' % (class_name, self.origin, self.pos)


class Base(models.AbstractModel):
    """Extend to add odootil helper methods."""

    _inherit = 'base'

    # Search helpers.

    @api.model
    def name_search_multi_leaf(
        self,
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
        domain = get_name_search_domain(
            name,
            keys,
            leaf_conditions=leaf_conditions,
            args=args,
            operator=operator
        )
        uid = name_get_uid or self._uid
        ids = self._search(domain, limit=limit, access_rights_uid=uid)
        recs = self.browse(ids)
        return models.lazy_name_get(recs.with_user(uid))

    # orderby transformation helpers.

    @api.model
    def to_writable_keys(self, keys):
        """Filter keys, leaving only those that could be writable."""
        return [k for k in keys if k not in models.MAGIC_COLUMNS]

    @api.model
    def _orderby_to_items(self, order_spec=None):
        order_spec = order_spec or self._order
        for item in order_spec.split(','):
            # Remove leading white space that might be hanging after
            # splitting.
            item = item.lstrip()
            # E.g. 'name asc NULLS FIRST' -> ('name', 'asc NULLS FIRST')
            key, *options = item.split(' ', 1)
            options = options[0] if options else ''
            yield (key.replace(' ', ''), options)

    @api.model
    def orderby_to_keys(self, order_spec=None):
        """Transform Model's _order to list keys only.

        Strips all options, like asc, desc, NULLS {FIRST | LAST}.
        """
        return [item[0] for item in self._orderby_to_items(
            order_spec=order_spec)]

    @api.model
    def orderby_to_writable_keys(self, order_spec=None):
        """Transform Model's _order to list with writable keys."""
        return self.to_writable_keys(self.orderby_to_keys(
            order_spec=order_spec))

    @api.model
    def orderby_to_sort_keys(self, order_spec=None):
        """Transform Model's _order to list of tuple keys.

        First item in tuple is key, second boolean value, indicating if
        key order must be reversed (usually descending).
        """
        def is_reversed(options):
            return PSQL_DESC in options.lower()
        return [
            (i[0], is_reversed(i[1])) for i in self._orderby_to_items(
                order_spec=order_spec)
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

    def get_record_index(
        self,
        record,
        start=0,
        end=None,
        msg=None,
            raise_if_not_found=True):
        """Get lowest zero-based index as record value in recordset.

        Can specify optional range.

        Args:
            record (recordset): single record to find its index position
                in recordset.
            start (int): start index for recordset (default: {0})
            end (int): end index for recordset (default: {None})
            msg (str): custom exception message to use if record is not
                found inside recordset (default: {None}).
            raise_if_not_found (bool): raise ValidationError if record
                is not in recordset (default: {True})

        Returns:
            record index position in recordset or raise if not found, or
            -1 if not raising.
            int

        """
        if not end:
            end = len(self)
        if start > end:
            raise ValidationError(_("end index must be greater than start."))
        for i in range(start, end):
            if self[i] == record:
                return i
        if raise_if_not_found:
            if not msg:
                msg = _("%s is not in recordset") % record
            raise ValidationError(msg)
        return -1

    def sorted_virtual(self, order_spec=None, reverse=False):
        """Return sorted recordset. Records can have pseudo NewId.

        If order_spec has no 'id' column, it uses recordset `sorted`
        method.

        If need to sort by 'id', sort data from recordset is extracted
        into separate list and attributes are sorted like recordset,
        except for 'id' attribute. 'id' attribute is sorted using
        NewIdSorted class. Read NewIdSorted docstring about 'id'
        attribute sorting.

        Args:
            order_spec (str): sorting spec as used by attribute _order
                (default: {None}).
            reverse (bool): if sorted recordset is to be reversed
                (default: {False}).

        Returns:
            recordset: sorted recordset.

        """
        def create_data_to_sort(record, pos, keys):
            vals = {k: record[k] for k in keys}
            newid_kwargs = {'pos': pos}
            if record.id:  # real record
                newid_kwargs['origin'] = record.id
            else:  # virtual record
                newid_kwargs['ref'] = record.id.ref
            # False is NewId record that can have ref.
            vals['id'] = NewIdSorted(**newid_kwargs)
            return vals

        def to_sortable_with_map(keys):
            records_map = {}
            to_sort = []
            for pos, record in enumerate(self):
                data = create_data_to_sort(record, pos, keys)
                records_map[data['id']._pseudo_id] = record
                to_sort.append(data)
            return to_sort, records_map  # map is to convert back.

        def extract_sorted_records(sorted_data, records_map):
            sorted_recordset = self.env[self._name]
            for dummy in sorted_data:
                sorted_recordset |= records_map[dummy['id']._pseudo_id]
            return sorted_recordset

        order_keys = self.orderby_to_keys(order_spec)
        sort_keys = self.orderby_to_sort_keys(order_spec)
        key_func = self.get_sort_key_function(sort_keys)
        # Only need to hack, if order contains 'id'
        if 'id' in order_keys:
            to_sort, records_map = to_sortable_with_map(
                self.to_writable_keys(order_keys))
            sorted_data = sorted(to_sort, key=key_func, reverse=reverse)
            return extract_sorted_records(sorted_data, records_map)
        return self.sorted(key=key_func, reverse=reverse)

    def new_multi(
        self,
        values=None,
            refs=None):
        """Return new virtual record using provided record values.

        This is wrapper for `new` method to handle multiple virtual
        records at once.

        Args:
            values (dict): extra values to use in update.
                (default: {None}).
            refs (iterable): list of references to NewId. Only used for
                empty recordset. Otherwise, record is passed as origin
                on new. (default: {None}).

        Returns:
            recordset with NewId.

        """
        def get_items_and_key():
            if self:
                return (self, 'origin')
            return (refs, 'ref')

        if not values:
            values = {}
        items, key = get_items_and_key()
        if items:
            new_recs = self.env[self._name]
            for item in items:
                new_recs |= self.new(values=values, **{key: item})
            return new_recs
        return self.new(values=values)

    # Selection field helpers.

    @api.model
    def get_selection_map(self, fname):
        """Return OrderedDict selection mapping for record field.

        Args:
            fname (str): selection field name
        Returns:
            OrderedDict: selection mapping in OrderedDict form.
        """
        return collections.OrderedDict(self._fields[fname].selection)

    def get_selection_label(self, fname):
        """Return Label of current selection field value.

        If selection value is falsy, returns empty string. This might
        return unexpected results if one of the selection field values
        is falsy value. It is good practice to specify only truthy
        values for selection values.

        Args:
            fname (str): selection field name

        Returns:
            str: label of current selection field value.

        """
        self.ensure_one()
        val = self[fname]
        if not val:
            return ''
        selection_map = self.get_selection_map(fname)
        return selection_map[val]

    # Context helpers

    @api.model
    def with_context_force(self, **kwargs):
        """Build context with custom arguments and force context update.

        Context is updated for argument `obj`.

        Usual context update `self = self.with_context(...)` doesn't
        work in onchange method, therefore we use a solution, suggested
        here: https://github.com/odoo/odoo/issues/7472
        """
        self.env.context = self.with_context(**kwargs).env.context

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

    # View Manipulation Helpers

    def validate_form_required_fields(self):
        """Validate record required fields as it was saved on form.

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

        self.ensure_one()
        with Form(self) as form:
            field_labels = []
            IrTranslation = self.env['ir.translation']
            model_name = self._name
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

    # ir.actions helpers.

    @api.model
    def _get_default_act_window_data(self):
        return {
            'name': self._description,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
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

    def prepare_act_window_data(self, act_xml_id=None, options=None):
        """Prepare act_window dict to open its record or records.

        If no extra args are passed, default act_window dict will be
        used with tree and form views.

        Can set manual option, to not use any conditions and modify what
        is manually specified.

        Default condition for using all views: need to be more than one
        record.
        Default condition for form view: need to be exactly one record.

        Args:
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
                    - manual (bool): whether to ignore any condition
                        and use only specified options.

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

        def handle_conditions():
            condi_all, condi_form = get_conditions(
                options.get('conditions', {})
            )
            if condi_all(self):
                act_dict['domain'] = [('id', 'in', self.ids)]
                return True
            elif condi_form(self):
                views = filter_views(act_dict['views'], ['form'])
                act_dict.update(
                    res_id=self.id,
                    view_mode='form',
                    views=views
                )
                return True
            else:
                act_dict['type'] = 'ir.actions.act_window_close'
                return False

        if not options:
            options = {}
        if act_xml_id:
            act_dict = self.env.ref(act_xml_id).read()[0]
        else:
            act_dict = self._get_default_act_window_data()
        # Set custom vals on act_dict.
        act_dict.update(options.get('custom_vals', {}))
        condi_all, condi_form = get_conditions(options.get('conditions', {}))
        if not options.get('manual'):
            condi_res = handle_conditions()
            if not condi_res:
                # Return here, to avoid any other updates that might come
                # at the end of method.
                return act_dict
        if options.get('view_xml_ids_map'):
            view_xml_ids_map = options['view_xml_ids_map']
            self._update_act_window_views(act_dict['views'], view_xml_ids_map)
        return act_dict
