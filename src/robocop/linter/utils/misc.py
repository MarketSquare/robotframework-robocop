from __future__ import annotations

import ast
import difflib
import fnmatch
import re
import token as python_token
import tokenize
from collections import Counter, defaultdict, namedtuple
from io import StringIO
from pathlib import Path
from tokenize import generate_tokens
from typing import TYPE_CHECKING

import platformdirs
from robot.api import Token

try:
    from robot.api.parsing import Variable
except ImportError:
    from robot.parsing.model.statements import Variable

from robot.variables.search import search_variable
from robot.version import VERSION as RF_VERSION

from robocop import __version__
from robocop.linter.utils.variable_matcher import VariableMatches
from robocop.linter.utils.version_matching import Version

if TYPE_CHECKING:
    from collections.abc import Generator

    from robot.parsing.model import File, Keyword, Section, VariableSection
    from robot.parsing.model.statements import KeywordCall, Node, TestTemplate, Var

    from robocop.linter.diagnostics import Diagnostic

ROBOT_VERSION = Version(RF_VERSION)
ROBOT_WITH_LANG = Version("6.0")
ROBOCOP_RULES_URL = "https://robocop.readthedocs.io/en/{version}/rules_list.html"


ReturnClasses = namedtuple("ReturnClasses", ["return_class", "return_setting_class"])  # noqa: PYI024


def get_return_classes() -> ReturnClasses:
    """
    Import return classes depending on the Robot version and return it as mapping.

    Robot Framework change model names for [Return] and RETURN depending on the RF version. To achieve backward
    compatibility we need to define mapping.
    """
    from robot.parsing.model.statements import Return

    if ROBOT_VERSION.major < 5:
        return_class = Return  # it does not exist, but we define it for backward compatibility
        return_setting_class = Return
    elif ROBOT_VERSION.major < 7:
        from robot.api.parsing import ReturnStatement

        return_class = ReturnStatement
        return_setting_class = Return
    else:
        from robot.api.parsing import ReturnSetting

        return_class = Return
        return_setting_class = ReturnSetting
    return ReturnClasses(return_class, return_setting_class)


RETURN_CLASSES = get_return_classes()


def rf_supports_lang() -> bool:
    return ROBOT_VERSION >= ROBOT_WITH_LANG


def remove_variable_type_conversion(name: str) -> str:
    name, *_ = name.split(": ", maxsplit=1)
    return name


def normalize_robot_name(name: str, remove_prefix: str | None = None) -> str:
    name = name.replace(" ", "").replace("_", "").lower() if name else ""
    if remove_prefix:
        return name[name.startswith(remove_prefix) and len(remove_prefix) :]
    return name


def normalize_robot_var_name(name: str) -> str:
    return normalize_robot_name(name)[2:-1] if name else ""


def remove_nested_variables(var_name: str) -> str:
    for match in VariableMatches(var_name, ignore_errors=True):
        # take what surrounds it and run the check again
        return remove_nested_variables(match.before + match.after)
    return var_name.strip()


def keyword_col(node: Keyword) -> int:
    return token_col(node, Token.KEYWORD)


def token_col(node: type[Node], *token_type) -> int:
    if ROBOT_VERSION.major == 3:
        for tok_type in token_type:
            token = node.get_token(tok_type)
            if token is not None:
                break
        else:
            return 1
    else:
        token = node.get_token(*token_type)

    if token is None:
        return 1
    return token.col_offset + 1


def issues_to_lsp_diagnostic(issues: list[Diagnostic]) -> list[dict]:
    return [
        {
            "range": {
                "start": {
                    "line": max(0, issue.range.start.line - 1),
                    "character": max(0, issue.range.start.line - 1),
                },
                "end": {
                    "line": max(0, issue.range.end.line - 1),
                    "character": max(0, issue.range.end.character - 1),
                },
            },
            "severity": issue.severity.diag_severity(),
            "code": issue.rule.rule_id,
            "source": "robocop",
            "message": issue.rule.message,
            "codeDescription": {"href": f"{ROBOCOP_RULES_URL.format(version=__version__)}#{issue.rule.name}"},
        }
        for issue in issues
    ]


def str2bool(v: bool | str) -> bool:
    if isinstance(v, bool):
        return v
    return v.lower() in ("yes", "true", "1")


class AssignmentTypeDetector(ast.NodeVisitor):
    """Visitor for counting number and type of assignments"""

    def __init__(self):
        self.keyword_sign_counter = Counter()
        self.keyword_most_common = None
        self.variables_sign_counter = Counter()
        self.variables_most_common = None

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.generic_visit(node)
        if len(self.keyword_sign_counter) >= 2:
            self.keyword_most_common = self.keyword_sign_counter.most_common(1)[0][0]
        if len(self.variables_sign_counter) >= 2:
            self.variables_most_common = self.variables_sign_counter.most_common(1)[0][0]

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        if node.assign:  # if keyword returns any value
            sign = self.get_assignment_sign(node.assign[-1])
            self.keyword_sign_counter[sign] += 1

    def visit_VariableSection(self, node: VariableSection) -> VariableSection:  # noqa: N802
        for child in node.body:
            if not isinstance(child, Variable):
                continue
            var_token = child.get_token(Token.VARIABLE)
            sign = self.get_assignment_sign(var_token.value)
            self.variables_sign_counter[sign] += 1
        return node

    @staticmethod
    def get_assignment_sign(token_value: str) -> str:
        variable = search_variable(token_value, ignore_errors=True)
        return variable.after


def parse_assignment_sign_type(value: str) -> str:
    types = {
        "none": "",
        "equal_sign": "=",
        "space_and_equal_sign": " =",
        "autodetect": "autodetect",
    }
    if value not in types:
        raise ValueError(
            f"Expected one of ('none', 'equal_sign', 'space_and_equal_sign', 'autodetect') but got '{value}' instead"
        )
    return types[value]


class RecommendationFinder:
    def find_similar(self, name: str, candidates: list[str] | dict) -> str:
        norm_name = self.normalize(name)
        norm_cand = self.get_normalized_candidates(candidates)
        matches = []
        for norm in norm_name:
            matches += self.find(norm, norm_cand.keys())
        if not matches:
            return ""
        matches = self.get_original_candidates(matches, norm_cand)
        suggestion = "Did you mean:\n"
        suggestion += "\n".join(f"    {match}" for match in matches)
        return suggestion

    def find(self, name: str, candidates: list[str] | dict, max_matches: int = 5) -> list[str]:
        """Return a list of close matches to `name` from `candidates`."""
        if not name or not candidates:
            return []
        cutoff = self._calculate_cutoff(name)
        return difflib.get_close_matches(name, candidates, n=max_matches, cutoff=cutoff)

    @staticmethod
    def _calculate_cutoff(string: str, min_cutoff: float = 0.5, max_cutoff: float = 0.85, step: float = 0.03) -> float:
        """
        Calculate cutoff for difflib string matching.

        The longer the string the bigger required cutoff.
        """
        cutoff = min_cutoff + len(string) * step
        return min(cutoff, max_cutoff)

    @staticmethod
    def normalize(name: str) -> str:
        """
        Normalize name.

        Returns tuple where first element is string created from sorted words in name,
        and second element is name without `-` and `_`.
        """
        norm = re.split("[-_ ]+", name)
        return " ".join(sorted(norm)), name.replace("-", "").replace("_", "")

    @staticmethod
    def get_original_candidates(candidates: list[str] | dict, norm_candidates: defaultdict[str, list]) -> list[str]:
        """Map found normalized candidates to unique original candidates."""
        return sorted({c for cand in candidates for c in norm_candidates[cand]})

    def get_normalized_candidates(self, candidates: list[str] | dict) -> defaultdict[str, list]:
        """
        Find all possible variations of the name after normalization.

        Thanks for normalizing and sorting we can find cases like this-is, thisis, this-is1 instead of is-this.
        Normalized names form dictionary that point to original names - we're using list because several names can
        have one common normalized name.
        Different normalization methods try to imitate possible mistakes done when typing name - different order,
        missing `-` etc.
        """
        norm = defaultdict(list)
        for cand in candidates:
            for norm_cand in self.normalize(cand):
                norm[norm_cand].append(cand)
        return norm


class TestTemplateFinder(ast.NodeVisitor):
    def __init__(self):
        self.templated = False

    def visit_TestTemplate(self, node: TestTemplate) -> None:  # noqa: N802
        self.templated = bool(node.value)


def is_suite_templated(model: File) -> bool:
    finder = TestTemplateFinder()
    finder.visit(model)
    return finder.templated


def next_char_is(string: str, i: int, char: str) -> bool:
    if not i < len(string) - 1:
        return False
    return string[i + 1] == char


def remove_robot_vars(name: str) -> str:
    var_start = set("$@%&")
    brackets = 0
    open_bracket, close_bracket = "", ""
    replaced = ""
    index = 0
    while index < len(name):
        if brackets:
            if name[index] == open_bracket:
                brackets += 1
            elif name[index] == close_bracket:
                brackets -= 1
            # check if next chars are not ['key']
            if not brackets and next_char_is(name, index, "["):
                brackets += 1
                index += 1
                open_bracket, close_bracket = "[", "]"
        # it looks for $ (or other var starter) and then check if next char is { and previous is not escape \
        elif name[index] in var_start and next_char_is(name, index, "{") and not (index and name[index - 1] == "\\"):
            open_bracket = "{"
            close_bracket = "}"
            brackets += 1
            index += 1
        else:
            replaced += name[index]
        index += 1
    return replaced


def find_robot_vars(name: str) -> list[tuple[int, int]]:
    """Return list of tuples with (start, end) pos of vars in name"""
    var_start = set("$@%&")
    brackets = 0
    index = 0
    start = -1
    variables = []
    while index < len(name):
        if brackets:
            if name[index] == "{":
                brackets += 1
            elif name[index] == "}":
                brackets -= 1
                if not brackets:
                    variables.append((start, index + 1))
        # it looks for $ (or other var starter) and then check if next char is { and previous is not escape \
        elif name[index] in var_start and next_char_is(name, index, "{") and not (index and name[index - 1] == "\\"):
            brackets += 1
            start = index
            index += 1
        index += 1
    return variables


def pattern_type(value: str) -> re.Pattern:
    try:
        pattern = re.compile(value)
    except re.error as err:
        raise ValueError(f"Invalid regex pattern: {err}") from err
    return pattern


def compile_rule_pattern(rule_pattern: str) -> re.Pattern:
    return re.compile(fnmatch.translate(rule_pattern))


def get_section_name(node: Section) -> str:
    if not node.header:
        #  Lines before first section are considered to be in `*** Comments ***` section even if header name is missing
        return "*** Comments ***"
    for token in node.header.data_tokens:
        if ROBOT_VERSION.major > 3:
            if token.type in node.header.handles_types:
                return token.value
        elif "HEADER" in token.type:
            return token.value
    return ""


def get_errors(node: type[Node]) -> tuple[str, ...] | list[str]:
    if ROBOT_VERSION.major == 3:
        return [node.error] if node.error else []
    return node.errors


def find_escaped_variables(string: str) -> list[str]:
    r"""
    Return list of $escaped or \${escaped} variables from the string.

    We are tokenizing the string using Python ast modules. This allows us to find valid Python-like names and check
    if they are escaped Robot Framework variables.
    """
    variable_started = False
    variables = []
    try:
        for toknum, tokval, _, _, _ in generate_tokens(StringIO(string).readline):
            if variable_started:
                if toknum == python_token.NAME:
                    variables.append(tokval)
                variable_started = False
            if tokval == "$":
                variable_started = True
    except tokenize.TokenError:
        pass
    return variables


def get_variables_from_string(string: str) -> Generator[str, None, None]:
    """
    Tokenize string and find base variable names.

    For example 'arg1 * 3' will yield arg1, 'arg2[3] + arg3' will yield arg2 and arg3.
    """
    try:
        for toknum, tokval, _, _, _ in generate_tokens(StringIO(string).readline):
            if tokval and toknum == python_token.NAME:
                yield tokval
    except tokenize.TokenError:
        return


def get_robocop_cache_directory(ensure_exists: bool) -> Path:
    return Path(platformdirs.user_cache_dir("robocop", ensure_exists=ensure_exists))


def get_string_diff(prev_count: int, count: int) -> str:
    """Get +0, -10 string."""
    diff = count - prev_count
    prefix = "+" if diff >= 0 else ""
    return prefix + str(diff)


def get_plural_form(container: int) -> str:
    return "" if container == 1 else "s"


def is_var_scope_local(node: Var) -> bool:
    is_local = True
    for option in node.get_tokens(Token.OPTION):
        if "scope=" in option.value:
            is_local = option.value.lower() == "scope=local"
    return is_local
