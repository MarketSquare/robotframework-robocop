# setup workdir to overwrite_modes
# test with default cli, overwrite clis
# mock runner? or better, see if file will be formatted


import shutil
from pathlib import Path

import pytest
import typer

from robocop.run import format_files
from tests import working_directory

TEST_DATA = Path(__file__).parent / "test_data" / "overwrite_modes"


def prepare_files(temporary_directory: Path, config_name: str):
    config = TEST_DATA / config_name
    example_file = TEST_DATA / "example_file.robot"
    shutil.copy(config, temporary_directory / "pyproject.toml")
    shutil.copy2(example_file, temporary_directory)


class TestOverwriteModes:
    @pytest.mark.parametrize(
        ("modes", "overwrite_args", "file_modified", "exit_code"),
        [
            ("check", {}, False, 1),
            ("check", {"check": True}, False, 1),
            ("check", {"check": False}, True, 0),
            ("check", {"overwrite": True}, True, 1),
            ("check", {"overwrite": False}, False, 1),
            ("overwrite_check", {}, True, 1),
            ("overwrite_check", {"overwrite": False}, False, 1),
            ("overwrite", {}, True, 0),
            ("overwrite", {"overwrite": False}, False, 0),
            ("overwrite", {"check": True}, True, 1),
        ],
    )
    def test_check_from_config(self, modes, overwrite_args, file_modified, exit_code, tmp_path, capsys):
        # Arrange
        prepare_files(tmp_path, config_name=f"{modes}.toml")
        if file_modified:
            msg = "\n1 file reformatted, 0 files left unchanged.\n"
        else:
            msg = "\n1 file would be reformatted, 0 files would be left unchanged.\n"

        # Act
        with working_directory(tmp_path), pytest.raises(typer.Exit) as exit_status:
            format_files(**overwrite_args)
        out, _ = capsys.readouterr()

        # Assert
        assert msg in out
        assert exit_status.value.exit_code == exit_code
