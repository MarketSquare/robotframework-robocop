import pytest

from robocop.config import LinterConfig, RuleMatcher
from robocop.linter.rules import Rule, RuleSeverity


class CustomRule(Rule):
    rule_id = "0101"
    name = "some-message"
    message = "Some description"
    severity = RuleSeverity.WARNING


def get_message_with_id(rule_id: str) -> CustomRule:
    custom_rule = CustomRule()
    custom_rule.rule_id = rule_id
    custom_rule.name = f"some-message-{rule_id}"
    return custom_rule


class TestIncludingExcluding:
    @pytest.mark.parametrize(
        ("selected", "ignored"),
        [
            (["0101"], ["0102", "0501", "0402"]),
            (["W0101", "0102"], ["0501", "0402"]),
            (["E0501", "I0402"], ["0101", "0102"]),
        ],
    )
    def test_only_selected(self, selected, ignored):
        linter_config = LinterConfig(select=selected, ignore=ignored)
        linter_config.load_configuration()
        rule_matcher = RuleMatcher(linter_config)
        assert all(rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in ignored)

    @pytest.mark.parametrize(
        ("patterns", "selected", "ignored"),
        [
            (["01*"], [], ["0202", "0501", "0403"]),
            (["01*", "*5"], ["0101", "0105", "0405"], ["0204", "0402"]),
            (["some-message-04*"], ["0401"], ["0101", "0502"]),
            (["*"], ["0101", "0105", "0204", "0405", "0405"], []),
        ],
    )
    def test_only_selected_patterns(self, patterns, selected, ignored):
        linter_config = LinterConfig(select=patterns)
        linter_config.load_configuration()
        rule_matcher = RuleMatcher(linter_config)
        assert all(rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in ignored)

    @pytest.mark.parametrize(
        ("selected", "ignored"),
        [
            (["0101"], ["0102", "0501", "0402"]),
            (["W0101", "0102"], ["0501", "0402"]),
            (["E0501", "I0402"], ["0101", "0102"]),
        ],
    )
    def test_only_ignored(self, selected, ignored):
        linter_config = LinterConfig(ignore=ignored)
        linter_config.load_configuration()
        rule_matcher = RuleMatcher(linter_config)
        assert all(rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in ignored)

    @pytest.mark.parametrize(
        ("patterns", "selected", "ignored"),
        [
            (["01*"], ["0204", "0405", "0405"], ["0101", "0105"]),
            (["01*", "*5"], ["0204"], ["0101", "0105", "0405", "0405"]),
            (["some-message-04*"], ["0101", "0105", "0204"], ["0405", "0405"]),
            (["*"], [], ["0101", "0105", "0204", "0405", "0405"]),
        ],
    )
    def test_only_ignored_patterns(self, patterns, selected, ignored):
        """
        Configure with patterns to be ignored.

        Test data contains rules with rule id's "0101", "0105", "0204", "0405", "0405"
        and rule names created using `some-message-{rule_id}` pattern
        """
        linter_config = LinterConfig(ignore=patterns)
        linter_config.load_configuration()
        rule_matcher = RuleMatcher(linter_config)
        assert all(rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in ignored)

    def test_both_selected_excluded(self):
        linter_config = LinterConfig(select=["0101"], ignore=["0101"])
        linter_config.load_configuration()
        rule_matcher = RuleMatcher(linter_config)
        msg = get_message_with_id("0101")
        assert rule_matcher.is_rule_disabled(msg)
        assert not rule_matcher.is_rule_enabled(msg)
