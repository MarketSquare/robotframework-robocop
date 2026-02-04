import shutil
import sys
from pathlib import Path

import pytest
import typer

from robocop import exceptions
from robocop.config import schema as config_model
from robocop.config.builder import ConfigBuilder
from robocop.config.manager import ConfigManager
from robocop.config.parser import TargetVersion, read_toml_config
from robocop.linter.rules import RuleSeverity
from robocop.linter.runner import RobocopLinter
from robocop.runtime.resolver import ConfigResolver
from robocop.version_handling import ROBOT_VERSION
from tests import working_directory


@pytest.fixture(scope="module")
def test_data() -> Path:
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="module")
def cli_config_path(test_data) -> Path:
    return test_data / "cli_config" / "pyproject.toml"


@pytest.fixture(scope="module")
def cli_config(cli_config_path) -> config_model.Config:
    configuration = read_toml_config(cli_config_path)
    raw_config = config_model.RawConfig.from_dict(configuration, cli_config_path)
    return ConfigBuilder().from_raw(cli_raw=None, file_raw=raw_config)


@pytest.fixture
def overwrite_config() -> config_model.RawConfig:
    """
    Overwrite config is by default a config with everything set to None.

    Such values are ignored when merging cli config with file configs.
    """
    file_filters = config_model.RawFileFiltersOptions()
    linter = config_model.RawLinterConfig()
    formatter = config_model.RawFormatterConfig()
    cache = config_model.RawCacheConfig()
    return config_model.RawConfig(
        file_filters=file_filters,
        linter=linter,
        formatter=formatter,
        cache=cache,
    )


def get_sources_and_configs(config_dir: Path, **kwargs) -> dict[Path, config_model.Config]:
    with working_directory(config_dir):
        config_manager = ConfigManager(**kwargs)
        return {source.path: source.config for source in config_manager.paths}


class TestConfigFinder:
    def test_single_config(self, test_data):
        # Arrange
        config_dir = test_data / "one_config_root"
        config_path = config_dir / "pyproject.toml"
        config_file_raw = config_model.RawConfig.from_dict(
            config_dict=read_toml_config(config_path), config_path=config_path
        )
        config = ConfigBuilder().from_raw(cli_raw=None, file_raw=config_file_raw)
        config.linter.configure = ["line-too-long.line_length=110"]
        config.cache.cache_dir = config_dir / ".robocop_cache"

        expected_results = {
            config_dir / "file1.robot": config,
            config_dir / "subdir" / "file2.robot": config,
            config_dir / "subdir" / "file3.resource": config,
        }

        # Act
        actual_results = get_sources_and_configs(config_dir)

        # Assert
        assert actual_results == expected_results

    @pytest.mark.parametrize(
        "config_dir_name",
        ["config_with_all_options", "config_with_all_options_hyphens"],
    )
    def test_single_config_all_options(self, test_data, config_dir_name):
        # Arrange
        config_dir = test_data / config_dir_name
        raw_linter = config_model.RawLinterConfig(
            configure=["line-too-long.line_length=110"],
            select=["rulename", "ruleid"],
            extend_select=["customrule"],
            ignore=["ruleid"],
            custom_rules=["CustomRules.py"],
            threshold=RuleSeverity.WARNING,
            reports=["all", "sarif"],
            issue_format="{source_abs}:{line}:{col} [{severity}] {rule_id} {desc} ({name})",
            persistent=True,
            compare=True,
            exit_zero=True,
        )
        file_filter = config_model.RawFileFiltersOptions(
            exclude=["deprecated.robot"],
            default_exclude=["archived/"],
            include=["custom.txt"],
            default_include=["*.robot"],
        )
        whitespace_config = config_model.RawWhitespaceConfig(
            space_count=2, indent=3, continuation_indent=5, line_length=110, separator="tab", line_ending="windows"
        )
        skip_config = config_model.RawSkipConfig(
            skip={"comments", "documentation"},
            sections={"comments"},
            keyword_call={"DeprecatedKeyword"},
            keyword_call_pattern={"DeprecatedKeyword$"},
        )
        formatter_config = config_model.RawFormatterConfig(
            select=["NormalizeNewLines"],
            extend_select=["CustomFormatter.py"],
            configure=["NormalizeNewLines.flatten_lines=True"],
            force_order=True,
            diff=True,
            color=False,
            overwrite=False,
            check=True,
            start_line=10,
            end_line=12,
            reruns=5,
            whitespace_config=whitespace_config,
            skip_config=skip_config,
        )
        config_raw = config_model.RawConfig(
            file_filters=file_filter,
            linter=raw_linter,
            formatter=formatter_config,
            target_version=TargetVersion.RF4,
            language=["en", "pl"],
        )
        config = ConfigBuilder().from_raw(cli_raw=None, file_raw=config_raw)
        config.cache.cache_dir = config_dir / ".robocop_cache"

        expected_results = {config_dir / "test.robot": config}

        # Act
        actual_results = get_sources_and_configs(config_dir)

        # Assert
        assert actual_results == expected_results

    def test_one_config_subdir(self, test_data):
        """
        Directory with a configuration file in the subdirectory.

        Files found earlier should use the default configuration.
        """
        # Arrange
        builder = ConfigBuilder()
        config_dir = test_data / "one_config_subdir"
        default_config = builder.from_raw(cli_raw=None, file_raw=None)
        default_config.cache.cache_dir = config_dir / ".robocop_cache"

        linter_config = config_model.RawLinterConfig(configure=["line-too-long.line_length=110"])
        file_filters = config_model.RawFileFiltersOptions(default_exclude=["file3.resource"])
        raw_config = config_model.RawConfig(linter=linter_config, file_filters=file_filters)
        raw_config.config_source = str(config_dir / "subdir" / "pyproject.toml")
        subdir_config = builder.from_raw(cli_raw=None, file_raw=raw_config)
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
        builder = ConfigBuilder()
        config_dir = test_data / "one_config_subdir"
        overwrite_option = ["file2.robot"]
        overwrite_config.file_filters.default_exclude = overwrite_option
        cli_raw = config_model.RawConfig()
        cli_raw.file_filters = config_model.RawFileFiltersOptions(default_exclude=overwrite_option)
        default_config = builder.from_raw(cli_raw=cli_raw, file_raw=None)
        cli_sub_raw = config_model.RawConfig()
        cli_sub_raw.file_filters = config_model.RawFileFiltersOptions(default_exclude=overwrite_option)
        cli_sub_raw.linter = config_model.RawLinterConfig(configure=["line-too-long.line_length=110"])
        cli_sub_raw.config_source = str(config_dir / "subdir" / "pyproject.toml")
        subdir_config = builder.from_raw(cli_raw=cli_sub_raw, file_raw=None)
        expected_results = {
            config_dir / "file1.robot": default_config,
            # file2.robot should be included, but cli option overwrites it
            # "subdir" / "file2.robot": subdir_config,
            # file3.resource would be excluded by config, but cli config overwrites it
            config_dir / "subdir" / "file3.resource": subdir_config,
        }

        # Act
        actual_results = get_sources_and_configs(config_dir, overwrite_config=overwrite_config)

        # Assert
        assert actual_results == expected_results

    def test_one_config_subdir_with_overwrite_config_and_option(self, test_data, overwrite_config, cli_config_path):
        """Both overridden config and cli option will be used (cli option takes precedence)."""
        # Arrange
        config_dir = test_data / "one_config_subdir"
        overwrite_option = ["file1.robot"]
        overwrite_config.file_filters.default_exclude = overwrite_option

        # Arrange - expected config
        configuration = read_toml_config(cli_config_path)
        raw_config = config_model.RawConfig.from_dict(configuration, cli_config_path)
        raw_config.file_filters.default_exclude = overwrite_option
        cli_config = ConfigBuilder().from_raw(cli_raw=None, file_raw=raw_config)
        cli_config.cache.cache_dir = config_dir / ".robocop_cache"
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
        builder = ConfigBuilder()
        config_dir = test_data / "two_config"

        first_config_raw = config_model.RawConfig(
            linter=config_model.RawLinterConfig(configure=["line-too-long.line_length=110"]),
            file_filters=config_model.RawFileFiltersOptions(default_exclude=["excluded_dir/"]),
        )
        first_config_raw.config_source = str(config_dir / "subdir" / "pyproject.toml")
        first_config = builder.from_raw(None, file_raw=first_config_raw)

        second_config_raw = config_model.RawConfig(
            linter=config_model.RawLinterConfig(configure=["line-too-long.line_length=140"]),
            file_filters=config_model.RawFileFiltersOptions(default_exclude=["file1.robot"]),
        )
        second_config_raw.config_source = str(config_dir / "subdir" / "pyproject.toml")
        second_config = builder.from_raw(None, file_raw=second_config_raw)

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
            Path(config_manager.default_config.formatter.extend_select[0]).resolve()
            == (relative_parent / "custom_formatters").resolve()
        )

    def test_multiple_sources_and_configs(self, tmp_path):
        """Multiple source paths passed to the entry command, with different configuration files."""
        # Arrange - create two test files with two closest configurations
        builder = ConfigBuilder()
        config_file_1 = tmp_path / "pyproject.toml"
        config_file_1.write_text("[tool.robocop]\nverbose = true\n", encoding="utf-8")
        first_config_raw = config_model.RawConfig(verbose=True, config_source=str(config_file_1))
        first_config = builder.from_raw(None, file_raw=first_config_raw)
        test_file_1 = tmp_path / "test.robot"
        test_file_1.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        config_file_2 = tmp_path / "subdir" / "pyproject.toml"
        config_file_2.parent.mkdir(parents=True, exist_ok=True)
        config_file_2.write_text("[tool.robocop]\nverbose = false\n", encoding="utf-8")
        second_config_raw = config_model.RawConfig(verbose=False, config_source=str(config_file_2))
        second_config = builder.from_raw(None, file_raw=second_config_raw)
        test_file_2 = tmp_path / "subdir" / "test.robot"
        test_file_2.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")
        expected_results = {test_file_1: first_config, test_file_2: second_config}

        # Act
        actual_results = get_sources_and_configs(tmp_path, sources=[test_file_1, test_file_2])

        # Assert
        assert actual_results == expected_results

    def test_fail_on_deprecated_config_options(self, test_data, capsys):
        """Unknown or deprecated options in the configuration file should raise an error."""
        config_path = test_data / "old_config" / "pyproject.toml"
        configuration = read_toml_config(config_path)
        with pytest.raises(typer.Exit):
            config_model.RawConfig.from_dict(configuration, config_path)
        out, _ = capsys.readouterr()
        assert (
            f"Configuration file seems to use Robocop < 6.0.0 or Robotidy syntax. "
            f"Please migrate the config: {config_path}" in out
        )

    def test_fail_on_unknown_config_options(self, test_data, capsys):
        """Unknown or deprecated options in the configuration file should raise an error."""
        config_path = test_data / "invalid_config" / "invalid.toml"
        configuration = read_toml_config(config_path)
        with pytest.raises(typer.Exit):
            config_model.RawConfig.from_dict(configuration, config_path)
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
        configuration = read_toml_config(config_path)

        # Act & Assert
        with pytest.raises(
            typer.BadParameter,
            match="Invalid target Robot Framework version: '100' is not one of",
        ):
            config_model.RawConfig.from_dict(configuration, config_path)

    @pytest.mark.parametrize(
        ("force_exclude", "skip_gitignore", "should_exclude_file"),
        [
            (False, False, False),  # file filter or skip gitignore would exclude file
            (True, False, True),  # file filter or/and gitignore excludes file
            (False, True, False),  # file filter excludes file
            (True, True, True),  # file filter is ignored and file is not excluded
        ],
    )
    def test_force_exclude_and_skip_gitignore(self, test_data, force_exclude, skip_gitignore, should_exclude_file):
        """
        When source is passed directly, it is not checked against file filter and skip gitignore.

        --force-exclude flag disables this behaviour.
        """
        # Arrange
        non_robot_file = test_data / "non_robot_files" / "log.html"
        expected_paths = [] if should_exclude_file else [non_robot_file]

        # Act
        actual_results = get_sources_and_configs(
            non_robot_file.parent,
            sources=[str(non_robot_file)],
            force_exclude=force_exclude,
            skip_gitignore=skip_gitignore,
        )

        # Assert
        assert list(actual_results.keys()) == expected_paths

    @pytest.mark.parametrize("skip_gitignore", [True, False])
    def test_skip_gitignore(self, test_data, skip_gitignore):
        # Arrange
        test_dir = test_data / "non_robot_files"
        non_robot_file = test_dir / "log.html"
        expected_paths = [non_robot_file] if skip_gitignore else []
        raw_config = config_model.RawConfig(file_filters=config_model.RawFileFiltersOptions(default_include=["*.html"]))

        # Act
        actual_results = get_sources_and_configs(
            non_robot_file.parent,
            sources=[str(test_dir)],
            overwrite_config=raw_config,
            skip_gitignore=skip_gitignore,
        )

        # Assert
        assert list(actual_results.keys()) == expected_paths

    @pytest.mark.skipif(sys.platform != "linux", reason="Test only runs on Linux")
    def test_symlink_path(self, test_data, tmp_path):
        # Arrange
        absolute_path = tmp_path / "test.robot"
        absolute_path2 = test_data / "simple" / "test.robot"
        absolute_path.write_text("*** Settings ***")
        (tmp_path / "test2.robot").symlink_to(absolute_path2)
        (tmp_path / "test3.robot").symlink_to(absolute_path2)
        (tmp_path / "test4.robot").symlink_to("idontexist")
        expected_paths = [absolute_path, absolute_path2]

        # Act
        actual_results = get_sources_and_configs(tmp_path)

        # Assert
        assert sorted(actual_results.keys()) == sorted(expected_paths)

    @pytest.mark.skipif(sys.platform != "linux", reason="Test only runs on Linux")
    def test_exclude_symlink_path(self, test_data, tmp_path):
        # Arrange
        absolute_path = tmp_path / "test.robot"
        absolute_path2 = test_data / "simple" / "test.robot"
        absolute_path3 = test_data / "simple" / "test2.robot"
        absolute_path.write_text("*** Settings ***")
        (tmp_path / "test2.robot").symlink_to(absolute_path2)
        (tmp_path / "test3.robot").symlink_to(absolute_path3)
        expected_paths = [absolute_path, absolute_path2]
        overwrite_config = config_model.RawConfig(
            file_filters=config_model.RawFileFiltersOptions(exclude=["test3.robot"])
        )

        # Act
        actual_results = get_sources_and_configs(tmp_path, overwrite_config=overwrite_config)

        # Assert
        assert sorted(actual_results.keys()) == sorted(expected_paths)

    def test_reports_loaded_from_top_config(self, test_data):
        # Arrange
        test_dir = test_data / "robot_toml_with_reports"
        expected_reports = ["version", "all", "text_file", "return_status"]

        # Act
        with working_directory(test_dir):
            config_manager = ConfigManager()

        # Assert
        assert config_manager.default_config.linter.reports == expected_reports

    def test_combine_configure(self, test_data, overwrite_config):
        # Arrange
        test_dir = test_data / "robot_toml_with_reports"
        overwrite_config.linter.configure = ["line-too-long.line_length=140"]

        # Act
        actual_results = get_sources_and_configs(test_dir, overwrite_config=overwrite_config)

        # Assert
        assert "line-too-long.line_length=140" in actual_results[test_dir / "test.robot"].linter.configure
        assert "line-too-long.line_length=200" in actual_results[test_dir / "test.robot"].linter.configure

    def test_multiple_files_with_single_config(self, test_data, overwrite_config, capsys):
        # Arrange
        test_dir = test_data / "multiple_files_one_config"
        overwrite_config.verbose = True

        # Act
        with working_directory(test_dir):
            config_manager = ConfigManager(overwrite_config=overwrite_config)
            linter = RobocopLinter(config_manager)
        out, _ = capsys.readouterr()

        # Assert
        assert out == f"Loaded {test_dir / 'robocop.toml'} configuration file.\n"
        assert len(linter.reports) > 2

    def test_fail_on_invalid_language(self, capsys):
        if ROBOT_VERSION.major < 6:
            pytest.skip("Test enabled only for RF 6.0+")
        raw_config = config_model.RawConfig(language=["invalid", "en"])
        with pytest.raises(typer.Exit):
            ConfigBuilder().from_raw(raw_config, None)
        out, _ = capsys.readouterr()
        expected_error = (
            "Failed to load languages: invalid, en. "
            "Verify if language is one of the supported languages: "
            "https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#translations"
        )
        assert expected_error in out

    def test_incorrect_enabled(self, test_data, capsys):
        # Arrange
        test_dir = test_data / "config_with_enabled"
        resolver = ConfigResolver(load_formatters=True)

        # Act
        with working_directory(test_dir):
            config_manager = ConfigManager(config=Path("enabled.toml"))
        with pytest.raises(exceptions.InvalidParameterValueError):
            resolver.resolve_config(config_manager.default_config)
        _, err = capsys.readouterr()
        normalized_error = " ".join(err.split())

        # Assert
        assert (
            "OrderSettingsSection: Invalid 'enabled' parameter value: 'True :new_lines_between_groups=2'. "
            "It should be 'true' or 'false'" in normalized_error
        )


class TestCacheConfigOverride:
    """Test that CLI cache options properly override config file cache settings."""

    def test_cli_cache_enabled_overrides_config_disabled(self, tmp_path, overwrite_config):
        """Test CLI --cache enables cache when config file has cache=false."""
        # Arrange - create config file with cache disabled
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = false\n", encoding="utf-8")
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Create CLI overwrite config with cache enabled
        overwrite_config.cache.enabled = True

        # Act
        with working_directory(tmp_path):
            config_manager = ConfigManager(overwrite_config=overwrite_config)

        # Assert - CLI should override file config
        assert config_manager.default_config.cache.enabled is True

    def test_cli_no_cache_overrides_config_enabled(self, tmp_path, overwrite_config):
        """Test CLI --no-cache disables cache when config file has cache=true."""
        # Arrange - create config file with cache enabled
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = true\n", encoding="utf-8")
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Create CLI overwrite config with cache disabled
        overwrite_config.cache.enabled = False

        # Act
        with working_directory(tmp_path):
            config_manager = ConfigManager(overwrite_config=overwrite_config)

        # Assert - CLI should override file config
        assert config_manager.default_config.cache.enabled is False

    def test_cli_cache_dir_overrides_config(self, tmp_path, overwrite_config):
        """Test CLI --cache-dir overrides config file cache_dir."""
        # Arrange - create config file with cache_dir set
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache_dir = 'config_cache_dir'\n", encoding="utf-8")
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Create CLI overwrite config with different cache_dir
        cli_cache_dir = tmp_path / "cli_cache_dir"
        overwrite_config.cache.enabled = True
        overwrite_config.cache.cache_dir = cli_cache_dir

        # Act
        with working_directory(tmp_path):
            config_manager = ConfigManager(overwrite_config=overwrite_config)

        # Assert - CLI should override file config
        assert config_manager.default_config.cache.cache_dir == cli_cache_dir

    def test_cli_cache_enabled_with_cache_dir_overrides_config(self, tmp_path, overwrite_config):
        """Test CLI --cache --cache-dir overrides config file with cache disabled."""
        # Arrange - create config file with cache disabled
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = false\n", encoding="utf-8")
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Create CLI overwrite config with cache enabled and custom cache_dir
        cli_cache_dir = tmp_path / "custom_cache"
        overwrite_config.cache.enabled = True
        overwrite_config.cache.cache_dir = cli_cache_dir

        # Act
        with working_directory(tmp_path):
            config_manager = ConfigManager(overwrite_config=overwrite_config)

        # Assert - CLI should override file config for both enabled and cache_dir
        assert config_manager.default_config.cache.enabled is True
        assert config_manager.default_config.cache.cache_dir == cli_cache_dir

    def test_no_cli_cache_option_uses_config_file_defaults(self, tmp_path, overwrite_config):
        """Test that when no CLI cache option is provided, config file settings are used."""
        # Arrange - create config file with cache disabled
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop]\ncache = false\n", encoding="utf-8")
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Create CLI overwrite config with cache=None (no CLI option provided)
        # provided in overwrite_config fixture already

        # Act
        with working_directory(tmp_path):
            config_manager = ConfigManager(overwrite_config=overwrite_config)

        # Assert - should use config file setting
        assert config_manager.default_config.cache.enabled is False
