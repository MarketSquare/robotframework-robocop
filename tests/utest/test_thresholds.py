import pytest

import robocop.exceptions
from robocop.rules import Rule, RuleParam, RuleSeverity, SeverityThreshold


def get_message_with_id_sev(rule_id, sev):
    for severity in RuleSeverity:
        rule_id = rule_id.replace(severity.value, "")
    return Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0101",
        name=f"some-message-{rule_id}",
        msg="Some description",
        severity=sev,
    )


class TestThresholds:
    @pytest.mark.parametrize(
        "threshold, included, excluded",
        [
            ("E", ["E"], ["I", "W"]),
            ("W", ["E", "W"], ["I"]),
            ("I", ["E", "W", "I"], []),
        ],
    )
    def test_disable_rules_below_threshold(self, threshold, included, excluded, robocop_pre_load):
        robocop_pre_load.config.threshold = RuleSeverity(threshold)
        for severity in included:
            msg = get_message_with_id_sev("0101", severity)
            assert robocop_pre_load.config.is_rule_enabled(msg)
        for severity in excluded:
            msg = get_message_with_id_sev("0101", severity)
            assert not robocop_pre_load.config.is_rule_enabled(msg)


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

    def test_invalid_threshold_config(self):
        thresholds = SeverityThreshold("line_length")
        exp_error = (
            "Invalid severity value 'error'. " "It should be list of `severity=param_value` pairs, separated by `:`."
        )
        with pytest.raises(robocop.exceptions.InvalidArgumentError, match=exp_error):
            thresholds.value = "error"
        exp_error = "Invalid severity value 'invalid'. Choose one from: I, W, E"
        with pytest.raises(robocop.exceptions.InvalidArgumentError, match=exp_error):
            thresholds.value = "invalid=100"
