from collections import namedtuple
from footil.formatting import to_new_named_format, generate_name

from odoo import models

from odoo.addons.base.models.res_partner import ADDRESS_FIELDS


class AddressFormatMixin(models.AbstractModel):
    """Class to format address according to related country format.

    Default address fields are based on res.partner. To change fields,
    extend `address_fields` property.

    If object does not have some of address fields, it can be marked
    with None value to be ignored.
    """

    _name = 'address.format.mixin'
    _description = "Address Format Mixin"

    # TODO: implement address compute following similarly
    # _display_address_depends if this mixin to be used for more than
    # reports.

    @property
    def address_fields_map(self):
        """Return mapping between address placeholders and fields.

        Extend to modify or add new placeholder/fields.
        """
        # Taking same fields as in res.partner, but adding as map, so
        # it would be possible to provide different fields for other
        # models.
        return {k: k for k in ADDRESS_FIELDS}

    @property
    def _address_vals(self):
        """Lookup field values from address_fields_map."""
        self.ensure_one()
        ph_vals = {}
        for ph, fname in self.address_fields_map.items():
            ph_vals[ph] = self[fname]
        return ph_vals

    @property
    def address_format_kwargs(self):
        """Return all possible arguments for address format."""
        self.ensure_one()
        ph_vals = self._address_vals
        state = ph_vals['state_id']
        country = ph_vals['country_id']
        return {
            'state_code': state.code or '',
            'state_name': state.name or '',
            'country_code': country.code or '',
            'country_name': country.name or '',
            **{k: v or '' for k, v in ph_vals.items()}
        }

    def _address_create_data_class(self, keys):
        """Instantiate AddressData named tuple."""
        self.ensure_one()
        return namedtuple('AddressData', ' '.join(keys))

    @property
    def _address_data_obj(self):
        self.ensure_one()
        kwargs = self.address_format_kwargs
        AddressData = self._address_create_data_class(kwargs.keys())
        return AddressData(**kwargs)

    @property
    def address_default_format(self):
        """Return default address format."""
        return self.env.company.default_address_format or ''

    @property
    def address_format(self):
        """Return format either from related country or default one."""
        self.ensure_one()
        country = self[self.address_fields_map['country_id']]
        if (
            self.env.company.use_country_address_format
            and country.address_format
        ):
            return country.address_format
        return self.address_default_format

    def address_interpolate(self, strip_falsy=True):
        """Interpolate country or default address format."""
        self.ensure_one()
        # We have old style formatting from country objects, but we want
        # to convert it to new style formatting, so we would be able to
        # manage falsy values better.
        fmt = to_new_named_format(self.address_format)
        address_obj = self._address_data_obj
        return generate_name(fmt, address_obj, strip_falsy=strip_falsy)
