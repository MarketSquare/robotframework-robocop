"""Tests for validating keyword call arguments against the keyword definition."""

from __future__ import annotations

import pytest

from robocop.project.definitions import ArgumentsSpec, usage_name_pattern


def spec(*arguments: str) -> ArgumentsSpec:
    return ArgumentsSpec.from_arguments(list(arguments))


class TestArgumentsSpec:
    def test_no_arguments(self):
        parsed = spec()
        assert parsed.min_args == 0
        assert parsed.max_args == 0
        assert not parsed.accepts_named

    def test_positional(self):
        parsed = spec("${a}", "${b}")
        assert parsed.positional == ("a", "b")
        assert parsed.min_args == 2
        assert parsed.max_args == 2

    def test_defaults(self):
        parsed = spec("${a}", "${b}=2")
        assert parsed.min_args == 1
        assert parsed.max_args == 2

    def test_varargs(self):
        parsed = spec("${a}", "@{rest}")
        assert parsed.min_args == 1
        assert parsed.max_args is None

    def test_kwargs(self):
        parsed = spec("${a}", "&{opts}")
        assert parsed.accepts_named

    def test_named_only(self):
        parsed = spec("${a}", "@{}", "${strict}")
        assert parsed.named_only == ("strict",)

    def test_invalid_arguments_give_empty_spec(self):
        parsed = spec("not a variable")
        assert parsed == ArgumentsSpec()


class TestDescribeAccepted:
    @pytest.mark.parametrize(
        ("arguments", "expected"),
        [
            ((), "0 arguments"),
            (("${a}",), "1 argument"),
            (("${a}", "${b}"), "2 arguments"),
            (("${a}", "${b}=2"), "from 1 to 2 arguments"),
            (("${a}", "@{rest}"), "at least 1 argument"),
            (("@{rest}",), "at least 0 arguments"),
        ],
    )
    def test_description(self, arguments, expected):
        assert spec(*arguments).describe_accepted() == expected

    def test_named_only_included(self):
        assert spec("${a}", "@{}", "${strict}").describe_accepted() == ("1 argument and named-only argument ${strict}")


class TestValidateCall:
    @pytest.mark.parametrize(
        ("arguments", "call"),
        [
            ((), ()),
            (("${a}", "${b}"), ("1", "2")),
            (("${a}", "${b}"), ("a=1", "b=2")),
            (("${a}", "${b}"), ("1", "b=2")),
            (("${a}", "${b}=2"), ("1",)),
            (("${a}", "${b}=2"), ("1", "2")),
            (("${a}", "@{rest}"), ("1", "2", "3")),
            (("${a}", "&{opts}"), ("1", "anything=2")),
            (("${a}",), ("value=with=equals",)),
            (("${a}",), (r"escaped\=value",)),
            (("${a}", "@{}", "${strict}"), ("1", "strict=yes")),
        ],
    )
    def test_valid_calls(self, arguments, call):
        assert spec(*arguments).validate_call(call) is None

    def test_too_few(self):
        mismatch = spec("${a}", "${b}").validate_call(("1",))
        assert mismatch is not None
        assert mismatch.provided == 1
        assert mismatch.missing == ("b",)

    def test_too_many(self):
        mismatch = spec("${a}").validate_call(("1", "2"))
        assert mismatch is not None
        assert mismatch.provided == 2
        assert mismatch.missing == ()

    def test_missing_named_only(self):
        mismatch = spec("${a}", "@{}", "${strict}").validate_call(("1",))
        assert mismatch is not None
        assert mismatch.missing == ("strict",)

    def test_unknown_named_treated_as_positional(self):
        """Keyword does not accept free named arguments, so ``x=1`` is a positional value."""
        assert spec("${a}").validate_call(("x=1",)) is None
        assert spec().validate_call(("x=1",)) is not None

    def test_argument_given_twice_is_not_reported(self):
        assert spec("${a}", "${b}").validate_call(("1", "a=2")) is None

    def test_named_built_from_variable_is_not_reported(self):
        assert spec("${a}").validate_call(("${name}=1", "2", "3")) is None


class TestUsageNamePattern:
    def test_only_variable_matches_everything(self):
        assert usage_name_pattern("${name}") is None

    def test_prefix(self):
        pattern = usage_name_pattern("Login ${type}")
        assert pattern is not None
        assert pattern.fullmatch("loginadmin")
        assert not pattern.fullmatch("logout")

    def test_suffix(self):
        pattern = usage_name_pattern("${type} Login")
        assert pattern is not None
        assert pattern.fullmatch("adminlogin")

    def test_no_variable(self):
        pattern = usage_name_pattern("Login")
        assert pattern is not None
        assert pattern.fullmatch("login")
        assert not pattern.fullmatch("loginadmin")
