from pathlib import Path

import pytest

from robocop import Config, Robocop


@pytest.mark.parametrize(
    "configuration, expected",
    [
        ("invalid-char-in-name:invalid_chars::", {":"}),
        (None, set("?.")),
        ("invalid-char-in-name:invalid_chars::%#", set(":%#")),
    ],
)
class TestConfigureRule:
    def test_configure_with_two_semicolons(self, configuration, expected):
        config = Config(root=str(Path(__file__).parent))
        config.configure = [configuration] if configuration else []
        config.include = ["invalid-char-in-name"]
        robocop_runner = Robocop(config=config)
        robocop_runner.reload_config()
        # find rule and then associated checker([1]), and compare param
        assert robocop_runner.rules["invalid-char-in-name"][1].invalid_chars == expected
