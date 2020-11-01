from contextlib import contextmanager

from odoo import registry
from odoo import api


@contextmanager
def get_environment(self):
    """Return new env, transaction is committed on closing env."""
    Registry = registry(self.cr.dbname)
    with Registry.cursor() as cr:
        yield api.Environment(cr, self.uid, self.context)
        cr.commit()


# Attach new env creation helper to Environment class.
api.Environment.get_environment = get_environment
