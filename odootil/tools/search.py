"""Search related fucntion helpers."""

from odoo.osv import expression


def get_name_search_domain(
    name,
    keys,
    leaf_conditions=None,
    args=None,
        operator='ilike'):
    """Prepare domain to be used for name_search with custom keys.

    keys (path to field in object) argument is used to create
    domain leafs separated by OR operator.

    Args:
        name (str): search value.
        keys (list): list of string keys specifying left operand.
        leaf_conditions (dict): specify condition for name argument
            for specific key. key is key from keys arg and value is
            check function that takes search value as argument.
            (default: {None})
        args (list): Optional argument to append to domain after
            domain is created (default: {None})
        operator (str): operator that will be used in all domain
            leafs. (default: {'ilike'})

    Returns:
        name_search
        list

    """
    def check_key(key):
        condition = leaf_conditions.get(key)
        # Can pass if there is no condition, or condition is
        # specified.
        return not condition or condition(name)

    args = list(args or [])
    if not leaf_conditions:
        leaf_conditions = {}
    domains = [[(k, operator, name)] for k in keys if check_key(k)]
    # Convert little domains into full domain separating
    # it with OR.
    domain = expression.OR(domains)
    # Add extra args.
    return expression.AND([domain, args])
