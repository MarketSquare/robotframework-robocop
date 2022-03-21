import datetime
import sys
from collections import defaultdict
from pathlib import Path


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

extensions = ["sphinx.ext.autodoc", "sphinx_design"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

exclude_patterns = []

html_theme = "furo"
html_title = f"Robocop {release}"
html_logo = "images/robocop_logo_small.png"
html_theme_options = {
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/MarketSquare/robotframework-robocop",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}
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
                    {
                        "name": param.name,
                        "default": param.raw_value,
                        "type": param.converter.__name__,
                        "desc": param.desc,
                    }
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
