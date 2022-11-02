""" General E2E tests to catch any general issue in Robocop """

import sys
from pathlib import Path
from unittest import mock

import pytest
from packaging import version

import robocop.exceptions
from robocop.config import Config
from robocop.exceptions import (
    ArgumentFileNotFoundError,
    ConfigGeneralError,
    FileError,
    InvalidArgumentError,
    NestedArgumentFileError,
)
from robocop.rules import RuleSeverity
from robocop.run import Robocop
from robocop.utils.misc import ROBOT_VERSION, rf_supports_lang


@pytest.fixture
def robocop_instance():
    return Robocop(from_cli=True)


@pytest.fixture
def robocop_instance_not_cli():
    return Robocop(from_cli=False)


@pytest.fixture
def test_data_dir():
    return Path(Path(__file__).parent.parent, "test_data")


INVALID_TEST_DATA = Path(__file__).parent.parent / "test_data_invalid"


def should_run_with_config(robocop_instance, cfg):
    with mock.patch.object(sys, "argv", ["robocop", *cfg.split()]):
        config = Config(from_cli=True)
    robocop_instance.config = config
    with pytest.raises(SystemExit):
        robocop_instance.run()
    return robocop_instance


def configure_robocop(robocop_instance, args):
    with mock.patch.object(sys, "argv", ["robocop", *args.split()]):
        config = Config(from_cli=True)
    robocop_instance.config = config
    robocop_instance.reload_config()


class TestE2E:
    def test_run_all_checkers(self, robocop_instance, test_data_dir):
        should_run_with_config(robocop_instance, str(test_data_dir))

    def test_run_all_checkers_not_cli(self, robocop_instance_not_cli, test_data_dir):
        robocop_instance_not_cli.config.paths = [str(test_data_dir)]
        issues = robocop_instance_not_cli.run()
        assert issues
        assert isinstance(issues[0], dict)

    def test_run_all_checkers_not_recursive(self, robocop_instance, test_data_dir):
        should_run_with_config(robocop_instance, f"--no-recursive {test_data_dir}")

    def test_all_reports(self, robocop_instance, test_data_dir):
        should_run_with_config(robocop_instance, f"-r all {test_data_dir}")

    def test_no_issues_all_reports(self, robocop_instance, test_data_dir):
        should_run_with_config(robocop_instance, f'-r all {test_data_dir / "all_passing.robot"}')

    def test_ignore_file_with_pattern(self, robocop_instance, test_data_dir):
        should_run_with_config(robocop_instance, f"--ignore *.robot --include 0502 {test_data_dir}")

    def test_include_one_rule(self, robocop_instance, test_data_dir):
        should_run_with_config(robocop_instance, f"--include 0503 {test_data_dir}")

    def test_run_non_existing_file(self, robocop_instance):
        config = Config()
        config.paths = ["some_path"]
        robocop_instance.config = config
        with pytest.raises(FileError) as err:
            robocop_instance.run()
        assert 'File "some_path" does not exist' in str(err)

    def test_run_with_return_status_0(self, robocop_instance, test_data_dir):
        runner = should_run_with_config(robocop_instance, f"-c return_status:quality_gate:E=-1:W=-1 {test_data_dir}")
        assert runner.reports["return_status"].return_status == 0

    def test_run_with_return_status_bigger_than_zero(self, robocop_instance, test_data_dir):
        runner = should_run_with_config(
            robocop_instance,
            f"--configure return_status:quality_gate:E=0:W=0 {test_data_dir}",
        )
        assert runner.reports["return_status"].return_status > 0

    def test_configure_rule_severity(self, robocop_instance, test_data_dir):
        configure_robocop(robocop_instance, args=f"-c 0201:severity:E -c E0202:severity:I {test_data_dir}")

    def test_configure_rule_option(self, robocop_instance, test_data_dir):
        configure_robocop(robocop_instance, args=f"-c line-too-long:line_length:1000 {test_data_dir}")

    @pytest.mark.parametrize(
        "rule, expected",
        [
            ("idontexist", "Provided rule or report 'idontexist' does not exist."),
            (
                "not-enough-whitespace-after-newline-mark",
                r"Provided rule or report 'not-enough-whitespace-after-newline-mark' does not exist. "
                r"Did you mean:\n    not-enough-whitespace-after-newline-marker",
            ),
        ],
    )
    def test_configure_invalid_rule(self, robocop_instance, rule, expected, test_data_dir):
        with pytest.raises(ConfigGeneralError) as err:
            configure_robocop(robocop_instance, args=f"--configure {rule}:severity:E {test_data_dir}")
        assert expected in str(err)

    @pytest.mark.parametrize(
        "rules, expected",
        [
            ("invalid", f"Provided rule 'invalid' does not exist."),
            ("parsing-error,invalid", "Provided rule 'invalid' does not exist."),
            (
                "line-toolong",
                r"Provided rule 'line-toolong' does not exist. Did you mean:\n    line-too-long",
            ),
        ],
    )
    def test_include_exclude_invalid_rule(self, robocop_instance, rules, expected):
        for method in ("--include", "--exclude"):
            config = Config()
            config.parse_args([method, rules, "."])
            robocop_instance.config = config
            with pytest.raises(ConfigGeneralError) as err:
                robocop_instance.reload_config()
            assert expected in str(err)

    def test_configure_invalid_param(self, robocop_instance, test_data_dir):
        with pytest.raises(ConfigGeneralError) as err:
            configure_robocop(robocop_instance, args=f"--configure 0202:idontexist:E {test_data_dir}")
        assert "Provided param 'idontexist' for rule 'missing-doc-test-case' does not exist. " in err.value.args[0]

    def test_configure_invalid_config(self, robocop_instance, test_data_dir):
        with pytest.raises(ConfigGeneralError) as err:
            configure_robocop(robocop_instance, args=f"--configure 0202: {test_data_dir}")
        assert "Provided invalid config: '0202:' (general pattern: <rule>:<param>:<value>)" in str(err)

    def test_configure_return_status_invalid_value(self, robocop_instance, test_data_dir):
        should_run_with_config(
            robocop_instance,
            f"--configure return_status:quality_gate:E0 {test_data_dir}",
        )

    def test_configure_return_status_with_non_exist(self, robocop_instance):
        with pytest.raises(ConfigGeneralError) as err:
            configure_robocop(robocop_instance, args=f"--configure return_status:smth:E=0:W=0 {test_data_dir}")
        assert "Provided param 'smth' for report 'return_status' does not exist" in str(err)

    def test_use_argument_file(self, robocop_instance, test_data_dir):
        config = Config()
        config.parse_args(["-A", str(test_data_dir / "argument_file" / "args.txt")])

    def test_use_not_existing_argument_file(self, test_data_dir):
        config = Config()
        with pytest.raises(ArgumentFileNotFoundError) as err:
            config.parse_args(["--argumentfile", "some_file", str(test_data_dir)])
        assert 'Argument file "some_file" does not exist' in str(err)

    def test_argument_file_without_path(self):
        config = Config()
        with pytest.raises(ArgumentFileNotFoundError) as err:
            config.parse_args(["--argumentfile"])
        assert 'Argument file "" does not exist' in str(err)

    def test_use_nested_argument_file(self, test_data_dir):
        config = Config()
        nested_args_path = str(test_data_dir / "argument_file" / "args_nested.txt")
        with pytest.raises(NestedArgumentFileError) as err:
            config.parse_args(["-A", nested_args_path, str(test_data_dir)])
        assert "Nested argument file in " in str(err)

    @pytest.mark.parametrize("threshold", ["i", "I", "e", "error", "W", "WARNING"])
    def test_set_rule_threshold(self, threshold, robocop_instance, test_data_dir):
        with mock.patch.object(sys, "argv", f"robocop --threshold {threshold}".split()):
            Config(from_cli=True)

    def test_set_rule_invalid_threshold(self, robocop_instance, test_data_dir):
        error = "Invalid configuration for Robocop:\nInvalid severity value '3'. Choose one from: I, W, E."
        with mock.patch.object(
            sys,
            "argv",
            "robocop --threshold 3".split(),
        ), pytest.raises(InvalidArgumentError, match=error):
            Config(from_cli=True)

    def test_configure_severity(self, robocop_instance, test_data_dir):
        # issue 402
        configure_robocop(
            robocop_instance,
            args=f"--configure wrong-case-in-keyword-name:severity:E "
            f"-c wrong-case-in-keyword-name:convention:first_word_capitalized "
            f"{test_data_dir}",
        )

    def test_diff_encoded_chars(self, robocop_instance, test_data_dir, capsys):
        # issue 455
        should_run_with_config(robocop_instance, str(test_data_dir / "encodings.robot"))
        out, _ = capsys.readouterr()
        assert "Failed to decode" not in out

    def test_override_severity(self, test_data_dir):
        config = Config()
        config.threshold = RuleSeverity("W")
        config.configure = ["missing-doc-test-case:severity:i"]
        test_file = test_data_dir / "override_severity" / "test.robot"
        config.paths = [str(test_file)]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        assert not robocop_instance.reports["json_report"].issues

    @pytest.mark.skipif(ROBOT_VERSION > version.parse("4.0"), reason="Error occurs only in RF < 5")
    def test_handling_error_in_robot_module(self):
        config = Config()
        test_file = INVALID_TEST_DATA / "invalid_syntax" / "invalid_file.robot"
        config.paths = [str(test_file)]
        robocop_instance = Robocop(config=config)
        with pytest.raises(robocop.exceptions.RobotFrameworkParsingError):
            robocop_instance.run()


@pytest.mark.skipif(not rf_supports_lang(), reason="Requires RF 6.0 with languages support")
class TestTranslatedRobot:
    @staticmethod
    def assert_issue_was_found(robocop_instance, issue_desc):
        assert any(issue_desc in issue["description"] for issue in robocop_instance.reports["json_report"].issues)

    @staticmethod
    def assert_issue_was_not_found(robocop_instance, issue_desc):
        assert all(issue_desc not in issue["description"] for issue in robocop_instance.reports["json_report"].issues)

    def test_translated_default_lang(self, test_data_dir):
        config = Config()
        test_file = test_data_dir / "translation" / "fi.robot"
        config.paths = [str(test_file)]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        return self.assert_issue_was_found(robocop_instance, "Unrecognized section")

    def test_translated_fi_lang(self, test_data_dir):
        config = Config()
        test_file = test_data_dir / "translation" / "fi.robot"
        config.paths = [str(test_file)]
        config.language = ["fi"]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        return self.assert_issue_was_not_found(robocop_instance, "Unrecognized section")

    def test_translated_mixed_with_fi_lang(self, test_data_dir):
        config = Config()
        test_file = test_data_dir / "translation" / "fi_and_pl.robot"
        config.paths = [str(test_file)]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        return self.assert_issue_was_found(robocop_instance, "Unrecognized section")

    def test_translated_mixed_with_fi_and_pl_lang(self, test_data_dir):
        config = Config()
        test_file = test_data_dir / "translation" / "fi_and_pl.robot"
        config.paths = [str(test_file)]
        config.language = ["fi", "pl"]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        return self.assert_issue_was_not_found(robocop_instance, "Unrecognized section")
