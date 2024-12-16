import os
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

import robocop.exceptions
from robocop.config import Config
from robocop.utils.version_matching import Version

TEST_DATA = Path(__file__).parent.parent / "test_data" / "ext_rules"
EXT_MODULE = str(TEST_DATA / "ext_rule_module")
EXT_MODULE_SIMPLE = str(TEST_DATA / "ext_rule_module_simple_import")
EXT_MODULE_ROBOCOP_IMPORT = str(TEST_DATA / "ext_rule_module_import_robocop")
EXT_MODULE_WITH_RELATIVE_IMPORT = str(TEST_DATA / "ext_rule_module_with_relative_import")


@contextmanager
def add_sys_path(path):
    """Temporarily add the given path to `sys.path`."""
    try:
        sys.path.insert(0, path)
        yield
    finally:
        sys.path.remove(path)


def clear_imported_module(module):
    sys.modules.pop(module, None)


@contextmanager
def working_directory(path):
    """Change working directory and return to previous on exit"""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def assert_no_duplicated_checker(checkers):
    seen_checkers = []
    for checker in checkers:
        checker_name = checker.__class__.__name__
        for seen_checker in seen_checkers:
            if checker_name == seen_checker.__class__.__name__:
                assert sorted(checker.rules.keys()) != sorted(
                    seen_checker.rules.keys()
                ), f"Checker {checker_name} was imported more than once."
        seen_checkers.append(checker)


class TestExternalRules:
    def test_loading_external_rule(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "ext_rule" / "external_rule.py")}
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules

    def test_loading_external_rule_from_module(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
        with add_sys_path(EXT_MODULE):
            robocop_pre_load.config.ext_rules = {"RobocopRules"}
            robocop_pre_load.load_checkers()
            assert "9903" in robocop_pre_load.rules

    def test_loading_external_rule_from_module_simple_import(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
        with add_sys_path(EXT_MODULE_SIMPLE):
            robocop_pre_load.config.ext_rules = {"RobocopRules"}
            robocop_pre_load.load_checkers()
            assert "9904" in robocop_pre_load.rules
            assert "9903" in robocop_pre_load.rules
            assert_no_duplicated_checker(robocop_pre_load.checkers)

    def test_loading_external_rule_with_robocop_import(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
        with add_sys_path(EXT_MODULE_ROBOCOP_IMPORT):
            robocop_pre_load.config.ext_rules = {"RobocopCustomRules"}
            robocop_pre_load.load_checkers()
            assert_no_duplicated_checker(robocop_pre_load.checkers)

    def test_loading_external_rule_from_dotted_module(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
        with add_sys_path(EXT_MODULE):
            robocop_pre_load.config.ext_rules = {"RobocopRules.submodule"}
            robocop_pre_load.load_checkers()
            assert "9904" in robocop_pre_load.rules
            assert "9903" not in robocop_pre_load.rules

    def test_loading_external_rule_including_relative_import(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
        with add_sys_path(EXT_MODULE_WITH_RELATIVE_IMPORT):
            robocop_pre_load.config.ext_rules = {EXT_MODULE_WITH_RELATIVE_IMPORT}
            robocop_pre_load.load_checkers()
            assert "9905" in robocop_pre_load.rules

    @pytest.mark.parametrize("config_dir", ["config_robocop", "config_pyproject"])
    def test_loading_external_rule_in_robocop_config(self, robocop_pre_load, config_dir):
        clear_imported_module("RobocopRules")
        src = TEST_DATA / config_dir
        with add_sys_path(EXT_MODULE), working_directory(src), patch.object(sys, "argv", ["prog"]):
            config = Config(from_cli=True)
            robocop_pre_load.config = config
            robocop_pre_load.load_checkers()
            assert "9903" in robocop_pre_load.rules

    def test_loading_multiple_external_rules(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
        robocop_pre_load.config.ext_rules = {
            str(TEST_DATA / "ext_rule" / "external_rule.py"),
            str(TEST_DATA / "ext_rule" / "external_rule2.py"),
        }
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules
        assert "1102" in robocop_pre_load.rules

    def test_loading_external_rule_dir(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "ext_rule")}
        robocop_pre_load.load_checkers()
        assert "1101" in robocop_pre_load.rules
        assert "1102" in robocop_pre_load.rules

    def test_loading_non_existing_rule(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "ext_rule" / "non_existing.py")}
        with pytest.raises(robocop.exceptions.InvalidExternalCheckerError) as err:
            robocop_pre_load.load_checkers()
        assert "Fatal error: Failed to load external rules from file" in str(err)

    def test_loading_duplicated_rule(self, robocop_pre_load):
        clear_imported_module("RobocopRules")
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

    def test_load_disabled_by_default(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {
            str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
            str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
        }
        robocop_pre_load.load_checkers()
        assert robocop_pre_load.rules["1101"].enabled
        assert not robocop_pre_load.rules["1102"].enabled

    @pytest.mark.parametrize(
        "params",
        [
            {"include": {"1102"}, "exclude": None, "expected_1101": False, "expected_1102": True},
            {"include": {"1101"}, "exclude": None, "expected_1101": True, "expected_1102": False},
            {"include": {"1102"}, "exclude": {"1102"}, "expected_1101": False, "expected_1102": False},
            {"include": None, "exclude": {"1102"}, "expected_1101": True, "expected_1102": False},
        ],
    )
    def test_load_disabled_by_default_include(self, robocop_pre_load, params):
        robocop_pre_load.config.ext_rules = {
            str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
            str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
        }
        if params["include"]:
            robocop_pre_load.config.include = params["include"]
        if params["exclude"]:
            robocop_pre_load.config.exclude = params["exclude"]
        robocop_pre_load.load_checkers()
        robocop_pre_load.check_for_disabled_rules()
        assert robocop_pre_load.rules["1101"].enabled == params["expected_1101"]
        assert robocop_pre_load.rules["1102"].enabled == params["expected_1102"]

    def test_load_disabled_by_default_enable(self, robocop_pre_load):
        robocop_pre_load.config.ext_rules = {
            str(TEST_DATA / "disabled_by_default" / "external_rule.py"),
            str(TEST_DATA / "disabled_by_default" / "external_rule2.py"),
        }
        robocop_pre_load.config.configure = ["1102:enabled:True"]
        robocop_pre_load.load_checkers()
        robocop_pre_load.configure_checkers_or_reports()
        robocop_pre_load.check_for_disabled_rules()
        assert robocop_pre_load.rules["1101"].enabled
        assert robocop_pre_load.rules["1102"].enabled


class TestDeprecatedRules:
    def test_load_deprecated_rules(self, robocop_pre_load, capsys):
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "deprecated" / "deprecated_rules.py")}
        robocop_pre_load.reload_config()
        # Rules loaded correctly
        assert all(
            rule in robocop_pre_load.rules for rule in ("not-deprecated", "deprecated", "deprecated-no-implementation")
        )
        # Rules enabled status is set correctly
        assert all(not robocop_pre_load.rules[rule].enabled for rule in ("deprecated", "deprecated-no-implementation"))
        assert robocop_pre_load.rules["not-deprecated"].enabled
        # Deprecated rules are disabled, non deprecated are not
        assert all(
            not robocop_pre_load.config.is_rule_enabled(robocop_pre_load.rules[rule])
            for rule in ("deprecated", "deprecated-no-implementation")
        )
        assert robocop_pre_load.config.is_rule_enabled(robocop_pre_load.rules["not-deprecated"])
        # No warning if rule not mentioned in the configuration
        out, _ = capsys.readouterr()
        assert "Rule W1103 deprecated-no-implementation is deprecated. Remove it from your configuration.\n" not in out
        assert "Rule W1102 deprecated is deprecated. Remove it from your configuration.\n" not in out

    def test_use_deprecated_rule(self, robocop_pre_load, capsys):
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "deprecated" / "deprecated_rules.py")}
        robocop_pre_load.config.configure = ["deprecated:enabled:True"]
        robocop_pre_load.config.include = {"deprecated-no-implementation"}
        robocop_pre_load.config.exclude = {"deprecated", "not-deprecated"}
        robocop_pre_load.reload_config()
        out, _ = capsys.readouterr()
        assert "Rule W1103 deprecated-no-implementation is deprecated. Remove it from your configuration.\n" in out
        assert "Rule W1102 deprecated is deprecated. Remove it from your configuration.\n"


class TestVersionMatching:
    @pytest.mark.parametrize(
        ("rf_version", "rules_status"),
        [
            (
                "4.0",
                {"no-version": True, "lower-than-5": True, "higher-or-equal-than-5": False, "range-5-and-6": False},
            ),
            (
                "5.0",
                {"no-version": True, "lower-than-5": False, "higher-or-equal-than-5": True, "range-5-and-6": False},
            ),
            ("6.0", {"no-version": True, "lower-than-5": False, "higher-or-equal-than-5": True, "range-5-and-6": True}),
        ],
    )
    def test_no_version_always_enabled(self, robocop_pre_load, rf_version, rules_status):
        robocop_pre_load.config.ext_rules = {str(TEST_DATA / "version_matching" / "rules_with_version_limits.py")}

        with patch("robocop.rules.ROBOT_VERSION", Version(rf_version)):
            robocop_pre_load.reload_config()
        actual_status = {rule: robocop_pre_load.rules[rule].enabled for rule in rules_status}
        assert actual_status == rules_status
