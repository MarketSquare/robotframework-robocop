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

extensions = ["sphinx.ext.autodoc"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

exclude_patterns = []

html_theme = "alabaster"

html_theme_options = {
    "description": "Tool for static code analysis (linting) of Robot Framework language",
    "logo": "robocop_logo_small.png",
    "logo_name": True,
    "logo_text_align": "center",
    "show_powered_by": False,
    "github_user": "MarketSquare",
    "github_repo": "robotframework-robocop",
    "github_banner": False,
    "github_button": True,
    "show_related": False,
    "note_bg": "#FFF59C",
    "github_type": "star",
    "fixed_sidebar": True,
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["images", "static"]
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
    app.add_css_file("theme.css")


def get_checker_docs():
    """
    Load rules for dynamic docs generation
    """
    checker_docs = defaultdict(list)
    for module_name, rule in robocop.checkers.get_rules():
        module_name = module_name.title()
        checker_docs[module_name].append(
            {
                "name": rule.name,
                "id": rule.rule_id,
                "severity": rule.severity.value,
                "desc": rule.msg,
                "ext_docs": rule.docs,
                "version": rule.supported_version,
                "params": [
                    {"name": param.name, "default": param.default, "type": param.converter.__name__, "desc": param.desc}
                    for param in rule.config.values()
                ],
            }
        )
    groups_sorted_by_id = []
    for module_name in checker_docs:
        sorted_rules = sorted(checker_docs[module_name], key=lambda x: x["id"])
        group_id = int(sorted_rules[0]["id"][:2])
        groups_sorted_by_id.append((module_name, sorted_rules, group_id))
    groups_sorted_by_id = sorted(groups_sorted_by_id, key=lambda x: x[2])
    return groups_sorted_by_id


html_context = {"checker_groups": get_checker_docs()}
