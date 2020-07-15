from robot.parsing.model.statements import Documentation, Comment
from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(KeywordDocumentationChecker(linter))


class KeywordDocumentationChecker(VisitorChecker):
    """ Checker for missing documentation.

        Reports:
        W0201: missing-doc-keyword: Missing documentation in keyword
        Configurable:
        severity: MessageSeverity

        W0202: missing-doc-testcase: Missing documentation in test case
        Configurable:
        severity: MessageSeverity

        W0303: missing-doc-suite: Missing documentation in suite
        Configurable:
        severity: MessageSeverity
     """
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

    def visit_Keyword(self, node):
        self.check_if_docs_are_present(node, "missing-doc-keyword")

    def visit_TestCase(self, node):
        self.check_if_docs_are_present(node, "missing-doc-testcase")

    def visit_SettingSection(self, node):
        # TODO: if settingsection is missing, it should also throw missing-doc-suite
        self.check_if_docs_are_present(node, "missing-doc-suite")

    def check_if_docs_are_present(self, node, msg):
        for statement in node.body:
            if isinstance(statement, Documentation):
                break
        else:
            self.report(msg, node=node)
