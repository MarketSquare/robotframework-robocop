"""Lengths checkers"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import VariableError
from robot.parsing.model.blocks import CommentSection, Keyword, TestCase
from robot.parsing.model.statements import (
    Arguments,
    Comment,
    Documentation,
    EmptyLine,
    KeywordCall,
    Template,
    TemplateArguments,
)
from robot.variables.search import search_variable

try:
    from robot.api.parsing import Break, Continue
except ImportError:
    Break, Continue = None, None
try:  # RF7+
    from robot.api.parsing import Var
except ImportError:
    Var = None

from robocop.linter import sonar_qube
from robocop.linter.rules import (
    RawFileChecker,
    Rule,
    RuleParam,
    RuleSeverity,
    SeverityThreshold,
    VisitorChecker,
    arguments,
)
from robocop.linter.utils.misc import (
    RETURN_CLASSES,
    find_escaped_variables,
    get_section_name,
    normalize_robot_name,
    pattern_type,
    rf_supports_type,
    split_argument_default_value,
    str2bool,
    strip_equals_from_assignment,
)

if TYPE_CHECKING:
    from robot.parsing.model import VariableSection
    from robot.parsing.model.statements import Node


class TooLongKeywordRule(Rule):
    """
    Keyword is too long.

    Avoid too long keywords for readability and maintainability.
    """

    name = "too-long-keyword"
    rule_id = "LEN01"
    message = "Keyword '{keyword_name}' is too long ({keyword_length}/{allowed_length})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="max_len", default=40, converter=int, desc="number of lines allowed in a keyword"),
        RuleParam(name="ignore_docs", default=False, converter=str2bool, show_type="bool", desc="Ignore documentation"),
    ]
    severity_threshold = SeverityThreshold("max_len", compare_method="greater", substitute_value="allowed_length")
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FOCUSED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0501",)


class TooFewCallsInKeywordRule(Rule):
    """
    Too few keyword calls in keyword.

    Consider if the custom keyword is required at all.

    Incorrect code example:

        *** Test Cases ***
        Test
            Thin Wrapper

        *** Keywords ***
        Thin Wrapper
            Other Keyword    ${arg}

    Correct code example:

        *** Test Cases ***
        Test
            Other Keyword    ${arg}

    """

    name = "too-few-calls-in-keyword"
    rule_id = "LEN02"
    message = "Keyword '{keyword_name}' has too few keywords inside ({keyword_count}/{min_allowed_count})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="min_calls", default=1, converter=int, desc="number of keyword calls required in a keyword")
    ]
    severity_threshold = SeverityThreshold("min_calls", compare_method="less", substitute_value="min_allowed_count")
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.MODULAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0502",)


class TooManyCallsInKeywordRule(Rule):
    """
    Too many keyword calls in keyword.

    Avoid too long keywords for readability and maintainability.
    """

    name = "too-many-calls-in-keyword"
    rule_id = "LEN03"
    message = "Keyword '{keyword_name}' has too many keywords inside ({keyword_count}/{max_allowed_count})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="max_calls", default=10, converter=int, desc="number of keyword calls allowed in a keyword")
    ]
    severity_threshold = SeverityThreshold("max_calls", compare_method="greater", substitute_value="max_allowed_count")
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FOCUSED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0503",)


class TooLongTestCaseRule(Rule):
    """
    Test case is too long.

    Avoid too long test cases for readability and maintainability.
    """

    name = "too-long-test-case"
    rule_id = "LEN04"
    message = "Test case '{test_name}' is too long ({test_length}/{allowed_length})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="max_len", default=20, converter=int, desc="number of lines allowed in a test case"),
        RuleParam(name="ignore_docs", default=False, converter=str2bool, show_type="bool", desc="Ignore documentation"),
        RuleParam(
            name="ignore_templated", default=False, converter=str2bool, show_type="bool", desc="Ignore templated tests"
        ),
    ]
    severity_threshold = SeverityThreshold("max_len", compare_method="greater", substitute_value="allowed_length")
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.MODULAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0504",)


class TooFewCallsInTestCaseRule(Rule):
    """
    Too few keyword calls in test cases.

    Test without keywords will fail. Add more keywords or set results using ``Fail``, ``Pass Execution`` or
    ``Skip`` keywords:

        *** Test Cases ***
        Test case
            [Tags]    smoke
            Skip    Test case draft

    """

    name = "too-few-calls-in-test-case"
    rule_id = "LEN05"
    message = "Test case '{test_name}' has too few keywords inside ({keyword_count}/{min_allowed_count})"
    severity = RuleSeverity.ERROR
    parameters = [
        RuleParam(name="min_calls", default=1, converter=int, desc="number of keyword calls required in a test case"),
        RuleParam(
            name="ignore_templated", default=False, converter=str2bool, show_type="bool", desc="Ignore templated tests"
        ),
    ]
    added_in_version = "2.4.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.MODULAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0528",)


class TooManyCallsInTestCaseRule(Rule):
    """
    Too many keyword calls in test case.

    Redesign the test and move complex logic to separate keywords to increase readability.
    """

    name = "too-many-calls-in-test-case"
    rule_id = "LEN06"
    message = "Test case '{test_name}' has too many keywords inside ({keyword_count}/{max_allowed_count})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="max_calls", default=10, converter=int, desc="number of keyword calls allowed in a test case"),
        RuleParam(
            name="ignore_templated", default=False, converter=str2bool, show_type="bool", desc="Ignore templated tests"
        ),
    ]
    severity_threshold = SeverityThreshold("max_calls", compare_method="greater", substitute_value="max_allowed_count")
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.MODULAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


class FileTooLongRule(Rule):
    """File has too many lines."""

    name = "file-too-long"
    rule_id = "LEN28"
    message = "File has too many lines ({lines_count}/{max_allowed_count})"
    severity = RuleSeverity.WARNING
    file_wide_rule = True
    parameters = [
        RuleParam(name="max_lines", default=400, converter=int, desc="number of lines allowed in a file"),
    ]
    severity_threshold = SeverityThreshold("max_lines", compare_method="greater", substitute_value="max_allowed_count")
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FOCUSED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0506",)


class TooManyArgumentsRule(Rule):
    """Keyword has too many arguments."""

    name = "too-many-arguments"
    rule_id = "LEN07"
    message = "Keyword '{keyword_name}' has too many arguments ({arguments_count}/{max_allowed_count})"
    severity = RuleSeverity.WARNING
    parameters = [RuleParam(name="max_args", default=5, converter=int, desc="number of lines allowed in a file")]
    severity_threshold = SeverityThreshold("max_args", compare_method="greater", substitute_value="max_allowed_count")
    added_in_version = "1.0.0"
    style_guide_ref = ["#arguments"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FOCUSED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0507",)


class LineTooLongRule(Rule):
    r"""
    The line is too long.

    Comments with disabler directives (such as ``# robocop: off``) are ignored. Lines that contain URLs are also
    ignored.

    It is possible to ignore lines that match the regex pattern. Configure it using the following option:

        robocop check --configure line-too-long.ignore_pattern=pattern

    """

    name = "line-too-long"
    rule_id = "LEN08"
    message = "Line is too long ({line_length}/{allowed_length})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="line_length", default=120, converter=int, desc="number of characters allowed in line"),
        RuleParam(
            name="ignore_pattern",
            default=None,
            converter=pattern_type,
            show_type="regex",
            desc="ignore lines that contain configured pattern",
        ),
    ]
    severity_threshold = SeverityThreshold("line_length", substitute_value="allowed_length")
    added_in_version = "1.0.0"
    style_guide_ref = ["#line-length"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0508",)


class EmptySectionRule(Rule):
    """Section is empty."""

    name = "empty-section"
    rule_id = "LEN09"
    message = "Section '{section_name}' is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0509",)


class NumberOfReturnedValuesRule(Rule):
    """Too many return values."""

    name = "number-of-returned-values"
    rule_id = "LEN10"
    message = "Too many return values ({return_count}/{max_allowed_count})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="max_returns", default=4, converter=int, desc="allowed number of returned values from a keyword")
    ]
    severity_threshold = SeverityThreshold(
        "max_returns", compare_method="greater", substitute_value="max_allowed_count"
    )
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FOCUSED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0510",)


class EmptyMetadataRule(Rule):
    """
    Metadata settings does not have any value set.

    Incorrect code example:

        *** Settings ***
        Metadata

    Correct code example:

        *** Settings ***
        Metadata    Platform    ${PLATFORM}

    """

    name = "empty-metadata"
    rule_id = "LEN11"
    message = "Metadata settings does not have any value set"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0511",)


class EmptyDocumentationRule(Rule):
    """Documentation is empty."""

    name = "empty-documentation"
    rule_id = "LEN12"
    message = "Documentation of {block_name} is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0512",)


class EmptyForceTagsRule(Rule):  # TODO: Rename/deprecate and replace with Test Tags
    """Force Tags are empty."""

    name = "empty-force-tags"
    rule_id = "LEN13"
    message = "Force Tags are empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"  # TODO: check for new settings, such as Keyword Tags
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0513",)


class EmptyDefaultTagsRule(Rule):
    """Default Tags are empty."""

    name = "empty-default-tags"
    rule_id = "LEN14"
    message = "Default Tags are empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0514",)


class EmptyVariablesImport(Rule):
    """Import variables path is empty."""

    name = "empty-variables-import"
    rule_id = "LEN15"
    message = "Import variables path is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0515",)


class EmptyResourceImport(Rule):
    """Import resources path is empty."""

    name = "empty-resource-import"
    rule_id = "LEN16"
    message = "Import resource path is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0516",)


class EmptyLibraryImport(Rule):
    """Import library path is empty."""

    name = "empty-library-import"
    rule_id = "LEN17"
    message = "Import library path is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0517",)


class EmptySetupRule(Rule):
    """Empty setup."""

    name = "empty-setup"
    rule_id = "LEN18"
    message = "Setup of {block_name} does not have any keywords"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0518",)


class EmptySuiteSetupRule(Rule):
    """Empty Suite Setup."""

    name = "empty-suite-setup"
    rule_id = "LEN19"
    message = "Suite Setup does not have any keywords"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0519",)


class EmptyTestSetupRule(Rule):
    """Empty Test Setup."""

    name = "empty-test-setup"
    rule_id = "LEN20"
    message = "Test Setup does not have any keywords"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0520",)


class EmptyTeardownRule(Rule):
    """Empty Teardown."""

    name = "empty-teardown"
    rule_id = "LEN21"
    message = "Teardown of {block_name} does not have any keywords"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0521",)


class EmptySuiteTeardownRule(Rule):
    """Empty Suite Teardown."""

    name = "empty-suite-teardown"
    rule_id = "LEN22"
    message = "Suite Teardown does not have any keywords"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0522",)


class EmptyTestTeardownRule(Rule):
    """Empty Test Teardown."""

    name = "empty-test-teardown"
    rule_id = "LEN23"
    message = "Test Teardown does not have any keywords"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0523",)


class EmptyTimeoutRule(Rule):
    """Empty Timeout."""

    name = "empty-timeout"
    rule_id = "LEN24"
    message = "Timeout of {block_name} is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0524",)


class EmptyTestTimeoutRule(Rule):
    """Empty Test Timeout."""

    name = "empty-test-timeout"
    rule_id = "LEN25"
    message = "Test Timeout is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0525",)


class EmptyArgumentsRule(Rule):
    """Empty ``[Arguments]`` setting."""

    name = "empty-arguments"
    rule_id = "LEN26"
    message = "Arguments of {block_name} are empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0526",)


class TooManyTestCasesRule(Rule):
    """Too many test cases."""

    name = "too-many-test-cases"
    rule_id = "LEN27"
    message = "Too many test cases ({test_count}/{max_allowed_count})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="max_testcases", default=50, converter=int, desc="number of test cases allowed in a suite"),
        RuleParam(
            name="max_templated_testcases",
            default=100,
            converter=int,
            desc="number of test cases allowed in a templated suite",
        ),
    ]
    severity_threshold = SeverityThreshold(
        "max_testcases or max_templated_testcases", substitute_value="max_allowed_count"
    )
    added_in_version = "1.10.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.MODULAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0527",)


class EmptyTestTemplateRule(Rule):
    """
    Test Template is empty.

    ``Test Template`` sets the template to all tests in a suite. Empty value is considered an error
    because it leads the users to wrong impression on how the suite operates.
    Without value, the setting is ignored and the tests are not templated.
    """

    name = "empty-test-template"
    rule_id = "LEN29"
    message = "Test Template is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "3.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class EmptyTemplateRule(Rule):
    """
    ``[Template]`` is empty.

    The ``[Template]`` setting overrides the possible template set in the Setting section, and an empty value for
    ``[Template]`` means that the test has no template even when Test Template is used.

    If it is intended behavior, use a more explicit `` NONE `` value to indicate that you want to overwrite suite
    Test Template:

        *** Settings ***
        Test Template    Template Keyword

        *** Test Cases ***
        Templated test
            argument

        Not templated test
            [Template]    NONE

    """

    name = "empty-template"
    rule_id = "LEN30"
    message = "Template of {block_name} is empty. To overwrite suite Test Template use more explicit [Template]  NONE"
    severity = RuleSeverity.WARNING
    added_in_version = "3.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0530",)


class EmptyKeywordTagsRule(Rule):
    """Keyword Tags are empty."""

    name = "empty-keyword-tags"
    rule_id = "LEN31"
    message = "Keyword Tags are empty"
    severity = RuleSeverity.WARNING
    version = ">=6"
    added_in_version = "3.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0531",)


class TooLongVariableNameRule(Rule):
    """
    Variable name is too long.

    Avoid too long variable names for readability and maintainability.
    """

    name = "too-long-variable-name"
    rule_id = "LEN32"
    message = "Variable name '{variable_name}' is too long ({variable_name_length}/{allowed_length})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="max_len", default=40, converter=int, desc="allowed length of a variable name"),
    ]
    severity_threshold = SeverityThreshold("max_len", compare_method="greater", substitute_value="allowed_length")
    added_in_version = "6.7.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FOCUSED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


def is_data_statement(node) -> bool:
    return not isinstance(node, (EmptyLine, Comment))


def is_not_standalone_comment(node):
    return isinstance(node, Comment) and node.tokens[0].type == Token.SEPARATOR


def check_node_length(node, ignore_docs):
    last_node = node
    for child in node.body[::-1]:
        if is_data_statement(child) or is_not_standalone_comment(child):
            last_node = child
            break
    if ignore_docs:
        return (last_node.end_lineno - node.lineno - get_documentation_length(node)), last_node.end_lineno
    return (last_node.end_lineno - node.lineno), last_node.end_lineno


def get_documentation_length(node):
    doc_len = 0
    for child in node.body:
        if isinstance(child, Documentation):
            doc_len += child.end_lineno - child.lineno + 1
    return doc_len


@dataclass
class CachedVariable:
    name: str
    node: Node
    end_col: int


class LengthChecker(VisitorChecker):
    """
    Checker for max and min length of keyword or test case. It analyses number of lines and also number of
    keyword calls (as you can have just few keywords but very long ones or vice versa).
    """

    too_few_calls_in_keyword: TooFewCallsInKeywordRule
    too_few_calls_in_test_case: TooFewCallsInTestCaseRule
    too_many_calls_in_keyword: TooManyCallsInKeywordRule
    too_many_calls_in_test_case: TooManyCallsInTestCaseRule
    too_long_keyword: TooLongKeywordRule
    too_long_test_case: TooLongTestCaseRule
    file_too_long: FileTooLongRule
    too_many_arguments: TooManyArgumentsRule

    def __init__(self):
        self.keyword_call_alike = tuple(
            klass
            for klass in (
                KeywordCall,
                TemplateArguments,
                RETURN_CLASSES.return_class,
                RETURN_CLASSES.return_setting_class,
                Break,
                Continue,
                Var,
            )
            if klass
        )
        super().__init__()

    def visit_File(self, node) -> None:  # noqa: N802
        if node.end_lineno > self.file_too_long.max_lines:
            self.report(
                self.file_too_long,
                lines_count=node.end_lineno,
                max_allowed_count=self.file_too_long.max_lines,
                node=node,
                lineno=node.end_lineno,
                end_col=node.end_col_offset,
                sev_threshold_value=node.end_lineno,
            )
        super().visit_File(node)

    def visit_Keyword(self, node) -> None:  # noqa: N802
        if node.name.lstrip().startswith("#"):
            return
        for child in node.body:
            if isinstance(child, Arguments):
                args_number = len(child.values)
                if args_number > self.too_many_arguments.max_args:
                    name_token = child.data_tokens[0]
                    self.report(
                        self.too_many_arguments,
                        keyword_name=node.name,
                        arguments_count=args_number,
                        max_allowed_count=self.too_many_arguments.max_args,
                        node=name_token,
                        end_lineno=child.end_lineno,
                        end_col=child.end_col_offset,
                        extended_disablers=(node.lineno, node.end_lineno),
                        sev_threshold_value=args_number,
                    )
                break
        length, node_end_line = check_node_length(node, ignore_docs=self.too_long_keyword.ignore_docs)
        if length > self.too_long_keyword.max_len:
            self.report(
                self.too_long_keyword,
                keyword_name=node.name,
                keyword_length=length,
                allowed_length=self.too_long_keyword.max_len,
                node=node,
                end_col=node.col_offset + len(node.name) + 1,
                extended_disablers=(node.lineno, node_end_line),
                sev_threshold_value=length,
            )
            return
        key_calls = self.count_keyword_calls(node)
        if key_calls < self.too_few_calls_in_keyword.min_calls:
            self.report(
                self.too_few_calls_in_keyword,
                keyword_name=node.name,
                keyword_count=key_calls,
                min_allowed_count=self.too_few_calls_in_keyword.min_calls,
                node=node,
                end_col=node.col_offset + len(node.name) + 1,
                extended_disablers=(node.lineno, node.end_lineno),
                sev_threshold_value=key_calls,
            )
        elif key_calls > self.too_many_calls_in_keyword.max_calls:
            self.report(
                self.too_many_calls_in_keyword,
                keyword_name=node.name,
                keyword_count=key_calls,
                max_allowed_count=self.too_many_calls_in_keyword.max_calls,
                node=node,
                end_col=node.col_offset + len(node.name) + 1,
                extended_disablers=(node.lineno, node.end_lineno),
                sev_threshold_value=key_calls,
            )

    def test_is_templated(self, node):
        if self.templated_suite:
            return True
        if not node.body:
            return False
        return any(isinstance(statement, Template) for statement in node.body)

    def visit_TestCase(self, node) -> None:  # noqa: N802
        if self.too_long_test_case.ignore_templated and self.test_is_templated(node):
            return
        length, node_end_line = check_node_length(node, ignore_docs=self.too_long_test_case.ignore_docs)
        if length > self.too_long_test_case.max_len:
            self.report(
                self.too_long_test_case,
                test_name=node.name,
                test_length=length,
                allowed_length=self.too_long_test_case.max_len,
                node=node,
                end_col=node.col_offset + len(node.name) + 1,
                extended_disablers=(node.lineno, node_end_line),
                sev_threshold_value=length,
            )
        test_is_templated = self.test_is_templated(node)
        skip_too_many = test_is_templated and self.too_many_calls_in_test_case.ignore_templated
        skip_too_few = test_is_templated and self.too_few_calls_in_test_case.ignore_templated
        if skip_too_few and skip_too_many:
            return
        key_calls = self.count_keyword_calls(node)  # TODO: could be handled inside rule, at least reporting
        if not skip_too_many and (key_calls > self.too_many_calls_in_test_case.max_calls):
            self.report(
                self.too_many_calls_in_test_case,
                test_name=node.name,
                keyword_count=key_calls,
                max_allowed_count=self.too_many_calls_in_test_case.max_calls,
                node=node,
                sev_threshold_value=key_calls,
                extended_disablers=(node.lineno, node.end_lineno),
                end_col=node.col_offset + len(node.name) + 1,
            )
        elif not skip_too_few and (key_calls < self.too_few_calls_in_test_case.min_calls):
            self.report(
                self.too_few_calls_in_test_case,
                test_name=node.name,
                keyword_count=key_calls,
                min_allowed_count=self.too_few_calls_in_test_case.min_calls,
                node=node,
                sev_threshold_value=key_calls,
                extended_disablers=(node.lineno, node.end_lineno),
                end_col=node.col_offset + len(node.name) + 1,
            )

    def count_keyword_calls(self, node):
        if isinstance(node, self.keyword_call_alike):
            return 1
        if not hasattr(node, "body"):
            return 0
        calls = sum(self.count_keyword_calls(child) for child in node.body)
        while node and getattr(node, "orelse", None):
            node = node.orelse
            calls += sum(self.count_keyword_calls(child) for child in node.body)
        while node and getattr(node, "next", None):
            node = node.next
            calls += sum(self.count_keyword_calls(child) for child in node.body)
        return calls


class VariableNameLengthChecker(VisitorChecker):
    """Checker for max length variable names."""

    too_long_variable_name: TooLongVariableNameRule

    set_variable_keywords = {
        "setlocalvariable",
        "settestvariable",
        "settaskvariable",
        "setsuitevariable",
        "setglobalvariable",
    }

    def __init__(self) -> None:
        super().__init__()
        self.variables: dict[str, tuple] = {}
        self.var_identifiers = "$@&"

    def visit_Node(self, node) -> None:  # noqa: N802
        if not node.errors:
            self.generic_visit(node)

    def new_variable_scope(self, node: Keyword | TestCase | VariableSection):
        """Handle new scope by resetting list of known variables."""
        self.variables.clear()
        if isinstance(node, Keyword):
            self.parse_embedded_arguments(node.header.get_token(Token.KEYWORD_NAME))
        self.generic_visit(node)
        self.check_variable_names_and_report()

    visit_TestCase = visit_VariableSection = visit_Keyword = new_variable_scope  # noqa: N815

    def parse_embedded_arguments(self, name_token) -> None:
        """Store embedded arguments from keyword name. Ignore embedded variables patterns (${var:pattern})."""
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    self.add_variable_to_scope(token, has_pattern=True)
        except VariableError:
            pass

    def add_variable_to_scope(self, node, var_name=None, has_pattern=False):
        """
        Determine name of variable by stripping item accessors and type conversions
        and add it to known variables if not already present.
        """
        end_col_offset = 1
        if getattr(node, "errors", None) or getattr(node, "error", None):
            return
        if not var_name:
            var_name = node.name if hasattr(node, "name") else node.value
        # Escaped variable name handling : \${var}
        # Using robot.utils.unescape(var_name) does not only unescape start of name
        escaped_var, var_name = var_name.startswith("\\"), var_name.lstrip("\\")
        if escaped_var:
            end_col_offset += 1  # leading backslash
        # Strip all item and possible type conversions : ${list}[0] , ${var: int}
        try:
            search = search_variable(var_name, parse_type=True) if rf_supports_type() else search_variable(var_name)  # pylint: disable=unexpected-keyword-arg
        except VariableError:  # Incomplete data, e.g. `${arg`
            return
        # Handle var name without brackets passed to Set Local/Global/Suite/Test Variable : $var
        # And escaped sytnax containing unescaped variables $var_${var2}
        if search.base and not find_escaped_variables(var_name):
            name = search.base
            # The reason for moving this here is the search_variable("$var_@{var2}[0]_something").items is ['0'] :
            # Dynamic variable names are insane
            for i in search.items:
                end_col_offset -= len(i) + 2  # highlight variable only, not item accessors
        else:
            name = search.string.lstrip(self.var_identifiers)
        # Item assignment using extended variable syntax : ${dict.key}
        # dynamic variable name with extended syntax like ${var_${var2.key}} :
        if not any(i in name for i in self.var_identifiers):
            name, *_ = name.split(".", maxsplit=1)  # re.split(r"(?<!\\)\.", name, maxsplit=1)  # unescaped dots only
        # Strip pattern from variable name
        if has_pattern:
            name, *_ = name.split(":", maxsplit=1)  # re.split(r"(?<!\\):", name, 1)  # unescaped colon only
        # Finally cache variable in current scope for checking, if not already present
        if (norm_name := normalize_robot_name(name)) not in self.variables:
            if len(var_name) + end_col_offset <= 0:
                return  # sanity check
            self.variables[norm_name] = CachedVariable(name, node, len(var_name) + end_col_offset)

    def check_variable_names_and_report(self):
        for var in self.variables.values():
            if (length := len(var.name)) > self.too_long_variable_name.max_len:
                self.report(
                    self.too_long_variable_name,
                    variable_name=var.name,
                    variable_name_length=length,
                    allowed_length=self.too_long_variable_name.max_len,
                    node=var.node,
                    end_col=var.node.col_offset + var.end_col,
                    sev_threshold_value=length,
                )

    visit_Variable = add_variable_to_scope  # noqa: N815

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        if not node.keyword:
            return
        for variable in node.get_tokens(Token.ASSIGN):
            self.add_variable_to_scope(variable, strip_equals_from_assignment(variable.value))
        if normalize_robot_name(node.keyword) in self.set_variable_keywords:  # Only check args of 'Set ... Variable'
            argument = node.get_token(Token.ARGUMENT)
            if argument.value.startswith(tuple(self.var_identifiers + "\\")):  # Otherwise this is invalid RF syntax
                self.add_variable_to_scope(argument)

    def visit_Var(self, node):  # noqa: N802
        if variable := node.get_token(Token.VARIABLE):
            self.add_variable_to_scope(variable, strip_equals_from_assignment(variable.value))

    def visit_Arguments(self, node):  # noqa: N802
        for argument in node.get_tokens(Token.ARGUMENT):
            name, _ = split_argument_default_value(argument.value)
            self.add_variable_to_scope(argument, name)

    def visit_For(self, node):  # noqa: N802
        if node.header.errors:
            return
        for variable in node.header.get_tokens(Token.VARIABLE):
            self.add_variable_to_scope(variable)
        self.generic_visit(node)  # continue to nested loops

    def visit_Try(self, node):  # noqa: N802
        if (node.type is Token.EXCEPT) and (variable := node.header.get_token(Token.VARIABLE)):
            self.add_variable_to_scope(variable)
        self.generic_visit(node)  # continue to all branches


class LineLengthChecker(RawFileChecker):
    """Checker for the maximum length of a line."""

    line_too_long: LineTooLongRule

    def check_line(self, line, lineno) -> None:
        line = line.rstrip().expandtabs(4)
        if len(line) <= self.line_too_long.line_length:
            return
        # the line is potentially too long, so we need to check if it can be false positive
        if self.line_is_ignored(line):
            return
        if self.url_in_line(line):
            return
        if self.line_too_long.ignore_pattern and self.line_too_long.ignore_pattern.search(line):
            return
        line = self.strip_disablers(line)
        if len(line) > self.line_too_long.line_length:
            self.report(
                self.line_too_long,
                line_length=len(line),
                allowed_length=self.line_too_long.line_length,
                lineno=lineno,
                col=self.line_too_long.line_length,
                end_col=len(line) + 1,
                sev_threshold_value=len(line),
            )

    @staticmethod
    def strip_disablers(line: str) -> str:
        """Strip whole comments if it contains disabler."""
        if "#" not in line:
            return line
        if "noqa" in line or "robocop:" in line or "fmt: " in line:
            return line.split("# ", 1)[0].rstrip()
        return line

    def url_in_line(self, line: str) -> bool:
        """Check if a line contains URL starting before the maximum line length."""
        return 0 < line.find("://") < self.line_too_long.line_length

    def line_is_ignored(self, line: str) -> bool:
        return self.line_too_long.ignore_pattern and self.line_too_long.ignore_pattern.search(line)


class EmptySectionChecker(VisitorChecker):
    """Checker for detecting empty sections."""

    empty_section: EmptySectionRule

    def check_if_empty(self, node) -> None:
        if not node.header:
            return
        anything_but = EmptyLine if isinstance(node, CommentSection) else (Comment, EmptyLine)
        if all(isinstance(child, anything_but) for child in node.body):
            self.report(
                self.empty_section,
                section_name=get_section_name(node),
                node=node,
                col=node.col_offset + 1,
                end_col=node.header.end_col_offset,
            )

    def visit_Section(self, node) -> None:  # noqa: N802
        self.check_if_empty(node)


class NumberOfReturnedArgsChecker(VisitorChecker):
    """Checker for number of returned values from a keyword."""

    number_of_returned_values: NumberOfReturnedValuesRule

    def visit_Return(self, node) -> None:  # noqa: N802
        self.check_node_returns(len(node.values), node)

    visit_ReturnStatement = visit_ReturnSetting = visit_Return  # noqa: N815

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        if not node.keyword:
            return

        normalized_name = normalize_robot_name(node.keyword, remove_prefix="builtin.")
        if normalized_name == "returnfromkeyword":
            self.check_node_returns(len(node.args), node)
        elif normalized_name == "returnfromkeywordif":
            self.check_node_returns(len(node.args) - 1, node)

    def check_node_returns(self, return_count, node) -> None:
        if return_count > self.number_of_returned_values.max_returns:
            self.report(
                self.number_of_returned_values,
                return_count=return_count,
                max_allowed_count=self.number_of_returned_values.max_returns,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.data_tokens[0].end_col_offset + 1,
                sev_threshold_value=return_count,
            )


class EmptySettingsChecker(VisitorChecker):
    """Checker for detecting empty settings."""

    empty_metadata: EmptyMetadataRule
    empty_documentation: EmptyDocumentationRule
    empty_force_tags: EmptyForceTagsRule
    empty_default_tags: EmptyDefaultTagsRule
    empty_variables_import: EmptyVariablesImport
    empty_resource_import: EmptyResourceImport
    empty_library_import: EmptyLibraryImport
    empty_setup: EmptySetupRule
    empty_suite_setup: EmptySuiteSetupRule
    empty_test_setup: EmptyTestSetupRule
    empty_teardown: EmptyTeardownRule
    empty_suite_teardown: EmptySuiteTeardownRule
    empty_test_teardown: EmptyTestTeardownRule
    empty_timeout: EmptyTimeoutRule
    empty_test_timeout: EmptyTestTimeoutRule
    empty_template: EmptyTemplateRule
    empty_test_template: EmptyTestTemplateRule
    empty_arguments: EmptyArgumentsRule
    empty_keyword_tags: EmptyKeywordTagsRule

    def __init__(self):
        self.parent_node_name = ""
        super().__init__()

    def visit_SettingSection(self, node) -> None:  # noqa: N802
        self.parent_node_name = "Test Suite"
        self.generic_visit(node)

    def visit_TestCaseName(self, node) -> None:  # noqa: N802
        if node.name:
            self.parent_node_name = f"'{node.name}' Test Case"
        else:
            self.parent_node_name = ""
        self.generic_visit(node)

    def visit_Keyword(self, node) -> None:  # noqa: N802
        if node.name:
            self.parent_node_name = f"'{node.name}' Keyword"
        else:
            self.parent_node_name = ""
        self.generic_visit(node)

    def visit_Metadata(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.empty_metadata, node=node, col=node.col_offset + 1)

    def visit_Documentation(self, node) -> None:  # noqa: N802
        if not node.value:
            self.report(
                self.empty_documentation,
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_ForceTags(self, node) -> None:  # noqa: N802
        if not node.values:
            self.report(self.empty_force_tags, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_DefaultTags(self, node) -> None:  # noqa: N802
        if not node.values:
            self.report(self.empty_default_tags, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_KeywordTags(self, node) -> None:  # noqa: N802
        if not node.values:
            self.report(self.empty_keyword_tags, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_VariablesImport(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.empty_variables_import, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_ResourceImport(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.empty_resource_import, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_LibraryImport(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.empty_library_import, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_Setup(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(
                self.empty_setup,
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_SuiteSetup(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.empty_suite_setup, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_TestSetup(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.empty_test_setup, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_Teardown(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(
                self.empty_teardown,
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_SuiteTeardown(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.empty_suite_teardown, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_TestTeardown(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.empty_test_teardown, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_TestTemplate(self, node) -> None:  # noqa: N802
        if not node.value:
            self.report(self.empty_test_template, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_Template(self, node) -> None:  # noqa: N802
        if len(node.data_tokens) < 2:
            self.report(
                self.empty_template,
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_Timeout(self, node) -> None:  # noqa: N802
        if not node.value:
            self.report(
                self.empty_timeout,
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_TestTimeout(self, node) -> None:  # noqa: N802
        if not node.value:
            self.report(self.empty_test_timeout, node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_Arguments(self, node) -> None:  # noqa: N802
        if not node.values:
            self.report(
                self.empty_arguments,
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )


class TestCaseNumberChecker(VisitorChecker):  # TODO: good example of checker that could be merged
    """Checker for counting number of test cases depending on suite type"""

    too_many_test_cases: TooManyTestCasesRule

    def visit_TestCaseSection(self, node) -> None:  # noqa: N802
        max_testcases = (
            self.too_many_test_cases.max_templated_testcases
            if self.templated_suite
            else self.too_many_test_cases.max_testcases
        )
        discovered_testcases = sum(isinstance(child, TestCase) for child in node.body)
        if discovered_testcases > max_testcases:
            self.report(
                self.too_many_test_cases,
                test_count=discovered_testcases,
                max_allowed_count=max_testcases,
                node=node,
                end_col=node.header.end_col_offset,
                sev_threshold_value=discovered_testcases,
            )


class TooManyArgumentsInLineChecker(VisitorChecker):
    arguments_per_line: arguments.ArgumentsPerLineRule

    def visit_Arguments(self, node) -> None:  # noqa: N802
        any_cont_token = node.get_token(Token.CONTINUATION)
        if not any_cont_token:  # only one line, ignoring
            return
        max_args = self.arguments_per_line.max_args
        for line in node.lines:
            args_count = sum(1 for token in line if token.type == Token.ARGUMENT)
            if args_count > max_args:
                data_token = self.first_non_sep(line)
                last_token = line[-1]
                if data_token:
                    self.report(
                        self.arguments_per_line,
                        node=data_token,
                        col=data_token.col_offset + 1,
                        end_col=last_token.end_col_offset,
                        arguments_count=args_count,
                        max_arguments_count=max_args,
                    )

    @staticmethod
    def first_non_sep(line: list[Token]) -> Token | None:
        for token in line:
            if token.type != Token.SEPARATOR:
                return token
        return None
