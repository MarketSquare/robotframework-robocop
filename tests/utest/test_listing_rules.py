import pytest

import robocop.config
from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity


class EmptyChecker(VisitorChecker):
    rules = {}
    pass


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


def dummy_parser(value):
    return value


@pytest.fixture
def msg_0101_config_meta():
    return {
        "0101": Rule(
            RuleParam(name="conf_param", converter=int, default=0, desc=""),
            RuleParam(name="conf_param2", converter=dummy_parser, default=0, desc="meta information"),
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
def msg_0102_0204():
    return {
        "0102": Rule(rule_id="0102", name="other-message", msg="""this is description""", severity=RuleSeverity.ERROR),
        "0204": Rule(
            rule_id="0204", name="another-message", msg=f"Message with meaning {4}", severity=RuleSeverity.INFO
        ),
    }


def init_empty_checker(robocop_instance_pre_load, rule, exclude=False, **kwargs):
    checker = EmptyChecker()
    checker.rules = rule
    checker.__dict__.update(**kwargs)
    if exclude:
        robocop_instance_pre_load.config.exclude.update(set(rule.keys()))
        robocop_instance_pre_load.config.translate_patterns()
    robocop_instance_pre_load.register_checker(checker)
    return checker


class TestListingRules:
    def test_list_rule(self, robocop_pre_load, msg_0101, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern("*")
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (enabled)\n\n"
            "Altogether 1 rule(s) with following severity:\n"
            "    0 error rule(s),\n"
            "    1 warning rule(s),\n"
            "    0 info rule(s).\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules.html page for detailed documentation.\n"
        )

    def test_list_disabled_rule(self, robocop_pre_load, msg_0101, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern("*")
        init_empty_checker(robocop_pre_load, msg_0101, exclude=True)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert (
            out == "Rule - 0101 [W]: some-message: Some description (disabled)\n\n"
            "Altogether 1 rule(s) with following severity:\n"
            "    0 error rule(s),\n"
            "    1 warning rule(s),\n"
            "    0 info rule(s).\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules.html page for detailed documentation.\n"
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

    def test_list_configurables(self, robocop_pre_load, msg_0101_config_meta, capsys):
        robocop_pre_load.config.list_configurables = robocop.config.translate_pattern("*")
        init_empty_checker(robocop_pre_load, msg_0101_config_meta, conf_param=1001)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert (
            out == "All rules have configurable parameter 'severity'. "
            "Allowed values are:\n    E / error\n    W / warning\n    I / info\n"
            "Rule - 0101 [W]: some-message: Some description (enabled)\n"
            "    conf_param = 0\n"
            "        type: int\n"
            "    conf_param2 = 0\n"
            "        type: dummy_parser\n"
            "        info: meta information\n\n"
            "Altogether 1 rule(s) with following severity:\n"
            "    0 error rule(s),\n"
            "    1 warning rule(s),\n"
            "    0 info rule(s).\n\n"
            "Visit https://robocop.readthedocs.io/en/stable/rules.html page for detailed documentation.\n"
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
