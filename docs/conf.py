import datetime
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

extensions = ["sphinx_rtd_theme", "sphinx.ext.autodoc"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

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
    def __init__(self, rule):
        self.name = f"[{rule.severity.value}{rule.rule_id}] {rule.name}: {rule.desc}"
        self.params = self.get_params(rule)
        self.rule_id = rule.rule_id

    def __str__(self):
        return f"Group: {self.group}\nName: {self.name}\n  Params: {self.params}"

    @staticmethod
    def get_params(rule):
        params = []
        for param in rule.config.values():
            params.append((
                param.name,
                param.converter.__name__,
                param.value,
                param.desc
            ))
        return params

    def __lt__(self, other):
        return self.rule_id < other.rule_id


def get_checker_docs():
    """
    Load rules for dynamic docs generation
    """
    checker_docs = defaultdict(list)
    for module_name, rule in robocop.checkers.get_docs():
        module_name = module_name.split(".")[-1].title()
        rule_doc = RuleDoc(rule)
        checker_docs[module_name].append((rule_doc.rule_id, rule_doc.name, rule_doc.params))
    groups_sorted_by_id = []
    for module_name in checker_docs:
        sorted_rules = sorted(checker_docs[module_name], key=lambda x: x[0][-2:])
        group_id = int(sorted_rules[0][0][:2])
        groups_sorted_by_id.append((module_name, sorted_rules, group_id))
    groups_sorted_by_id = sorted(groups_sorted_by_id, key=lambda x: x[2])
    return groups_sorted_by_id


html_context = {"checker_groups": get_checker_docs()}
