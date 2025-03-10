import shutil
from pathlib import Path

import pytest
import typer

from robocop import files
from robocop.config import Config, ConfigManager, FileFiltersOptions, FormatterConfig, LinterConfig
from robocop.linter.rules import RuleSeverity
from tests import working_directory


@pytest.fixture(scope="module")
def test_data() -> Path:
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="module")
def cli_config_path(test_data) -> Path:
    return test_data / "cli_config" / "pyproject.toml"


@pytest.fixture(scope="module")
def cli_config(cli_config_path) -> Config:
    configuration = files.read_toml_config(cli_config_path)
    return Config.from_toml(configuration, cli_config_path)


@pytest.fixture(scope="module")
def overwrite_config() -> Config:
    """
    Overwrite config is by default a config with everything set to None.

    Such values are ignored when merging cli config with file configs.
    """
    file_filters = FileFiltersOptions(None, None, None, None)
    linter = LinterConfig(
        configure=None,
        select=None,
        ignore=None,
        issue_format=None,
        threshold=None,
        custom_rules=None,
        reports=None,
        persistent=None,
        compare=None,
        exit_zero=None,
    )
    formatter = FormatterConfig(
        overwrite=None,
        diff=None,
        color=None,
        check=None,
        reruns=None,
        start_line=None,
        end_line=None,
    )
    return Config(sources=None, file_filters=file_filters, linter=linter, formatter=formatter, language=None)


def get_sources_and_configs(config_dir: Path, **kwargs) -> dict[Path, Config]:
    with working_directory(config_dir):
        config_manager = ConfigManager(**kwargs)
        return dict(config_manager.paths)


class TestConfigFinder:
    def test_single_config(self, test_data):
        # Arrange
        config_dir = test_data / "one_config_root"
        config = Config()
        config.config_source = str(config_dir / "pyproject.toml")
        config.linter.configure = ["line-too-long.line_length=110"]

        expected_results = {
            config_dir / "file1.robot": config,
            config_dir / "subdir" / "file2.robot": config,
            config_dir / "subdir" / "file3.resource": config,
        }

        # Act
        actual_results = get_sources_and_configs(config_dir)

        # Assert
        assert actual_results == expected_results

    def test_single_config_all_options(self, test_data):
        # Arrange
        config_dir = test_data / "config_with_all_options"
        config = Config()
        config.config_source = str(config_dir / "pyproject.toml")
        config.linter.configure = ["line-too-long.line_length=110"]
        config.file_filters.exclude = {"deprecated.robot"}
        config.file_filters.default_exclude = {"archived/"}
        config.file_filters.include = {"custom.txt"}
        config.file_filters.default_include = {"*.robot"}
        config.target_version = 6
        config.linter.select = ["rulename", "ruleid"]
        config.linter.ignore = ["ruleid"]
        config.linter.include_rules = {"rulename", "ruleid"}
        config.linter.exclude_rules = {"ruleid"}
        config.linter.threshold = RuleSeverity.WARNING
        config.linter.reports = ["all", "sarif"]
        config.linter.issue_format = "{source_abs}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
        config.language = ["eng", "pl"]
        config.linter.custom_rules = ["CustomRules.py"]
        config.linter.persistent = True
        config.linter.compare = True
        config.linter.exit_zero = True

        config.formatter.select = ["NormalizeNewLines"]
        config.formatter.custom_formatters = ["CustomFormatter.py"]
        config.formatter.configure = ["NormalizeNewLines.flatten_lines=True"]
        config.formatter.force_order = True
        config.formatter.diff = True
        config.formatter.overwrite = False
        config.formatter.check = True
        config.formatter.start_line = 10
        config.formatter.end_line = 12
        config.formatter.whitespace_config.space_count = 2
        config.formatter.whitespace_config.indent = 3
        config.formatter.whitespace_config.continuation_indent = 5
        config.formatter.whitespace_config.line_length = 110
        config.formatter.whitespace_config.separator = "tab"
        config.formatter.whitespace_config.line_ending = "windows"
        config.formatter.skip_config.skip = {"comments", "documentation"}
        config.formatter.skip_config.sections = {"comments"}
        config.formatter.skip_config.keyword_call = {"DeprecatedKeyword"}
        config.formatter.skip_config.keyword_call_pattern = {"DeprecatedKeyword$"}
        config.formatter.reruns = 5

        expected_results = {config_dir / "test.robot": config}

        # Act
        actual_results = get_sources_and_configs(config_dir)

        # Assert
        assert actual_results == expected_results

    def test_one_config_subdir(self, test_data):
        """
        Directory with configuration file in the subdirectory.

        Files found earlier should use default configuration.
        """
        # Arrange
        config_dir = test_data / "one_config_subdir"
        default_config = Config()
        subdir_config = Config()
        subdir_config.config_source = str(config_dir / "subdir" / "pyproject.toml")
        subdir_config.linter.configure = ["line-too-long.line_length=110"]
        subdir_config.file_filters.default_exclude = {"file3.resource"}
        expected_results = {
            config_dir / "file1.robot": default_config,
            config_dir / "subdir" / "file2.robot": subdir_config,
            # file3.resource is excluded in the subdir config
        }

        # Act
        actual_results = get_sources_and_configs(config_dir)

        # Assert
        assert actual_results == expected_results

    def test_one_config_subdir_with_overwrite_config(
        self, test_data, cli_config, cli_config_path
    ):  # TODO do the same with --extend-exclude
        """Ignore found configuration files if --config is used."""
        # Arrange
        config_dir = test_data / "one_config_subdir"
        expected_results = {
            config_dir / "file1.robot": cli_config,
            config_dir / "subdir" / "file2.robot": cli_config,
            # file3.resource would be excluded by config, but cli config overwrites it
            config_dir / "subdir" / "file3.resource": cli_config,
        }

        # Act
        actual_results = get_sources_and_configs(config_dir, config=cli_config_path)

        # Assert
        assert actual_results == expected_results

    def test_one_config_subdir_with_overwrite_option(self, test_data, overwrite_config):
        """
        Overwrite configuration files option with option from the cli.

        CLI options are passed as `overwrite_config` to ConfigManager.
        """
        # Arrange
        config_dir = test_data / "one_config_subdir"
        overwrite_option = ["file2.robot"]
        overwrite_config.file_filters.default_exclude = overwrite_option
        default_config = Config()
        default_config.file_filters.default_exclude = overwrite_option
        subdir_config = Config()
        subdir_config.config_source = str(config_dir / "subdir" / "pyproject.toml")
        subdir_config.linter.configure = ["line-too-long.line_length=110"]
        subdir_config.file_filters.default_exclude = overwrite_option
        expected_results = {
            config_dir / "file1.robot": default_config,
            # file2.robot should be included, but cli option overwrites it
            # config_dir / "subdir" / "file2.robot": subdir_config,
            # file3.resource would be excluded by config, but cli config overwrites it
            config_dir / "subdir" / "file3.resource": subdir_config,
        }

        # Act
        actual_results = get_sources_and_configs(config_dir, overwrite_config=overwrite_config)

        # Assert
        assert actual_results == expected_results

    def test_one_config_subdir_with_overwrite_config_and_option(
        self, test_data, overwrite_config, cli_config, cli_config_path
    ):
        """Both overridden config and cli option will be used (cli option takes precedence)."""
        # Arrange
        config_dir = test_data / "one_config_subdir"
        overwrite_option = ["file1.robot"]
        overwrite_config.file_filters.default_exclude = overwrite_option
        cli_config.file_filters.default_exclude = overwrite_option
        expected_results = {
            # excluded by cli option
            # config_dir / "file1.robot": cli_config,
            # file2.robot is excluded by cli config, but cli option overwrites it
            config_dir / "subdir" / "file2.robot": cli_config,
            # file3.resource would be excluded by config, but cli option overwrites it
            config_dir / "subdir" / "file3.resource": cli_config,
        }

        # Act
        actual_results = get_sources_and_configs(config_dir, overwrite_config=overwrite_config, config=cli_config_path)

        # Assert
        assert actual_results == expected_results

    def test_two_configs(self, test_data):
        """
        File tree with 2 configuration files.

        Includes two extra scenarios:
         - excluded_dir with configuration file, which is not loaded as the whole directory is excluded
         - invalid_dir with invalid (missing robocop section) configuration file

        """
        # Arrange
        config_dir = test_data / "two_config"
        first_config = Config()
        first_config.config_source = str(config_dir / "pyproject.toml")
        first_config.file_filters.default_exclude = {"excluded_dir/"}
        first_config.linter.configure = ["line-too-long.line_length=110"]
        second_config = Config()
        second_config.config_source = str(config_dir / "subdir" / "pyproject.toml")
        second_config.file_filters.default_exclude = {"file1.robot"}
        second_config.linter.configure = ["line-too-long.line_length=140"]
        expected_results = {
            config_dir / "file1.robot": first_config,
            config_dir / "subdir" / "file2.robot": second_config,
            config_dir / "subdir" / "file3.resource": second_config,
        }

        # Act
        actual_results = get_sources_and_configs(config_dir)

        # Assert
        assert actual_results == expected_results

    def test_relative_paths_from_config_option(self, test_data):
        """Relative paths in --config configuration file should be resolved."""
        config_path = test_data / "relative_paths" / "pyproject.toml"
        relative_parent = config_path.parent
        config_manager = ConfigManager(config=config_path)
        assert (
            Path(config_manager.default_config.linter.custom_rules[0]).resolve()
            == (relative_parent / "custom_rules/CustomRules.py").resolve()
        )
        assert (
            Path(config_manager.default_config.formatter.custom_formatters[0]).resolve()
            == (relative_parent / "custom_formatters").resolve()
        )

    def test_fail_on_deprecated_config_options(self, test_data, capsys):
        """Unknown or deprecated options in configuration file should raise an error."""
        config_path = test_data / "old_config" / "pyproject.toml"
        configuration = files.read_toml_config(config_path)
        with pytest.raises(typer.Exit):
            Config.from_toml(configuration, config_path)
        out, _ = capsys.readouterr()
        assert (
            f"Configuration file seems to use Robocop < 6.0.0 or Robotidy syntax. "
            f"Please migrate the config: {config_path}" in out
        )

    def test_fail_on_unknown_config_options(self, test_data, capsys):
        """Unknown or deprecated options in configuration file should raise an error."""
        config_path = test_data / "invalid_config" / "pyproject.toml"
        configuration = files.read_toml_config(config_path)
        with pytest.raises(typer.Exit):
            Config.from_toml(configuration, config_path)
        out, _ = capsys.readouterr()
        assert f"Unknown configuration key: 'unknown' in {config_path}" in out

    def test_filter_paths_from_config(self, test_data, tmp_path):
        # Arrange
        test_files = test_data / "filter_paths"
        tmp_test_files = tmp_path / "filter_paths"
        git_dir = tmp_path / "filter_paths" / ".git"
        git_dir.mkdir(parents=True)
        shutil.copy(test_files / "file.py", tmp_test_files)
        shutil.copy(test_files / "file.robot", tmp_test_files)
        shutil.copy(test_files / "file.robot", git_dir)

        # Act
        actual_results = get_sources_and_configs(tmp_test_files)

        # Assert
        assert tmp_test_files / "file.robot" in actual_results
        assert len(actual_results) == 1

    def test_filter_paths_from_gitignore(self, test_data):
        # Arrange
        test_dir = test_data / "gitignore"

        # Act
        actual_results = get_sources_and_configs(test_dir)

        # Assert
        assert test_dir / "file.robot" in actual_results
        assert len(actual_results) == 1

    def test_invalid_option_value(self, test_data):
        # Arrange
        config_path = test_data / "invalid_option_values" / "invalid_target_version.toml"
        configuration = files.read_toml_config(config_path)

        # Act & Assert
        with pytest.raises(typer.BadParameter, match="Invalid target Robot Framework version: '100' is not one of"):
            Config.from_toml(configuration, config_path)
