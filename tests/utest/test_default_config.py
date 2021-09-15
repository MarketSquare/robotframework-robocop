import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import robocop.config
from robocop.exceptions import InvalidArgumentError


@pytest.fixture
def config():
    return robocop.config.Config()


@pytest.fixture
def path_to_test_data():
    return Path(Path(__file__).parent.parent, "test_data")


class TestDefaultConfig:
    def test_find_project_root_same_dir(self, path_to_test_data, config):
        src = path_to_test_data / "default_config"
        os.chdir(str(src))
        root = config.find_file_in_project_root(".robocop")
        assert root == src / ".robocop"

    def test_find_project_root_missing_but_git(self, path_to_test_data, config):
        src = path_to_test_data / "default_config_missing" / "nested" / "deeper"
        os.chdir(str(src))
        root = config.find_file_in_project_root(".robocop")
        assert root == Path(__file__).parent.parent.parent / ".robocop"

    def test_load_config_from_default_file(self, path_to_test_data, config):
        src = path_to_test_data / "default_config"
        os.chdir(str(src))
        with patch.object(sys, "argv", ["prog"]):
            config.parse_opts()
        assert {"0810"} == config.include

    def test_load_config_with_format_option(self, path_to_test_data, config):
        src = path_to_test_data / "config_with_format"
        os.chdir(str(src))
        with patch.object(sys, "argv", ["prog"]):
            config.parse_opts()
        assert '"{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"' == config.format.strip()

    def test_load_config_with_comments(self, path_to_test_data, config):
        src = path_to_test_data / "config_with_comments"
        os.chdir(str(src))
        with patch.object(sys, "argv", ["prog"]):
            config.parse_opts()

    def test_load_config_from_default_file_verbose(self, path_to_test_data, config, capsys):
        src = path_to_test_data / "default_config"
        os.chdir(str(src))
        config.from_cli = True
        config.exec_dir = str(src)
        with patch.object(sys, "argv", ["prog", "--verbose"]):
            config.parse_opts()
        out, _ = capsys.readouterr()
        assert out == f"Loaded configuration from {config.config_from}\n"

    def test_ignore_config_from_default_file(self, path_to_test_data, config):
        src = path_to_test_data / "default_config"
        os.chdir(str(src))
        with patch.object(sys, "argv", ["prog", "--include", "0202"]):
            config.parse_opts()
        assert {"0202"} == config.include

    def test_load_default_config_before_pyproject(self, path_to_test_data, config):
        src = path_to_test_data / "default_config_and_pyproject"
        os.chdir(str(src))
        with patch.object(sys, "argv", ["prog"]):
            config.parse_opts()
        assert {"0810"} == config.include

    def test_pyproject(self, path_to_test_data, config):
        src = path_to_test_data / "only_pyproject"
        os.chdir(str(src))
        config.from_cli = True
        config.exec_dir = str(src)
        with patch.object(sys, "argv", ["prog"]):
            config.parse_opts()
        expected_config = robocop.config.Config(from_cli=True)
        with patch.object(
            sys,
            "argv",
            [
                "robocop",
                "--include",
                "W0504",
                "-i",
                "*doc*",
                "--exclude",
                "0203",
                "--reports",
                "rules_by_id,scan_timer",
                "--ignore",
                "ignore_me.robot",
                "--ext-rules",
                "path_to_external\\dir",
                "--filetypes",
                ".txt,tsv",
                "--threshold",
                "E",
                "--no-recursive",
                "--format",
                "{source}:{line}:{col} [{severity}] {rule_id} {desc} (name)1",
                "--output",
                "robocop.log",
                "--configure",
                "line-too-long:line_length:150",
                "-c",
                "0201:severity:E",
                "tests\\atest\\rules\\bad-indent",
                "tests\\atest\\rules\\duplicated-library",
            ],
        ):
            expected_config.parse_opts()
        config.config_from = ""
        config.parser, expected_config.parser = None, None
        config.output, expected_config.output = None, None
        assert len(config.include_patterns) == len(expected_config.include_patterns)
        config.include_patterns, expected_config.include_patterns = None, None
        assert config.__dict__ == expected_config.__dict__

    def test_pyproject_verbose(self, path_to_test_data, config, capsys):
        src = path_to_test_data / "only_pyproject"
        os.chdir(str(src))
        config.from_cli = True
        config.exec_dir = str(src)
        with patch.object(sys, "argv", ["prog", "--verbose"]):
            config.parse_opts()
        out, _ = capsys.readouterr()
        assert out == f"Loaded configuration from {config.config_from}\n"

    def test_not_supported_option_pyproject(self, path_to_test_data, config):
        src = path_to_test_data / "not_supported_option_pyproject"
        os.chdir(str(src))
        with pytest.raises(InvalidArgumentError) as e, patch.object(sys, "argv", ["prog"]):
            config.parse_opts()
        assert (
            "Invalid configuration for Robocop:\\n"
            "Option 'list' is not supported in pyproject.toml configuration file." in str(e)
        )

    def test_invalid_toml_pyproject(self, path_to_test_data, config):
        src = path_to_test_data / "invalid_pyproject"
        os.chdir(str(src))
        with pytest.raises(InvalidArgumentError) as e, patch.object(sys, "argv", ["prog"]):
            config.parse_opts()
        assert "Invalid configuration for Robocop:\\nFailed to decode " in str(e)

    @pytest.mark.parametrize("config_dir", ["empty_config", "empty_config2"])
    def test_load_empty_config(self, path_to_test_data, config, capsys, config_dir):
        src = path_to_test_data / config_dir
        os.chdir(str(src))
        config.from_cli = True
        config.exec_dir = str(src)
        with patch.object(sys, "argv", ["prog", "--verbose"]):
            config.parse_opts()
        out, _ = capsys.readouterr()
        assert out == "No config file found or configuration is empty. Using default configuration\n"

    @pytest.mark.parametrize('config_no', [1, 2])
    def test_load_config_with_utf8_encoding(self, path_to_test_data, config, config_no):
        src = path_to_test_data / f"config_with_encoding{config_no}"
        os.chdir(str(src))
        with patch.object(sys, "argv", ["prog"]):
            config.parse_opts()
