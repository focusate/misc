import os
import six
from num2words import num2words
import operator
import validators

from odoo import models, api, fields, _
from odoo.tools.convert import convert_file
from odoo.exceptions import ValidationError, UserError

from odoo.addons.base.models.ir_sequence import IrSequence

# Common constants.
PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High')]
DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

# Cache for singleton records.
singleton_records = {}


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
            IrSequence = self.env['ir.sequence']
            if company_id:
                return IrSequence.with_company(company_id).next_by_code(code)
            return IrSequence.next_by_code(code)
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
    def get_months_selection(self):
        """Return list of months with their indexes."""
        # Could be a constant, but constants don't support translations.
        return [
            (1, _("January")),
            (2, _("February")),
            (3, _("March")),
            (4, _("April")),
            (5, _("May")),
            (6, _("June")),
            (7, _("July")),
            (8, _("August")),
            (9, _("September")),
            (10, _("October")),
            (11, _("November")),
            (12, _("December")),
        ]

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
                uom_ratio = uom._compute_quantity(
                    1.0, bom.product_uom_id, round=False)
                # BOM should always have some qty entered, but there is
                # an issue and it is allowed to enter zero value.
                # Issue is reported to Odoo.
                if bom.product_qty and uom_ratio:
                    # Quantity which is requested is important, because
                    # depending on quantity, BOM cost price might
                    # variate.
                    factor = options.get('quantity', 1.0) * uom_ratio
                    # BOM Structure & Cost report already calculates all
                    # needed values and we can reuse them.
                    bom_data = self.env[
                        'report.mrp.report_bom_structure']._get_bom(
                            bom_id=bom.id, product_id=product, line_qty=factor)
                    # We except UOM ratio when it is below 1.0,
                    # because total is already counted for 1 UOM and
                    # there is no need to do extra conversions.
                    price = bom_data['total']
                    if uom_ratio >= 1.0:
                        price = price / bom_data['bom_qty'] * uom_ratio
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

    # Other constraint helpers

    @api.model
    def check_url(self, url):
        """Check URL validity.

        Args:
            url (str): url to check

        Returns:
            None

        Raises:
            ValidationError if not valid

        """
        # Using '' as default, to make sure False value is not passed,
        # which cant be validated by validators.url.
        if not validators.url(url or ''):
            raise ValidationError(_("'%s' is not valid URL.") % url)
