import pytest

from robocop.linter.rules import Rule, RuleParam, RuleSeverity


@pytest.fixture
def rule():
    return Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0101",
        name="some-message",
        msg="Some description",
        severity=RuleSeverity.WARNING,
    )


@pytest.fixture
def rule2():
    return Rule(
        rule_id="0902",
        name="other-message",
        msg="Some description. Example::\n",
        severity=RuleSeverity.ERROR,
    )


@pytest.fixture
def error_msg():
    return Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0101",
        name="error-message",
        msg="Some description",
        severity=RuleSeverity.ERROR,
    )


@pytest.fixture
def warning_msg():
    return Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0102",
        name="warning-message",
        msg="Some description",
        severity=RuleSeverity.WARNING,
    )


@pytest.fixture
def info_msg():
    return Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0103",
        name="info-message",
        msg="Some description",
        severity=RuleSeverity.INFO,
    )
