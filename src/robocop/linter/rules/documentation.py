"""Documentation checkers"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from robot.parsing.model.statements import Documentation

from robocop.linter.rules import Rule, RuleParam, RuleSeverity, VisitorChecker
from robocop.linter.utils.misc import str2bool

if TYPE_CHECKING:
    from robot.parsing.model import File, Keyword, SettingSection, TestCase


class MissingDocKeywordRule(Rule):
    """
    Keyword without documentation.

    Keyword documentation is displayed in a tooltip in most code editors,
    so it is recommended to write it for each keyword.

    You can add documentation to keyword using following syntax::

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


class MissingDocTestCaseRule(Rule):
    """
    Test case without documentation.

    You can add documentation to test case using following syntax::

        *** Test Cases ***
        Test
            [Documentation]  Test documentation
            Keyword Step
            Other Step

    The rule by default ignores templated test cases but it can be configured with::

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


class MissingDocTestSuiteRule(Rule):
    """
    Test suite without documentation.

    You can add documentation to suite using following syntax::

        *** Settings ***
        Documentation    Suite documentation

    """

    name = "missing-doc-suite"
    rule_id = "DOC03"
    message = "Missing documentation in suite"
    severity = RuleSeverity.WARNING
    file_wide_rule = True
    added_in_version = "1.0.0"


class MissingDocResourceFileRule(Rule):
    """
    Resource file without documentation.

    You can add documentation to resource file using following syntax::

        *** Settings ***
        Documentation    Resource file documentation

    """

    name = "missing-doc-resource-file"
    rule_id = "DOC04"
    message = "Missing documentation in resource file"
    severity = RuleSeverity.WARNING
    file_wide_rule = True
    added_in_version = "2.8.0"


class MissingDocumentationChecker(VisitorChecker):
    """Checker for missing documentation."""

    missing_doc_keyword: MissingDocKeywordRule
    missing_doc_test_case: MissingDocTestCaseRule
    missing_doc_test_suite: MissingDocTestSuiteRule
    missing_doc_resource_file: MissingDocResourceFileRule

    def __init__(self):
        self.is_resource = False
        self.settings_section_exists = False
        super().__init__()

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        if node.name.lstrip().startswith("#"):  # TODO: edge case for parsing with RF3?
            return
        self.check_if_docs_are_present(
            node, self.missing_doc_keyword, extend_disablers=True
        )  # TODO: could be self.missing_doc_keyword.check_docs(node)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        if self.templated_suite and self.missing_doc_test_case.ignore_templated:
            return
        self.check_if_docs_are_present(node, self.missing_doc_test_case, extend_disablers=True)

    def visit_SettingSection(self, node: SettingSection) -> None:  # noqa: N802
        self.settings_section_exists = True
        if self.is_resource:
            self.check_if_suite_docs_are_present(node, self.missing_doc_resource_file)
        else:
            self.check_if_suite_docs_are_present(node, self.missing_doc_test_suite)

    def visit_File(self, node: File) -> None:  # noqa: N802
        source = node.source if node.source else self.source
        self.is_resource = source and ".resource" in Path(source).suffix
        self.settings_section_exists = False
        self.generic_visit(node)
        if not self.settings_section_exists:
            if self.is_resource:
                self.report(self.missing_doc_resource_file, node=node, lineno=1, col=1)
            else:
                self.report(self.missing_doc_test_suite, node=node, lineno=1, col=1)

    def check_if_docs_are_present(  # TODO: could be implemented inside 'MissingDocumentationRule' class
        self, node: Keyword | TestCase | SettingSection, rule: Rule, extend_disablers: bool
    ) -> None:
        # TODO indent
        for statement in node.body:
            if isinstance(statement, Documentation):
                break
        else:
            extended_disablers = (node.lineno, node.end_lineno) if extend_disablers else None
            if hasattr(node, "name"):
                self.report(
                    rule,
                    name=node.name,
                    node=node,
                    end_col=node.col_offset + len(node.name) + 1,
                    extended_disablers=extended_disablers,
                )
            else:
                self.report(rule, node=node, end_col=node.end_col_offset, extended_disablers=extended_disablers)

    def check_if_suite_docs_are_present(self, node: SettingSection, rule: Rule):
        for statement in node.body:
            if isinstance(statement, Documentation):
                return
        self.report(rule, node=node)
