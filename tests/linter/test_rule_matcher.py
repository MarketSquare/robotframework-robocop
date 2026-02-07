import pytest

from robocop.linter.diagnostics import Diagnostic
from robocop.linter.fix import Fix, FixAvailability
from robocop.linter.rules import FixableRule, Rule, RuleSeverity
from robocop.runtime.resolver import RuleMatcher
from robocop.version_handling import ROBOT_VERSION


class CustomRule(Rule):
    rule_id = "0101"
    name = "some-message"
    message = "Some description"
    severity = RuleSeverity.WARNING


class CustomFixableRule(FixableRule):
    rule_id = "0102"
    name = "some-fixable-message"
    message = "Some description"
    severity = RuleSeverity.WARNING
    fix_availability = FixAvailability.ALWAYS

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        return None


def get_enabled_rule(rule_id: str, severity: RuleSeverity = RuleSeverity.INFO) -> CustomRule:
    custom_rule = CustomRule()
    custom_rule.rule_id = rule_id
    custom_rule.name = f"some-message-{rule_id}"
    custom_rule.severity = severity
    return custom_rule


def get_disabled_rule(rule_id: str) -> CustomRule:
    custom_rule = CustomRule()
    custom_rule.rule_id = rule_id
    custom_rule.name = f"some-message-{rule_id}"
    custom_rule.enabled = False
    return custom_rule


def get_fixable_message_with_id(rule_id: str) -> CustomFixableRule:
    custom_rule = CustomFixableRule()
    custom_rule.rule_id = rule_id
    custom_rule.name = f"some-message-{rule_id}"
    return custom_rule


class TestRuleMatcher:
    @pytest.mark.parametrize(
        ("selected", "ignored"),
        [
            (["0101"], ["0102", "0501", "0402"]),
            (["W0101", "0102"], ["0501", "0402"]),
            (["E0501", "I0402"], ["0101", "0102"]),
        ],
    )
    def test_only_selected(self, selected, ignored):
        rule_matcher = RuleMatcher(
            select=selected,
            extend_select=[],
            ignore=ignored,
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )
        assert all(rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in ignored)

    @pytest.mark.parametrize(
        ("select", "extend_select", "enabled", "not_enabled"),
        [
            # with nothing configured, default rules are enabled and non-defaults are not
            ([], [], ["SPC01", "SPC02"], ["KW02"]),
            # select only enabled selected
            (["SPC01"], [], ["SPC01"], ["SPC02", "KW02"]),
            # defaults + extend select
            ([], ["KW02"], ["SPC01", "SPC02", "KW02"], []),
            # extend allows adding on top of selected rules
            (["SPC01"], ["SPC02"], ["SPC01", "SPC02"], ["KW02"]),
            # test with rule names
            (["some-message-SPC01"], ["some-message-SPC02"], ["SPC01", "SPC02"], ["KW02"]),
            (["SPC01"], ["SPC02", "KW02"], ["SPC01", "SPC02", "KW02"], []),
        ],
    )
    def test_select_and_extend_select(self, select, extend_select, enabled, not_enabled):
        rule_matcher = RuleMatcher(
            select=select,
            extend_select=extend_select,
            ignore=[],
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )

        assert all(rule_matcher.is_rule_enabled(get_enabled_rule(rule)) for rule in enabled)
        assert all(not rule_matcher.is_rule_enabled(get_disabled_rule(rule)) for rule in not_enabled)

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
        rule_matcher = RuleMatcher(
            select=patterns,
            extend_select=[],
            ignore=ignored,
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )

        assert all(rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in ignored)

    @pytest.mark.parametrize(
        ("patterns", "selected", "ignored"),
        [
            (["01*"], [], ["0202", "0501", "0403"]),
            (["01*", "*5"], ["0101", "0105", "0405"], ["0204", "0402"]),
            (["some-message-04*"], ["0401"], ["0101", "0502"]),
            (["*"], ["0101", "0105", "0204", "0405", "0405"], []),
        ],
    )
    def test_only_extend_select_patterns(self, patterns, selected, ignored):
        rule_matcher = RuleMatcher(
            select=[],
            extend_select=patterns,
            ignore=ignored,
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )

        assert all(rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in selected)
        assert all(rule_matcher.is_rule_enabled(get_disabled_rule(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in ignored)

    @pytest.mark.parametrize(
        ("selected", "ignored"),
        [
            (["0101"], ["0102", "0501", "0402"]),
            (["W0101", "0102"], ["0501", "0402"]),
            (["E0501", "I0402"], ["0101", "0102"]),
        ],
    )
    def test_only_ignored(self, selected, ignored):
        rule_matcher = RuleMatcher(
            select=[],
            extend_select=[],
            ignore=ignored,
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )

        assert all(rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in ignored)

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
        rule_matcher = RuleMatcher(
            select=[],
            extend_select=[],
            ignore=patterns,
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )

        assert all(rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in selected)
        assert all(not rule_matcher.is_rule_enabled(get_enabled_rule(msg)) for msg in ignored)

    def test_both_selected_excluded(self):
        rule_matcher = RuleMatcher(
            select=["0101"],
            extend_select=[],
            ignore=["0101"],
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )

        msg = get_enabled_rule("0101")
        assert rule_matcher.is_rule_disabled(msg)
        assert not rule_matcher.is_rule_enabled(msg)

    def test_select_all(self):
        rule_matcher = RuleMatcher(
            select=["ALL", "0101"],
            extend_select=[],
            ignore=["0103"],
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )

        assert rule_matcher.is_rule_enabled(get_enabled_rule("0101"))
        assert rule_matcher.is_rule_enabled(get_enabled_rule("0102"))
        assert not rule_matcher.is_rule_enabled(get_enabled_rule("0103"))

    def test_fixable_unfixable_nothing_selected(self):
        rule_matcher = RuleMatcher(
            select=[],
            extend_select=[],
            ignore=[],
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=[],
        )

        assert rule_matcher.is_rule_fixable(get_enabled_rule("0101")) is False
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0102")) is True

    def test_unfixable_selected(self):
        rule_matcher = RuleMatcher(
            select=[],
            extend_select=[],
            ignore=[],
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=[],
            unfixable=["0102"],
        )

        assert rule_matcher.is_rule_fixable(get_enabled_rule("0101")) is False
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0102")) is False
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0103")) is True

    def test_fixable_selected(self):
        rule_matcher = RuleMatcher(
            select=[],
            extend_select=[],
            ignore=[],
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=["0102", "0103"],
            unfixable=[],
        )

        assert rule_matcher.is_rule_fixable(get_enabled_rule("0101")) is False
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0102")) is True
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0103")) is True
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0104")) is False

    def test_both_unfixable_fixable(self):
        rule_matcher = RuleMatcher(
            select=[],
            extend_select=[],
            ignore=[],
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=["0102", "0103"],
            unfixable=["0102"],
        )

        assert rule_matcher.is_rule_fixable(get_enabled_rule("0101")) is False
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0102")) is False
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0103")) is True
        assert rule_matcher.is_rule_fixable(get_fixable_message_with_id("0104")) is False

    @pytest.mark.parametrize(
        ("threshold", "included", "excluded"),
        [
            ("E", ["E"], ["I", "W"]),
            ("W", ["E", "W"], ["I"]),
            ("I", ["E", "W", "I"], []),
        ],
    )
    def test_disable_rules_below_threshold(self, threshold, included, excluded):
        rule_matcher = RuleMatcher(
            select=[],
            extend_select=[],
            ignore=[],
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity(threshold),
            fixable=[],
            unfixable=[],
        )

        for severity in included:
            rule = get_enabled_rule("0101", severity=RuleSeverity(severity))
            assert rule_matcher.is_rule_enabled(rule)
        for severity in excluded:
            rule = get_enabled_rule("0101", severity=RuleSeverity(severity))
            assert not rule_matcher.is_rule_enabled(rule)
