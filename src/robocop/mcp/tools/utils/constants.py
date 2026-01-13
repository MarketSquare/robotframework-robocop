"""Constants used across MCP tools modules."""

from __future__ import annotations

from robocop.linter.rules import RuleSeverity

# Valid Robot Framework file extensions
VALID_EXTENSIONS = frozenset((".robot", ".resource"))

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

# Configuration section names for natural language config
CONFIG_SECTIONS = ("common", "lint", "format")
NESTED_CONFIG_SECTIONS = frozenset(("lint", "format"))

# Robocop configuration file names
CONFIG_NAMES = frozenset(("robocop.toml", "pyproject.toml", "robot.toml"))
