"""Tests for parsing of the ``--variable`` option and variables from the configuration file."""

from __future__ import annotations

import pytest
import typer

from robocop.config.parser import normalize_config_keys, parse_variables


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
