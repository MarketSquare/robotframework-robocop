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
