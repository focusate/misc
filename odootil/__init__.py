"""Various odoo helper methods.

These methods do not require odootil model and can be run without
installing this module.
"""
from . import models
__all__ = ['models']

from odoo import api, SUPERUSER_ID


# TODO: move all methods from odootil model that do not really
# need access to Odoo models registry (this way most of functionality
# could be used without even installing this module and depending
# on it).
# Method to be run as post_init_hook for modules that depend on
# mrp_quality module.
def _enable_group_mrp_routings(cr, registry):
    """Enable group_mrp_routings option in settings."""
    # This hook is run, because if we only install quality_mrp, in
    # settings, Odoo will start throwing warnings, that
    # group_mrp_routings option was unset and proceeding with it, will
    # actually try to uninstall quality_mrp (and its dependencies). This
    # happens, because group_mrp_routings option enables multiple things
    # and by installing only quality_mrp, we are enabling it only
    # partially, which can cause issues. So we execute this to fully
    # enable that option, meaning that if quality_mrp is installed,
    # then that option must always be enabled.
    env = api.Environment(cr, SUPERUSER_ID, {})
    cfg = env['res.config.settings'].create({})
    if not cfg.group_mrp_routings:
        cfg.group_mrp_routings = True
        cfg.execute()
