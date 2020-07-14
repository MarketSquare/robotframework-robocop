from robot.parsing.model.statements import Documentation, Comment
from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(KeywordDocumentationChecker(linter))


class KeywordDocumentationChecker(VisitorChecker):
    msgs = {
        "0201": (
            "missing-doc-keyword",
            "Missing documentation in keyword",
            MessageSeverity.WARNING
        )
    }

    def visit_Keyword(self, node):
        self.check_if_docs_are_present(node)
                       

    def check_if_docs_are_present(self, node):
        if self.is_disabled(node, "missing-doc-keyword"):
            return
        for statement in node.body:
            if isinstance(statement, Documentation):
                break
        else:
            self.report("missing-doc-keyword", node=node)
