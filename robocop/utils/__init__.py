"""
Parsing utils
"""
from robocop.utils.disablers import DisablersFinder
from robocop.utils.file_types import FileType, FileTypeChecker
from robocop.utils.misc import (
    modules_from_path,
    modules_from_paths,
    modules_in_current_dir,
    normalize_robot_name,
    normalize_robot_var_name,
    IS_RF4,
    DISABLED_IN_4,
    ENABLED_IN_4,
    keyword_col,
    issues_to_lsp_diagnostic,
    AssignmentTypeDetector,
    parse_assignment_sign_type,
    token_col,
    RecommendationFinder,
    is_suite_templated,
    last_non_empty_line,
    remove_robot_vars
)
