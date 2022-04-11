"""
Documentation checkers
"""
from robot.parsing.model.blocks import SettingSection
from robot.parsing.model.statements import Documentation

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity
from robocop.utils.misc import str2bool

rules = {
    "0201": Rule(
        rule_id="0201",
        name="missing-doc-keyword",
        msg="Missing documentation in '{{ name }}' keyword",
        severity=RuleSeverity.WARNING,
        docs="""
        You can add documentation to keyword using following syntax::
        
            Keyword
                [Documentation]  Keyword documentation
                Keyword Step
                Other Step

        """,
    ),
    "0202": Rule(
        RuleParam(
            name="ignore_templated",
            default="True",
            converter=str2bool,
            desc="whether templated tests should be documented or not",
        ),
        rule_id="0202",
        name="missing-doc-test-case",
        msg="Missing documentation in '{{ name }}' test case",
        severity=RuleSeverity.WARNING,
        docs="""
        You can add documentation to test case using following syntax::
        
            Test
                [Documentation]  Test documentation
                Keyword Step
                Other Step
        
        The rule by default ignores templated test cases but it can be configured with::
        
            robocop --configure missing-doc-test-case:ignore_templated:False
        
        Possible values are: Yes / 1 / True (default) or No / False / 0.
        """,
    ),
    "0203": Rule(
        rule_id="0203",
        name="missing-doc-suite",
        msg="Missing documentation in suite",
        severity=RuleSeverity.WARNING,
        docs="""
        You can add documentation to suite using following syntax::
        
            *** Settings ***
            Documentation    Suite documentation

        """,
    ),
}


class MissingDocumentationChecker(VisitorChecker):
    """Checker for missing documentation."""

    reports = (
        "missing-doc-keyword",
        "missing-doc-test-case",
        "missing-doc-suite",
    )

    def visit_Keyword(self, node):  # noqa
        if node.name.lstrip().startswith("#"):
            return
        self.check_if_docs_are_present(node, "missing-doc-keyword")

    def visit_TestCase(self, node):  # noqa
        if self.param("missing-doc-test-case", "ignore_templated") and self.templated_suite:
            return
        self.check_if_docs_are_present(node, "missing-doc-test-case")

    def visit_SettingSection(self, node):  # noqa
        self.check_if_docs_are_present(node, "missing-doc-suite")

    def visit_File(self, node):  # noqa
        for section in node.sections:
            if isinstance(section, SettingSection):
                break
        else:
            self.report("missing-doc-suite", node=node, lineno=1)
        super().visit_File(node)

    def check_if_docs_are_present(self, node, msg):
        for statement in node.body:
            if isinstance(statement, Documentation):
                break
        else:
            if hasattr(node, "name"):
                self.report(msg, name=node.name, node=node)
            else:
                self.report(msg, node=node)
