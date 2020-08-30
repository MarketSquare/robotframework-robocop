# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import sys
from pathlib import Path
from collections import defaultdict
import sphinx_rtd_theme
sys.path.append(str(Path(__file__).parent.parent))
import robocop


# -- Project information -----------------------------------------------------

project = 'Robocop'
copyright = '2020, Bartlomiej Hirsz, Mateusz Nojek'
author = 'Bartlomiej Hirsz, Mateusz Nojek'

# The full version, including alpha/beta/rc tags
# release = robocop.version
release = "0.0.1"

master_doc = 'index'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


def rstjinja(app, docname, source):
    """
    Render our pages as a jinja template for fancy templating goodness.
    """
    # Make sure we're outputting HTML
    if app.builder.format != 'html':
        return
    src = source[0]
    rendered = app.builder.templates.render_string(
        src, app.config.html_context
    )
    source[0] = rendered


def setup(app):
    app.connect("source-read", rstjinja)


def get_checker_docs():
    """
    Load checkers and rules attributes for dynamic docs generation
    :return: dict with checker groups as keys, checkers in group list as values
    """
    checker_docs = defaultdict(list)
    for checker in robocop.checkers.get_docs():
        checker_doc = []
        for rule, rule_def in checker.rules.items():
            rule_name = f"[{rule_def[2].value}{rule}] {rule_def[0]}: {rule_def[1]}"
            rule_params = [("severity", ":class:`robocop.rules.RuleSeverity`")]
            if len(rule_def) > 3:
                rule_params.append((rule_def[3][0], str(rule_def[3][2])))
            checker_doc.append((rule_name, rule_params))
        module_name = checker.__module__.split('.')[-1].title()
        checker_docs[module_name].append((checker.__module__ + '.' + checker.__name__, checker_doc))
    return checker_docs


html_context = {
    'checker_groups': get_checker_docs()
}
