import os
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

import robocop.exceptions
from robocop.config import Config

TEST_DATA = Path(__file__).parent.parent / "test_data" / "ext_rules"
EXT_MODULE = str(TEST_DATA / "ext_rule_module")


@contextmanager
def add_sys_path(path):
    """Temporarily add the given path to `sys.path`."""
    try:
        sys.path.insert(0, path)
        yield
    finally:
        sys.path.remove(path)


@contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit"""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


class TestExternalRules:
    def test_loading_external_rule(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "ext_rule" / "external_rule.py")}
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules

    def test_loading_external_rule_from_module(self, robocop_pre_load):
        with add_sys_path(EXT_MODULE):
            robocop_pre_load.config.ext_rules = {"RobocopRules"}
            robocop_pre_load.load_checkers()
            assert "9903" in robocop_pre_load.rules

    def test_loading_external_rule_from_dotted_module(self, robocop_pre_load):
        with add_sys_path(EXT_MODULE):
            robocop_pre_load.config.ext_rules = {"RobocopRules.submodule"}
            robocop_pre_load.load_checkers()
            assert "9904" in robocop_pre_load.rules
            assert "9903" not in robocop_pre_load.rules

    @pytest.mark.parametrize("config_dir", ["config_robocop", "config_pyproject"])
    def test_loading_external_rule_in_robocop_config(self, robocop_pre_load, config_dir):
        src = TEST_DATA / config_dir
        with add_sys_path(EXT_MODULE), working_directory(src), patch.object(sys, "argv", ["prog"]):
            config = Config(from_cli=True)
            robocop_pre_load.config = config
            robocop_pre_load.load_checkers()
            assert "9903" in robocop_pre_load.rules

    def test_loading_multiple_external_rules(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {
            str(TEST_DATA / "ext_rule" / "external_rule.py"),
            str(TEST_DATA / "ext_rule" / "external_rule2.py"),
        }
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules
        assert "1102" in robocop_pre_load.rules

    def test_loading_external_rule_dir(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "ext_rule")}
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules
        assert "1102" in robocop_pre_load.rules

    def test_loading_non_existing_rule(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "ext_rule" / "non_existing.py")}
        with pytest.raises(robocop.exceptions.InvalidExternalCheckerError) as err:
            robocop_pre_load.load_checkers()
        assert "Fatal error: Failed to load external rules from file" in str(err)

    def test_loading_duplicated_rule(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {
            str(TEST_DATA / "ext_rule" / "external_rule.py"),
            str(TEST_DATA / "ext_rule_duplicate" / "external_rule_dup.py"),
        }
        # duplicated rule should be overwritten - it's expected behaviour that allows you to overwrite default rules
        robocop_pre_load.load_checkers()

    def test_reports_not_existing_rule(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "ext_rule_invalid_reports" / "external_rule.py")}
        with pytest.raises(robocop.exceptions.RuleReportsNotFoundError) as err:
            robocop_pre_load.load_checkers()
        assert "SmthChecker checker `reports` attribute contains unknown rule `idontexist`" in str(err)

    # def test_load_disabled_by_default(self, robocop_pre_load):
    #     robocop_pre_load.config.ext_rules = {
    #         str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
    #         str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
    #     }
    #     robocop_pre_load.load_checkers()
    #     assert robocop_pre_load.rules["1101"].enabled
    #     assert not robocop_pre_load.rules["1102"].enabled
    #
    # @pytest.mark.parametrize(
    #     "params",
    #     [
    #         {"include": {"1102"}, "exclude": None, "expected_1101": False, "expected_1102": True},
    #         {"include": {"1101"}, "exclude": None, "expected_1101": True, "expected_1102": False},
    #         {"include": {"1102"}, "exclude": {"1102"}, "expected_1101": False, "expected_1102": False},
    #         {"include": None, "exclude": {"1102"}, "expected_1101": True, "expected_1102": False},
    #     ],
    # )
    # def test_load_disabled_by_default_include(self, robocop_pre_load, params):
    #     robocop_pre_load.config.ext_rules = {
    #         str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
    #         str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
    #     }
    #     if params["include"]:
    #         robocop_pre_load.config.include = params["include"]
    #     if params["exclude"]:
    #         robocop_pre_load.config.exclude = params["exclude"]
    #     robocop_pre_load.load_checkers()
    #     robocop_pre_load.check_for_disabled_rules()
    #     assert robocop_pre_load.rules["1101"].enabled == params["expected_1101"]
    #     assert robocop_pre_load.rules["1102"].enabled == params["expected_1102"]
    #
    # def test_load_disabled_by_default_enable(self, robocop_pre_load):
    #     robocop_pre_load.config.ext_rules = {
    #         str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
    #         str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
    #     }
    #     robocop_pre_load.config.configure = ["1102:enabled:True"]
    #     robocop_pre_load.load_checkers()
    #     robocop_pre_load.configure_checkers_or_reports()
    #     robocop_pre_load.check_for_disabled_rules()
    #     assert robocop_pre_load.rules["1101"].enabled
    #     assert robocop_pre_load.rules["1102"].enabled
