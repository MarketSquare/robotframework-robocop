import builtins
from unittest.mock import Mock

import pytest
from robot.errors import DataError

from robocop.source_file import SourceFile
from robocop.version_handling import ROBOT_VERSION, Version


@pytest.fixture
def config():
    config = Mock()
    config.languages = None
    config.linter.diff = False
    return config


def test_file_is_read_once(tmp_path, config, monkeypatch):
    path = tmp_path / "test.robot"
    path.write_bytes(b"\xef\xbb\xbf*** Test Cases ***\r\nTest\r\n    Log    1\r\n")
    opened = []
    original_open = builtins.open

    def counting_open(file, *args, **kwargs):
        if str(file) == str(path):
            opened.append(file)
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", counting_open)
    source_file = SourceFile(path=path, config=config)

    model = source_file.model
    source_lines = source_file.source_lines

    assert len(opened) == 1
    assert source_lines == ["\ufeff*** Test Cases ***\r\n", "Test\r\n", "    Log    1\r\n"]
    assert model.sections[0].body[0].name == "Test"
    assert model.source == (path if Version("6.1") <= ROBOT_VERSION else str(path))


def test_model_of_not_utf8_file_raises_data_error(tmp_path, config):
    path = tmp_path / "test.robot"
    path.write_bytes(b"*** Test Cases ***\nTest\n    Log    \xff\n")
    source_file = SourceFile(path=path, config=config)

    with pytest.raises(DataError):
        _ = source_file.model
