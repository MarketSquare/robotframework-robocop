import contextlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from robocop.config import Config
from robocop.exceptions import InvalidArgumentError
from robocop.files import find_file_in_project_root


@pytest.fixture
def path_to_test_data():
    return Path(Path(__file__).parent.parent, "test_data")


@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit"""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


class TestDefaultConfig:
    def test_find_project_root_same_dir(self, path_to_test_data):
        src = path_to_test_data / "default_config"
        with working_directory(src):
            root = find_file_in_project_root(".robocop", src)
        assert root == src / ".robocop"

    def test_find_project_root_missing_but_git(self, path_to_test_data):
        src = path_to_test_data / "default_config_missing" / "nested" / "deeper"
        with working_directory(src):
            root = find_file_in_project_root(".robocop", src)
        assert root == Path(__file__).parent.parent.parent / ".robocop"

    def test_load_config_from_default_file(self, path_to_test_data):
        src = path_to_test_data / "default_config"
        with working_directory(src), patch.object(sys, "argv", ["prog"]):
            config = Config(from_cli=True)
        assert {"0810"} == config.include

    def test_load_config_with_format_option(self, path_to_test_data):
        src = path_to_test_data / "config_with_format"
        with working_directory(src), patch.object(sys, "argv", ["prog"]):
            config = Config()
        assert '"{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"' == config.format.strip()

    def test_load_config_with_comments(self, path_to_test_data):
        src = path_to_test_data / "config_with_comments"
        with working_directory(src), patch.object(sys, "argv", ["prog"]):
            Config()

    def test_load_config_from_default_file_verbose(self, path_to_test_data, capsys):
        src = path_to_test_data / "default_config"
        with working_directory(src), patch.object(sys, "argv", ["prog", "--verbose"]):
            config = Config(from_cli=True)
        config.print_config_source()
        out, _ = capsys.readouterr()
        assert out == f"Loaded configuration from {config.config_from}\n"

    def test_append_config_from_default_file(self, path_to_test_data):
        src = path_to_test_data / "default_config"
        with working_directory(src), patch.object(sys, "argv", ["prog", "--include", "0202"]):
            config = Config(from_cli=True)

        assert ["line-too-long:line_length:150"] == config.configure
        assert {"0202", "0810"} == config.include

    def test_load_default_config_before_pyproject(self, path_to_test_data):
        src = path_to_test_data / "default_config_and_pyproject"
        with working_directory(src), patch.object(sys, "argv", ["prog"]):
            config = Config()
        assert {"0810"} == config.include

    def test_pyproject(self, path_to_test_data):
        src = path_to_test_data / "only_pyproject"
        with working_directory(src), patch.object(sys, "argv", ["prog"]):
            config = Config(from_cli=True)

        src = path_to_test_data
        argv = [
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
            "--language",
            "pt,fi",
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
        ]
        with working_directory(src), patch.object(
            sys,
            "argv",
            argv,
        ):
            expected_config = Config(from_cli=True)

        expected_config.exec_dir = ""
        expected_config.root = src / "only_pyproject"
        config.exec_dir = ""
        config.config_from = ""
        config.parser, expected_config.parser = None, None
        config.output, expected_config.output = None, None
        assert len(config.include_patterns) == len(expected_config.include_patterns)
        config.include_patterns, expected_config.include_patterns = None, None
        assert config.threshold.value == expected_config.threshold.value
        config.threshold, expected_config.threshold = None, None
        # paths from config files are absolute paths, resolved with root of the config file
        expected_config.paths = [str(Path(expected_config.root) / path) for path in expected_config.paths]
        assert config.__dict__ == expected_config.__dict__

    def test_append_config_pyproject_file(self, path_to_test_data):
        src = path_to_test_data / "only_pyproject"
        with working_directory(src), patch.object(
            sys, "argv", ["prog", "--configure", "too-many-calls-in-keyword:max_calls:20", "--exclude", "0810"]
        ):
            config = Config(from_cli=True)

        assert {"0203", "0810"} == config.exclude
        assert [
            "line-too-long:line_length:150",
            "0201:severity:E",
            "too-many-calls-in-keyword:max_calls:20",
        ] == config.configure

    def test_pyproject_verbose(self, path_to_test_data, capsys):
        src = path_to_test_data / "only_pyproject"
        with working_directory(src), patch.object(sys, "argv", ["prog", "--verbose"]):
            config = Config(from_cli=True)
        config.print_config_source()
        out, _ = capsys.readouterr()
        assert out == f"Loaded configuration from {config.config_from}\n"

    def test_not_supported_option_pyproject(self, path_to_test_data):
        src = path_to_test_data / "not_supported_option_pyproject"
        with working_directory(src), pytest.raises(InvalidArgumentError) as e, patch.object(sys, "argv", ["prog"]):
            Config(from_cli=True)
        assert (
            "Invalid configuration for Robocop:\\n"
            "Option 'list' is not supported in pyproject.toml configuration file." in str(e)
        )

    def test_invalid_toml_pyproject(self, path_to_test_data):
        src = path_to_test_data / "invalid_pyproject"
        with working_directory(src), pytest.raises(InvalidArgumentError) as e, patch.object(sys, "argv", ["prog"]):
            Config(from_cli=True)
        assert "Invalid configuration for Robocop:\\nFailed to decode " in str(e)

    @pytest.mark.parametrize("config_dir", ["empty_config", "empty_config2"])
    def test_load_empty_config(self, path_to_test_data, capsys, config_dir):
        src = path_to_test_data / config_dir
        with working_directory(src), patch.object(sys, "argv", ["prog", "--verbose"]):
            config = Config(from_cli=True)
        config.print_config_source()
        out, _ = capsys.readouterr()
        assert out == "No config file found or configuration is empty. Using default configuration\n"

    @pytest.mark.parametrize("config_no", [1, 2])
    def test_load_config_with_utf8_encoding(self, path_to_test_data, config_no):
        src = path_to_test_data / f"config_with_encoding{config_no}"
        expected = ["line-too-long:line_length:150", "not-allowed-char-in-name:pattern:[Á]"]
        with working_directory(src), patch.object(sys, "argv", ["prog"]):
            config = Config(from_cli=True)
        assert sorted(config.configure) == expected

    def test_load_config_with_relative_paths_pyproject(self, path_to_test_data):
        """
        pyproject.toml resolves relative path to config directory.
        For example if root/pyproject.toml contains test.py, it will become root/test.py
        """
        src = path_to_test_data / "relative_path_in_config_pyproject"
        work_dir = src / "nested"
        with working_directory(work_dir), patch.object(sys, "argv", ["robocop"]):
            config = Config(from_cli=True)
            ext_rule_path = config.ext_rules.pop()
            assert Path(ext_rule_path).absolute() == src / "test.py"

    def test_load_config_with_relative_paths_robocop(self, path_to_test_data):
        """
        .robocop argument files does not resolve relative paths -
        they are relative to the path Robocop is running.
        For example if root/.robocop contains test.py,
        and you're running robocop from root/nested,
        it will become root/nested/test.py
        """
        src = path_to_test_data / "relative_path_in_config_robocop"
        work_dir = src / "nested"
        with working_directory(work_dir), patch.object(sys, "argv", ["robocop"]):
            config = Config(from_cli=True)
            ext_rule_path = config.ext_rules.pop()
            assert Path(ext_rule_path).absolute() == work_dir / "test.py"

    def test_override_default_config(self, path_to_test_data):
        """
        Default config should not be loaded if "--argumentfile" option is used.
        """
        default_config = path_to_test_data / "only_pyproject"
        other_config = path_to_test_data / "default_config_and_pyproject" / ".robocop"
        for option_name in ("-A", "--argumentfile"):
            with working_directory(default_config), patch.object(
                sys, "argv", ["robocop", option_name, str(other_config)]
            ):
                config = Config(from_cli=True)
            assert str(config.config_from) == str(other_config)
            assert config.include == {"0810"}
