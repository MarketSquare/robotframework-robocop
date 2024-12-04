"""Documentation checkers"""

from pathlib import Path

from robot.parsing.model.statements import Documentation

from robocop.checkers import VisitorChecker
from robocop.rules import DefaultRule, RuleParam, RuleSeverity
from robocop.utils.misc import str2bool

RULE_CATEGORY_ID = "02"

rules = {
    "0201": DefaultRule(
        rule_id="0201",
        name="missing-doc-keyword",
        msg="Missing documentation in '{{ name }}' keyword",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
        docs="""
        Keyword documentation is displayed in a tooltip in most code editors,
        so it is recommended to write it for each keyword.

        You can add documentation to keyword using following syntax::

            *** Keywords ***
            Keyword
                [Documentation]  Keyword documentation
                Keyword Step
                Other Step
        """,
    ),
    "0202": DefaultRule(
        RuleParam(
            name="ignore_templated",
            default="True",
            converter=str2bool,
            show_type="bool",
            desc="whether templated tests should be documented or not",
        ),
        rule_id="0202",
        name="missing-doc-test-case",
        msg="Missing documentation in '{{ name }}' test case",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
        docs="""
        You can add documentation to test case using following syntax::

            *** Test Cases ***
            Test
                [Documentation]  Test documentation
                Keyword Step
                Other Step

        The rule by default ignores templated test cases but it can be configured with::

            robocop --configure missing-doc-test-case:ignore_templated:False

        Possible values are: ``Yes`` / ``1`` / ``True`` (default) or ``No`` / ``False`` / ``0``.
        """,
    ),
    "0203": DefaultRule(
        rule_id="0203",
        name="missing-doc-suite",
        msg="Missing documentation in suite",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
        docs="""
        You can add documentation to suite using following syntax::

            *** Settings ***
            Documentation    Suite documentation
        """,
    ),
    "0204": DefaultRule(
        rule_id="0204",
        name="missing-doc-resource-file",
        msg="Missing documentation in resource file",
        severity=RuleSeverity.WARNING,
        added_in_version="2.8.0",
        docs="""
        You can add documentation to resource file using following syntax::

            *** Settings ***
            Documentation    Resource file documentation
        """,
    ),
}


class MissingDocumentationChecker(VisitorChecker):
    """Checker for missing documentation."""

    reports = (
        "missing-doc-keyword",
        "missing-doc-test-case",
        "missing-doc-suite",
        "missing-doc-resource-file",
    )

    def __init__(self):
        self.is_resource = False
        self.settings_section_exists = False
        super().__init__()

    def visit_Keyword(self, node):  # noqa: N802
        if node.name.lstrip().startswith("#"):
            return
        self.check_if_docs_are_present(node, "missing-doc-keyword", extend_disablers=True)

    def visit_TestCase(self, node):  # noqa: N802
        if self.param("missing-doc-test-case", "ignore_templated") and self.templated_suite:
            return
        self.check_if_docs_are_present(node, "missing-doc-test-case", extend_disablers=True)

    def visit_SettingSection(self, node):  # noqa: N802
        self.settings_section_exists = True
        if self.is_resource:
            self.check_if_docs_are_present(node, "missing-doc-resource-file", extend_disablers=False)
        else:
            self.check_if_docs_are_present(node, "missing-doc-suite", extend_disablers=False)

    def visit_File(self, node):  # noqa: N802
        source = node.source if node.source else self.source
        self.is_resource = source and ".resource" in Path(source).suffix
        self.settings_section_exists = False
        self.generic_visit(node)
        if not self.settings_section_exists:
            if self.is_resource:
                self.report("missing-doc-resource-file", node=node, lineno=1, col=1)
            else:
                self.report("missing-doc-suite", node=node, lineno=1, col=1)

    def check_if_docs_are_present(self, node, msg, extend_disablers):
        for statement in node.body:
            if isinstance(statement, Documentation):
                break
        else:
            extended_disablers = (node.lineno, node.end_lineno) if extend_disablers else None
            if hasattr(node, "name"):
                self.report(
                    msg,
                    name=node.name,
                    node=node,
                    end_col=node.col_offset + len(node.name) + 1,
                    extended_disablers=extended_disablers,
                )
            else:
                self.report(msg, node=node, end_col=node.end_col_offset, extended_disablers=extended_disablers)
