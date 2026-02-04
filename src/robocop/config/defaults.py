DEFAULT_INCLUDE: tuple[str, ...] = ("*.robot", "*.resource")
DEFAULT_EXCLUDE: tuple[str, ...] = (".direnv", ".eggs", ".git", ".svn", ".hg", ".nox", ".tox", ".venv", "venv", "dist")
DEFAULT_ISSUE_FORMAT = "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"

SKIP_OPTIONS = frozenset(
    {
        "skip_documentation",
        "skip_return_values",
        "skip_keyword_call",
        "skip_keyword_call_pattern",
        "skip_settings",
        "skip_arguments",
        "skip_setup",
        "skip_teardown",
        "skip_timeout",
        "skip_template",
        "skip_return_statement",
        "skip_tags",
        "skip_comments",
        "skip_block_comments",
        "skip_sections",
    }
)

# common

VERBOSE = False
SILENT = False

# cache

CACHE_DIR_NAME = ".robocop_cache"
CACHE_FILE_NAME = "cache.msgpack"

# reports cache

ROBOCOP_CACHE_FILE = ".robocop_cache"

# linter

PERSISTENT = False
COMPARE = False
EXIT_ZERO = False
FIX = False
UNSAFE_FIXES = False
FIX_DIFF = False
LINTER_RETURN_RESULT = False

# formatter

FORCE_ORDER = False
ALLOW_DISABLED = False  # used when importing formatters, set to True when listing available ones
OVERWRITE = None
DIFF = False
COLOR = True
CHECK = False
RERUNS = 0
START_LINE = None
END_LINE = None
FORMATTER_RETURN_RESULT = False  # for cli entrypoint, which raises SystemExit by default
