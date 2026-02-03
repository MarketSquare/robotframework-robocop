import textwrap
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from robocop.config.parser import TargetVersion
from robocop.linter.rules import Rule, RuleSeverity
from robocop.linter.rules_list import RuleFilter
from robocop.run import list_rules
from robocop.runtime.resolver import ConfigResolver
from robocop.version_handling import ROBOT_VERSION
from tests import working_directory

TEST_DATA = Path(__file__).parent.parent / "test_data" / "custom_rules"


class CustomRule(Rule):
    rule_id = "0101"
    name = "some-message"
    message = "Some description"
    severity = RuleSeverity.WARNING


def get_mocked_rule(rule_id: str, **kwargs) -> Rule:
    rule = CustomRule()
    rule.rule_id = rule_id
    for name, value in kwargs.items():
        setattr(rule, name, value)
    rule.load_config()
    return rule


def get_resolved_config(*rules: Rule) -> Mock:
    rule_container = {rule.rule_id: rule for rule in rules}
    mocked_config = Mock()
    mocked_config.rules = rule_container
    return mocked_config


@pytest.fixture
def rule_0101() -> Rule:
    return get_mocked_rule(rule_id="0101")


@pytest.fixture
def rule_0102() -> Rule:
    return get_mocked_rule(
        rule_id="0102", name="other-message", message="this is description", severity=RuleSeverity.ERROR, enabled=False
    )


@pytest.fixture
def rule_0204() -> Rule:
    return get_mocked_rule(rule_id="0204", name="another-message", message=f"Message with meaning {4}")


@pytest.fixture
def rule_non_default() -> Rule:
    return get_mocked_rule(rule_id="19999", name="non-default-rule", enabled=False)


@pytest.fixture
def rule_deprecated() -> Rule:
    return get_mocked_rule(
        rule_id="9991", name="deprecated-rule", message="Deprecated rule", severity=RuleSeverity.ERROR, deprecated=True
    )


@pytest.fixture
def rule_deprecated_disabled() -> Rule:
    return get_mocked_rule(
        rule_id="9992",
        name="deprecated-disabled-rule",
        message="Deprecated and disabled rule",
        severity=RuleSeverity.INFO,
        deprecated=True,
        enabled=False,
    )


@pytest.fixture
def rule_disabled_after_4() -> Rule:
    return get_mocked_rule(
        rule_id="9999", name="disabled-in-four", message="This is desc", severity=RuleSeverity.WARNING, version="<4.0"
    )


@pytest.fixture
def rule_future() -> Rule:
    return get_mocked_rule(
        rule_id="FUT01", name="enabled-in-future", message="This is desc", severity=RuleSeverity.WARNING, version=">=20"
    )


class TestListingRules:
    def test_list_rule(self, capsys, tmp_path, rule_0101, rule_non_default, rule_deprecated, rule_deprecated_disabled):
        """List rules with default options."""
        mocked_config = get_resolved_config(rule_0101, rule_non_default, rule_deprecated, rule_deprecated_disabled)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config

        with (
            working_directory(tmp_path),
            patch("robocop.run.ConfigResolver", resolver_mock),
        ):
            list_rules()
        out, _ = capsys.readouterr()
        assert (
            out == "0101 [W]: some-message: Some description (enabled)\n"
            "19999 [W]: non-default-rule: Some description (disabled)\n\n"
            "Altogether 2 rules (1 enabled).\n\n"
            "Visit https://robocop.dev/stable/rules_list/ page for detailed documentation.\n"
        )

    def test_list_disabled_rule(self, rule_0101, rule_disabled_after_4, capsys):
        rule_0101.enabled = False
        mocked_config = get_resolved_config(rule_0101, rule_disabled_after_4)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config

        if ROBOT_VERSION.major >= 4:
            enabled_count = 0
            enabled_for = "disabled - supported only for RF version <4.0"
        else:
            enabled_count = 1
            enabled_for = "enabled"
        with patch("robocop.run.ConfigResolver", resolver_mock):
            list_rules(filter_pattern="*")
        out, _ = capsys.readouterr()
        assert (
            out == "0101 [W]: some-message: Some description (disabled)\n"
            f"9999 [W]: disabled-in-four: This is desc ({enabled_for})\n\n"
            f"Altogether 2 rules ({enabled_count} enabled).\n\n"
            "Visit https://robocop.dev/stable/rules_list/ page for detailed documentation.\n"
        )

    def test_list_filter_enabled(self, rule_0101, rule_non_default, capsys):
        mocked_config = get_resolved_config(rule_0101, rule_non_default)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config
        with patch("robocop.run.ConfigResolver", resolver_mock):
            list_rules(filter_category=RuleFilter.ENABLED)
        out, _ = capsys.readouterr()
        assert (
            out == "0101 [W]: some-message: Some description (enabled)\n\n"
            "Altogether 1 rule (1 enabled).\n\n"
            "Visit https://robocop.dev/stable/rules_list/ page for detailed documentation.\n"
        )

    def test_list_filter_disabled(self, rule_0101, rule_non_default, capsys):
        mocked_config = get_resolved_config(rule_0101, rule_non_default)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config
        with patch("robocop.run.ConfigResolver", resolver_mock):
            list_rules(filter_category=RuleFilter.DISABLED)
        out, _ = capsys.readouterr()
        assert (
            out == "19999 [W]: non-default-rule: Some description (disabled)\n\n"
            "Altogether 1 rule (0 enabled).\n\n"
            "Visit https://robocop.dev/stable/rules_list/ page for detailed documentation.\n"
        )

    def test_list_filter_deprecated(self, rule_0101, rule_deprecated, rule_deprecated_disabled, capsys):
        mocked_config = get_resolved_config(rule_0101, rule_deprecated, rule_deprecated_disabled)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config
        with patch("robocop.run.ConfigResolver", resolver_mock):
            list_rules(filter_category=RuleFilter.DEPRECATED)
        out, _ = capsys.readouterr()
        assert (
            out == "9991 [E]: deprecated-rule: Deprecated rule (deprecated)\n"
            "9992 [I]: deprecated-disabled-rule: Deprecated and disabled rule (deprecated)\n\n"
            "Altogether 2 rules (0 enabled).\n\n"
            "Visit https://robocop.dev/stable/rules_list/ page for detailed documentation.\n"
        )

    def test_list_filtered(self, rule_0101, rule_deprecated, rule_0102, rule_0204, capsys):
        mocked_config = get_resolved_config(rule_0101, rule_0102, rule_0204, rule_deprecated)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config
        with patch("robocop.run.ConfigResolver", resolver_mock):
            list_rules(filter_pattern="01*")
        out, _ = capsys.readouterr()
        exp_msg = (
            "0101 [W]: some-message: Some description (enabled)\n",
            "0102 [E]: other-message: this is description (disabled)\n",
        )
        not_exp_msg = "0204 [I]: another-message: Message with meaning 4 (disabled)\n"
        assert all(msg in out for msg in exp_msg)
        assert not_exp_msg not in out

    @pytest.mark.parametrize("config", [{"filter_pattern": "*"}, {"filter_category": RuleFilter.ALL}])
    def test_list_rule_filtered_and_non_default(self, config, rule_0101, rule_non_default, capsys):
        mocked_config = get_resolved_config(rule_0101, rule_non_default)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config
        with patch("robocop.run.ConfigResolver", resolver_mock):
            list_rules(**config)
        out, _ = capsys.readouterr()
        assert (
            out == "0101 [W]: some-message: Some description (enabled)\n"
            "19999 [W]: non-default-rule: Some description (disabled)\n\n"
            "Altogether 2 rules (1 enabled).\n\n"
            "Visit https://robocop.dev/stable/rules_list/ page for detailed documentation.\n"
        )

    def test_list_with_target_version(self, rule_0101, rule_future, capsys):
        mocked_config = get_resolved_config(rule_0101, rule_future)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config
        with patch("robocop.run.ConfigResolver", resolver_mock):
            list_rules(target_version=TargetVersion(str(ROBOT_VERSION.major)))
        out, _ = capsys.readouterr()
        expected = textwrap.dedent("""
        0101 [W]: some-message: Some description (enabled)
        FUT01 [W]: enabled-in-future: This is desc (disabled - supported only for RF version >=20)

        Altogether 2 rules (1 enabled).

        Visit https://robocop.dev/stable/rules_list/ page for detailed documentation.
        """).lstrip()
        assert out == expected

    def test_list_with_return_result(
        self, rule_0101, rule_non_default, rule_deprecated, rule_deprecated_disabled, tmp_path
    ):
        # arrange
        mocked_config = get_resolved_config(rule_0101, rule_non_default, rule_deprecated, rule_deprecated_disabled)
        resolver_mock = Mock(spec=ConfigResolver)
        resolver_instance_mock = Mock()
        resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_config.return_value = mocked_config
        # act
        with (
            working_directory(tmp_path),
            patch("robocop.run.ConfigResolver", resolver_mock),
        ):
            result_no_return = list_rules()
            result_with_return = list_rules(return_result=True)
        # assert
        assert result_no_return is None
        assert len(result_with_return) == 2
        assert result_with_return[0].rule_id == "0101"
        assert result_with_return[0].enabled is True
        assert result_with_return[1].rule_id == "19999"
        assert result_with_return[1].enabled is False

    # def test_list_custom_rules_disabled_by_default(self, empty_linter, capsys):  # TODO
    #     empty_linter.config.custom_rules = {
    #         str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
    #         str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
    #     }
    #     empty_linter.load_checkers()
    #     with patch("robocop.config_manager.ConfigManager", MagicMock(return_value=empty_linter.config_manager)):
    #         list_rules(filter_pattern="*")
    #     out, _ = capsys.readouterr()
    #     exp_msg = (
    #         "1101 [E]: smth: Keyword call after [Return] statement (enabled)\n",
    #         "1102 [E]: smth2: Keyword call after [Return] statement (disabled)\n",
    #     )
    #     assert all(msg in out for msg in exp_msg)

    # def test_list_custom_rules_disabled_by_default_enable(self, empty_linter, capsys):  # TODO
    #     empty_linter.config.custom_rules = {
    #         str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
    #         str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
    #     }
    #     empty_linter.config.include = {"1102"}
    #     empty_linter.load_checkers()
    #     empty_linter.check_for_disabled_rules()
    #     with patch("robocop.config.ConfigManager", MagicMock(return_value=empty_linter.config_manager)):
    #         list_rules(filter_pattern="*")
    #     out, _ = capsys.readouterr()
    #     exp_msg = (
    #         "1101 [E]: smth: Keyword call after [Return] statement (disabled)\n",
    #         "1102 [E]: smth2: Keyword call after [Return] statement (enabled)\n",
    #     )
    #     assert all(msg in out for msg in exp_msg)
