"""
Write or verify the committed ``docs/rules_list.md`` file.

``docs/rules_list.md`` is generated from the live rule metadata. During the site build the mkdocs
``gen-files`` plugin renders it on the fly, but a materialized copy is also committed to the repository so
that tools which read the raw sources (for example Context7, which indexes documentation for AI assistants)
get the complete, up-to-date rule reference.

Usage:

    python docs/update_rules_list.py            # regenerate and write docs/rules_list.md
    python docs/update_rules_list.py --check     # exit non-zero if the committed file is out of date
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from docs.rules_list_generator import generate_rules_list

RULES_LIST_FILE = Path(__file__).parent / "rules_list.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify docs/rules_list.md")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check whether the committed file is up to date (do not write).",
    )
    args = parser.parse_args()

    content = generate_rules_list()
    current = RULES_LIST_FILE.read_text(encoding="utf-8") if RULES_LIST_FILE.exists() else None

    if args.check:
        if current != content:
            print(
                f"{RULES_LIST_FILE} is out of date. Regenerate it with:\n\n    python docs/update_rules_list.py\n",
                file=sys.stderr,
            )
            return 1
        return 0

    if current != content:
        RULES_LIST_FILE.write_text(content, encoding="utf-8", newline="\n")
        print(f"Updated {RULES_LIST_FILE}")
    else:
        print(f"{RULES_LIST_FILE} is already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
