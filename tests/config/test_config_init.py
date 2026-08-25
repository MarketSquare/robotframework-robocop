"""Tests for the ``robocop config init`` command and the config generator."""

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib

from typer.testing import CliRunner

from robocop.run import app
from tests import working_directory


def _read_enabled_summary(runner: CliRunner, args: list[str]) -> str:
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    for line in result.stdout.splitlines():
        if "Altogether" in line:
            return line
    raise AssertionError("No summary line found in the output")


class TestConfigInit:
    def test_generate_to_stdout(self):
        runner = CliRunner()
        result = runner.invoke(app, ["config", "init", "--output", "-"])
        assert result.exit_code == 0
        assert "[tool.robocop]" in result.stdout
        assert "[tool.robocop.lint]" in result.stdout
        assert "[tool.robocop.format]" in result.stdout

    def test_generated_file_is_valid_toml(self, tmp_path):
        runner = CliRunner()
        with working_directory(tmp_path):
            result = runner.invoke(app, ["config", "init"])
        assert result.exit_code == 0
        config_file = tmp_path / "robocop.toml"
        assert config_file.exists()
        data = tomllib.loads(config_file.read_text(encoding="utf-8"))
        assert "lint" in data["tool"]["robocop"]
        assert "format" in data["tool"]["robocop"]

    def test_generated_file_contains_rules_and_formatters(self, tmp_path):
        runner = CliRunner()
        with working_directory(tmp_path):
            runner.invoke(app, ["config", "init"])
        content = (tmp_path / "robocop.toml").read_text(encoding="utf-8")
        # a default-enabled rule appears as an active select entry with an inline comment
        assert '"todo-in-comment",  # Found a marker' in content
        # a default-enabled rule and its parameter in the configure section
        assert '# "todo-in-comment.markers=todo,fixme"' in content
        # a non-default (default-disabled) rule is listed commented out in select
        assert '# "unresolved-resource-import",' in content
        assert "(project rule)" in content
        # a default formatter and a disabled one
        assert "NormalizeSeparators" in content
        assert "Translate" in content

    def test_rules_listed_in_select(self, tmp_path):
        """Rules are represented as a select list, not as per-rule configure comment blocks."""
        runner = CliRunner()
        with working_directory(tmp_path):
            runner.invoke(app, ["config", "init"])
        data = tomllib.loads((tmp_path / "robocop.toml").read_text(encoding="utf-8"))
        select = data["tool"]["robocop"]["lint"]["select"]
        # only default-enabled rules are active entries
        assert "todo-in-comment" in select
        # non-default and project rules are commented out, not active
        assert "unresolved-resource-import" not in select

    def test_severity_documented_once(self, tmp_path):
        """The severity parameter is documented once, not repeated for every rule."""
        runner = CliRunner()
        with working_directory(tmp_path):
            runner.invoke(app, ["config", "init"])
        content = (tmp_path / "robocop.toml").read_text(encoding="utf-8")
        assert "Every rule also accepts a `severity` parameter" in content
        # `.severity=` should only appear in the single documentation example, not per rule
        # (`.severity_threshold=` is a different parameter and is excluded).
        severity_entries = [
            line for line in content.splitlines() if ".severity=" in line and ".severity_threshold=" not in line
        ]
        assert len(severity_entries) == 1
        assert "line-too-long.severity=E" in severity_entries[0]

    def test_target_version_is_major_only(self, tmp_path):
        runner = CliRunner()
        with working_directory(tmp_path):
            runner.invoke(app, ["config", "init"])
        data = tomllib.loads((tmp_path / "robocop.toml").read_text(encoding="utf-8"))
        # target_version line is commented, so assert the rendered value in raw text
        content = (tmp_path / "robocop.toml").read_text(encoding="utf-8")
        assert "# target_version = " in content
        for line in content.splitlines():
            if line.startswith("# target_version = "):
                value = line.split("=", 1)[1].strip().strip('"')
                assert value.isdigit(), f"target_version should be a major version, got {value!r}"
                break
        assert "lint" in data["tool"]["robocop"]

    def test_generated_file_reproduces_default_behaviour(self, tmp_path):
        """Using the generated file as configuration should not change which rules are enabled."""
        runner = CliRunner()
        with working_directory(tmp_path):
            runner.invoke(app, ["config", "init"])
            config_file = tmp_path / "robocop.toml"
            with_config = _read_enabled_summary(runner, ["list", "rules", "--config", str(config_file)])
        default = _read_enabled_summary(runner, ["list", "rules"])
        assert with_config == default

    def test_custom_output_path(self, tmp_path):
        runner = CliRunner()
        destination = tmp_path / "nested" / "custom.toml"
        with working_directory(tmp_path):
            result = runner.invoke(app, ["config", "init", "--output", str(destination)])
        assert result.exit_code == 0
        assert destination.exists()

    def test_existing_file_is_not_overwritten(self, tmp_path):
        runner = CliRunner()
        config_file = tmp_path / "robocop.toml"
        config_file.write_text("original", encoding="utf-8")
        with working_directory(tmp_path):
            result = runner.invoke(app, ["config", "init"])
        assert result.exit_code == 1
        assert "already exists" in result.stdout
        assert config_file.read_text(encoding="utf-8") == "original"

    def test_force_overwrites_existing_file(self, tmp_path):
        runner = CliRunner()
        config_file = tmp_path / "robocop.toml"
        config_file.write_text("original", encoding="utf-8")
        with working_directory(tmp_path):
            result = runner.invoke(app, ["config", "init", "--force"])
        assert result.exit_code == 0
        assert config_file.read_text(encoding="utf-8") != "original"
        assert "[tool.robocop]" in config_file.read_text(encoding="utf-8")

    def test_generated_config_can_be_used_for_check(self, tmp_path):
        runner = CliRunner()
        (tmp_path / "test.robot").write_text("*** Settings ***\n", encoding="utf-8")
        with working_directory(tmp_path):
            runner.invoke(app, ["config", "init"])
            config_file = tmp_path / "robocop.toml"
            result = runner.invoke(app, ["check", "--config", str(config_file), "--no-cache", "test.robot"])
        assert result.exit_code in (0, 1)
        assert "Unknown configuration key" not in result.stdout
