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
        assert rule_matcher._is_rule_disabled(msg)  # noqa: SLF001
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

    def test_check_matched_rules_rule_ids(self, capsys):
        select = ["0101"]
        extend_select = ["0102"]
        ignore = ["0103"]
        fixable = ["0104"]
        unfixable = ["0105"]
        rule_matcher = RuleMatcher(
            select=select,
            extend_select=extend_select,
            ignore=ignore,
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=fixable,
            unfixable=unfixable,
        )

        # Check without checking any rule - so nothing should be matched
        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert "Option value '0101' from '--select' did not match with any rule name or id" in err
        assert "Option value '0102' from '--extend-select' did not match with any rule name or id" in err
        assert "Option value '0103' from '--ignore' did not match with any rule name or id" in err
        assert "Option value '0104' from '--fixable' did not match with any rule name or id" not in err
        assert "Option value '0105' from '--unfixable' did not match with any rule name or id" not in err

        # Match --select and --ignore. It should not be present anymore in the error message
        rule_matcher.is_rule_enabled(get_enabled_rule("0101"))
        rule_matcher.is_rule_enabled(get_enabled_rule("0103"))

        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert "Option value '0101' from '--select' did not match with any rule name or id" not in err
        assert "Option value '0102' from '--extend-select' did not match with any rule name or id" in err
        assert "Option value '0103' from '--ignore' did not match with any rule name or id" not in err
        assert "Option value '0104' from '--fixable' did not match with any rule name or id" not in err
        assert "Option value '0105' from '--unfixable' did not match with any rule name or id" not in err

        # Match with remaining rules - nothing should be printed
        rule_matcher.is_rule_enabled(get_enabled_rule("0102"))
        rule_matcher.is_rule_fixable(get_fixable_message_with_id("0104"))
        rule_matcher.is_rule_fixable(get_fixable_message_with_id("0105"))
        rule_matcher.is_rule_enabled(get_enabled_rule("0106"))  # extra, not in filters

        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert not err

    def test_check_matched_rules_rule_names(self, capsys):
        select = ["some-message-0101"]
        extend_select = ["some-message-0102"]
        ignore = ["some-message-0103"]
        fixable = ["some-message-0104"]
        unfixable = ["some-message-0105"]
        rule_matcher = RuleMatcher(
            select=select,
            extend_select=extend_select,
            ignore=ignore,
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=fixable,
            unfixable=unfixable,
        )

        # Check without checking any rule - so nothing should be matched
        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert "Option value 'some-message-0101' from '--select' did not match with any rule name or id" in err
        assert "Option value 'some-message-0102' from '--extend-select' did not match with any rule name or id" in err
        assert "Option value 'some-message-0103' from '--ignore' did not match with any rule name or id" in err
        assert "Option value 'some-message-0104' from '--fixable' did not match with any rule name or id" not in err
        assert "Option value 'some-message-0105' from '--unfixable' did not match with any rule name or id" not in err

        # Match --select, --fixable and --ignore. It should not be present anymore in the error message
        rule_matcher.is_rule_enabled(get_enabled_rule("some-message-0101"))
        rule_matcher.is_rule_enabled(get_enabled_rule("some-message-0103"))
        rule_matcher.is_rule_fixable(get_fixable_message_with_id("some-message-0104"))

        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert "Option value 'some-message-0101' from '--select' did not match with any rule name or id" not in err
        assert "Option value 'some-message-0102' from '--extend-select' did not match with any rule name or id" in err
        assert "Option value 'some-message-0103' from '--ignore' did not match with any rule name or id" not in err
        assert "Option value 'some-message-0104' from '--fixable' did not match with any rule name or id" not in err
        assert "Option value 'some-message-0105' from '--unfixable' did not match with any rule name or id" not in err

        # Match with remaining rules - nothing should be printed
        rule_matcher.is_rule_enabled(get_enabled_rule("0102"))
        rule_matcher.is_rule_fixable(get_fixable_message_with_id("0105"))
        rule_matcher.is_rule_enabled(get_enabled_rule("0106"))  # extra, not in filters

        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert not err

    def test_check_matched_rules_rule_patterns(self, capsys):
        select = ["some-message-0*01"]
        extend_select = ["some-*essage-0102"]
        ignore = ["some-message-0103"]
        fixable = ["some-message-*104"]
        unfixable = ["010*"]
        rule_matcher = RuleMatcher(
            select=select,
            extend_select=extend_select,
            ignore=ignore,
            target_version=ROBOT_VERSION,
            threshold=RuleSeverity.INFO,
            fixable=fixable,
            unfixable=unfixable,
        )

        # Check without checking any rule - so nothing should be matched
        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert "Option value 'some-message-0*01' from '--select' did not match with any rule name or id" in err
        assert "Option value 'some-*essage-0102' from '--extend-select' did not match with any rule name or id" in err
        assert "Option value 'some-message-0103' from '--ignore' did not match with any rule name or id" in err
        assert "Option value 'some-message-*104' from '--fixable' did not match with any rule name or id" not in err
        assert "Option value '010*' from '--unfixable' did not match with any rule name or id" not in err

        # Match --select and --ignore. It should not be present anymore in the error message
        rule_matcher.is_rule_enabled(get_enabled_rule("some-message-0*01"))
        rule_matcher.is_rule_enabled(get_enabled_rule("some-message-0103"))

        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert "Option value 'some-message-0*01' from '--select' did not match with any rule name or id" not in err
        assert "Option value 'some-*essage-0102' from '--extend-select' did not match with any rule name or id" in err
        assert "Option value 'some-message-0103' from '--ignore' did not match with any rule name or id" not in err
        assert "Option value 'some-message-*104' from '--fixable' did not match with any rule name or id" not in err
        assert "Option value '010*' from '--unfixable' did not match with any rule name or id" not in err

        # Match with remaining rules - nothing should be printed
        rule_matcher.is_rule_enabled(get_enabled_rule("0102"))
        rule_matcher.is_rule_fixable(get_fixable_message_with_id("0104"))
        rule_matcher.is_rule_fixable(get_fixable_message_with_id("0105"))
        rule_matcher.is_rule_enabled(get_enabled_rule("0106"))  # extra, not in filters

        rule_matcher.check_unmatched_filters()
        _, err = capsys.readouterr()
        assert err == ""
