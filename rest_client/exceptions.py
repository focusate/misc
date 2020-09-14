from odoo.exceptions import ValidationError


class AuthDataError(ValidationError):
    """Exception when Authentication object data can't be used."""

    pass
