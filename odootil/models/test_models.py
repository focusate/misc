from odoo import models, fields


from . odootil_item_cycle import ITEM_CYCLE_CONTAINER_COMPUTE


class ItemCycleTestWeek(models.Model):
    """Test model using odootil.item_cycle."""

    _name = 'item_cycle.test.week'
    _description = 'Item Cycle Test Week'
    _inherit = 'odootil.item_cycle'


class ItemCycleTestWeekContainer(models.Model):
    """Test model using odootil.item_cycle.container."""

    _name = 'item_cycle.test.week.container'
    _description = 'Item Cycle Test Week Container'
    _inherit = 'odootil.item_cycle.container'
    _odootil_item_cycle_field_labels = ('Start Week', 'End Week')

    name = fields.Char(required=True)
    odootil_item_cycle_ids = fields.Many2many(
        'item_cycle.test.week',
        string="Weeks Range",
        compute=ITEM_CYCLE_CONTAINER_COMPUTE,
        store=True)
