from robot.parsing.model.statements import Error

from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, RuleSeverity, VisitorChecker


class CustomWithFix(FixableRule):
    """
    Custom rule that does have a fix.

    The fix is available only when reporting the issue.
    """

    name = "fixable-rule"
    rule_id = "FIX01"
    message = "Custom rule message"
    severity = RuleSeverity.INFO
    added_in_version = "8.0.0"
    fix_availability = FixAvailability.ALWAYS


class CustomChecker(VisitorChecker):
    fixable_rule: CustomWithFix

    def visit_File(self, node):  # noqa: N802
        if isinstance(node.sections[0].body[-1], Error):  # placeholder added in first run
            return
        fix = Fix(
            edits=[
                TextEdit(
                    rule_id=self.fixable_rule.rule_id,
                    rule_name=self.fixable_rule.name,
                    start_line=node.end_lineno,
                    end_line=node.end_lineno,
                    start_col=node.end_col_offset + 1,
                    end_col=node.end_col_offset + 1,
                    replacement="PLACEHOLDER",
                )
            ],
            message="Replace last character of file with 'PLACEHOLDER'",
            applicability=FixApplicability.SAFE,
        )
        self.report(self.fixable_rule, lineno=node.lineno, col=node.col_offset + 1, fix=fix)
