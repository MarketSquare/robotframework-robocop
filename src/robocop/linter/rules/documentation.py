"""Documentation checkers"""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import VariableError
from robot.parsing.model.statements import Documentation

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleParam, RuleSeverity
from robocop.linter.utils.misc import str2bool

if TYPE_CHECKING:
    from robot.parsing.model import File, Keyword, SettingSection, TestCase
    from robot.parsing.model.statements import Statement


def report_if_documentation_is_missing(rule: Rule, node: Keyword | TestCase) -> None:
    """Report ``rule`` if the block does not contain the [Documentation] setting."""
    if any(isinstance(statement, Documentation) for statement in node.body):
        return
    rule.report(
        name=node.name,
        node=node,
        end_col=node.col_offset + len(node.name) + 1,
        extended_disablers=(node.lineno, node.end_lineno),
    )


def report_if_suite_documentation_is_missing(rule: Rule, node: SettingSection) -> None:
    """Report ``rule`` if the settings section does not contain the Documentation setting."""
    if any(isinstance(statement, Documentation) for statement in node.body):
        return
    rule.report(node=node)


class MissingDocKeywordRule(Rule):
    """
    Keyword without documentation.

    Keyword documentation is displayed in a tooltip in most code editors,
    so it is recommended to write it for each keyword.

    You can add documentation to keyword using following syntax:

        *** Keywords ***
        Keyword
            [Documentation]  Keyword documentation
            Keyword Step
            Other Step

    """

    name = "missing-doc-keyword"
    rule_id = "DOC01"
    message = "Missing documentation in '{name}' keyword"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0201",)
    fix_suggestion = "Add a [Documentation] setting to the keyword."

    def check(self, node: Keyword) -> None:
        if not self.enabled:
            return
        report_if_documentation_is_missing(self, node)


class MissingDocTestCaseRule(Rule):
    """
    Test case without documentation.

    You can add documentation to test case using following syntax:

        *** Test Cases ***
        Test
            [Documentation]  Test documentation
            Keyword Step
            Other Step

    The rule by default ignores templated test cases but it can be configured with:

        robocop check --configure missing-doc-test-case.ignore_templated=False

    Possible values are: ``Yes`` / ``1`` / ``True`` (default) or ``No`` / ``False`` / ``0``.

    """

    name = "missing-doc-test-case"  # TODO: separate rule for templated tests
    rule_id = "DOC02"
    message = "Missing documentation in '{name}' test case"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    parameters = [
        RuleParam(
            name="ignore_templated",
            default="True",
            converter=str2bool,
            show_type="bool",
            desc="whether templated tests should be documented or not",
        )
    ]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0202",)
    fix_suggestion = "Add a [Documentation] setting to the test case."

    def check(self, node: TestCase, templated_suite: bool) -> None:
        if not self.enabled or (templated_suite and self.ignore_templated):
            return
        report_if_documentation_is_missing(self, node)


class MissingDocTestSuiteRule(Rule):
    """
    Test suite without documentation.

    You can add documentation to suite using following syntax:

        *** Settings ***
        Documentation    Suite documentation

    """

    name = "missing-doc-suite"
    rule_id = "DOC03"
    message = "Missing documentation in suite"
    severity = RuleSeverity.WARNING
    file_wide_rule = True
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0203",)

    def check(self, node: SettingSection) -> None:
        if not self.enabled:
            return
        report_if_suite_documentation_is_missing(self, node)

    def check_missing_settings_section(self, node: File) -> None:
        """Report the rule for a file that does not define the settings section at all."""
        if not self.enabled:
            return
        self.report(node=node, lineno=1, col=1)


class MissingDocResourceFileRule(Rule):
    """
    Resource file without documentation.

    You can add documentation to resource file using following syntax:

        *** Settings ***
        Documentation    Resource file documentation

    """

    name = "missing-doc-resource-file"
    rule_id = "DOC04"
    message = "Missing documentation in resource file"
    severity = RuleSeverity.WARNING
    file_wide_rule = True
    added_in_version = "2.8.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0204",)

    def check(self, node: SettingSection) -> None:
        if not self.enabled:
            return
        report_if_suite_documentation_is_missing(self, node)

    def check_missing_settings_section(self, node: File) -> None:
        """Report the rule for a file that does not define the settings section at all."""
        if not self.enabled:
            return
        self.report(node=node, lineno=1, col=1)


class VariableInDocumentationRule(Rule):
    r"""
    Unescaped variable syntax in documentation.

    Robot Framework resolves variables in suite, test case and user keyword documentation when a suite is executed.
    This includes scalar (``${name}``), list (``@{items}``), dictionary (``&{mapping}``) and environment
    (``%{NAME}``) variable syntax. Defined variables are replaced with their values. Undefined variables are left
    unchanged, which can make an unescaped literal example appear correct until a variable with the same name becomes
    available.

    For example, this documentation changes at runtime if ``${value}`` exists:

        *** Test Cases ***
        Example
            [Documentation]    The argument syntax is ${value}.
            No Operation

    Escape syntax that should be displayed literally:

        *** Test Cases ***
        Example
            [Documentation]    Scalar: \${value}; list: \@{items}; dictionary: \&{mapping}; environment: \%{HOME}.
            No Operation

    The leading backslash prevents substitution and is removed from the rendered documentation. The rule checks suite,
    test case and user keyword documentation, including continuation lines.

    The rule is disabled by default. Enable it with:

        robocop check --select variable-in-documentation

    There is no automatic fix. Robocop cannot determine whether interpolation is intentional, and escaping an
    intentionally dynamic value would change the rendered documentation. If interpolation is intended, leave the
    syntax unescaped and disable the rule locally where needed.

    """

    name = "variable-in-documentation"
    rule_id = "DOC05"
    message = "Unescaped variable '{variable}' in documentation"
    severity = RuleSeverity.INFO
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    fix_suggestion = "If literal variable syntax is intended, escape it with a backslash."

    def check(self, node: Statement) -> None:
        if not self.enabled:
            return
        for token in node.get_tokens(Token.ARGUMENT):
            try:
                variables = token.tokenize_variables()
                for variable in variables:
                    if variable.type != Token.VARIABLE:
                        continue
                    self.report(
                        variable=variable.value,
                        node=variable,
                        end_col=variable.end_col_offset + 1,
                    )
            except VariableError:
                continue
