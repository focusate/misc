from footil.formatting import generate_names

from odoo import models, api, _
from odoo.exceptions import ValidationError


class OdootilSeq(models.AbstractModel):
    """Mixin model meant to be inherited by other models.

    Its purpose is to streamline sequence functionality on records,
    where each record gets number assigned from provided sequence.
    Sequence can be global or per company.

    Set up after inheriting mixin:

    `_odootil_seq_field` must be defined on target class. If
    default is used, then such field can be defined:
        `number = fields.Char(index=True, copy=False, readonly=True)`

    `_odootil_seq_code` or `_odootil_seq_xmlid` must
    be specified, where first one is ir.sequence code, second one, xmlid
    pointing to ir.sequence record. If none of these are specified,
    sequence will not be incremented and can stop from creating record,
    depending on chosen implementation.

    `_odootil_seq_name_pattern` is used in name_get to generate
    custom display_name for each record. Can be overwritten with None to
    use original name_get.

    `_odootil_seq_search_keys`: tuple of keys to use in custom
    name_search. Can be overwritten with None to use original
    name_search implementation.
    `_odootil_seq_company_constraint_msg`: message to raise if
    `_odootil_seq_check_number` constraint is used.
    """

    _name = 'odootil.seq'
    _description = 'Odootil Sequence Mixin'
    # Should be overwritten with appropriate values on target model.
    _odootil_seq_field = 'number'
    _odootil_seq_code = None
    _odootil_seq_xmlid = None
    _odootil_seq_name_pattern = (
        "[{%s}] {name}" % _odootil_seq_field)
    _odootil_seq_search_keys = ('name', _odootil_seq_field)
    _odootil_seq_company_constraint_msg = _(
        "Number must be unique for records without company selected.")

    @api.model
    def _odootil_seq_get_code_sequence(self):
        xmlid = self._odootil_seq_xmlid
        return (
            self._odootil_seq_code,
            self.env.ref(xmlid) if xmlid else None
        )

    def odootil_seq_check_number(self):
        """Check number uniqueness for records with no company set."""
        self.ensure_one()
        # SQL constraint does not handle uniqueness when some fields
        # are NULL, so we must explicitly handle case when company_id
        # is NULL. It is the case when company_id is not required on
        # target model.
        number_fld = self._odootil_seq_field
        domain = [
            ('id', '!=', self.id),
            (number_fld, '=', self[number_fld]),
            ('company_id', '=', False)
        ]
        fields = ['id', number_fld, 'company_id']
        groupby = [number_fld, 'company_id']
        # Using sudo() because regular user might not have access to
        # all records. Searching among archived records also.
        if (not self.company_id and
                self.with_context(active_test=False).sudo().read_group(
                    domain, fields, groupby)):
            raise ValidationError(
                self._odootil_seq_company_constraint_msg)

    def odootil_seq_autoset_number(self):
        """Autoset seq number for records that do no have one yet.

        Intended to be reused in _post_init hook.
        """
        # This can happen if there are already records before
        # module was installed which could need to set `number` as
        # required field.
        # We need to set number on all records, even inactive ones, because
        # otherwise required constraint won't be set if it would be
        # triggered.
        number_fld = self._odootil_seq_field
        records = self.with_context(active_test=False).search(
            [(number_fld, '=', False)]
        )
        get_sequence_number = self.env['odootil'].get_sequence_number
        code, sequence = self._odootil_seq_get_code_sequence()
        has_company_id = hasattr(self, 'company_id')
        for record in records:
            number = get_sequence_number(
                code=code,
                sequence=sequence,
                company_id=record.company_id.id if has_company_id else None
            )
            record.write({number_fld: number})

    @api.model
    def create(self, vals):
        """Override to automatically set number value from sequence."""
        code, sequence = self._odootil_seq_get_code_sequence()
        self.env['odootil'].set_sequence_number(
            vals, self._odootil_seq_field,
            code=code,
            sequence=sequence,
            company_id=vals.get('company_id')
        )
        return super(OdootilSeq, self).create(vals)

    def name_get(self):
        """Override to use custom name pattern."""
        pattern = self._odootil_seq_name_pattern
        if pattern:
            return generate_names(
                {'pattern': pattern, 'objects': self})
        return super(OdootilSeq, self).name_get()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Override search to also search using number field value."""
        search_keys = self._odootil_seq_search_keys
        if search_keys:
            query_obj = self.name_search_multi_leaf(
                name,
                search_keys,
                args=args,
                operator=operator,
                limit=limit
            )
            return self.browse(query_obj).name_get()
        return super(OdootilSeq, self).name_search(
            name, args=args, operator=operator, limit=limit)
