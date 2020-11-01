"""Data formatting herlpers."""
import yattag


def build_html_table(data, options=None):
    """Build div layout HTML table.

    Generated table is not converted to string, to allow building
    HTML further if needed.

    Args:
        data (list): list of tuples. Tuple is row where each item in
            tuple is row's value.
        options (dict): extra options to build table default ({None}):
            - labels (tuple): header row tuple that should consists of
                labels for columns (default: {None}).
            - ttl (tuple): yattag doc, tag, text, line objects. If not
                specified, will be created by default (default: {None}).
            - row_classes_func (callable): function to return CSS
                classes for row. Can use some kind of condition to
                determine which class is appropriate per each row (not
                    applied to labels).

    Returns:
        (doc, tag, text, line) that were used to build HTML table.
        tuple

    """
    def _build_row(*row, row_classes=None):
        kwargs = {}
        # Hack to set keyword argument only if it is Truthy.
        if row_classes:
            kwargs['klass'] = row_classes
        with tag('div', **kwargs):
            for item in row:
                line('div', item)

    def build_header(*row):
        _build_row(*row)

    def build_row(*row):
        row_classes = row_classes_func(row)
        _build_row(*row, row_classes=row_classes)

    if not options:
        options = {}
    ttl = options.get('ttl')
    # If no function is specified, it will default to dummy function
    # that returns None. Meaning no classes are used.
    row_classes_func = options.get('row_classes_func', lambda row: None)
    if ttl:
        doc, tag, text, line = ttl
    else:
        doc, tag, text, line = yattag.Doc().ttl()
    with tag('div', klass='o_odootil_div_table'):
        # Build header row if labels were specified.
        labels = options.get('labels')
        if labels:
            build_header(*labels)
        for row in data:
            build_row(*row)
    return doc, tag, text, line
