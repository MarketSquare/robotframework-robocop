import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

from robocop import __version__
from robocop.linter.rules import RuleSeverity
from robocop.runtime.resolver import RuleMatcher, RulesLoader
from robocop.version_handling import ROBOT_VERSION
from tests import working_directory

TEST_DATA = Path(__file__).parent / "test_data" / "custom_rules"
EXT_MODULE = str(TEST_DATA / "custom_rule_module")
EXT_MODULE_SIMPLE = str(TEST_DATA / "custom_rule_module_simple_import")
EXT_MODULE_ROBOCOP_IMPORT = str(TEST_DATA / "custom_rule_module_import_robocop")
EXT_MODULE_WITH_RELATIVE_IMPORT = str(TEST_DATA / "custom_rule_module_with_relative_import")
EXT_MODULE_WITH_CONFLICT = str(TEST_DATA / "rule_with_name_conflict")


@pytest.fixture
def loader() -> RulesLoader:
    rule_matcher = RuleMatcher(
        select=[],
        extend_select=[],
        ignore=[],
        target_version=ROBOT_VERSION,
        threshold=RuleSeverity.INFO,
        fixable=[],
        unfixable=[],
    )
    return RulesLoader(rule_matcher=rule_matcher, custom_rules=[], configure=[], silent=True, config_source="mock")


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


def assert_no_duplicated_checker(checkers: list) -> None:
    seen_checkers = []
    for checker in checkers:
        checker_name = checker.__class__.__name__
        for seen_checker in seen_checkers:
            if checker_name == seen_checker.__class__.__name__:
                assert sorted(checker.rules.keys()) != sorted(seen_checker.rules.keys()), (
                    f"Checker {checker_name} was imported more than once."
                )
        seen_checkers.append(checker)


def test_load_custom_rule_abs_path(loader):
    loader.custom_rules = [str(TEST_DATA / "custom_rule" / "external_rule.py")]
    loader.load_rules()
    assert "EXT01" in loader.rules


def test_load_custom_rule_rel_path(loader):
    with working_directory(TEST_DATA):
        loader.custom_rules = ["custom_rule/external_rule.py"]
        loader.load_rules()
    assert "EXT01" in loader.rules


def test_load_custom_rule_from_module(loader):
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE):
        loader.custom_rules = ["RobocopRules"]
        loader.load_rules()
    assert "EXT03" in loader.rules
    assert "EXT04" not in loader.rules


def test_loading_external_rule_from_dotted_module(loader):
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE):
        loader.custom_rules = ["RobocopRules.submodule"]
        loader.load_rules()
    assert "EXT03" not in loader.rules
    assert "EXT04" in loader.rules


def test_loading_custom_rule_from_module_simple_import(loader):
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE_SIMPLE):
        loader.custom_rules = ["RobocopRules"]
        loader.load_rules()
    assert "EXT03" in loader.rules
    assert "EXT04" in loader.rules
    assert_no_duplicated_checker(loader.base_checkers)
    # assert default and overriden docs url
    assert loader.rules["EXT03"].docs_url == "https://your.company.com/robocop/rules/external-rule"
    assert loader.rules["EXT04"].docs_url == f"https://robocop.dev/v{__version__}/rules_list/#ext04-external-rule2"


def test_loading_custom_rule_with_robocop_import(loader):
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE_ROBOCOP_IMPORT):
        loader.custom_rules = ["RobocopCustomRules"]
        loader.load_rules()
    assert_no_duplicated_checker(loader.base_checkers)


def test_loading_custom_rule_including_relative_import(loader):
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE_WITH_RELATIVE_IMPORT):
        loader.custom_rules = [EXT_MODULE_WITH_RELATIVE_IMPORT]
        loader.load_rules()
    assert "EXT03" not in loader.rules
    assert "EXT05" in loader.rules


def test_loading_custom_rule_with_name_conflict(loader):
    """Import another module inside a custom rule that uses the same name as robocop module (like deprecated.py)."""
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE_WITH_CONFLICT):
        loader.custom_rules = [EXT_MODULE_WITH_CONFLICT]
        loader.load_rules()
    assert "CUS01" in loader.rules


def test_builtin_deprecated_rules_are_registered(loader):
    """Deprecated built-in rules are discovered and registered so they can be recognized in configuration."""
    loader.load_rules()
    # Registered by name, rule id and legacy (deprecated) name.
    assert "unnecessary-string-conversion" in loader.rules
    assert "MISC12" in loader.rules
    assert "0923" in loader.rules
    assert loader.rules["MISC12"].deprecated
    # Deprecated rules are shared with the matcher so referencing them reports a deprecation warning.
    assert loader.rule_matcher.deprecated_rules is not loader.rules
    assert loader.rule_matcher.deprecated_rules["MISC12"].deprecated


def test_selecting_deprecated_rule_reports_warning(capsys):
    """Selecting a deprecated rule reports a deprecation warning instead of an unknown rule error."""
    rule_matcher = RuleMatcher(
        select=["unnecessary-string-conversion"],
        extend_select=[],
        ignore=[],
        target_version=ROBOT_VERSION,
        threshold=RuleSeverity.INFO,
        fixable=[],
        unfixable=[],
    )
    loader = RulesLoader(rule_matcher=rule_matcher, custom_rules=[], configure=[], silent=False, config_source="mock")
    loader.load_rules()
    _, err = capsys.readouterr()
    assert "unnecessary-string-conversion is deprecated" in err
    assert "did not match with any rule name or id" not in err
