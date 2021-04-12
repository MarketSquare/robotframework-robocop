import pytest

import robocop.config
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


class EmptyChecker(VisitorChecker):
    rules = {}
    pass


@pytest.fixture
def msg_0101_config():
    return {
        '0101': (
            "some-message",
            "Some description",
            RuleSeverity.WARNING,
            ("conf_param", "conf_param", int)
        )
    }


@pytest.fixture
def msg_0101_config_meta():
    return {
        '0101': (
            "some-message",
            "Some description",
            RuleSeverity.WARNING,
            ("conf_param", "conf_param", int),
            ("conf_param2", "conf_param2", msg_0101_config_meta, 'meta information')
        )
    }


@pytest.fixture
def msg_0102_0204_config():
    return {
        '0102': (
            'other-message',
            '''this is description''',
            RuleSeverity.ERROR,
            ("conf_param1", "conf_param1", int)
        ),
        '0204': (
            "another-message",
            f"Message with meaning {4}",
            RuleSeverity.INFO,
            ("conf_param2", "conf_param2", int)
        )
    }


@pytest.fixture
def msg_0101():
    return {
        '0101': (
            "some-message",
            "Some description",
            RuleSeverity.WARNING
        )
    }


@pytest.fixture
def msg_0102_0204():
    return {
        '0102': (
            'other-message',
            '''this is description''',
            RuleSeverity.ERROR
        ),
        '0204': (
            "another-message",
            f"Message with meaning {4}",
            RuleSeverity.INFO
        )
    }


def init_empty_checker(robocop_instance_pre_load, rule, exclude=False, **kwargs):
    checker = EmptyChecker()
    checker.rules = rule
    checker.register_rules(checker.rules)
    checker.__dict__.update(**kwargs)
    if exclude:
        robocop_instance_pre_load.config.exclude.update(set(rule.keys()))
        robocop_instance_pre_load.config.translate_patterns()
    robocop_instance_pre_load.register_checker(checker)
    return checker


class TestListingRules:
    def test_list_rule(self, robocop_pre_load, msg_0101, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern('*')
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert out == 'Rule - 0101 [W]: some-message: Some description (enabled)\n'

    def test_list_disabled_rule(self, robocop_pre_load, msg_0101, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern('*')
        init_empty_checker(robocop_pre_load, msg_0101, exclude=True)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert out == 'Rule - 0101 [W]: some-message: Some description (disabled)\n'

    def test_list_reports(self, robocop_pre_load, msg_0101, capsys):
        robocop_pre_load.config.list_reports = True
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.load_reports()
        out, _ = capsys.readouterr()
        first_line = out.split('\n')[0]
        assert first_line == 'Available reports:'

    def test_multiple_checkers(self, robocop_pre_load, msg_0101, msg_0102_0204, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern('*')
        init_empty_checker(robocop_pre_load, msg_0102_0204, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            'Rule - 0101 [W]: some-message: Some description (enabled)\n',
            'Rule - 0102 [E]: other-message: this is description (disabled)\n',
            'Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n'
        )
        assert all(msg in out for msg in exp_msg)

    def test_list_filtered(self, robocop_pre_load, msg_0101, msg_0102_0204, capsys):
        robocop_pre_load.config.list = robocop.config.translate_pattern('01*')
        init_empty_checker(robocop_pre_load, msg_0102_0204, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            'Rule - 0101 [W]: some-message: Some description (enabled)\n',
            'Rule - 0102 [E]: other-message: this is description (disabled)\n'
        )
        not_exp_msg = 'Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n'
        assert all(msg in out for msg in exp_msg)
        assert not_exp_msg not in out

    def test_list_configurables(self, robocop_pre_load, msg_0101_config_meta, capsys):
        robocop_pre_load.config.list_configurables = robocop.config.translate_pattern('*')
        init_empty_checker(robocop_pre_load, msg_0101_config_meta, conf_param=1001)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert out == "All rules have configurable parameter 'severity'. " \
                      "Allowed values are:\n    E / error\n    W / warning\n    I / info\n" \
                      "Rule - 0101 [W]: some-message: Some description (enabled)\n" \
                      "    conf_param = 1001\n" \
                      "        type: int\n" \
                      "    conf_param2 = None\n" \
                      "        type: msg_0101_config_meta\n" \
                      "        info: meta information\n"

    def test_list_configurables_filtered(self, robocop_pre_load, msg_0101_config, msg_0102_0204_config, capsys):
        robocop_pre_load.config.list_configurables = 'another-message'
        init_empty_checker(robocop_pre_load, msg_0102_0204_config, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101_config)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        not_exp_msg = (
            'Rule - 0101 [W]: some-message: Some description (enabled)\n',
            'Rule - 0102 [E]: other-message: this is description (disabled)\n'
        )
        exp_msg = 'Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n'
        assert all(msg not in out for msg in not_exp_msg)
        assert exp_msg in out

    def test_list_configurables_mixed(self, robocop_pre_load, msg_0101, msg_0102_0204_config, capsys):
        robocop_pre_load.config.list_configurables = robocop.config.translate_pattern('*')
        init_empty_checker(robocop_pre_load, msg_0102_0204_config, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        not_exp_msg = 'Rule - 0101 [W]: some-message: Some description (enabled)\n'
        exp_msg = (
            'Rule - 0102 [E]: other-message: this is description (disabled)\n',
            'Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n'
        )
        assert not_exp_msg not in out
        assert all(msg in out for msg in exp_msg)

    def test_list_configurables_no_config(self, robocop_pre_load, msg_0101_config, msg_0102_0204_config, capsys):
        robocop_pre_load.config.list_configurables = robocop.config.translate_pattern('*')
        init_empty_checker(robocop_pre_load, msg_0102_0204_config, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101_config)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            'Rule - 0102 [E]: other-message: this is description (disabled)\n',
            'Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n',
            'Rule - 0101 [W]: some-message: Some description (enabled)\n'
        )
        assert all(msg in out for msg in exp_msg)
