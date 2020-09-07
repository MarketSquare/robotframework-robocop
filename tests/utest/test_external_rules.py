from pathlib import Path

import pytest

import robocop.exceptions


class TestExternalRules:
    def test_loading_external_rule(self, robocop_pre_load):  # noqa
        robocop_pre_load.config.ext_rules = {f'{Path(__file__).parent.parent}/test_data/ext_rule/external_rule.py'}
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules

    def test_loading_multiple_external_rules(self, robocop_pre_load):  # noqa
        robocop_pre_load.config.ext_rules = {
            f'{Path(__file__).parent.parent}/test_data/ext_rule/external_rule.py',
            f'{Path(__file__).parent.parent}/test_data/ext_rule/external_rule2.py'
        }
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules
        assert "1102" in robocop_pre_load.rules

    def test_loading_external_rule_dir(self, robocop_pre_load):  # noqa
        robocop_pre_load.config.ext_rules = {f'{Path(__file__).parent.parent}/test_data/ext_rule/'}
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules
        assert "1102" in robocop_pre_load.rules

    def test_loading_non_existing_rule(self, robocop_pre_load):  # noqa
        robocop_pre_load.config.ext_rules = {f'{Path(__file__).parent.parent}/test_data/ext_rule/non_existing.py'}
        with pytest.raises(robocop.exceptions.InvalidExternalCheckerError) as err:
            robocop_pre_load.load_checkers()
        assert "Fatal error: Failed to load external rules from file" in str(err)

    def test_loading_duplicated_rule(self, robocop_pre_load):  # noqa
        robocop_pre_load.config.ext_rules = {
            f'{Path(__file__).parent.parent}/test_data/ext_rule/external_rule.py',
            f'{Path(__file__).parent.parent}/test_data/ext_rule_duplicate/external_rule_dup.py'
        }
        with pytest.raises(robocop.exceptions.DuplicatedRuleError) as err:
            robocop_pre_load.load_checkers()
        assert "Fatal error: Message name 'smth' defined in SmthChecker was already defined in SmthChecker" in str(err)

    def test_load_external_rule_no_register_method(self, robocop_pre_load):  # noqa
        robocop_pre_load.config.ext_rules = {
            f'{Path(__file__).parent.parent}/test_data/ext_rule_missing_register/external_rule_missing_register.py'
        }
        with pytest.raises(robocop.exceptions.MissingRegisterMethodCheckerError) as err:
            robocop_pre_load.load_checkers()
        assert "Fatal error: Tried to load rule file" in str(err)
        assert "but register method was missing" in str(err)
