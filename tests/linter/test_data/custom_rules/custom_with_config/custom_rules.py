from __future__ import annotations

from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity


class ExternalRule(Rule):
    """
    Custom rule summary.

    Custom rule documentation.
    """
    name = "smth"
    rule_id = "EXT01"
    message = "Keyword call after [Return] statement"
    severity = RuleSeverity.ERROR



class SmthChecker(VisitorChecker):
    """Empty checker.."""

    smth: ExternalRule
