"""Various odoo helper methods.

These methods do not require odootil model and can be run without
installing this module.
"""
import os
import jinja2
import yattag

from . import models
__all__ = ['models']

from odoo.tools import convert
from odoo.tools.misc import file_open


# Import helpers.

def convert_file_realpath(cfg):
    """Import file data into odoo using file's real path.

    This is reimplementation of convert_file, except it accepts real
    path and not odoo module's relative path, and path here is
    required (original argument is pathname) and filename argument is
    not used, because it is taken from path.
    """
    cr, module, path = cfg['cr'], cfg['module'], cfg['path']
    idref = cfg.get('idref')
    mode = cfg.get('mode', 'update')
    noupdate = cfg.get('noupdate', False)
    filename = os.path.basename(path)
    ext = os.path.splitext(filename)[1].lower()
    with open(path) as f:
        if ext == '.csv':
            convert.convert_csv_import(
                cr, module, path, f.read(), idref, mode, noupdate)
        elif ext == '.sql':
            convert.convert_sql_import(cr, f)
        elif ext == '.xml':
            convert.convert_xml_import(
                cr,
                module,
                f,
                idref,
                mode,
                noupdate,
                report=cfg.get('report'))
        elif ext == '.js':
            pass  # .js files are valid but ignored here.
        else:
            raise ValueError("Can't load unknown file type %s.", filename)


# Render helpers.

def render_file_template(path, variables, encoding='utf-8'):
    """Render data from file template using specified variables.

    Jinja2 engine is used to render template, so its syntax is expected.

    Args:
        path (str): path to data template file. If path is relative
            path, it will be treated as relative path from odoo module.
        variables (dict): data to be used when rendering template.
        encoding (str): encoding to encode data before returning it. If
            set to False, will not encode it. (default: {'utf-8'})

    Returns:
        rendered data.
        str or bytes

    """
    def render_template(template):
        data = template.render(**variables)
        if encoding:
            return data.encode(encoding)
        return data

    # We assume that relative path is path from odoo module, so we
    # use file_open that is appropriate for such path.
    fopen = open if os.path.isabs(path) else file_open
    with fopen(path) as f:
        template = jinja2.Template(f.read())
        return render_template(template)


# Formatting helpers.

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
