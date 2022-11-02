import io
import pathlib

import pytest

from robocop.config import Config
from robocop.version import __version__


@pytest.fixture()
def config():
    return Config()


class TestArgumentValidation:
    def test_prog_name(self, config):
        parser = config._create_parser()
        assert parser.prog == "robocop"

    def test_parser_default_help_disabled(self, config):
        parser = config._create_parser()
        assert not parser.add_help

    def test_default_args(self, config):
        assert config.filetypes == {".resource", ".robot", ".tsv"}
        assert config.include == set()
        assert config.exclude == set()
        assert config.reports, ["return_status"]
        assert config.configure == []
        assert config.format == "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
        assert config.paths == ["."]
        assert config.output is None
        assert not config.list_reports

    def test_default_args_after_parse(self, config):
        config.parse_args([""])
        assert config.filetypes == {".resource", ".robot", ".tsv"}
        assert config.include == set()
        assert config.exclude == set()
        assert config.reports == ["return_status"]
        assert config.configure == []
        assert config.format == "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
        assert config.paths == [""]
        assert config.output is None

    def test_filetypes_duplicate_defaults(self, config):
        config.parse_args(["--filetypes", "robot,resource", ""])
        assert config.filetypes == {".resource", ".robot", ".tsv"}

    def test_filetypes_duplicate_dot_prefixed_defaults(self, config):
        config.parse_args(["--filetypes", ".robot,.resource", ""])
        assert config.filetypes == {".resource", ".robot", ".tsv"}

    def test_include_one_rule(self, config):
        rule_name = "missing-doc-keyword"
        config.parse_args(["--include", rule_name, ""])
        assert config.include == {rule_name}

    def test_include_two_same_rules_comma_separated(self, config):
        rule_name = "missing-doc-keyword"
        config.parse_args(["--include", ",".join([rule_name, rule_name]), ""])
        assert config.include == {rule_name}

    def test_include_two_same_rules_provided_separately(self, config):
        rule_name = "missing-doc-keyword"
        config.parse_args(["--include", rule_name, "--include", rule_name, ""])
        assert config.include == {rule_name}

    def test_include_two_different_rules_comma_separated(self, config):
        rule_name1 = "missing-doc-keyword"
        rule_name2 = "not-allowed-char-in-name"
        rules_names = ",".join([rule_name1, rule_name2])
        config.parse_args(["--include", rules_names, ""])
        assert config.include == {rule_name1, rule_name2}

    def test_include_two_different_rules_provided_separately(self, config):
        rule_name1 = "missing-doc-keyword"
        rule_name2 = "not-allowed-char-in-name"
        config.parse_args(["--include", rule_name1, "--include", rule_name2, ""])
        assert config.include == {rule_name1, rule_name2}

    def test_exclude_one_rule(self, config):
        rule_name = "missing-doc-keyword"
        config.parse_args(["--exclude", rule_name, ""])
        assert config.exclude == {rule_name}

    def test_exclude_two_same_rules_comma_separated(self, config):
        rule_name = "missing-doc-keyword"
        config.parse_args(["--exclude", ",".join([rule_name, rule_name]), ""])
        assert config.exclude == {rule_name}

    def test_exclude_two_same_rules_provided_separately(self, config):
        rule_name = "missing-doc-keyword"
        config.parse_args(["--exclude", rule_name, "--exclude", rule_name, ""])
        assert config.exclude == {rule_name}

    def test_exclude_two_different_rules_comma_separated(self, config):
        rule_name1 = "missing-doc-keyword"
        rule_name2 = "not-allowed-char-in-name"
        rules_names = ",".join([rule_name1, rule_name2])
        config.parse_args(["--exclude", rules_names, ""])
        assert config.exclude == {rule_name1, rule_name2}

    def test_exclude_two_different_rules_provided_separately(self, config):
        rule_name1 = "missing-doc-keyword"
        rule_name2 = "not-allowed-char-in-name"
        config.parse_args(["--exclude", rule_name1, "--exclude", rule_name2, ""])
        assert config.exclude == {rule_name1, rule_name2}

    def test_format_overwrite_default(self, config):
        default_format = "{source}:{line}:{col} [{severity}] {rule_id} {desc}"
        config.parse_args(["--format", default_format, ""])
        assert config.format == default_format

    def test_format_empty(self, config):
        empty_format = ""
        config.parse_args(["--format", empty_format, ""])
        assert config.format == ""

    def test_format_new_value(self, config):
        new_format = "{source}: {rule_id} {desc}"
        config.parse_args(["--format", new_format, ""])
        assert config.format == new_format

    def test_output_new_value(self, config):
        output_file = "results"
        config.parse_args(["--output", output_file, ""])
        assert isinstance(config.output, io.TextIOWrapper)
        assert config.output.name == output_file
        assert config.output.mode == "w"
        assert pathlib.Path(output_file).exists()
        # parser will not close the file itself
        if not config.output.closed:
            config.output.close()
        # remove created file
        pathlib.Path(output_file).unlink()

    @pytest.mark.parametrize("cmd", ["-h", "--help"])
    def test_help_message(self, config, cmd, capsys):
        with pytest.raises(SystemExit):
            config.parse_args([cmd])
        out, _ = capsys.readouterr()
        assert "usage:" in out

    @pytest.mark.parametrize("cmd", ["-v", "--version"])
    def test_version_number(self, config, cmd, capsys):
        with pytest.raises(SystemExit):
            config.parse_args(["-v"])
        out, _ = capsys.readouterr()
        assert __version__ in out

    def test_paths_new_value(self, config):
        config.parse_args(["tests.robot"])
        assert config.paths == ["tests.robot"]

    def test_paths_two_values(self, config):
        config.parse_args(["tests.robot", "test2.robot"])
        assert config.paths == ["tests.robot", "test2.robot"]

    def test_list_reports(self, config):
        config.parse_args(["--list-reports"])
        assert config.list_reports

    def test_single_language(self, config):
        config.parse_args(["--lang", "fi"])
        assert ["fi"] == config.language

    def test_two_languages(self, config):
        config.parse_args(["--lang", "fi,pl"])
        assert ["fi", "pl"] == config.language
