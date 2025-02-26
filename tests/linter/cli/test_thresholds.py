import pytest

from robocop.config import RuleMatcher
from robocop.linter import exceptions
from robocop.linter.rules import Diagnostic, Rule, RuleParam, RuleSeverity, SeverityThreshold


def get_rule_with_id_sev(rule_id, sev):
    class CustomRule(Rule):
        rule_id = "0101"
        name = "some-message"
        message = "Some description"
        severity = RuleSeverity(sev)
        parameters = [RuleParam(name="param_name", converter=int, default=1, desc="")]

    rule = CustomRule()
    rule.rule_id = rule_id
    rule.message = f"some-message-{rule_id}"
    return CustomRule()


def get_diag_with_sev_value(rule: Rule, sev_value) -> Diagnostic:
    return Diagnostic(
        rule,
        source="",
        node=None,
        lineno=1,
        end_lineno=1,
        col=1,
        end_col=1,
        sev_threshold_value=sev_value,
        extended_disablers=None,
        severity=None,
    )


class TestThresholds:
    @pytest.mark.parametrize(
        ("threshold", "included", "excluded"),
        [
            ("E", ["E"], ["I", "W"]),
            ("W", ["E", "W"], ["I"]),
            ("I", ["E", "W", "I"], []),
        ],
    )
    def test_disable_rules_below_threshold(self, empty_linter, threshold, included, excluded):
        empty_linter.config.linter.threshold = RuleSeverity(threshold)
        matcher = RuleMatcher(empty_linter.config.linter)
        for severity in included:
            rule = get_rule_with_id_sev("0101", severity)
            assert matcher.is_rule_enabled(rule)
        for severity in excluded:
            rule = get_rule_with_id_sev("0101", severity)
            assert not matcher.is_rule_enabled(rule)


class TestRuleSeverityThreshold:
    def test_rule_threshold(self):
        thresholds = SeverityThreshold("line_length")
        thresholds.value = "warning=100:info=50:error=150"
        assert thresholds.get_severity(30) is None
        assert thresholds.get_severity(55) == RuleSeverity.INFO
        assert thresholds.get_severity(100) == RuleSeverity.WARNING
        assert thresholds.get_severity(101) == RuleSeverity.WARNING
        assert thresholds.get_severity(149) == RuleSeverity.WARNING
        assert thresholds.get_severity(150) == RuleSeverity.ERROR

    def test_rule_severity_threshold_and_filter_threshold(self):
        rule = get_rule_with_id_sev("0101", "W")
        rule.severity_threshold = SeverityThreshold("param_name", compare_method="greater")
        rule.severity_threshold.value = "W=0:E=1"
        msg_1 = get_diag_with_sev_value(rule, 0)
        msg_2 = get_diag_with_sev_value(rule, 1)
        msg_3 = get_diag_with_sev_value(rule, 2)
        assert [msg_1.severity, msg_2.severity, msg_3.severity] == [
            RuleSeverity.WARNING,
            RuleSeverity.ERROR,
            RuleSeverity.ERROR,
        ]

    # # TODO
    def test_invalid_threshold_config(self):
        thresholds = SeverityThreshold("line_length")
        exp_error = (
            "Invalid configuration for Robocop:\n"
            "Invalid severity value 'error'. It should be list of `severity=param_value` pairs, separated by `:`."
        )
        with pytest.raises(exceptions.InvalidArgumentError, match=exp_error):
            thresholds.value = "error"
        exp_error = "Invalid severity value 'invalid'. Choose one from: I, W, E"
        with pytest.raises(exceptions.InvalidArgumentError, match=exp_error):
            thresholds.value = "invalid=100"
