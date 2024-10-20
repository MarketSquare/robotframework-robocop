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


def get_message_with_sev_value(rule, sev_value):
    return rule.prepare_message(
        source=None,
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
    def test_disable_rules_below_threshold(self, threshold, included, excluded, robocop_pre_load):
        robocop_pre_load.config.threshold = RuleSeverity(threshold)
        for severity in included:
            msg = get_message_with_id_sev("0101", severity)
            assert robocop_pre_load.config.is_rule_enabled(msg)
        for severity in excluded:
            msg = get_message_with_id_sev("0101", severity)
            assert not robocop_pre_load.config.is_rule_enabled(msg)


# filter messages properly - if -t E, severity threshold returns W -> should filter


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
        rule = Rule(
            RuleParam(name="param_name", converter=int, default=1, desc=""),
            SeverityThreshold("param_name", compare_method="greater"),
            rule_id="0101",
            name="some-message",
            msg="Some description",
            severity=RuleSeverity.WARNING,
        )
        rule.config["severity_threshold"].value = "W=0:E=1"
        msg_1 = get_message_with_sev_value(rule, 0)
        msg_2 = get_message_with_sev_value(rule, 1)
        msg_3 = get_message_with_sev_value(rule, 2)
        assert [msg_1.severity, msg_2.severity, msg_3.severity] == [
            RuleSeverity.WARNING,
            RuleSeverity.ERROR,
            RuleSeverity.ERROR,
        ]

    def test_invalid_threshold_config(self):
        thresholds = SeverityThreshold("line_length")
        exp_error = (
            "Invalid configuration for Robocop:\n"
            "Invalid severity value 'error'. It should be list of `severity=param_value` pairs, separated by `:`."
        )
        with pytest.raises(robocop.exceptions.InvalidArgumentError, match=exp_error):
            thresholds.value = "error"
        exp_error = "Invalid severity value 'invalid'. Choose one from: I, W, E"
        with pytest.raises(robocop.exceptions.InvalidArgumentError, match=exp_error):
            thresholds.value = "invalid=100"
