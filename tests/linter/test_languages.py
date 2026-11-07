import pytest

from robocop.run import check_files
from robocop.version_handling import ROBOT_VERSION, Version
from tests import working_directory

POLISH_WITH_HEADER = """\
language: pl

*** Przypadki Testowe ***
Test
    Log    1
"""

POLISH_WITHOUT_HEADER = """\
*** Przypadki Testowe ***
Test
    Log    1
"""


@pytest.mark.skipif(ROBOT_VERSION < Version("6.1"), reason="invalid-section requires RF 6.1+")  # noqa: SIM300
def test_language_header_does_not_leak_to_other_files(tmp_path):
    (tmp_path / "a_with_header.robot").write_text(POLISH_WITH_HEADER)
    (tmp_path / "b_without_header.robot").write_text(POLISH_WITHOUT_HEADER)
    with working_directory(tmp_path):
        diagnostics = check_files(return_result=True, silent=True, cache=False, select=["ERR01", "NAME16"])

    assert {diag.source.path.name for diag in diagnostics} == {"b_without_header.robot"}
