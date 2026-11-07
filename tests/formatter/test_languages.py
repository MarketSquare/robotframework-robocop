import shutil

import pytest

from robocop.run import format_files
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
  Log  1
  IF  $condition
    Log  2
  END
"""


@pytest.mark.skipif(ROBOT_VERSION < Version("6.0"), reason="Language support requires RF 6.0+")  # noqa: SIM300
def test_language_header_does_not_leak_to_other_files(tmp_path):
    together, alone = tmp_path / "together", tmp_path / "alone"
    together.mkdir()
    alone.mkdir()
    (together / "a_with_header.robot").write_text(POLISH_WITH_HEADER)
    (together / "b_without_header.robot").write_text(POLISH_WITHOUT_HEADER)
    shutil.copy(together / "b_without_header.robot", alone)

    for path in (together, alone):
        with working_directory(path):
            format_files(return_result=True, silent=True, cache=False)

    formatted_alone = (alone / "b_without_header.robot").read_text()
    assert (together / "b_without_header.robot").read_text() == formatted_alone
