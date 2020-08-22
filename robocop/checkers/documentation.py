"""
Documentation checkers
"""
from robot.parsing.model.blocks import SettingSection
from robot.parsing.model.statements import Documentation
from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(MissingDocumentationChecker(linter))


class MissingDocumentationChecker(VisitorChecker):
    """ Checker for missing documentation. """
    msgs = {
        "0201": (
            "missing-doc-keyword",
            "Missing documentation in keyword",
            MessageSeverity.WARNING
        ),
        "0202": (
            "missing-doc-testcase",
            "Missing documentation in test case",
            MessageSeverity.WARNING
        ),
        "0203": (
            "missing-doc-suite",
            "Missing documentation in suite",
            MessageSeverity.WARNING
        )
    }

    def visit_Keyword(self, node):  # noqa
        self.check_if_docs_are_present(node, "missing-doc-keyword")

    def visit_TestCase(self, node):  # noqa
        self.check_if_docs_are_present(node, "missing-doc-testcase")

    def visit_SettingSection(self, node):  # noqa
        self.check_if_docs_are_present(node, "missing-doc-suite")

    def visit_File(self, node):  # noqa
        for section in node.sections:
            if isinstance(section, SettingSection):
                break
        else:
            self.report("missing-doc-suite", node=node)
        super().visit_File(node)

    def check_if_docs_are_present(self, node, msg):
        for statement in node.body:
            if isinstance(statement, Documentation):
                break
        else:
            self.report(msg, node=node)
