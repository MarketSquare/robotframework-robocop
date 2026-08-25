"""Lengths checkers"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from robot.api import Token
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

try:
    from robot.api.parsing import Break, Continue
except ImportError:
    Break, Continue = None, None
try:  # RF7+
    from robot.api.parsing import Var
except ImportError:
    Var = None

from robocop.linter import sonar_qube
from robocop.linter.fix import FixAvailability, remove_empty_setting_fix, remove_lines_fix
from robocop.linter.rules import (
    FixableRule,
    Rule,
    RuleParam,
    RuleSeverity,
    SeverityThreshold,
)
from robocop.linter.utils.misc import (
    RETURN_CLASSES,
    get_section_name,
    pattern_type,
    str2bool,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from robot.parsing import File
    from robot.parsing.model.blocks import Section
    from robot.parsing.model.statements import Node, Statement

    from robocop.linter.diagnostics import Diagnostic
    from robocop.linter.fix import Fix


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
    fix_suggestion = "Split the keyword into smaller, focused keywords."

    def check(self, node: Keyword) -> bool:
        """Report the rule and return whether the keyword exceeds the allowed length."""
        length, node_end_line = check_node_length(node, ignore_docs=self.ignore_docs)
        if length <= self.max_len:
            return False
        self.report(
            keyword_name=node.name,
            keyword_length=length,
            allowed_length=self.max_len,
            node=node,
            end_col=node.col_offset + len(node.name) + 1,
            extended_disablers=(node.lineno, node_end_line),
            sev_threshold_value=length,
        )
        return True


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

    def check(self, node: Keyword, keyword_count: int) -> bool:
        """Report the rule and return whether the keyword has too few keyword calls."""
        if keyword_count >= self.min_calls:
            return False
        self.report(
            keyword_name=node.name,
            keyword_count=keyword_count,
            min_allowed_count=self.min_calls,
            node=node,
            end_col=node.col_offset + len(node.name) + 1,
            extended_disablers=(node.lineno, node.end_lineno),
            sev_threshold_value=keyword_count,
        )
        return True


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

    def check(self, node: Keyword, keyword_count: int) -> bool:
        """Report the rule and return whether the keyword has too many keyword calls."""
        if keyword_count <= self.max_calls:
            return False
        self.report(
            keyword_name=node.name,
            keyword_count=keyword_count,
            max_allowed_count=self.max_calls,
            node=node,
            end_col=node.col_offset + len(node.name) + 1,
            extended_disablers=(node.lineno, node.end_lineno),
            sev_threshold_value=keyword_count,
        )
        return True


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

    def check(self, node: TestCase) -> None:
        length, node_end_line = check_node_length(node, ignore_docs=self.ignore_docs)
        if length <= self.max_len:
            return
        self.report(
            test_name=node.name,
            test_length=length,
            allowed_length=self.max_len,
            node=node,
            end_col=node.col_offset + len(node.name) + 1,
            extended_disablers=(node.lineno, node_end_line),
            sev_threshold_value=length,
        )


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

    def check(self, node: TestCase, keyword_count: int) -> bool:
        """Report the rule and return whether the test case has too few keyword calls."""
        if keyword_count >= self.min_calls:
            return False
        self.report(
            test_name=node.name,
            keyword_count=keyword_count,
            min_allowed_count=self.min_calls,
            node=node,
            sev_threshold_value=keyword_count,
            extended_disablers=(node.lineno, node.end_lineno),
            end_col=node.col_offset + len(node.name) + 1,
        )
        return True


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

    def check(self, node: TestCase, keyword_count: int) -> bool:
        """Report the rule and return whether the test case has too many keyword calls."""
        if keyword_count <= self.max_calls:
            return False
        self.report(
            test_name=node.name,
            keyword_count=keyword_count,
            max_allowed_count=self.max_calls,
            node=node,
            sev_threshold_value=keyword_count,
            extended_disablers=(node.lineno, node.end_lineno),
            end_col=node.col_offset + len(node.name) + 1,
        )
        return True


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

    def check(self, node: File) -> None:
        if not self.enabled or node.end_lineno <= self.max_lines:
            return
        self.report(
            lines_count=node.end_lineno,
            max_allowed_count=self.max_lines,
            node=node,
            lineno=node.end_lineno,
            end_col=node.end_col_offset,
            sev_threshold_value=node.end_lineno,
        )


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

    def check(self, node: Keyword) -> None:
        if not self.enabled:
            return
        for child in node.body:
            if not isinstance(child, Arguments):
                continue
            args_number = len(child.values)
            if args_number > self.max_args:
                name_token = child.data_tokens[0]
                self.report(
                    keyword_name=node.name,
                    arguments_count=args_number,
                    max_allowed_count=self.max_args,
                    node=name_token,
                    end_lineno=child.end_lineno,
                    end_col=child.end_col_offset,
                    extended_disablers=(node.lineno, node.end_lineno),
                    sev_threshold_value=args_number,
                )
            break


class LineTooLongRule(Rule):
    r"""
    The line is too long.

    Comments with disabler directives (such as ``# robocop: off``) are ignored. Lines that contain URLs are also
    ignored.

    It is possible to ignore lines that match the regex pattern. Configure it using the following option:

        robocop check --configure line-too-long.ignore_pattern=pattern

    Lines that are part of a documentation (the ``Documentation`` setting or the ``[Documentation]`` setting of a
    test case or keyword, together with their ``...`` continuation lines) can be ignored using the following option:

        robocop check --configure line-too-long.ignore_docs=True

    This rule is not fixed by ``robocop check --fix``. Use the ``SplitTooLongLine`` formatter
    (``robocop format``) to fix it.

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
        RuleParam(
            name="ignore_docs",
            default=False,
            converter=str2bool,
            show_type="bool",
            desc="ignore lines that are part of a documentation",
        ),
    ]
    severity_threshold = SeverityThreshold("line_length", substitute_value="allowed_length")
    added_in_version = "1.0.0"
    style_guide_ref = ["#line-length"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0508",)
    fix_suggestion = "Break long lines using the '...' continuation syntax."

    def check(self, line: str, lineno: int, doc_lines: frozenset[int] = frozenset()) -> None:
        if not self.enabled:
            return
        if lineno in doc_lines:
            return
        line = line.rstrip().expandtabs(4)
        if len(line) <= self.line_length:
            return
        # the line is potentially too long, so we need to check if it can be false positive
        if self.line_is_ignored(line):
            return
        if self.url_in_line(line):
            return
        line = self.strip_disablers(line)
        if len(line) > self.line_length:
            self.report(
                line_length=len(line),
                allowed_length=self.line_length,
                lineno=lineno,
                col=self.line_length,
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
        return bool(0 < line.find("://") < self.line_length)

    def line_is_ignored(self, line: str) -> bool:
        return bool(self.ignore_pattern and self.ignore_pattern.search(line))

    @staticmethod
    def get_documentation_lines(model: File) -> frozenset[int]:
        """Collect line numbers covered by documentation settings (including continuation lines)."""
        doc_lines: set[int] = set()
        for doc in _iter_documentation(model):
            doc_lines.update(range(doc.lineno, doc.end_lineno + 1))
        return frozenset(doc_lines)


class EmptySectionRule(FixableRule):
    """
    Section is empty.

    Empty section does not have any effect and can be removed.

    Incorrect code example:

        *** Variables ***


        *** Test Cases ***
        Test
            Keyword Call

    Correct code:

        *** Test Cases ***
        Test
            Keyword Call

    Sections that contain only comments are also reported, but they are not removed by the fix -
    it is not possible to tell whether such comments are still relevant.

    """

    name = "empty-section"
    rule_id = "LEN09"
    message = "Section '{section_name}' is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0509",)
    fix_availability = FixAvailability.SOMETIMES

    def check(self, node: Section) -> None:
        if not self.enabled or not node.header:
            return
        anything_but = EmptyLine if isinstance(node, CommentSection) else (Comment, EmptyLine)
        if all(isinstance(child, anything_but) for child in node.body):
            self.report(
                section_name=get_section_name(node),
                node=node,
                col=node.col_offset + 1,
                end_col=node.header.end_col_offset,
            )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        """
        Remove the empty section.

        Sections that contain comments are not fixed - removing them would remove the comments as well,
        and it is not possible to tell whether the comments are still relevant.
        """
        node = diag.node
        if node is None or node.header is None:
            return None
        if any(isinstance(statement, Comment) for statement in node.body):
            return None
        section_name = str(diag.reported_arguments["section_name"])
        return remove_lines_fix(self, node.lineno, node.end_lineno, f"Remove empty '{section_name}' section")


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

    def check(self, return_count: int, node: Node) -> None:
        if not self.enabled or return_count <= self.max_returns:
            return
        self.report(
            return_count=return_count,
            max_allowed_count=self.max_returns,
            node=node,
            col=node.data_tokens[0].col_offset + 1,
            end_col=node.data_tokens[0].end_col_offset + 1,
            sev_threshold_value=return_count,
        )

    def check_keyword_call(self, node: KeywordCall, normalized_keyword_name: str) -> None:
        if not self.enabled:
            return
        if normalized_keyword_name == "returnfromkeyword":
            self.check(len(node.args), node)
        elif normalized_keyword_name == "returnfromkeywordif":
            self.check(len(node.args) - 1, node)


class EmptySettingRule(FixableRule):
    """
    Base class for the rules reporting settings without any value.

    The fix removes such setting, since a setting without a value does not have any effect.
    The only exception are the test case settings that can overwrite the suite settings
    (``[Setup]``, ``[Teardown]``, ``[Timeout]`` and ``[Template]``). Those are not removed but filled with the
    explicit ``NONE`` value instead, since the suite setting can be also defined in the ``__init__.robot`` file
    of the parent suite.
    Comments are never removed by the fix.
    """

    fix_availability = FixAvailability.ALWAYS

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        return remove_empty_setting_fix(self, diag, source_lines)


def report_empty_setting(rule: Rule, node: Statement) -> None:
    """Report an empty setting that spans the whole statement."""
    rule.report(node=node, col=node.col_offset + 1, end_col=node.end_col_offset)


def report_empty_block_setting(
    rule: Rule, node: Statement, block_name: str, overwrites_suite_setting: bool = False
) -> None:
    """Report an empty setting whose message names the block (test case or keyword) it belongs to."""
    rule.report(
        block_name=block_name,
        overwrites_suite_setting=overwrites_suite_setting,
        node=node,
        col=node.data_tokens[0].col_offset + 1,
        end_col=node.end_col_offset,
    )


class EmptyMetadataRule(EmptySettingRule):
    """
    Metadata settings do not have any value set.

    Metadata can be defined in the ``*** Settings ***`` section for the whole suite, and - with
    Robot Framework 7.5 and newer - also inside a test case using the ``[Metadata]`` setting.

    Incorrect code example:

        *** Settings ***
        Metadata

        *** Test Cases ***
        Test
            [Metadata]
            Keyword

    Correct code example:

        *** Settings ***
        Metadata    Platform    ${PLATFORM}

        *** Test Cases ***
        Test
            [Metadata]    Owner    Team Robot
            Keyword

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

    def check(self, node: Statement) -> None:
        if not node.name:
            self.report(node=node, col=node.data_tokens[0].col_offset + 1)


class MetadataWithoutValueRule(Rule):
    """
    Metadata name is defined without a value.

    Metadata with only a name is recorded with an empty value, which is rarely intended and shows up as
    an empty entry in the report and log. Provide a value, or remove the metadata altogether.

    Metadata can be defined in the ``*** Settings ***`` section for the whole suite, and - with
    Robot Framework 7.5 and newer - also inside a test case using the ``[Metadata]`` setting.

    Incorrect code example:

        *** Settings ***
        Metadata    Platform

        *** Test Cases ***
        Test
            [Metadata]    Owner
            Keyword

    Correct code example:

        *** Settings ***
        Metadata    Platform    ${PLATFORM}

        *** Test Cases ***
        Test
            [Metadata]    Owner    Team Robot
            Keyword

    """

    name = "metadata-without-value"
    rule_id = "LEN33"
    message = "Metadata '{metadata_name}' does not have a value"
    severity = RuleSeverity.WARNING
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: Statement) -> None:
        if not self.enabled or not node.name or node.value:
            return
        name_token = node.get_token(Token.NAME)
        if name_token is None:
            return
        self.report(
            metadata_name=node.name,
            node=name_token,
            col=name_token.col_offset + 1,
            end_col=name_token.end_col_offset + 1,
        )


class EmptyDocumentationRule(EmptySettingRule):
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

    def check(self, node: Statement, block_name: str) -> None:
        if not node.value:
            report_empty_block_setting(self, node, block_name)


class EmptyForceTagsRule(EmptySettingRule):  # TODO: Rename/deprecate and replace with Test Tags
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

    def check(self, node: Statement) -> None:
        if not node.values:
            report_empty_setting(self, node)


class EmptyDefaultTagsRule(EmptySettingRule):
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

    def check(self, node: Statement) -> None:
        if not node.values:
            report_empty_setting(self, node)


class EmptyVariablesImport(EmptySettingRule):
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

    def check(self, node: Statement) -> None:
        if not node.name:
            report_empty_setting(self, node)


class EmptyResourceImport(EmptySettingRule):
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

    def check(self, node: Statement) -> None:
        if not node.name:
            report_empty_setting(self, node)


class EmptyLibraryImport(EmptySettingRule):
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

    def check(self, node: Statement) -> None:
        if not node.name:
            report_empty_setting(self, node)


class EmptySetupRule(EmptySettingRule):
    """
    Empty setup.

    ``[Setup]`` without a value does not have any effect and can be removed.
    If the intention is to overwrite the ``Test Setup`` from the settings section, use the explicit ``NONE`` value:

        *** Settings ***
        Test Setup    Open Application

        *** Test Cases ***
        Test without setup
            [Setup]    NONE
            Keyword Call

    """

    name = "empty-setup"
    rule_id = "LEN18"
    message = "Setup of {block_name} does not have any keywords"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0518",)

    def check(self, node: Statement, block_name: str, overwrites_suite_setting: bool = False) -> None:
        if not node.name:
            report_empty_block_setting(self, node, block_name, overwrites_suite_setting)


class EmptySuiteSetupRule(EmptySettingRule):
    """Empty Suite Setup."""

    name = "empty-suite-setup"
    rule_id = "LEN19"
    message = "Suite Setup does not have any keywords"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0519",)

    def check(self, node: Statement) -> None:
        if not node.name:
            report_empty_setting(self, node)


class EmptyTestSetupRule(EmptySettingRule):
    """Empty Test Setup."""

    name = "empty-test-setup"
    rule_id = "LEN20"
    message = "Test Setup does not have any keywords"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0520",)

    def check(self, node: Statement) -> None:
        if not node.name:
            report_empty_setting(self, node)


class EmptyTeardownRule(EmptySettingRule):
    """
    Empty Teardown.

    ``[Teardown]`` without a value does not have any effect and can be removed.
    If the intention is to overwrite the ``Test Teardown`` from the settings section, use the explicit ``NONE`` value:

        *** Settings ***
        Test Teardown    Close Application

        *** Test Cases ***
        Test without teardown
            [Teardown]    NONE
            Keyword Call

    """

    name = "empty-teardown"
    rule_id = "LEN21"
    message = "Teardown of {block_name} does not have any keywords"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0521",)

    def check(self, node: Statement, block_name: str, overwrites_suite_setting: bool = False) -> None:
        if not node.name:
            report_empty_block_setting(self, node, block_name, overwrites_suite_setting)


class EmptySuiteTeardownRule(EmptySettingRule):
    """Empty Suite Teardown."""

    name = "empty-suite-teardown"
    rule_id = "LEN22"
    message = "Suite Teardown does not have any keywords"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0522",)

    def check(self, node: Statement) -> None:
        if not node.name:
            report_empty_setting(self, node)


class EmptyTestTeardownRule(EmptySettingRule):
    """Empty Test Teardown."""

    name = "empty-test-teardown"
    rule_id = "LEN23"
    message = "Test Teardown does not have any keywords"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0523",)

    def check(self, node: Statement) -> None:
        if not node.name:
            report_empty_setting(self, node)


class EmptyTimeoutRule(EmptySettingRule):
    """
    Empty Timeout.

    ``[Timeout]`` without a value does not have any effect and can be removed.
    If the intention is to overwrite the ``Test Timeout`` from the settings section, use the explicit ``NONE`` value:

        *** Settings ***
        Test Timeout    1 min

        *** Test Cases ***
        Test without timeout
            [Timeout]    NONE
            Keyword Call

    """

    name = "empty-timeout"
    rule_id = "LEN24"
    message = "Timeout of {block_name} is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0524",)

    def check(self, node: Statement, block_name: str, overwrites_suite_setting: bool = False) -> None:
        # ``value`` is not used, since Robot Framework returns None for the explicit ``NONE`` timeout
        if len(node.data_tokens) < 2:
            report_empty_block_setting(self, node, block_name, overwrites_suite_setting)


class EmptyTestTimeoutRule(EmptySettingRule):
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

    def check(self, node: Statement) -> None:
        # ``value`` is not used, since Robot Framework returns None for the explicit ``NONE`` timeout
        if len(node.data_tokens) < 2:
            report_empty_setting(self, node)


class EmptyArgumentsRule(EmptySettingRule):
    """Empty ``[Arguments]`` setting."""

    name = "empty-arguments"
    rule_id = "LEN26"
    message = "Arguments of {block_name} are empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0526",)

    def check(self, node: Statement, block_name: str) -> None:
        if not node.values:
            report_empty_block_setting(self, node, block_name)


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

    def check(self, node: Statement, templated_suite: bool) -> None:
        if not self.enabled:
            return
        max_testcases = self.max_templated_testcases if templated_suite else self.max_testcases
        discovered_testcases = sum(isinstance(child, TestCase) for child in node.body)
        if discovered_testcases > max_testcases:
            self.report(
                test_count=discovered_testcases,
                max_allowed_count=max_testcases,
                node=node,
                end_col=node.header.end_col_offset,
                sev_threshold_value=discovered_testcases,
            )


class EmptyTestTemplateRule(EmptySettingRule):
    """
    Test Template is empty.

    ``Test Template`` sets the template to all tests in a suite. Empty value is considered an error
    because it leads the users to wrong impression on how the suite operates.
    Without value, the setting is ignored and the tests are not templated.
    """

    name = "empty-test-template"
    rule_id = "LEN29"
    message = "Test Template is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "3.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )

    def check(self, node: Statement) -> None:
        if not node.value:
            report_empty_setting(self, node)


class EmptyTemplateRule(EmptySettingRule):
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

    def check(self, node: Statement, block_name: str, overwrites_suite_setting: bool = False) -> None:
        if len(node.data_tokens) < 2:
            report_empty_block_setting(self, node, block_name, overwrites_suite_setting)


class EmptyKeywordTagsRule(EmptySettingRule):
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

    def check(self, node: Statement) -> None:
        if not node.values:
            report_empty_setting(self, node)


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


def is_data_statement(node: Node) -> bool:
    return not isinstance(node, (EmptyLine, Comment))


def is_not_standalone_comment(node: Node) -> bool:
    return isinstance(node, Comment) and node.tokens[0].type == Token.SEPARATOR


def check_node_length(node: Node, ignore_docs: bool) -> tuple[int, int]:
    last_node = node
    for child in node.body[::-1]:
        if is_data_statement(child) or is_not_standalone_comment(child):
            last_node = child
            break
    if ignore_docs:
        return (last_node.end_lineno - node.lineno - get_documentation_length(node)), last_node.end_lineno
    return (last_node.end_lineno - node.lineno), last_node.end_lineno


def get_documentation_length(node: Node) -> int:
    doc_len = 0
    for child in node.body:
        if isinstance(child, Documentation):
            doc_len += child.end_lineno - child.lineno + 1
    return doc_len


def _iter_documentation(model: File) -> Iterator[Documentation]:
    """Yield every ``Documentation`` statement in the model (suite, test case and keyword documentation)."""
    for node in ast.walk(model):
        if isinstance(node, Documentation):
            yield node


KEYWORD_CALL_ALIKE = tuple(
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


def count_keyword_calls(node: Node) -> int:
    """Recursively count keyword calls (and alike statements) in the node body."""
    if isinstance(node, KEYWORD_CALL_ALIKE):
        return 1
    if not hasattr(node, "body"):
        return 0
    calls = sum(count_keyword_calls(child) for child in node.body)
    while node and getattr(node, "orelse", None):
        node = node.orelse
        calls += sum(count_keyword_calls(child) for child in node.body)
    while node and getattr(node, "next", None):
        node = node.next
        calls += sum(count_keyword_calls(child) for child in node.body)
    return calls


def is_templated_test(node: TestCase, templated_suite: bool) -> bool:
    if templated_suite:
        return True
    if not node.body:
        return False
    return any(isinstance(statement, Template) for statement in node.body)


@dataclass
class CachedVariable:
    name: str
    node: Node
    end_col: int
