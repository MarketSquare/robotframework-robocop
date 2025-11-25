from pathlib import Path

from robocop.run import check_files
from tests import working_directory

TEST_DATA = Path(__file__).parent / "test_data" / "per_file_ignore"


def test_per_file_ignores():
    with working_directory(TEST_DATA):
        diagnostics = check_files(return_result=True, silent=True)
    for diag in diagnostics:
        if diag.source.match("test.robot"):
            assert diag.rule.rule_id != "VAR02"
        if diag.source.match("ignore_subdir/*"):
            assert diag.rule.rule_id not in {"DOC01", "SPC09"}
        if diag.source.match("ignore_only_here/test2.robot"):
            assert diag.rule.rule_id != "SPC10"


def test_per_file_ignores_disable_config():
    # it also tests that ignore_file_config=True disables config file parsing
    with working_directory(TEST_DATA):
        diagnostics = check_files(return_result=True, silent=True, ignore_file_config=True)
    assert any(diag.rule.rule_id == "VAR02" for diag in diagnostics if diag.source.match("test.robot"))
    assert any(diag.rule.rule_id in {"DOC01", "SPC09"} for diag in diagnostics if diag.source.match("ignore_subdir/*"))
    assert any(
        diag.rule.rule_id == "SPC10" for diag in diagnostics if diag.source.match("ignore_only_here/test2.robot")
    )
