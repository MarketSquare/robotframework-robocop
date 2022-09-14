"""
Parsing utils
"""
from robocop.utils.disablers import DisablersFinder
from robocop.utils.file_types import FileType, FileTypeChecker
from robocop.utils.misc import (
    ROBOT_VERSION,
    AssignmentTypeDetector,
    RecommendationFinder,
    find_robot_vars,
    get_errors,
    get_section_name,
    is_suite_templated,
    issues_to_lsp_diagnostic,
    keyword_col,
    modules_from_path,
    modules_from_paths,
    modules_in_current_dir,
    normalize_robot_name,
    normalize_robot_var_name,
    parse_assignment_sign_type,
    pattern_type,
    remove_robot_vars,
    str2bool,
    token_col,
)
