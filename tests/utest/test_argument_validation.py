import io
import pathlib
import unittest
from io import StringIO
from unittest.mock import patch

import pytest

from robocop.config import Config
from robocop.version import __version__


@pytest.fixture()
def config():
    return Config()


class TestArgumentValidation:
    def test_prog_name(self, config):
        assert config.parser.prog == "robocop"

    def test_parser_default_help_disabled(self, config):
        assert not config.parser.add_help

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
        args = config.parse_opts([""])
        assert args.filetypes == {".resource", ".robot", ".tsv"}
        assert args.include == set()
        assert args.exclude == set()
        assert args.reports == ["return_status"]
        assert args.configure == []
        assert args.format == "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
        assert args.paths == [""]
        assert args.output is None

    def test_filetypes_duplicate_defaults(self, config):
        args = config.parse_opts(["--filetypes", "robot,resource", ""])
        assert args.filetypes == {".resource", ".robot", ".tsv"}

    def test_filetypes_duplicate_dot_prefixed_defaults(self, config):
        args = config.parse_opts(["--filetypes", ".robot,.resource", ""])
        assert args.filetypes == {".resource", ".robot", ".tsv"}

    def test_include_one_rule(self, config):
        rule_name = "missing-keyword-doc"
        args = config.parse_opts(["--include", rule_name, ""])
        assert args.include == {rule_name}

    def test_include_two_same_rules_comma_separated(self, config):
        rule_name = "missing-keyword-doc"
        args = config.parse_opts(["--include", ",".join([rule_name, rule_name]), ""])
        assert args.include == {rule_name}

    def test_include_two_same_rules_provided_separately(self, config):
        rule_name = "missing-keyword-doc"
        args = config.parse_opts(["--include", rule_name, "--include", rule_name, ""])
        assert args.include == {rule_name}

    def test_include_two_different_rules_comma_separated(self, config):
        rule_name1 = "missing-keyword-doc"
        rule_name2 = "not-allowed-char-in-name"
        rules_names = ",".join([rule_name1, rule_name2])
        args = config.parse_opts(["--include", rules_names, ""])
        assert args.include == {rule_name1, rule_name2}

    def test_include_two_different_rules_provided_separately(self, config):
        rule_name1 = "missing-keyword-doc"
        rule_name2 = "not-allowed-char-in-name"
        args = config.parse_opts(["--include", rule_name1, "--include", rule_name2, ""])
        assert args.include == {rule_name1, rule_name2}

    def test_exclude_one_rule(self, config):
        rule_name = "missing-keyword-doc"
        args = config.parse_opts(["--exclude", rule_name, ""])
        assert args.exclude == {rule_name}

    def test_exclude_two_same_rules_comma_separated(self, config):
        rule_name = "missing-keyword-doc"
        args = config.parse_opts(["--exclude", ",".join([rule_name, rule_name]), ""])
        assert args.exclude == {rule_name}

    def test_exclude_two_same_rules_provided_separately(self, config):
        rule_name = "missing-keyword-doc"
        args = config.parse_opts(["--exclude", rule_name, "--exclude", rule_name, ""])
        assert args.exclude == {rule_name}

    def test_exclude_two_different_rules_comma_separated(self, config):
        rule_name1 = "missing-keyword-doc"
        rule_name2 = "not-allowed-char-in-name"
        rules_names = ",".join([rule_name1, rule_name2])
        args = config.parse_opts(["--exclude", rules_names, ""])
        assert args.exclude == {rule_name1, rule_name2}

    def test_exclude_two_different_rules_provided_separately(self, config):
        rule_name1 = "missing-keyword-doc"
        rule_name2 = "not-allowed-char-in-name"
        args = config.parse_opts(["--exclude", rule_name1, "--exclude", rule_name2, ""])
        assert args.exclude == {rule_name1, rule_name2}

    def test_format_overwrite_default(self, config):
        default_format = "{source}:{line}:{col} [{severity}] {rule_id} {desc}"
        args = config.parse_opts(["--format", default_format, ""])
        assert args.format == default_format

    def test_format_empty(self, config):
        empty_format = ""
        args = config.parse_opts(["--format", empty_format, ""])
        assert args.format == ""

    def test_format_new_value(self, config):
        new_format = "{source}: {rule_id} {desc}"
        args = config.parse_opts(["--format", new_format, ""])
        assert args.format == new_format

    def test_output_new_value(self, config):
        output_file = "results"
        args = config.parse_opts(["--output", output_file, ""])
        assert isinstance(args.output, io.TextIOWrapper)
        assert args.output.name == output_file
        assert args.output.mode == "w"
        assert pathlib.Path(output_file).exists()
        # parser will not close the file itself
        if not config.output.closed:
            config.output.close()
        # remove created file
        pathlib.Path(output_file).unlink()

    @pytest.mark.parametrize("cmd", ["-h", "--help"])
    def test_help_message(self, config, cmd, capsys):
        with pytest.raises(SystemExit):
            config.parse_opts([cmd])
        out, _ = capsys.readouterr()
        assert "usage:" in out

    @pytest.mark.parametrize("cmd", ["-v", "--version"])
    def test_version_number(self, config, cmd, capsys):
        with pytest.raises(SystemExit):
            config.parse_opts(["-v"])
        out, _ = capsys.readouterr()
        assert __version__ in out

    def test_paths_new_value(self, config):
        args = config.parse_opts(["tests.robot"])
        assert args.paths == ["tests.robot"]

    def test_paths_two_values(self, config):
        args = config.parse_opts(["tests.robot", "test2.robot"])
        assert args.paths == ["tests.robot", "test2.robot"]

    def test_list_reports(self, config):
        args = config.parse_opts(["--list-reports"])
        assert args.list_reports

    def test_single_language(self, config):
        args = config.parse_opts(["--lang", "fi"])
        assert ["fi"] == args

    def test_two_languages(self, config):
        args = config.parse_opts(["--lang", "fi,pl"])
        assert ["fi", "pl"] == args.lang
