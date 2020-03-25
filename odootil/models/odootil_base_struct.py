from odoo import models, fields


class OdootilBaseStruct(models.AbstractModel):
    """Mixin that can be used for models to include basic structure."""

    _name = 'odootil.base_struct'
    _description = "Odootil Base Structure Mixin"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [('name_uniq', 'unique(name)', "Name must be unique!")]
