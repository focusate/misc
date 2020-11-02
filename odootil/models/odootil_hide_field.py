from odoo import api, models


class OdootilHideField(models.AbstractModel):
    """Mixin model meant to be inherited by other models.

    There might be cases, when some fields must be hidden from advanced
    search filters and/or group by filters.

    Define how and which fields should be hidden in advanced search, by
    passing list of tuples containing field names, filter and group by
    visibility values, e.g.
    `_odootil_hide_field = [('field_1', True, True)]` means that field
    will be hidden from both - filter and group by options.
    """

    _name = 'odootil.hide_field'
    _description = 'Odootil Hide Field Mixin'
    _odootil_hide_field = []

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Override to manage field visibility in advanced search."""
        def disable_option(field_data, option):
            field_data[option] = False

        res = super().fields_get(allfields, attributes=attributes)
        for field, no_select, no_sort in self._odootil_hide_field:
            try:
                field_data = res[field]
            except KeyError:
                pass
            else:
                if no_select:
                    # Affects advanced search filters
                    disable_option(field_data, 'selectable')
                if no_sort:
                    # Affects advanced group by filters
                    disable_option(field_data, 'sortable')
        return res
