"""
mkdocs ``gen-files`` hook that renders the rules list page for the site build.

The rendering logic lives in ``docs/rules_list_generator.py`` so it can be shared with the standalone
``docs/update_rules_list.py`` script that keeps the committed ``docs/rules_list.md`` in sync.
"""

import sys
from pathlib import Path

import mkdocs_gen_files

sys.path.append(str(Path(__file__).parent.parent))
from docs.rules_list_generator import generate_rules_list

with mkdocs_gen_files.open("rules_list.md", "w") as f:
    f.write(generate_rules_list())
