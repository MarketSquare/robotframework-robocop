import re
from pathlib import Path

import pytest

from robocop import Config, Robocop


@pytest.mark.parametrize(
    "configuration, expected",
    [
        ("not-allowed-char-in-name:pattern:[:]", re.compile(r"[:]")),
        ("not-allowed-char-in-name:pattern:[:%#]", re.compile(r"[:%#]")),
        ("not-allowed-char-in-name:pattern:[^a-z]", re.compile(r"[^a-z]")),
    ],
)
class TestConfigureRule:
    def test_configure_with_two_semicolons(self, configuration, expected):
        print(str(Path(__file__).parent))
        config = Config(root=str(Path(__file__).parent))
        config.configure = [configuration] if configuration else []
        config.include = ["not-allowed-char-in-name"]
        robocop_runner = Robocop(config=config)
        robocop_runner.reload_config()
        assert (
            robocop_runner.rules["not-allowed-char-in-name"][1].param("not-allowed-char-in-name", "pattern") == expected
        )
