"""
Documentation checkers
"""
from robot.parsing.model.blocks import SettingSection
from robot.parsing.model.statements import Documentation

from robocop.checkers import VisitorChecker
from robocop.rules import Rule

rules = {
    "0201": Rule(rule_id="0201", name="missing-doc-keyword", msg="Missing documentation in keyword", severity="W"),
    "0202": Rule(rule_id="0202", name="missing-doc-test-case", msg="Missing documentation in test case", severity="W"),
    "0203": Rule(rule_id="0203", name="missing-doc-suite", msg="Missing documentation in suite", severity="W"),
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
            self.report(msg, node=node)
