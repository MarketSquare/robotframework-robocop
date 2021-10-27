import pytest

from robocop.rules import Rule, RuleParam, RuleSeverity


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
