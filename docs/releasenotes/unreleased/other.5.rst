New checker type - ProjectChecker (#1015)
-----------------------------------------

Robocop supported two type of checkers: ``VisitorChecker`` and ``RawFileChecker``. We have added new type of checker -
``ProjectChecker``. It extends the ``VisitorChecker`` but contains special ``scan_project`` method, that can be
overriden, which is called at the end of Robocop run. Typical usage of this checker would be collecting information
about our project using visitors and then performing checks and report issues in ``scan_project`` method.
Example custom rule with ``ProjectChecker``::

    from typing import List

    from robocop.checkers import ProjectChecker
    from robocop.rules import Message, Rule, RuleSeverity

    rules = {
        "9901": Rule(
            rule_id="9901",
            name="test-total-count",
            msg="There is total of {{ tests_count }} tests in the project.",
            severity=RuleSeverity.INFO,
        ),
    }


    class MyProjectChecker(ProjectChecker):
        """Checker for total tests count."""

        reports = ("test-total-count",)

        def __init__(self):
            self.test_count = 0
            super().__init__()

        def visit_TestCase(self, node):  # noqa
            self.test_count += 1

        def scan_project(self) -> List[Message]:
            # self.report is append issues to self.issues -> clearing it at the start of scan_project
            self.issues = []
            # Default issue format print file path with the issue - in this case we replace it with our custom string
            self.report("test-total-count", source="Project-name", tests_count=self.test_count)
            return self.issues
