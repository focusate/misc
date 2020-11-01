import re
from itertools import cycle

from odoo import models, fields, api

ITEM_CYCLE_START_FIELD = 'odootil_item_cycle_start_id'
ITEM_CYCLE_END_FIELD = 'odootil_item_cycle_end_id'
ITEM_CYCLE_CONTAINER_FIELD = 'odootil_item_cycle_ids'
ITEM_CYCLE_CONTAINER_COMPUTE = '_compute_odootil_item_cycle'


class OdootilItemCycle(models.AbstractModel):
    """Mixin to define specific range of items that are cycled.

    E.g. years, months, weeks etc.
    """

    _name = 'odootil.item_cycle'
    _description = "Odootil Item Cycle Mixin"
    _rec_name = 'position'
    _order = 'position'

    position = fields.Integer(index=True)

    _sql_constraints = [
        (
            'position_uniq',
            'unique (position)',
            'The position must be unique !'
        ),
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override to keep only numbers on name value."""
        name = re.sub(r"\D", "", name)
        return super().name_search(
            name=name, args=args, operator=operator, limit=limit)

    @api.model
    def get_container_models_to_recompute(self):
        """Override to include rel container models for recompute."""
        return []

    @api.model
    def _get_container_records_to_recompute(self, Model, domain=None):
        return Model.with_context(active_test=False).search(domain or [])

    def _recompute_container_fields(self):
        for model_name in self.get_container_models_to_recompute():
            Model = self.env[model_name]
            field = Model._fields[ITEM_CYCLE_CONTAINER_FIELD]
            records = self._get_container_records_to_recompute(Model)
            self.env.add_to_compute(field, records)
        self.recompute()

    @api.model_create_multi
    def create(self, vals_list):
        """Override to trigger related container fields recompute."""
        records = super().create(vals_list)
        self._recompute_container_fields()
        return records

    def write(self, vals):
        """Override to trigger related container fields recompute."""
        result = super().write(vals)
        if 'position' in vals:
            self._recompute_container_fields()
        return result


class OdootilItemCycleContainer(models.AbstractModel):
    """Mixin to add start/end range on another model for search.

    When inherited, must define odootil_item_cycle_ids compute method,
    that is of m2o type, has comodel_name for model that inherited
    from 'odootil.item_cycle', must be stored and use compute method
    name defined in ITEM_CYCLE_CONTAINER_COMPUTE. e.g:
        odootil_item_cycle_ids = fields.Many2many(
            'concreate.item_cycle.model',
            string="My Name",
            store=True,
            compute=ITEM_CYCLE_CONTAINER_COMPUTE,
        )

    When defined, it additionally adds two extra fields that indicate
    start and end range for items cycle.

    Optionally, it is possible to specify names for these fields via
    _odootil_item_cycle_field_labels attribute. It expects tuple where
    first item is label for start and second for end field respectively.
    """

    _name = 'odootil.item_cycle.container'
    _description = "Odootil Item Cycle Container Mixin"
    # Start and End names.
    _odootil_item_cycle_field_labels = (None, None)

    odootil_item_cycle_ids = None

    _sql_constraints = [
        (
            'stard_end_not_xor',
            'CHECK (({start} IS NOT NULL AND {end} IS NOT NULL) OR '
            '({start} IS NULL and {end} IS NULL))'.format(
                start=ITEM_CYCLE_START_FIELD,
                end=ITEM_CYCLE_END_FIELD),
            "Both Start and End must be specified or not specified!"
        ),
    ]

    @api.model
    def _odootil_item_cycle_get_comodel(self):
        return self._fields[ITEM_CYCLE_CONTAINER_FIELD].comodel_name

    def _odootil_item_cycle_get_rel_field(self, field_class, field_vals):
        # Remove None values.
        field_vals = {k: v for k, v in field_vals.items() if v is not None}
        return field_class(**field_vals)

    def _odootil_item_cycle_patch(self):

        @api.model
        def get_container_models_to_recompute_patched(s):
            models = get_container_models_to_recompute_patched.origin(s)
            models.append(self._name)
            return models

        # Patch get_container_models_to_recompute method to add this
        # model as container model for recomputation.
        comodel_name = self._odootil_item_cycle_get_comodel()
        self.env[comodel_name]._patch_method(
            'get_container_models_to_recompute',
            get_container_models_to_recompute_patched
        )

    @api.model
    def _setup_base(self):
        res = super()._setup_base()
        # _setup_base is called multiple times, so we check if these
        # fields were not already added.
        keys = self._fields.keys()
        if (ITEM_CYCLE_CONTAINER_FIELD in keys and ITEM_CYCLE_START_FIELD
                not in keys):
            start_label, end_label = self._odootil_item_cycle_field_labels
            comodel_name = self._odootil_item_cycle_get_comodel()
            common_vals = {
                'comodel_name': comodel_name,
                'ondelete': 'restrict',
            }
            self._add_field(
                ITEM_CYCLE_START_FIELD,
                self._odootil_item_cycle_get_rel_field(
                    fields.Many2one,
                    field_vals={'string': start_label, **common_vals}
                ),
            )
            self._add_field(
                ITEM_CYCLE_END_FIELD,
                self._odootil_item_cycle_get_rel_field(
                    fields.Many2one,
                    field_vals={'string': end_label, **common_vals}
                ),
            )
            self._odootil_item_cycle_patch()
        return res

    @api.model
    def _odootil_item_cycle_filter_range(
            self, item_cycle_items, start, end):
        current_item = next(item_cycle_items)
        filtered_items = self.env[current_item._name]
        while current_item.position != start:
            current_item = next(item_cycle_items)
        filtered_items |= current_item  # start
        while current_item.position != end:
            filtered_items |= current_item
            current_item = next(item_cycle_items)
        filtered_items |= current_item  # end
        return filtered_items

    @api.depends(ITEM_CYCLE_START_FIELD, ITEM_CYCLE_END_FIELD)
    def _compute_odootil_item_cycle(self):
        comodel_name = self._odootil_item_cycle_get_comodel()
        item_cycle_items = self.env[comodel_name].search([])
        # To be able to iterate in a cycle (indefinitely).
        item_cycle_items = cycle(item_cycle_items)
        for rec in self:
            if (not rec[ITEM_CYCLE_START_FIELD] or not
                    rec[ITEM_CYCLE_END_FIELD]):
                continue
            items = self._odootil_item_cycle_filter_range(
                item_cycle_items,
                rec[ITEM_CYCLE_START_FIELD].position,
                rec[ITEM_CYCLE_END_FIELD].position,
                )
            rec[ITEM_CYCLE_CONTAINER_FIELD] = items
