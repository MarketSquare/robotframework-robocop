import pytest

import robocop.config
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


class EmptyChecker(VisitorChecker):
    rules = {}
    pass


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


def init_empty_checker(robocop_instance_pre_load, rule, exclude=False):
    checker = EmptyChecker(robocop_instance_pre_load)
    checker.rules = rule
    checker.register_rules(checker.rules)
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

    def test_list_configurables(self, robocop_pre_load, msg_0101, capsys):
        robocop_pre_load.config.list_configurables = robocop.config.translate_pattern('*')
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        assert out == 'Rule - 0101 [W]: some-message: Some description (enabled)\n' \
                      '    Available configurable(s) for this rule:\n        severity\n'

    def test_list_configurables_filtered(self, robocop_pre_load, msg_0101, msg_0102_0204, capsys):
        robocop_pre_load.config.list_configurables = 'another-message'
        init_empty_checker(robocop_pre_load, msg_0102_0204, exclude=True)
        init_empty_checker(robocop_pre_load, msg_0101)
        with pytest.raises(SystemExit):
            robocop_pre_load.list_checkers()
        out, _ = capsys.readouterr()
        not_exp_msg = (
            'Rule - 0101 [W]: some-message: Some description (enabled)\n'
            '    Available configurable(s) for this rule:\n        severity\n',
            'Rule - 0102 [E]: other-message: this is description (disabled)\n'
            '    Available configurable(s) for this rule:\n        severity\n'
        )
        exp_msg = 'Rule - 0204 [I]: another-message: Message with meaning 4 (disabled)\n' \
                  '    Available configurable(s) for this rule:\n        severity\n'
        assert all(msg not in out for msg in not_exp_msg)
        assert exp_msg in out
