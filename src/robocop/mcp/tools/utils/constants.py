"""Constants used across MCP tools modules."""

from __future__ import annotations

from robocop.embedded import EMBEDDED_EXTENSIONS
from robocop.linter.rules import RuleSeverity

# Valid Robot Framework file extensions, including files that may embed Robot code (Markdown, Python).
VALID_EXTENSIONS = frozenset((".robot", ".resource")) | EMBEDDED_EXTENSIONS

# Threshold string to severity mapping
THRESHOLD_MAP = {
    "I": RuleSeverity.INFO,
    "W": RuleSeverity.WARNING,
    "E": RuleSeverity.ERROR,
}

# Characters that indicate a glob pattern
GLOB_CHARS = frozenset("*?[]")

# Valid group_by options for batch linting
VALID_GROUP_BY = frozenset(("severity", "rule", "file"))
