import sys
from contextlib import contextmanager
from pathlib import Path

from robocop.config import LinterConfig
from tests import working_directory

TEST_DATA = Path(__file__).parent / "test_data" / "custom_rules"
EXT_MODULE = str(TEST_DATA / "custom_rule_module")
EXT_MODULE_SIMPLE = str(TEST_DATA / "custom_rule_module_simple_import")
EXT_MODULE_ROBOCOP_IMPORT = str(TEST_DATA / "custom_rule_module_import_robocop")
EXT_MODULE_WITH_RELATIVE_IMPORT = str(TEST_DATA / "custom_rule_module_with_relative_import")


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


def test_load_custom_rule_abs_path():
    linter_config = LinterConfig(custom_rules=[str(TEST_DATA / "custom_rule" / "external_rule.py")])
    linter_config.load_configuration()
    assert "EXT01" in linter_config.rules


def test_load_custom_rule_rel_path():
    with working_directory(TEST_DATA):
        linter_config = LinterConfig(custom_rules=["custom_rule/external_rule.py"])
        linter_config.load_configuration()
    assert "EXT01" in linter_config.rules


def test_load_custom_rule_from_module():
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE):
        linter_config = LinterConfig(custom_rules=["RobocopRules"])
        linter_config.load_configuration()
    assert "EXT03" in linter_config.rules
    assert "EXT04" not in linter_config.rules


def test_loading_external_rule_from_dotted_module():
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE):
        linter_config = LinterConfig(custom_rules=["RobocopRules.submodule"])
        linter_config.load_configuration()
    assert "EXT03" not in linter_config.rules
    assert "EXT04" in linter_config.rules


def test_loading_custom_rule_from_module_simple_import():
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE_SIMPLE):
        linter_config = LinterConfig(custom_rules=["RobocopRules"])
        linter_config.load_configuration()
    assert "EXT03" in linter_config.rules
    assert "EXT04" in linter_config.rules
    assert_no_duplicated_checker(linter_config.checkers)


def test_loading_custom_rule_with_robocop_import():
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE_ROBOCOP_IMPORT):
        linter_config = LinterConfig(custom_rules=["RobocopCustomRules"])
        linter_config.load_configuration()
    assert_no_duplicated_checker(linter_config.checkers)


def test_loading_custom_rule_including_relative_import():
    clear_imported_module("RobocopRules")
    with add_sys_path(EXT_MODULE_WITH_RELATIVE_IMPORT):
        linter_config = LinterConfig(custom_rules=[EXT_MODULE_WITH_RELATIVE_IMPORT])
        linter_config.load_configuration()
    assert "EXT05" in linter_config.rules
