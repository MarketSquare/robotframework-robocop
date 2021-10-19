# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import datetime

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import sys
from collections import defaultdict
from functools import total_ordering
from pathlib import Path

import sphinx_rtd_theme

sys.path.append(str(Path(__file__).parent.parent))
import robocop

# -- Project information -----------------------------------------------------

project = "Robocop"
copyright = f"{datetime.datetime.now().year}, Bartlomiej Hirsz, Mateusz Nojek"
author = "Bartlomiej Hirsz, Mateusz Nojek"

# The full version, including alpha/beta/rc tags
release = robocop.__version__
version = robocop.__version__

master_doc = "index"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx_rtd_theme", "sphinx.ext.autodoc"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["images"]
html_favicon = "images/robocop.ico"


def rstjinja(app, docname, source):
    """
    Render our pages as a jinja template for fancy templating goodness.
    """
    # Make sure we're outputting HTML
    if app.builder.format != "html":
        return
    src = source[0]
    rendered = app.builder.templates.render_string(src, app.config.html_context)
    source[0] = rendered


def setup(app):
    app.connect("source-read", rstjinja)


@total_ordering
class RuleDoc:
    def __init__(self, rule, group, checker):
        self.name = f"[{rule.severity.value}{rule.rule_id}] {rule.name}: {rule.desc}"
        self.params = self.get_params(rule, checker)
        self.rule_id = rule.rule_id
        self.group = group

    def __str__(self):
        return f"Group: {self.group}\nName: {self.name}\n  Params: {self.params}"

    @staticmethod
    def get_params(rule, checker):
        params = [("severity", ":class:`robocop.rules.RuleSeverity`", str(rule.severity), "")]
        for param in rule.configurable:
            default = "" if len(param) != 4 else param[3]
            params.append(
                (
                    param[0],
                    param[2].__name__,
                    rule.get_default_value(param[1], checker),
                    default,
                )
            )
        return params

    def __lt__(self, other):
        return self.rule_id < other.rule_id


def get_checker_docs():
    """
    Load checkers and rules attributes for dynamic docs generation
    :return: dict with checker groups as keys, checkers in group list as values
    """
    checker_docs = defaultdict(list)
    for checker in robocop.checkers.get_docs():
        module_name = checker.__module__.split(".")[-1].title()
        checker_instance = checker()
        for rule in checker_instance.rules.values():
            rule_doc = RuleDoc(rule, checker.__module__ + "." + checker.__name__, checker_instance)
            checker_docs[module_name].append((rule_doc.rule_id, rule_doc.name, rule_doc.params, rule_doc.group))
    groups_sorted_by_id = []
    for module_name in checker_docs:
        sorted_rules = sorted(checker_docs[module_name], key=lambda x: x[0][-2:])
        group_id = int(sorted_rules[0][0][:2])
        groups_sorted_by_id.append((module_name, sorted_rules, group_id))
    groups_sorted_by_id = sorted(groups_sorted_by_id, key=lambda x: x[2])
    return groups_sorted_by_id


html_context = {"checker_groups": get_checker_docs()}
