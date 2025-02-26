import pytest

from robocop.config import Config
from robocop.linter.rules import Rule, RuleParam, RuleSeverity


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def rule():
    class CustomRule(Rule):
        rule_id = "0101"
        name = "some-message"
        message = "Some description"
        severity = RuleSeverity.WARNING
        parameters = [RuleParam(name="param_name", converter=int, default=1, desc="")]

    return CustomRule()


@pytest.fixture
def rule2():
    class CustomRule(Rule):
        rule_id = "0902"
        name = "other-message"
        message = "Some description. Example"
        severity = RuleSeverity.ERROR

    return CustomRule()


@pytest.fixture
def error_msg():
    class CustomRule(Rule):
        rule_id = "0101"
        name = "error-message"
        message = "Some description"
        severity = RuleSeverity.ERROR
        parameters = [RuleParam(name="param_name", converter=int, default=1, desc="")]

    return CustomRule()


@pytest.fixture
def warning_msg():
    class CustomRule(Rule):
        rule_id = "0102"
        name = "warning-message"
        message = "Some description"
        severity = RuleSeverity.WARNING
        parameters = [RuleParam(name="param_name", converter=int, default=1, desc="")]

    return CustomRule()


@pytest.fixture
def info_msg():
    class CustomRule(Rule):
        rule_id = "0103"
        name = "info-message"
        message = "Some description"
        severity = RuleSeverity.INFO
        parameters = [RuleParam(name="param_name", converter=int, default=1, desc="")]

    return CustomRule()
