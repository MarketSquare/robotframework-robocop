import pytest
from robocop.rules import RuleSeverity, Rule


def get_severity_enum(value):
    for sev in RuleSeverity:
        if sev.value == value:
            break
    else:
        sev = RuleSeverity.INFO
    return sev


def get_message_with_id_sev(rule_id, sev):
    for c in RuleSeverity:
        rule_id = rule_id.replace(c.value, '')
    sev = get_severity_enum(sev)
    msg = (
        f"some-message-{rule_id}",
        "Some description",
        sev
    )
    return Rule(rule_id, msg)


class TestThresholds:
    @pytest.mark.parametrize('threshold, included, excluded', [
        ('E', ['E'], ['I', 'W']),
        ('W', ['E', 'W'], ['I']),
        ('I', ['E', 'W', 'I'], []),
    ])
    def test_disable_rules_below_threshold(self, threshold, included, excluded, robocop_pre_load):
        robocop_pre_load.config.threshold = get_severity_enum(threshold)
        for severity in included:
            msg = get_message_with_id_sev('0101', severity)
            assert robocop_pre_load.config.is_rule_enabled(msg)
        for severity in excluded:
            msg = get_message_with_id_sev('0101', severity)
            assert not robocop_pre_load.config.is_rule_enabled(msg)
