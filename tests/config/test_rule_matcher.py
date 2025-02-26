import pytest

from robocop.config import Config, LinterConfig
from robocop.linter.rules import Rule, RuleSeverity, replace_severity_values
from robocop.linter.runner import RuleMatcher


def get_message_with_id(rule_id):
    rule_id = replace_severity_values(rule_id)
    return Rule(rule_id=rule_id, name=f"some-message-{rule_id}", msg="Some description", severity=RuleSeverity.WARNING)


class TestIncludingExcluding:
    @pytest.mark.parametrize(
        ("included", "excluded"),
        [
            (["0101"], ["0102", "0501", "0402"]),
            (["W0101", "0102"], ["0501", "0402"]),
            (["E0501", "I0402"], ["0101", "0102"]),
        ],
    )
    def test_only_included(self, included, excluded):
        linter_config = LinterConfig(include=included, exclude=excluded)
        config = Config(linter=linter_config)
        rule_matcher = RuleMatcher(config)
        assert all(rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    @pytest.mark.parametrize(
        ("patterns", "included", "excluded"),
        [
            (["01*"], [], ["0202", "0501", "0403"]),
            (["01*", "*5"], ["0101", "0105", "0405"], ["0204", "0402"]),
            (["some-message-04*"], ["0401"], ["0101", "0502"]),
            (["*"], ["0101", "0105", "0204", "0405", "0405"], []),
        ],
    )
    def test_only_included_patterns(self, patterns, included, excluded):
        linter_config = LinterConfig(include=patterns)
        config = Config(linter=linter_config)
        rule_matcher = RuleMatcher(config)
        assert all(rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    @pytest.mark.parametrize(
        ("included", "excluded"),
        [
            (["0101"], ["0102", "0501", "0402"]),
            (["W0101", "0102"], ["0501", "0402"]),
            (["E0501", "I0402"], ["0101", "0102"]),
        ],
    )
    def test_only_excluded(self, included, excluded):
        linter_config = LinterConfig(exclude=excluded)
        config = Config(linter=linter_config)
        rule_matcher = RuleMatcher(config)
        assert all(rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    @pytest.mark.parametrize(
        ("patterns", "included", "excluded"),
        [
            (["01*"], ["0204", "0405", "0405"], ["0101", "0105"]),
            (["01*", "*5"], ["0204"], ["0101", "0105", "0405", "0405"]),
            (["some-message-04*"], ["0101", "0105", "0204"], ["0405", "0405"]),
            (["*"], [], ["0101", "0105", "0204", "0405", "0405"]),
        ],
    )
    def test_only_excluded_patterns(self, patterns, included, excluded):
        """
        Test data contains rules with rule id's "0101", "0105", "0204", "0405", "0405"
        and rule names created using `some-message-{rule_id}` pattern
        """
        linter_config = LinterConfig(exclude=excluded)
        config = Config(linter=linter_config)
        rule_matcher = RuleMatcher(config)
        assert all(rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not rule_matcher.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    def test_both_included_excluded(self):
        linter_config = LinterConfig(include=["0101"], exclude=["W0101"])
        config = Config(linter=linter_config)
        rule_matcher = RuleMatcher(config)
        msg = get_message_with_id("0101")
        assert rule_matcher.is_rule_disabled(msg)
        assert not rule_matcher.is_rule_enabled(msg)
