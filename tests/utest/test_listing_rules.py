from pathlib import Path

import pytest

import robocop.config
from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleFilter, RuleParam, RuleSeverity
from robocop.utils import ROBOT_VERSION

TEST_DATA = Path(__file__).parent.parent / "test_data" / "ext_rules"


class EmptyChecker(VisitorChecker):
    rules = {}


@pytest.fixture
def msg_0101_config():
    return {
        "0101": Rule(
            RuleParam(name="conf_param", converter=int, default=0, desc=""),
            rule_id="0101",
            name="some-message",
            msg="Some description",
            severity=RuleSeverity.WARNING,
        )
    }


def example_parser(value):
    return value


@pytest.fixture
def msg_0101_config_meta():
    return {
        "0101": Rule(
            RuleParam(name="conf_param", converter=int, default=0, desc=""),
            RuleParam(name="conf_param2", converter=example_parser, default=0, desc="meta information"),
            rule_id="0101",
            name="some-message",
            msg="Some description",
            severity=RuleSeverity.WARNING,
        )
    }


@pytest.fixture
def msg_0102_0204_config():
    return {
        "0102": Rule(
            RuleParam(name="conf_param1", converter=int, default=0, desc=""),
            rule_id="0102",
            name="other-message",
            msg="""this is description""",
            severity=RuleSeverity.ERROR,
        ),
        "0204": Rule(
            RuleParam(name="conf_param2", converter=int, default=0, desc=""),
            rule_id="0204",
            name="another-message",
            msg=f"Message with meaning {4}",
            severity=RuleSeverity.INFO,
        ),
    }


@pytest.fixture
def msg_0101():
    return {"0101": Rule(rule_id="0101", name="some-message", msg="Some description", severity=RuleSeverity.WARNING)}


@pytest.fixture
def community_rule():
    rules = {
        "19999": Rule(rule_id="19999", name="community-rule", msg="Some description", severity=RuleSeverity.WARNING)
    }
    rules["19999"].community_rule = True
    return rules


@pytest.fixture
def msg_0102_0204():
    return {
        "0102": Rule(rule_id="0102", name="other-message", msg="""this is description""", severity=RuleSeverity.ERROR),
        "0204": Rule(
            rule_id="0204", name="another-message", msg=f"Message with meaning {4}", severity=RuleSeverity.INFO
        ),
    }


@pytest.fixture
def msg_disabled_for_4():
    return {
        "9999": Rule(
            rule_id="9999", name="disabled-in-four", msg="This is desc", severity=RuleSeverity.WARNING, version="<4.0"
        )
    }


def init_empty_checker(robocop_instance_pre_load, rule, exclude=False, **kwargs):
    checker = EmptyChecker()
    checker.rules = rule
    checker.__dict__.update(**kwargs)
    if exclude:
        robocop_instance_pre_load.config.exclude.update(set(rule.keys()))
        robocop_instance_pre_load.config.translate_patterns()
    robocop_instance_pre_load.register_checker(checker)
    robocop_instance_pre_load.check_for_disabled_rules()
    return checker


class TestListingRules:
    def test_list_rule(self, robocop_pre_load, msg_0101, community_rule, capsys):
        robocop_pre_load.config.list = RuleFilter.EMPTY_PATTERN
        init_empty_checker(robocop_pre_load, msg_0101)
        init_empty_checker(robocop_pre_load, community_rule)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (enabled)\n\n"
            "Altogether 1 rule with following severity:\n"
            "    0 error rules,\n"
            "    1 warning rule,\n"
            "    0 info rules.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    def test_list_disabled_rule(self, robocop_pre_load, msg_0101, msg_disabled_for_4, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern("*")
        init_empty_checker(robocop_pre_load, msg_0101, exclude=True)
        init_empty_checker(robocop_pre_load, msg_disabled_for_4)
        if ROBOT_VERSION.major >= 4:
            enabled_for = "disabled - supported only for RF version <4.0"
        else:
            enabled_for = "enabled"
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
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

    def test_list_filter_enabled(self, robocop_pre_load, msg_0101, msg_0102_0204, capsys):
        robocop_pre_load.config.list = "ENABLED"
        init_empty_checker(robocop_pre_load, msg_0101)
        init_empty_checker(robocop_pre_load, msg_0102_0204, exclude=True)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (enabled)\n\n"
            "Altogether 1 rule with following severity:\n"
            "    0 error rules,\n"
            "    1 warning rule,\n"
            "    0 info rules.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    def test_list_filter_disabled(self, robocop_pre_load, msg_0101, msg_0102_0204, capsys):
        robocop_pre_load.config.list = "DISABLED"
        init_empty_checker(robocop_pre_load, msg_0101)
        init_empty_checker(robocop_pre_load, msg_0102_0204, exclude=True)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
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

    def test_list_reports(self, robocop_pre_load, msg_0101, capsys):
        robocop_pre_load.config.list_reports = True
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.load_reports()
        out, _ = capsys.readouterr()
        first_line = out.split("\n")[0]
        assert first_line == "Available reports:"

    def test_multiple_checkers(self, robocop_pre_load, msg_0101, msg_0102_0204, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern("*")
        init_empty_checker(robocop_pre_load, msg_0102_0204, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            "Rule - 0101 [W]: some-message: Some description (enabled)\n",
            "Rule - 0102 [E]: other-message: this is description (disabled)\n",
            "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n",
        )
        assert all(msg in out for msg in exp_msg)

    def test_list_filtered(self, robocop_pre_load, msg_0101, msg_0102_0204, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern("01*")
        init_empty_checker(robocop_pre_load, msg_0102_0204, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            "Rule - 0101 [W]: some-message: Some description (enabled)\n",
            "Rule - 0102 [E]: other-message: this is description (disabled)\n",
        )
        not_exp_msg = "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n"
        assert all(msg in out for msg in exp_msg)
        assert not_exp_msg not in out

    @pytest.mark.parametrize("pattern", [robocop.config.translate_pattern("*"), "ALL"])
    def test_list_rule_filtered_and_community(self, pattern, robocop_pre_load, msg_0101, community_rule, capsys):
        robocop_pre_load.config.list = pattern
        init_empty_checker(robocop_pre_load, msg_0101)
        init_empty_checker(robocop_pre_load, community_rule)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (enabled)\n"
            "Rule - 19999 [W]: community-rule: Some description (enabled)\n\n"
            "Altogether 2 rules with following severity:\n"
            "    0 error rules,\n"
            "    2 warning rules,\n"
            "    0 info rules.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    def test_list_configurables(self, robocop_pre_load, msg_0101_config_meta, capsys):
        robocop_pre_load.config.list_configurables = robocop.config.translate_pattern("*")
        init_empty_checker(robocop_pre_load, msg_0101_config_meta, conf_param=1001)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert (
            out == "All rules have configurable parameter 'severity'. "
            "Allowed values are:\n    E / error\n    W / warning\n    I / info\n\n"
            "Rule - 0101 [W]: some-message: Some description (enabled)\n"
            "    conf_param = 0\n"
            "        type: int\n"
            "    conf_param2 = 0\n"
            "        type: example_parser\n"
            "        info: meta information\n\n"
            "Altogether 1 rule with following severity:\n"
            "    0 error rules,\n"
            "    1 warning rule,\n"
            "    0 info rules.\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules_list.html page for detailed documentation.\n"
        )

    def test_list_configurables_filtered(self, robocop_pre_load, msg_0101_config, msg_0102_0204_config, capsys):
        robocop_pre_load.config.list_configurables = "another-message"
        init_empty_checker(robocop_pre_load, msg_0102_0204_config, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101_config)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        not_exp_msg = (
            "Rule - 0101 [W]: some-message: Some description (enabled)\n",
            "Rule - 0102 [E]: other-message: this is description (disabled)\n",
        )
        exp_msg = "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n"
        assert all(msg not in out for msg in not_exp_msg)
        assert exp_msg in out

    def test_list_configurables_mixed(self, robocop_pre_load, msg_0101, msg_0102_0204_config, capsys):
        robocop_pre_load.config.list_configurables = robocop.config.translate_pattern("*")
        init_empty_checker(robocop_pre_load, msg_0102_0204_config, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        not_exp_msg = "Rule - 0101 [W]: some-message: Some description (enabled)\n"
        exp_msg = (
            "Rule - 0102 [E]: other-message: this is description (disabled)\n",
            "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n",
        )
        assert not_exp_msg not in out
        assert all(msg in out for msg in exp_msg)

    def test_list_configurables_no_config(self, robocop_pre_load, msg_0101_config, msg_0102_0204_config, capsys):
        robocop_pre_load.config.list_configurables = robocop.config.translate_pattern("*")
        init_empty_checker(robocop_pre_load, msg_0102_0204_config, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101_config)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            "Rule - 0102 [E]: other-message: this is description (disabled)\n",
            "Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n",
            "Rule - 0101 [W]: some-message: Some description (enabled)\n",
        )
        assert all(msg in out for msg in exp_msg)

    def test_list_ext_rules_disabled_by_default(self, robocop_pre_load, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern("*")
        robocop_pre_load.config.ext_rules = {
            str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
            str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
        }
        robocop_pre_load.load_checkers()
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            "Rule - 1101 [E]: smth: Keyword call after [Return] statement (enabled)\n",
            "Rule - 1102 [E]: smth2: Keyword call after [Return] statement (disabled)\n",
        )
        assert all(msg in out for msg in exp_msg)

    def test_list_ext_rules_disabled_by_default_enable(self, robocop_pre_load, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern("*")
        robocop_pre_load.config.ext_rules = {
            str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
            str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
        }
        robocop_pre_load.config.include = {"1102"}
        robocop_pre_load.load_checkers()
        robocop_pre_load.check_for_disabled_rules()
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            "Rule - 1101 [E]: smth: Keyword call after [Return] statement (disabled)\n",
            "Rule - 1102 [E]: smth2: Keyword call after [Return] statement (enabled)\n",
        )
        assert all(msg in out for msg in exp_msg)
