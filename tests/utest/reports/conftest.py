import pytest

from robocop.rules import CommunityRule, DefaultRule, Rule, RuleParam, RuleSeverity


@pytest.fixture
def rule():
    return DefaultRule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0101",
        name="some-message",
        msg="Some description",
        severity=RuleSeverity.WARNING,
    )


@pytest.fixture
def rule2():
    return DefaultRule(
        rule_id="0902",
        name="other-message",
        msg="Some description. Example::\n",
        severity=RuleSeverity.ERROR,
    )


@pytest.fixture
def community_rule():
    return CommunityRule(
        rule_id="10001",
        name="some-community-rule",
        msg="An amazing description. Example::\n",
        severity=RuleSeverity.INFO,
    )


@pytest.fixture
def custom_rule():
    return Rule(
        rule_id="CUSTOM01",
        name="some-custom-rule",
        msg="A rule made outside Robocop. It has no help URL",
        severity=RuleSeverity.ERROR,
    )


@pytest.fixture
def error_msg():
    return DefaultRule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0101",
        name="error-message",
        msg="Some description",
        severity=RuleSeverity.ERROR,
    )


@pytest.fixture
def warning_msg():
    return DefaultRule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0102",
        name="warning-message",
        msg="Some description",
        severity=RuleSeverity.WARNING,
    )


@pytest.fixture
def info_msg():
    return DefaultRule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0103",
        name="info-message",
        msg="Some description",
        severity=RuleSeverity.INFO,
    )
