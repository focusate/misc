from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class ResBank(models.Model):
    """Extend to add branches support for banks."""

    _inherit = 'res.bank'

    is_branch = fields.Boolean()
    parent_id = fields.Many2one('res.bank', "Main Bank")
    child_ids = fields.One2many('res.bank', 'parent_id', "Branches")
    use_bank_address = fields.Boolean("Use Main Bank Address")
    # Technical field used to know if bank has any childs/branches as
    # Odoo view is clunky when you need to use o2m field in domain
    # whether its empty or not..
    has_childs = fields.Boolean(
        compute='_compute_has_childs',
        string="Has Branches"
    )

    @api.depends('child_ids')
    def _compute_has_childs(self):
        for bank in self:
            bank.has_childs = bool(bank.child_ids)

    @api.constrains('parent_id', 'is_branch')
    def _check_parent_id(self):
        for bank in self:
            if not bank.is_branch and bank.parent_id:
                raise ValidationError(
                    _("Only branches can have main bank set!"))
            if not bank._check_recursion():
                raise ValidationError(
                    _('You cannot create recursive branches.')
                )

    @api.onchange('use_bank_address', 'parent_id')
    def _onchange_use_bank_address(self):
        if self.use_bank_address and self.parent_id:
            self.update(self.parent_id._prepare_address_vals())

    @api.onchange('is_branch')
    def _onchange_is_branch(self):
        if not self.is_branch:
            self.update({'parent_id': False, 'use_bank_address': False})

    def name_get(self):
        """Extend to add parent (main bank) name before branch."""
        res = super().name_get()
        branches = self.filtered('parent_id')
        if branches:
            res_dct = dict(res)
            for branch in branches:
                branch_id = branch.id
                name = f'{branch.parent_id.name} / {res_dct[branch_id]}'
                res_dct[branch_id] = name
            res = [(k, v) for k, v in res_dct.items()]
        return res

    @api.model
    def _name_search(
        self,
        name,
        args=None,
        operator='ilike',
        limit=100,
            name_get_uid=None):
        if name:
            # Make sure search is done asymmetrically
            name = name.split(' / ')[-1]
            # To be picked up by _search.
            self = self.with_context(
                domain_branch_parent=[('parent_id.name', operator, name)]
            )
        return super(ResBank, self)._name_search(
            name,
            args=args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid
        )

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
            access_rights_uid=None):
        domain_branch_parent = self._context.get('domain_branch_parent')
        if domain_branch_parent:
            args = expression.OR([args, domain_branch_parent])
            # To prevent maximum recursion loop.
            self = self.with_context(domain_branch_parent=False)
        return super(ResBank, self)._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
            access_rights_uid=access_rights_uid
        )

    @property
    @api.model
    def _bank_address_fields(self):
        return ['zip', 'street', 'street2', 'city', 'state', 'country']

    def _prepare_address_vals(self):
        self.ensure_one()
        # NOTE. Can't use `read` as it will fail on virtual records.
        vals = {}
        for fname in self._bank_address_fields:
            val = self[fname]
            if self._fields[fname].type == 'many2one':
                val = val.id
            vals[fname] = val
        return vals

    def sync_bank_address(self):
        """Sync bank address with its childs."""
        self.ensure_one()
        branches = self.child_ids.filtered('use_bank_address')
        if branches:
            branches.write(self._prepare_address_vals())

    @api.model_create_multi
    def create(self, vals_list):
        """Extend to sync bank address with its branches."""
        for vals in vals_list:
            if (
                vals.get('is_branch')
                and vals.get('use_bank_address')
                # To make sure self.ensure_one won't raise error.
                and vals.get('parent_id')
            ):
                bank = self.browse(vals['parent_id'])
                # Overwrite all address fields, to use banks.
                vals.update(bank._prepare_address_vals())
        return super().create(vals_list)

    def write(self, vals):
        """Extend to sync bank address with its branches."""
        res = super().write(vals)
        # Sync when its triggered from branch.
        if vals.get('is_branch') or vals.get('parent_id'):
            for bank in self.mapped('parent_id'):
                bank.sync_bank_address()
        # Sync when its triggered from bank.
        elif set(self._bank_address_fields).intersection(vals.keys()):
            for bank in self:
                bank.sync_bank_address()
        return res
