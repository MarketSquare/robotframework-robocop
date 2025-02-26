import contextlib
import os
from pathlib import Path

import pytest

from robocop.config import Config, LinterConfig, FormatterConfig, FileFiltersOptions, ConfigManager
from robocop import files


@pytest.fixture(scope="module")
def test_data() -> Path:
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="module")
def cli_config_path(test_data) -> Path:
    return test_data / "cli_config" / "pyproject.toml"


@contextlib.contextmanager
def working_directory(path: Path):
    """Change working directory and return to previous on exit"""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


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
        ext_rules=None,
        reports=None,
        persistent=None,
        compare=None
    )
    formatter = FormatterConfig(
        overwrite=None,
        show_diff=None,
        color=None,
        check=None,
        reruns=None,
        start_line=None,
        end_line=None,
    )
    return Config(
        sources=None,
        file_filters=file_filters,
        linter=linter,
        formatter=formatter,
        language=None,
        exit_zero=None
    )


def get_sources_and_configs(config_dir: Path, **kwargs) -> dict[Path, Config]:
    with working_directory(config_dir):
        config_manager = ConfigManager(**kwargs)
        return {path: config for path, config in config_manager.paths}


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
            config_dir / "subdir" / "file3.resource": config
        }

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
        subdir_config.file_filters.extend_exclude = ["file3.resource"]
        expected_results = {
            config_dir / "file1.robot": default_config,
            config_dir / "subdir" / "file2.robot": subdir_config
            # file3.resource is excluded in the subdir config
        }

        # Act
        actual_results = get_sources_and_configs(config_dir)

        # Assert
        assert actual_results == expected_results

    def test_one_config_subdir_with_overwrite_config(self, test_data, cli_config, cli_config_path):  # TODO do the same with --extend-exclude
        """Ignore found configuration files if --config is used."""
        # Arrange
        config_dir = test_data / "one_config_subdir"
        expected_results = {
            config_dir / "file1.robot": cli_config,
            config_dir / "subdir" / "file2.robot": cli_config,
            # file3.resource would be excluded by config, but cli config overwrites it
            config_dir / "subdir" / "file3.resource": cli_config
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
        overwrite_config.file_filters.extend_exclude = overwrite_option
        default_config = Config()
        default_config.file_filters.extend_exclude = overwrite_option
        subdir_config = Config()
        subdir_config.config_source = str(config_dir / "subdir" / "pyproject.toml")
        subdir_config.linter.configure = ["line-too-long.line_length=110"]
        subdir_config.file_filters.extend_exclude = overwrite_option
        expected_results = {
            config_dir / "file1.robot": default_config,
            # file2.robot should be included, but cli option overwrites it
            # config_dir / "subdir" / "file2.robot": subdir_config,
            # file3.resource would be excluded by config, but cli config overwrites it
            config_dir / "subdir" / "file3.resource": subdir_config
        }

        # Act
        actual_results = get_sources_and_configs(config_dir, overwrite_config=overwrite_config)

        # Assert
        assert actual_results == expected_results

    def test_one_config_subdir_with_overwrite_config_and_option(self, test_data, overwrite_config, cli_config, cli_config_path):
        """Both overridden config and cli option will be used (cli option takes precedence)."""
        # Arrange
        config_dir = test_data / "one_config_subdir"
        overwrite_option = ["file1.robot"]
        overwrite_config.file_filters.extend_exclude = overwrite_option
        cli_config.file_filters.extend_exclude = overwrite_option
        expected_results = {
            # excluded by cli option
            # config_dir / "file1.robot": cli_config,
            # file2.robot is excluded by cli config, but cli option overwrites it
            config_dir / "subdir" / "file2.robot": cli_config,
            # file3.resource would be excluded by config, but cli option overwrites it
            config_dir / "subdir" / "file3.resource": cli_config
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
        first_config.file_filters.extend_exclude = ["excluded_dir/"]
        first_config.linter.configure = ["line-too-long.line_length=110"]
        second_config = Config()
        second_config.config_source = str(config_dir / "subdir" / "pyproject.toml")
        second_config.file_filters.extend_exclude = ["file1.robot"]
        second_config.linter.configure = ["line-too-long.line_length=140"]
        expected_results = {
            config_dir / "file1.robot": first_config,
            config_dir / "subdir" / "file2.robot": second_config,
            config_dir / "subdir" / "file3.resource": second_config
        }

        # Act
        actual_results = get_sources_and_configs(config_dir)

        # Assert
        assert actual_results == expected_results
