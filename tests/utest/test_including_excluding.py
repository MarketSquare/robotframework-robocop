import pytest

from robocop.rules import RuleSeverity, Rule


def get_message_with_id(rule_id):
    for char in RuleSeverity:
        rule_id = rule_id.replace(char.value, "")
    msg = (f"some-message-{rule_id}", "Some description", RuleSeverity.WARNING)
    return Rule(rule_id, msg)


class TestIncludingExcluding:
    @pytest.mark.parametrize(
        "included, excluded",
        [
            (["0101"], ["0102", "0501", "0402"]),
            (["W0101", "0102"], ["0501", "0402"]),
            (["E0501", "I0402"], ["0101", "0102"]),
        ],
    )
    def test_only_included(self, included, excluded, robocop_pre_load):
        robocop_pre_load.config.include.update(set(included))
        robocop_pre_load.config.remove_severity()
        robocop_pre_load.config.translate_patterns()
        assert all(robocop_pre_load.config.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not robocop_pre_load.config.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    @pytest.mark.parametrize(
        "patterns, included, excluded",
        [
            (["01*"], [], ["0202", "0501", "0403"]),
            (["01*", "*5"], ["0101", "0105", "0405"], ["0204", "0402"]),
            (["some-message-04*"], ["0401"], ["0101", "0502"]),
        ],
    )
    def test_only_included_patterns(self, patterns, included, excluded, robocop_pre_load):
        robocop_pre_load.config.include.update(set(patterns))
        robocop_pre_load.config.remove_severity()
        robocop_pre_load.config.translate_patterns()
        assert all(robocop_pre_load.config.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not robocop_pre_load.config.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    @pytest.mark.parametrize(
        "included, excluded",
        [
            (["0101"], ["0102", "0501", "0402"]),
            (["W0101", "0102"], ["0501", "0402"]),
            (["E0501", "I0402"], ["0101", "0102"]),
        ],
    )
    def test_only_excluded(self, included, excluded, robocop_pre_load):
        robocop_pre_load.config.exclude.update(set(excluded))
        robocop_pre_load.config.remove_severity()
        robocop_pre_load.config.translate_patterns()
        assert all(robocop_pre_load.config.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not robocop_pre_load.config.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    def test_both_included_excluded(self, robocop_pre_load):
        robocop_pre_load.config.include = {"0101"}
        robocop_pre_load.config.exclude = {"W0101"}
        robocop_pre_load.config.remove_severity()
        robocop_pre_load.config.translate_patterns()
        msg = get_message_with_id("0101")
        assert robocop_pre_load.config.is_rule_disabled(msg)
        assert not robocop_pre_load.config.is_rule_enabled(msg)
