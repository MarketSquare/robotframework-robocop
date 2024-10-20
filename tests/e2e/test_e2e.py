"""General E2E tests to catch any general issue in Robocop"""

import re
import sys
from pathlib import Path
from unittest import mock

import pytest

import robocop.exceptions
from robocop.config import Config
from robocop.exceptions import CircularArgumentFileError, ConfigGeneralError, FileError, InvalidArgumentError
from robocop.rules import RuleSeverity
from robocop.run import Robocop
from robocop.utils.misc import ROBOT_VERSION, rf_supports_lang
from robocop.utils.version_matching import Version


@pytest.fixture
def robocop_instance():
    return Robocop(from_cli=True)


@pytest.fixture
def robocop_instance_not_cli():
    return Robocop(from_cli=False)


TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
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
    def test_run_all_checkers(self, robocop_instance):
        should_run_with_config(robocop_instance, str(TEST_DATA_DIR))

    def test_run_all_checkers_not_cli(self, robocop_instance_not_cli):
        robocop_instance_not_cli.config.paths = [str(TEST_DATA_DIR)]
        issues = robocop_instance_not_cli.run()
        assert issues
        assert isinstance(issues[0], dict)

    def test_run_all_checkers_not_recursive(self, robocop_instance):
        should_run_with_config(robocop_instance, f"--no-recursive {TEST_DATA_DIR}")

    @pytest.mark.parametrize("persistent", [True, False])
    def test_all_reports(self, robocop_instance, persistent):
        if persistent:
            command = f"--persistent -r all {TEST_DATA_DIR}"
        else:
            command = f"-r all {TEST_DATA_DIR}"
        should_run_with_config(robocop_instance, command)

    @pytest.mark.parametrize("persistent", [True, False])
    def test_no_issues_all_reports(self, robocop_instance, persistent, capfd):
        if persistent:
            command = f'--persistent -r all {TEST_DATA_DIR / "all_passing.robot"}'
        else:
            command = f'-r all {TEST_DATA_DIR / "all_passing.robot"}'
        should_run_with_config(robocop_instance, command)
        out, err = capfd.readouterr()
        assert "No issues found." in out

    def test_list_all_reports(self, robocop_instance, capfd):
        exp_msg = (
            "Available reports:\n"
            "compare_runs         - Compare reports between two Robocop runs. (disabled - non-default)\n"
            "file_stats           - Prints overall statistics about number of processed files (disabled)\n"
            "json_report          - Produces JSON file with found issues (disabled - non-default)\n"
            "rules_by_error_type  - Prints total number of issues grouped by severity (disabled)\n"
            "rules_by_id          - Groups detected issues by rule id and prints it ordered by most common (disabled)\n"
            "sarif                - Generate SARIF output file (disabled - non-default)\n"
            "scan_timer           - Returns Robocop execution time (disabled)\n"
            "timestamp            - Returns Robocop execution timestamp. (disabled)\n"
            "version              - Returns Robocop version (disabled)\n"
            "\nEnable report by passing report name using --reports option. "
            "Use `all` to enable all default reports. "
            "Non-default reports can be only enabled using report name.\n"
        )
        for option in ("--list-reports", "-lr"):
            should_run_with_config(robocop_instance, option)
            out, err = capfd.readouterr()
            assert out == exp_msg

    def test_list_enabled_reports(self, robocop_instance, capfd):
        def with_config_output_should_be(config: str, expected_msg: str):
            should_run_with_config(robocop_instance, config)
            out, err = capfd.readouterr()
            assert out == expected_msg

        for option in ("--list-reports", "-lr"):
            exp_nothing_enabled = (
                "Available reports:\n"
                "\nEnable report by passing report name using --reports option. "
                "Use `all` to enable all default reports. "
                "Non-default reports can be only enabled using report name.\n"
            )
            with_config_output_should_be(f"{option} ENABLED", exp_nothing_enabled)
            with_config_output_should_be(f"--reports version,sarif,None {option} ENABLED", exp_nothing_enabled)
            with_config_output_should_be(f"--reports None {option} ENABLED", exp_nothing_enabled)
            exp_msg = (
                "Available reports:\n"
                "sarif                - Generate SARIF output file (enabled - non-default)\n"
                "version              - Returns Robocop version (enabled)\n"
                "\nEnable report by passing report name using --reports option. "
                "Use `all` to enable all default reports. "
                "Non-default reports can be only enabled using report name.\n"
            )
            config = f"--reports version,sarif {option} ENABLED"
            with_config_output_should_be(config, exp_msg)

    def test_list_disabled_reports(self, robocop_instance, capfd):
        for option in ("--list-reports", "-lr"):
            exp_msg = (
                "Available reports:\n"
                "compare_runs         - Compare reports between two Robocop runs. (disabled - non-default)\n"
                "file_stats           - Prints overall statistics about number of processed files (disabled)\n"
                "json_report          - Produces JSON file with found issues (disabled - non-default)\n"
                "rules_by_error_type  - Prints total number of issues grouped by severity (disabled)\n"
                "rules_by_id          - Groups detected issues by rule id and prints it ordered by most common "
                "(disabled)\n"
                "sarif                - Generate SARIF output file (disabled - non-default)\n"
                "scan_timer           - Returns Robocop execution time (disabled)\n"
                "timestamp            - Returns Robocop execution timestamp. (disabled)\n"
                "version              - Returns Robocop version (disabled)\n"
                "\nEnable report by passing report name using --reports option. "
                "Use `all` to enable all default reports. "
                "Non-default reports can be only enabled using report name.\n"
            )
            config = f"{option} DISABLED"
            should_run_with_config(robocop_instance, config)
            out, err = capfd.readouterr()
            assert out == exp_msg
            exp_msg = (
                "Available reports:\n"
                "compare_runs         - Compare reports between two Robocop runs. (disabled - non-default)\n"
                "file_stats           - Prints overall statistics about number of processed files (disabled)\n"
                "json_report          - Produces JSON file with found issues (disabled - non-default)\n"
                "rules_by_error_type  - Prints total number of issues grouped by severity (disabled)\n"
                "rules_by_id          - Groups detected issues by rule id and prints it ordered by most common "
                "(disabled)\n"
                "scan_timer           - Returns Robocop execution time (disabled)\n"
                "timestamp            - Returns Robocop execution timestamp. (disabled)\n"
                "\nEnable report by passing report name using --reports option. "
                "Use `all` to enable all default reports. "
                "Non-default reports can be only enabled using report name.\n"
            )
            config = f"--reports version,sarif {option} DISABLED"
            should_run_with_config(robocop_instance, config)
            out, err = capfd.readouterr()
            assert out == exp_msg

    def test_ignore_file_with_pattern(self, robocop_instance):
        should_run_with_config(robocop_instance, f"--ignore *.robot --include 0502 {TEST_DATA_DIR}")

    def test_ignore_dir_with_pattern(self, robocop_instance, capfd):
        should_run_with_config(robocop_instance, f"--ignore {TEST_DATA_DIR}* {TEST_DATA_DIR}")
        out, err = capfd.readouterr()
        assert not out

    def test_include_one_rule(self, robocop_instance):
        should_run_with_config(robocop_instance, f"--include 0503 {TEST_DATA_DIR}")

    def test_run_non_existing_file(self, robocop_instance):
        config = Config()
        config.paths = ["some_path"]
        robocop_instance.config = config
        with pytest.raises(FileError) as err:
            robocop_instance.run()
        assert 'File "some_path" does not exist' in str(err)

    def test_run_with_return_status_0(self, robocop_instance):
        runner = should_run_with_config(robocop_instance, f"-c return_status:quality_gate:E=-1:W=-1 {TEST_DATA_DIR}")
        assert runner.reports["return_status"].return_status == 0

    def test_run_with_return_status_bigger_than_zero(self, robocop_instance):
        runner = should_run_with_config(
            robocop_instance,
            f"--configure return_status:quality_gate:E=0:W=0 {TEST_DATA_DIR}",
        )
        assert runner.reports["return_status"].return_status > 0

    def test_configure_rule_severity(self, robocop_instance):
        configure_robocop(robocop_instance, args=f"-c 0201:severity:E -c E0202:severity:I {TEST_DATA_DIR}")

    def test_configure_rule_option(self, robocop_instance):
        configure_robocop(robocop_instance, args=f"-c line-too-long:line_length:1000 {TEST_DATA_DIR}")

    @pytest.mark.parametrize(
        ("rule", "expected"),
        [
            ("idontexist", "Provided rule or report 'idontexist' does not exist."),
            (
                "not-enough-whitespace-after-newline-mark",
                r"Provided rule or report 'not-enough-whitespace-after-newline-mark' does not exist. "
                r"Did you mean:\n    not-enough-whitespace-after-newline-marker",
            ),
        ],
    )
    def test_configure_invalid_rule(self, robocop_instance, rule, expected):
        with pytest.raises(ConfigGeneralError) as err:
            configure_robocop(robocop_instance, args=f"--configure {rule}:severity:E {TEST_DATA_DIR}")
        assert expected in str(err)

    @pytest.mark.parametrize(
        ("rules", "expected"),
        [
            ("invalid", "Provided rule 'invalid' does not exist."),
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

    def test_configure_invalid_param(self, robocop_instance):
        with pytest.raises(ConfigGeneralError) as err:
            configure_robocop(robocop_instance, args=f"--configure 0202:idontexist:E {TEST_DATA_DIR}")
        assert "Provided param 'idontexist' for rule 'missing-doc-test-case' does not exist. " in err.value.args[0]

    def test_configure_invalid_config(self, robocop_instance):
        with pytest.raises(ConfigGeneralError) as err:
            configure_robocop(robocop_instance, args=f"--configure 0202: {TEST_DATA_DIR}")
        assert "Provided invalid config: '0202:' (general pattern: <rule>:<param>:<value>)" in str(err)

    def test_configure_return_status_invalid_value(self, robocop_instance):
        should_run_with_config(
            robocop_instance,
            f"--configure return_status:quality_gate:E0 {TEST_DATA_DIR}",
        )

    def test_configure_return_status_with_non_exist(self, robocop_instance):
        with pytest.raises(ConfigGeneralError) as err:
            configure_robocop(robocop_instance, args=f"--configure return_status:smth:E=0:W=0 {TEST_DATA_DIR}")
        assert "Provided param 'smth' for report 'return_status' does not exist" in str(err)

    def test_use_argument_file(self, robocop_instance):
        config = Config()
        config.parse_args(["-A", str(TEST_DATA_DIR / "argument_file" / "args.txt")])

    def test_use_circular_argument_file(self):
        config = Config()
        nested_args_path = str(TEST_DATA_DIR / "argument_file" / "args_nested.txt")
        with pytest.raises(CircularArgumentFileError) as err:
            config.parse_args(["-A", nested_args_path, str(TEST_DATA_DIR)])
        assert "Circular argument file import in " in str(err)

    @pytest.mark.parametrize("threshold", ["i", "I", "e", "error", "W", "WARNING"])
    def test_set_rule_threshold(self, threshold, robocop_instance):
        with mock.patch.object(sys, "argv", f"robocop --threshold {threshold}".split()):
            Config(from_cli=True)

    def test_set_rule_invalid_threshold(self, robocop_instance):
        error = "Invalid configuration for Robocop:\nInvalid severity value '3'. Choose one from: I, W, E."
        with (
            mock.patch.object(
                sys,
                "argv",
                "robocop --threshold 3".split(),
            ),
            pytest.raises(InvalidArgumentError, match=error),
        ):
            Config(from_cli=True)

    def test_configure_severity(self, robocop_instance):
        # issue 402
        configure_robocop(
            robocop_instance,
            args=f"--configure wrong-case-in-keyword-name:severity:E "
            f"-c wrong-case-in-keyword-name:convention:first_word_capitalized "
            f"{TEST_DATA_DIR}",
        )

    def test_diff_encoded_chars(self, robocop_instance, capsys):
        # issue 455
        should_run_with_config(robocop_instance, str(TEST_DATA_DIR / "encodings.robot"))
        out, _ = capsys.readouterr()
        assert "Failed to decode" not in out

    def test_override_severity(self):
        config = Config()
        config.threshold = RuleSeverity("W")
        config.configure = ["missing-doc-test-case:severity:i"]
        test_file = TEST_DATA_DIR / "override_severity" / "test.robot"
        config.paths = [str(test_file)]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        assert not robocop_instance.reports["internal_json_report"].issues

    @pytest.mark.skipif(ROBOT_VERSION > Version("4.0"), reason="Error occurs only in RF < 5")  # noqa: SIM300
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
        assert any(
            issue_desc in issue["description"] for issue in robocop_instance.reports["internal_json_report"].issues
        )

    @staticmethod
    def assert_issue_was_not_found(robocop_instance, issue_desc):
        assert all(
            issue_desc not in issue["description"] for issue in robocop_instance.reports["internal_json_report"].issues
        )

    def test_translated_default_lang(self):
        config = Config()
        test_file = TEST_DATA_DIR / "translation" / "fi.robot"
        config.paths = [str(test_file)]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        return self.assert_issue_was_found(robocop_instance, "Invalid section")

    def test_translated_fi_lang(self):
        config = Config()
        test_file = TEST_DATA_DIR / "translation" / "fi.robot"
        config.paths = [str(test_file)]
        config.language = ["fi"]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        return self.assert_issue_was_not_found(robocop_instance, "Invalid section")

    def test_translated_mixed_with_fi_lang(self):
        config = Config()
        test_file = TEST_DATA_DIR / "translation" / "fi_and_pl.robot"
        config.paths = [str(test_file)]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        return self.assert_issue_was_found(robocop_instance, "Invalid section")

    def test_translated_mixed_with_fi_and_pl_lang(self):
        config = Config()
        test_file = TEST_DATA_DIR / "translation" / "fi_and_pl.robot"
        config.paths = [str(test_file)]
        config.language = ["fi", "pl"]
        robocop_instance = Robocop(config=config)
        robocop_instance.run()
        return self.assert_issue_was_not_found(robocop_instance, "Invalid section")

    def test_all_rules_have_added_in_version_info(self, robocop_instance):
        robocop_instance.reload_config()
        without_version = {rule.name for rule in robocop_instance.rules.values() if not rule.added_in_version}
        assert without_version == set()

    def test_all_builtin_rules_should_be_enabled_by_default(self, robocop_instance):
        robocop_instance.reload_config()
        builtin_rules = [
            rule for rule in robocop_instance.rules.values() if not rule.community_rule and not rule.deprecated
        ]
        assert builtin_rules != []
        disabled_builtin = {rule.name for rule in builtin_rules if not rule.enabled and rule.enabled_in_version}
        assert disabled_builtin == set()

    def test_all_community_rules_should_be_disabled_by_default(self, robocop_instance):
        robocop_instance.reload_config()
        community_rules = [rule for rule in robocop_instance.rules.values() if rule.community_rule]
        assert community_rules != []
        enabled_community = {rule.name for rule in community_rules if rule.enabled}
        assert enabled_community == set()

    def test_builtin_rules_id_match_pattern(self, robocop_instance):
        robocop_instance.reload_config()
        builtin_rules_id = {rule.rule_id for rule in robocop_instance.rules.values() if not rule.community_rule}
        builtin_rule_id_pattern = re.compile("[0-9]{4}")
        invalid_ids = {rule_id for rule_id in builtin_rules_id if not builtin_rule_id_pattern.fullmatch(rule_id)}
        assert invalid_ids == set()

    def test_community_rules_id_match_pattern(self, robocop_instance):
        robocop_instance.reload_config()
        community_rules_id = {rule.rule_id for rule in robocop_instance.rules.values() if rule.community_rule}
        community_rule_id_pattern = re.compile("1[0-9]{4}")
        invalid_ids = {rule_id for rule_id in community_rules_id if not community_rule_id_pattern.fullmatch(rule_id)}
        assert invalid_ids == set()

    def test_builtin_rules_have_matching_category_id(self, robocop_instance):
        robocop_instance.reload_config()
        builtin_rules = [
            rule for rule in robocop_instance.rules.values() if not rule.community_rule and not rule.deprecated
        ]
        assert builtin_rules != []
        errors = []
        for rule in builtin_rules:
            if rule.category_id is None:
                raise ValueError(f"Missing category_id for rule {rule.rule_id} {rule.name}")
            if not rule.rule_id.startswith(rule.category_id):
                errors.append(
                    f"Rule {rule.rule_id} {rule.name} does not start with correct category id ({rule.category_id})"
                )
        assert errors == []

    def test_community_rules_have_matching_category_id(self, robocop_instance):
        robocop_instance.reload_config()
        community_rules = [rule for rule in robocop_instance.rules.values() if rule.community_rule]
        assert community_rules != []
        errors = []
        for rule in community_rules:
            if rule.category_id is None:
                raise ValueError(f"Missing category_id for rule {rule.rule_id} {rule.name}")
            if not rule.rule_id.startswith("1" + rule.category_id):
                errors.append(
                    f"Rule {rule.rule_id} {rule.name} does not start with correct category id ({rule.category_id})"
                )
        assert errors == []
