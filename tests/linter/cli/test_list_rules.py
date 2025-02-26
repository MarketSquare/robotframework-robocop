from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from robocop.cli import list_rules
from robocop.linter.rules import Rule, RuleFilter, RuleSeverity, VisitorChecker
from robocop.linter.utils.misc import ROBOT_VERSION

TEST_DATA = Path(__file__).parent.parent / "test_data" / "ext_rules"


# @pytest.fixture
# def msg_0101_config():
#     return {
#         "0101": Rule(
#             RuleParam(name="conf_param", converter=int, default=0, desc=""),
#             rule_id="0101",
#             name="some-message",
#             msg="Some description",
#             severity=RuleSeverity.WARNING,
#         )
#     }


def example_parser(value):
    return value


# @pytest.fixture
# def msg_0101_config_meta():
#     return {
#         "0101": Rule(
#             RuleParam(name="conf_param", converter=int, default=0, desc=""),
#             RuleParam(name="conf_param2", converter=example_parser, default=0, desc="meta information"),
#             rule_id="0101",
#             name="some-message",
#             msg="Some description",
#             severity=RuleSeverity.WARNING,
#         )
#     }


# @pytest.fixture
# def msg_0102_0204_checker_config():
#     return {
#         "0102": Rule(
#             RuleParam(name="conf_param1", converter=int, default=0, desc=""),
#             rule_id="0102",
#             name="other-message",
#             msg="""this is description""",
#             severity=RuleSeverity.ERROR,
#         ),
#         "0204": Rule(
#             RuleParam(name="conf_param2", converter=int, default=0, desc=""),
#             rule_id="0204",
#             name="another-message",
#             msg=f"Message with meaning {4}",
#             severity=RuleSeverity.INFO,
#         ),
#     }


@pytest.fixture
def msg_0101_checker():
    class CustomRule(Rule):
        rule_id = "0101"
        name = "some-message"
        message = "Some description"
        severity = RuleSeverity.WARNING

    class CustomVisitor(VisitorChecker):
        custom_rule: CustomRule

    checker = CustomVisitor()
    rule = CustomRule()
    checker.rules[rule.name] = rule
    checker.rules[rule.rule_id] = rule
    return checker


@pytest.fixture
def non_default_rule_checker():
    class CustomRule(Rule):
        rule_id = "19999"
        name = "non-default-rule"
        message = "Some description"
        severity = RuleSeverity.WARNING
        enabled = False

    class NonDefaultChecker(VisitorChecker):
        non_default_rule: CustomRule

    checker = NonDefaultChecker()
    rule = CustomRule()
    checker.rules[rule.name] = rule
    checker.rules[rule.rule_id] = rule
    return checker


@pytest.fixture
def msg_0102_0204_checker():
    class CustomRule(Rule):
        rule_id = "0102"
        name = "other-message"
        message = """this is description"""
        severity = RuleSeverity.ERROR

    class CustomRule2(Rule):
        rule_id = "0204"
        name = "another-message"
        message = f"Message with meaning {4}"
        severity = RuleSeverity.INFO

    class CustomVisitor(VisitorChecker):
        custom_rule: CustomRule
        custom_rule2: CustomRule2

    checker = CustomVisitor()
    rule = CustomRule()
    rule2 = CustomRule2()
    checker.rules[rule.name] = rule
    checker.rules[rule.rule_id] = rule
    checker.rules[rule2.name] = rule2
    checker.rules[rule2.rule_id] = rule2
    return checker


@pytest.fixture
def disabled_for_4_checker():
    class DisabledFor4(Rule):
        rule_id = "9999"
        name = "disabled-in-four"
        message = "This is desc"
        severity = RuleSeverity.WARNING
        version = "<4.0"

    class DisabledChecker(VisitorChecker):
        disabled_rule: DisabledFor4

    checker = DisabledChecker()
    rule = DisabledFor4()
    checker.rules[rule.name] = rule
    checker.rules[rule.rule_id] = rule
    return checker


@pytest.fixture
def deprecated_rules_checker():
    class DeprecatedRule(Rule):
        rule_id = "9991"
        name = "deprecated-rule"
        message = "Deprecated rule"
        severity = RuleSeverity.ERROR
        deprecated = True

    class DeprecatedRule2(Rule):
        rule_id = "9992"
        name = "deprecated-disabled-rule"
        message = "Deprecated and disabled rule"
        severity = RuleSeverity.INFO
        deprecated = True
        enabled = False

    class DeprecatedChecker(VisitorChecker):
        deprecated_rule: DeprecatedRule
        deprecated_rule2: DeprecatedRule2

    checker = DeprecatedChecker()  # TODO: improve mocking
    rule = DeprecatedRule()
    rule2 = DeprecatedRule2()
    checker.rules[rule.name] = rule
    checker.rules[rule.rule_id] = rule
    checker.rules[rule2.name] = rule2
    checker.rules[rule2.rule_id] = rule2
    return checker


class TestListingRules:
    def test_list_rule(
        self, empty_linter, msg_0101_checker, non_default_rule_checker, deprecated_rules_checker, capsys
    ):
        """List rules with default options."""
        for checker in (msg_0101_checker, non_default_rule_checker, deprecated_rules_checker):
            empty_linter.config.linter.register_checker(checker)
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_rules()
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (enabled)\n\n"
            "Altogether 1 rule with following severity:\n"
            "    0 error rules,\n"
            "    1 warning rule,\n"
            "    0 info rules.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    # should first load config (with excludes), then set enable/disable inside rule
    def test_list_disabled_rule(self, empty_linter, msg_0101_checker, disabled_for_4_checker, capsys):
        empty_linter.config.linter.register_checker(msg_0101_checker)
        empty_linter.config.linter.register_checker(disabled_for_4_checker)
        empty_linter.config.linter.exclude_rules = {"0101"}
        empty_linter.config.linter.check_for_disabled_rules()
        if ROBOT_VERSION.major >= 4:
            enabled_for = "disabled - supported only for RF version <4.0"
        else:
            enabled_for = "enabled"
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_rules(filter_pattern="*")
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (disabled)\n"
            f"Rule - 9999 [W]: disabled-in-four: This is desc ({enabled_for})\n\n"
            "Altogether 2 rules with following severity:\n"
            "    0 error rules,\n"
            "    2 warning rules,\n"
            "    0 info rules.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    def test_list_filter_enabled(self, empty_linter, msg_0101_checker, msg_0102_0204_checker, capsys):
        empty_linter.config.linter.register_checker(msg_0101_checker)
        empty_linter.config.linter.register_checker(msg_0102_0204_checker)
        empty_linter.config.linter.exclude_rules = {"0102", "0204"}
        empty_linter.config.linter.check_for_disabled_rules()

        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_rules(filter_category=RuleFilter.ENABLED)
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (enabled)\n\n"
            "Altogether 1 rule with following severity:\n"
            "    0 error rules,\n"
            "    1 warning rule,\n"
            "    0 info rules.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    def test_list_filter_disabled(
        self, empty_linter, msg_0101_checker, msg_0102_0204_checker, deprecated_rules_checker, capsys
    ):
        empty_linter.config.linter.register_checker(msg_0101_checker)
        empty_linter.config.linter.register_checker(msg_0102_0204_checker)
        empty_linter.config.linter.register_checker(deprecated_rules_checker)
        empty_linter.config.linter.exclude_rules = {"0102", "0204"}
        empty_linter.config.linter.check_for_disabled_rules()
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_rules(filter_category=RuleFilter.DISABLED)
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0102 [E]: other-message: this is description (disabled)\n"
            "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n\n"
            "Altogether 2 rules with following severity:\n"
            "    1 error rule,\n"
            "    0 warning rules,\n"
            "    1 info rule.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    def test_list_filter_deprecated(
        self, empty_linter, msg_0101_checker, msg_0102_0204_checker, deprecated_rules_checker, capsys
    ):
        empty_linter.config.linter.register_checker(msg_0101_checker)
        empty_linter.config.linter.register_checker(msg_0102_0204_checker)
        empty_linter.config.linter.register_checker(deprecated_rules_checker)
        empty_linter.config.linter.exclude_rules = {"0102", "0204"}
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_rules(filter_category=RuleFilter.DEPRECATED)
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 9991 [E]: deprecated-rule: Deprecated rule (deprecated)\n"
            "Rule - 9992 [I]: deprecated-disabled-rule: Deprecated and disabled rule (deprecated)\n\n"
            "Altogether 2 rules with following severity:\n"
            "    1 error rule,\n"
            "    0 warning rules,\n"
            "    1 info rule.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    def test_multiple_checkers(self, empty_linter, msg_0101_checker, msg_0102_0204_checker, capsys):
        empty_linter.config.linter.register_checker(msg_0101_checker)
        empty_linter.config.linter.register_checker(msg_0102_0204_checker)
        empty_linter.config.linter.exclude_rules = {"0102", "0204"}
        empty_linter.config.linter.check_for_disabled_rules()
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_rules(filter_pattern="*")
        out, _ = capsys.readouterr()
        exp_msg = (
            "Rule - 0101 [W]: some-message: Some description (enabled)\n",
            "Rule - 0102 [E]: other-message: this is description (disabled)\n",
            "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n",
        )
        assert all(msg in out for msg in exp_msg)

    def test_list_filtered(
        self, empty_linter, msg_0101_checker, msg_0102_0204_checker, deprecated_rules_checker, capsys
    ):
        empty_linter.config.linter.register_checker(msg_0101_checker)
        empty_linter.config.linter.register_checker(msg_0102_0204_checker)
        empty_linter.config.linter.register_checker(deprecated_rules_checker)
        empty_linter.config.linter.exclude_rules = {"0102", "0204"}
        empty_linter.config.linter.check_for_disabled_rules()
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_rules(filter_pattern="01*")
        out, _ = capsys.readouterr()
        exp_msg = (
            "Rule - 0101 [W]: some-message: Some description (enabled)\n",
            "Rule - 0102 [E]: other-message: this is description (disabled)\n",
        )
        not_exp_msg = "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n"
        assert all(msg in out for msg in exp_msg)
        assert not_exp_msg not in out

    @pytest.mark.parametrize("config", [{"filter_pattern": "*"}, {"filter_category": RuleFilter.ALL}])
    def test_list_rule_filtered_and_non_default(
        self, config, empty_linter, msg_0101_checker, non_default_rule_checker, capsys
    ):
        empty_linter.config.linter.register_checker(msg_0101_checker)
        empty_linter.config.linter.register_checker(non_default_rule_checker)
        with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
            list_rules(**config)
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (enabled)\n"
            "Rule - 19999 [W]: non-default-rule: Some description (disabled)\n\n"
            "Altogether 2 rules with following severity:\n"
            "    0 error rules,\n"
            "    2 warning rules,\n"
            "    0 info rules.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    # def test_list_configurables(self, empty_linter, msg_0101_checker_config_meta, capsys):  # TODO
    #     empty_linter.config.list_configurables = robocop.config.translate_pattern("*")
    #     add_empty_checker(empty_linter, msg_0101_checker_config_meta, conf_param=1001)
    #     with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
    #         list_rules(filter_pattern="*")
    #     out, _ = capsys.readouterr()
    #     assert (
    #         out == "All rules have configurable parameter 'severity'. "
    #         "Allowed values are:\n    E / error\n    W / warning\n    I / info\n\n"
    #         "Rule - 0101 [W]: some-message: Some description (enabled)\n"
    #         "    conf_param = 0\n"
    #         "        type: int\n"
    #         "    conf_param2 = 0\n"
    #         "        type: example_parser\n"
    #         "        info: meta information\n\n"
    #         "Altogether 1 rule with following severity:\n"
    #         "    0 error rules,\n"
    #         "    1 warning rule,\n"
    #         "    0 info rules.\n\n"
    #         "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
    #     )

    # def test_list_configurables_filtered(self, empty_linter, msg_0101_checker_config, msg_0102_0204_checker_config,
    # capsys):  # TODO
    #     empty_linter.config.list_configurables = "another-message"
    #     add_empty_checker(empty_linter, msg_0102_0204_checker_config, exclude=True)
    #     add_empty_checker(empty_linter, msg_0101_checker_config)
    #     with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
    #         list_rules(filter_category=RuleFilter.DISABLED)
    #     out, _ = capsys.readouterr()
    #     not_exp_msg = (
    #         "Rule - 0101 [W]: some-message: Some description (enabled)\n",
    #         "Rule - 0102 [E]: other-message: this is description (disabled)\n",
    #     )
    #     exp_msg = "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n"
    #     assert all(msg not in out for msg in not_exp_msg)
    #     assert exp_msg in out

    # def test_list_configurables_mixed(self, empty_linter, msg_0101_checker, msg_0102_0204_checker_config,
    # capsys):  # TODO
    #     empty_linter.config.list_configurables = robocop.config.translate_pattern("*")
    #     add_empty_checker(empty_linter, msg_0102_0204_checker_config, exclude=True)
    #     add_empty_checker(empty_linter, msg_0101_checker)
    #     with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
    #         list_rules(filter_category=RuleFilter.DISABLED)
    #     out, _ = capsys.readouterr()
    #     not_exp_msg = "Rule - 0101 [W]: some-message: Some description (enabled)\n"
    #     exp_msg = (
    #         "Rule - 0102 [E]: other-message: this is description (disabled)\n",
    #         "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n",
    #     )
    #     assert not_exp_msg not in out
    #     assert all(msg in out for msg in exp_msg)

    # def test_list_configurables_no_config(self, empty_linter, msg_0101_checker_config, msg_0102_0204_checker_config,
    # capsys):  # TODO
    #     empty_linter.config.list_configurables = robocop.config.translate_pattern("*")
    #     add_empty_checker(empty_linter, msg_0102_0204_checker_config, exclude=True)
    #     add_empty_checker(empty_linter, msg_0101_checker_config)
    #     with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
    #         list_rules(filter_category=RuleFilter.DISABLED)
    #     out, _ = capsys.readouterr()
    #     exp_msg = (
    #         "Rule - 0102 [E]: other-message: this is description (disabled)\n",
    #         "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n",
    #         "Rule - 0101 [W]: some-message: Some description (enabled)\n",
    #     )
    #     assert all(msg in out for msg in exp_msg)

    # def test_list_ext_rules_disabled_by_default(self, empty_linter, capsys):  # TODO
    #     empty_linter.config.ext_rules = {
    #         str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
    #         str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
    #     }
    #     empty_linter.load_checkers()
    #     with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
    #         list_rules(filter_pattern="*")
    #     out, _ = capsys.readouterr()
    #     exp_msg = (
    #         "Rule - 1101 [E]: smth: Keyword call after [Return] statement (enabled)\n",
    #         "Rule - 1102 [E]: smth2: Keyword call after [Return] statement (disabled)\n",
    #     )
    #     assert all(msg in out for msg in exp_msg)

    # def test_list_ext_rules_disabled_by_default_enable(self, empty_linter, capsys):  # TODO
    #     empty_linter.config.ext_rules = {
    #         str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
    #         str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
    #     }
    #     empty_linter.config.include = {"1102"}
    #     empty_linter.load_checkers()
    #     empty_linter.check_for_disabled_rules()
    #     with patch("robocop.cli.RobocopLinter", MagicMock(return_value=empty_linter)):
    #         list_rules(filter_pattern="*")
    #     out, _ = capsys.readouterr()
    #     exp_msg = (
    #         "Rule - 1101 [E]: smth: Keyword call after [Return] statement (disabled)\n",
    #         "Rule - 1102 [E]: smth2: Keyword call after [Return] statement (enabled)\n",
    #     )
    #     assert all(msg in out for msg in exp_msg)
