from robocop.linter.rules import Message, ProjectChecker, Rule, RuleSeverity

rules = {
    "9901": Rule(
        rule_id="9901",
        name="project-checker",
        msg="This check will be called after visiting all files",
        severity=RuleSeverity.INFO,
    ),
    "9902": Rule(
        rule_id="9902",
        name="test-total-count",
        msg="There is total of {{ tests_count }} tests in the project.",
        severity=RuleSeverity.INFO,
    ),
}


class MyProjectChecker(ProjectChecker):
    """Project checker."""

    reports = ("project-checker", "test-total-count")

    def __init__(self):
        self.sources = []
        self.test_count = 0
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.sources.append(node.source)
        self.generic_visit(node)

    def visit_TestCase(self, _node):  # noqa: N802
        self.test_count += 1

    def scan_project(self) -> list[Message]:
        self.issues = []
        for source in self.sources:
            self.report("project-checker", source=source)
        self.report("test-total-count", source="Project-name", tests_count=self.test_count)
        return self.issues
