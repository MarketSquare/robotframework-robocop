from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from robocop import plugins
from robocop.config.parser import read_toml_config
from robocop.config.schema import RawConfig
from robocop.exceptions import FatalError
from robocop.run import app
from tests import working_directory

TEST_DATA_DIR = Path(__file__).parent / "test_data"
PLUGIN_SITE_DIR = TEST_DATA_DIR / "example_plugin"
PLUGIN_DIR = PLUGIN_SITE_DIR / "example_plugin"


def generate_config(config_path: Path, config_content: str) -> Path:
    config_path.write_text(textwrap.dedent(config_content))
    return config_path


class TestPluginDiscovery:
    def test_plugin_is_discovered(self, example_plugin):
        assert "example" in example_plugin
        assert len(example_plugin) == 1
        plugin = example_plugin.plugins["example"]
        assert plugin.name == "example"
        assert plugin.module_path == "example_plugin"
        assert plugin.path == PLUGIN_DIR

    def test_no_plugins_installed(self, no_plugins):  # noqa: ARG002
        assert len(plugins.get_plugins()) == 0

    @pytest.mark.parametrize(
        ("reference", "expected"),
        [
            ("example", "example_plugin"),
            ("example.rules", "example_plugin.rules"),
            ("example.formatters.ExampleFormatter", "example_plugin.formatters.ExampleFormatter"),
            ("other.rules", None),
            ("rules", None),
            ("path/to/rules.py", None),
        ],
    )
    def test_resolve_module_reference(self, example_plugin, reference, expected):  # noqa: ARG002
        assert plugins.resolve_module_reference(reference) == expected

    def test_resolve_path_reference(self, example_plugin):  # noqa: ARG002
        assert plugins.resolve_path_reference("example.config.strict") == PLUGIN_DIR / "config" / "strict.toml"

    def test_resolve_path_reference_unknown_plugin(self, example_plugin):  # noqa: ARG002
        with pytest.raises(FatalError):
            plugins.resolve_path_reference("unknown.config.strict")

    def test_resolve_path_reference_without_path(self, example_plugin):  # noqa: ARG002
        with pytest.raises(FatalError):
            plugins.resolve_path_reference("example")


class TestPluginRules:
    def test_load_rules_from_plugin(self, example_plugin, loader):  # noqa: ARG002
        loader.custom_rules = ["example.rules"]
        loader.load_rules()
        assert "EXPL01" in loader.rules
        assert "plugin-rule" in loader.rules

    def test_load_rules_from_plugin_root(self, example_plugin, loader):  # noqa: ARG002
        loader.custom_rules = ["example"]
        loader.load_rules()
        assert "EXPL01" in loader.rules

    def test_unknown_plugin_is_not_treated_as_plugin(self, example_plugin, loader):  # noqa: ARG002
        loader.custom_rules = ["idontexist.rules"]
        with pytest.raises(FatalError):
            loader.load_rules()

    def test_check_with_plugin_rule(self, example_plugin):  # noqa: ARG002
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "check",
                "--no-cache",
                "--custom-rules",
                "example.rules",
                "--select",
                "plugin-rule",
                str(TEST_DATA_DIR / "test.robot"),
            ],
        )
        assert "EXPL01 Test case name 'Test' comes from the plugin rule" in result.output


class TestPluginFormatters:
    @pytest.fixture
    def source(self, tmp_path) -> Path:
        source = tmp_path / "test.robot"
        shutil.copy(TEST_DATA_DIR / "test.robot", source)
        return source

    @pytest.mark.parametrize("select", ["example.formatters.ExampleFormatter", "example.formatters"])
    def test_format_with_plugin_formatter(self, example_plugin, source, select):  # noqa: ARG002
        runner = CliRunner()
        result = runner.invoke(app, ["format", "--select", select, str(source)])
        assert result.exit_code == 0
        assert "Plugin Test" in source.read_text()

    def test_configure_plugin_formatter(self, example_plugin, source):  # noqa: ARG002
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "format",
                "--select",
                "example.formatters.ExampleFormatter",
                "--configure",
                "ExampleFormatter.test_name=Configured Name",
                str(source),
            ],
        )
        assert result.exit_code == 0
        assert "Configured Name" in source.read_text()


class TestPluginReports:
    @pytest.mark.parametrize("reports", ["example.reports", "example.reports.issues_count"])
    def test_check_with_plugin_report(self, example_plugin, reports):  # noqa: ARG002
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["check", "--no-cache", "--reports", reports, str(TEST_DATA_DIR / "test.robot")],
        )
        assert "Plugin report: found" in result.output

    def test_configure_plugin_report(self, example_plugin):  # noqa: ARG002
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "check",
                "--no-cache",
                "--reports",
                "example.reports",
                "--configure",
                "issues_count.prefix=Configured",
                str(TEST_DATA_DIR / "test.robot"),
            ],
        )
        assert "Configured: found" in result.output

    def test_list_plugin_report(self, example_plugin):  # noqa: ARG002
        runner = CliRunner()
        result = runner.invoke(app, ["list", "reports", "--reports", "example.reports"])
        assert result.exit_code == 0
        assert "issues_count" in result.output


class TestPluginConfigs:
    def test_extends_plugin_config(self, example_plugin, tmp_path):  # noqa: ARG002
        config_path = generate_config(
            tmp_path / "robocop.toml",
            """
            [tool.robocop]
            extends = ["example.config.strict"]

            [tool.robocop.lint]
            select = ["line-too-long"]
            """,
        )
        raw_config = RawConfig.from_dict(config_dict=read_toml_config(config_path), config_path=config_path)
        assert raw_config.linter.custom_rules == ["example.rules"]
        assert raw_config.linter.select == ["plugin-rule", "line-too-long"]
        assert raw_config.linter.configure == ["line-too-long.line_length=140"]
        assert raw_config.formatter.select == ["example.formatters.ExampleFormatter"]

    def test_extends_plugin_config_end_to_end(self, example_plugin, tmp_path):  # noqa: ARG002
        shutil.copy(TEST_DATA_DIR / "test.robot", tmp_path / "test.robot")
        generate_config(
            tmp_path / "robocop.toml",
            """
            [tool.robocop]
            extends = ["example.config.strict"]
            """,
        )
        runner = CliRunner()
        with working_directory(tmp_path):
            result = runner.invoke(app, ["check", "--no-cache"])
        assert "EXPL01 Test case name 'Test' comes from the plugin rule" in result.output

    def test_extends_unknown_plugin(self, example_plugin, tmp_path):  # noqa: ARG002
        config_path = generate_config(
            tmp_path / "robocop.toml",
            """
            [tool.robocop]
            extends = ["unknown.config.strict"]
            """,
        )
        with pytest.raises(FatalError):
            RawConfig.from_dict(config_dict=read_toml_config(config_path), config_path=config_path)

    def test_extends_missing_plugin_config(self, example_plugin, tmp_path):  # noqa: ARG002
        config_path = generate_config(
            tmp_path / "robocop.toml",
            """
            [tool.robocop]
            extends = ["example.config.idontexist"]
            """,
        )
        with pytest.raises(FatalError):
            RawConfig.from_dict(config_dict=read_toml_config(config_path), config_path=config_path)


class TestListPlugins:
    def test_list_plugins(self, example_plugin):  # noqa: ARG002
        runner = CliRunner()
        result = runner.invoke(app, ["list", "plugins"])
        assert result.exit_code == 0
        assert "example" in result.output
        assert "example_plugin" in result.output

    def test_list_plugins_no_plugins(self, no_plugins):  # noqa: ARG002
        runner = CliRunner()
        result = runner.invoke(app, ["list", "plugins"])
        assert result.exit_code == 0
        assert "There are no Robocop plugins installed." in result.output
