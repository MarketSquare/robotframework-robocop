"""Tests for parsing of the ``--variable`` option and variables from the configuration file."""

from __future__ import annotations

import pytest
import typer

from robocop.config.parser import normalize_config_keys, parse_variables
from robocop.config.schema import RawConfig


class TestParseVariables:
    def test_none(self):
        assert parse_variables(None) is None

    def test_empty(self):
        assert parse_variables([]) is None

    def test_simple(self):
        assert parse_variables(["NAME:value"]) == {"NAME": "value"}

    def test_multiple(self):
        assert parse_variables(["A:1", "B:2"]) == {"A": "1", "B": "2"}

    def test_value_with_colons(self):
        assert parse_variables(["URL:http://localhost:8080/path"]) == {"URL": "http://localhost:8080/path"}

    def test_empty_value(self):
        assert parse_variables(["NAME:"]) == {"NAME": ""}

    def test_name_is_stripped(self):
        assert parse_variables([" NAME :value"]) == {"NAME": "value"}

    def test_later_value_wins(self):
        assert parse_variables(["NAME:first", "NAME:second"]) == {"NAME": "second"}

    def test_name_with_hyphen(self):
        assert parse_variables(["MY-VAR:value"]) == {"MY-VAR": "value"}

    @pytest.mark.parametrize("value", ["NAME", "", "  ", ":value"])
    def test_invalid(self, value):
        with pytest.raises(typer.BadParameter):
            parse_variables([value])


class TestNormalizeConfigKeys:
    def test_dashes_replaced(self):
        assert normalize_config_keys({"line-length": 120}) == {"line_length": 120}

    def test_nested_dashes_replaced(self):
        assert normalize_config_keys({"tool": {"line-length": 120}}) == {"tool": {"line_length": 120}}

    def test_variable_names_are_not_normalized(self):
        config = {"variables": {"MY-VAR": "value", "OTHER_VAR": "value"}}
        assert normalize_config_keys(config) == config

    def test_nested_variable_names_are_not_normalized(self):
        config = {"lint": {"variables": {"MY-VAR": "value"}}}
        assert normalize_config_keys(config) == config


class TestPathOptionsFromConfigFile:
    """``python-path`` and ``variable-files`` from the configuration file are relative to the configuration file."""

    def test_python_path_is_resolved_relative_to_config(self, tmp_path):
        config_path = tmp_path / "robocop.toml"
        raw_config = RawConfig.from_dict({"python_path": ["libs", "resources"]}, config_path)
        assert raw_config.python_path == [str(tmp_path / "libs"), str(tmp_path / "resources")]

    def test_variable_files_are_resolved_relative_to_config(self, tmp_path):
        config_path = tmp_path / "robocop.toml"
        raw_config = RawConfig.from_dict({"variable_files": ["vars/values.py"]}, config_path)
        assert raw_config.variable_files == [str(tmp_path / "vars" / "values.py")]

    def test_absolute_path_is_not_changed(self, tmp_path):
        config_path = tmp_path / "robocop.toml"
        absolute = str((tmp_path / "libs").absolute())
        raw_config = RawConfig.from_dict({"python_path": [absolute]}, config_path)
        assert raw_config.python_path == [absolute]

    def test_glob_pattern_is_kept(self, tmp_path):
        config_path = tmp_path / "robocop.toml"
        raw_config = RawConfig.from_dict({"python_path": ["libs/*"]}, config_path)
        assert raw_config.python_path == [str(tmp_path / "libs" / "*")]

    def test_not_defined(self, tmp_path):
        raw_config = RawConfig.from_dict({}, tmp_path / "robocop.toml")
        assert raw_config.python_path is None
        assert raw_config.variable_files is None
