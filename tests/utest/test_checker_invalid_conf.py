"""
Those exceptions usually happens when trying to add new rules for Robocop and using wrong configuration (already
existing rule name or id, get value of non-existing parameter inside checker etc).
"""
import pytest

import robocop.exceptions
from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity


class ValidChecker(VisitorChecker):
    reports = ("some-message",)


class TestCheckerInvalidConf:
    def test_get_param_with_non_existing_rule(self, robocop_instance):
        checker = ValidChecker()
        checker.rules = {
            "some-message": Rule(
                RuleParam(name="param", converter=int, default=5, desc="This is desc"),
                rule_id="0101",
                name="some-message",
                msg="Some description",
                severity=RuleSeverity.WARNING,
            )
        }
        with pytest.raises(robocop.exceptions.RuleNotFoundError) as err:
            checker.param("idontexist", "param")
        assert "ValidChecker checker does not contain rule `idontexist`. Available rules: some-message" in str(err)

    def test_get_non_existing_param(self):
        checker = ValidChecker()
        checker.rules = {
            "some-message": Rule(
                RuleParam(name="param", converter=int, default=5, desc="This is desc"),
                rule_id="0101",
                name="some-message",
                msg="Some description",
                severity=RuleSeverity.WARNING,
            )
        }
        with pytest.raises(robocop.exceptions.RuleParamNotFoundError):
            checker.param("some-message", "param2")
