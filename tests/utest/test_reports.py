import json
import re
from pathlib import Path

import pytest

import robocop.exceptions
from robocop.config import Config
from robocop.exceptions import ConfigGeneralError
from robocop.reports import get_reports
from robocop.reports.file_stats_report import FileStatsReport
from robocop.reports.json_report import InternalJsonReport, JsonReport
from robocop.reports.robocop_version_report import RobocopVersionReport
from robocop.reports.sarif_report import SarifReport
from robocop.reports.timestamp_report import TimestampReport
from robocop.rules import Message, Rule, RuleParam, RuleSeverity
from robocop.version import __version__


@pytest.fixture
def rule():
    return Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="0101",
        name="some-message",
        msg="Some description",
        severity=RuleSeverity.WARNING,
    )


@pytest.fixture
def rule2():
    return Rule(
        rule_id="0902",
        name="other-message",
        msg="Some description. Example::\n",
        severity=RuleSeverity.ERROR,
    )


@pytest.mark.parametrize(
    "configured, expected",
    [
        (["timestamp", "sarif"], ["timestamp", "sarif"]),
        (["timestamp"], ["timestamp"]),
        (["version", "timestamp", "version"], ["version", "timestamp"]),
    ],
)
def test_get_reports(configured, expected):
    reports = get_reports(configured)
    assert list(reports.keys()) == expected


def test_get_reports_all():
    reports = get_reports(["all"])
    assert "timestamp" in reports and "sarif" not in reports
    reports = get_reports(["all", "sarif"])
    assert "timestamp" in reports and "sarif" in reports
    # Check order with all
    reports = get_reports(["version", "all", "sarif"])
    reports_list = list(reports.keys())
    assert reports_list.index("version") < reports_list.index("timestamp") < reports_list.index("sarif")


def test_get_unknown_report():
    with pytest.raises(robocop.exceptions.InvalidReportName, match="Provided report 'unknown' does not exist."):
        get_reports(["all", "unknown"])


class TestReports:
    @pytest.mark.parametrize(
        "files, files_with_issues, output",
        [
            (0, set(), "\nNo files were processed."),
            (10, set(), "\nProcessed 10 files but no issues were found."),
            (
                10,
                {"a.robot", "b.robot"},
                "\nProcessed 10 files from which 3 files contained issues.",
            ),
        ],
    )
    def test_file_stats_report(self, files, files_with_issues, output, rule):
        report = FileStatsReport()
        report.files_count = files
        report.files_with_issues = files_with_issues
        if files_with_issues:
            issue = Message(
                rule=rule,
                msg=rule.get_message(),
                source="some/path/file.robot",
                node=None,
                lineno=50,
                col=10,
                end_lineno=None,
                end_col=None,
            )
            report.add_message(issue)
        assert report.get_report() == output

    def test_version_report(self, rule):
        report = RobocopVersionReport()
        issue = Message(
            rule=rule,
            msg=rule.get_message(),
            source="some/path/file.robot",
            node=None,
            lineno=50,
            col=10,
            end_lineno=None,
            end_col=None,
        )
        report.add_message(issue)
        assert __version__ in report.get_report()

    def test_timestamp_report(self, rule):
        report = TimestampReport()
        issue = Message(
            rule=rule,
            msg=rule.get_message(),
            source="some/path/file.robot",
            node=None,
            lineno=50,
            col=10,
            end_lineno=None,
            end_col=None,
        )
        report.add_message(issue)
        assert "Reported: " in report.get_report()

    @pytest.mark.parametrize(
        "name, value, expected",
        [
            ("timezone", "UTC", r"\+0000"),
            ("format", "hello", r"Reported: hello"),
            ("format", "%Y-%m-%dT%H:%M:%S", r".*([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})"),
        ],
    )
    def test_timestamp_report_configure(self, name, value, expected):
        self._configure_and_run(name, value, expected)

    @pytest.mark.parametrize(
        "name, value, expected",
        [
            ("", "", "Provided param '' for report 'timestamp' does not exist"),
            ("BAD", "", "Provided param 'BAD' for report 'timestamp' does not exist"),
            ("timezone", "BAD", "Provided timezone 'BAD' for report 'timestamp' is not valid."),
        ],
    )
    def test_timestamp_configure_invalid(self, name, value, expected):
        with pytest.raises(ConfigGeneralError) as err:
            report = TimestampReport()
            report.configure(name, value)
            report.get_report()
        assert expected in str(err)

    @pytest.mark.parametrize(
        "name, value, expected",
        [
            ("format", "", r".*([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})"),
        ],
    )
    def test_timestamp_default_warning(self, name, value, expected):
        with pytest.warns(UserWarning):
            self._configure_and_run(name, value, expected)

    def _configure_and_run(self, name, value, expected):
        report = TimestampReport()
        report.configure(name, value)
        assert re.search(expected, report.get_report())


class TestJSONReport:
    @pytest.mark.parametrize("json_class", [JsonReport, InternalJsonReport])
    def test_json_report(self, rule, json_class):
        report = json_class()
        issue = Message(
            rule=rule,
            msg=rule.get_message(),
            source="some/path/file.robot",
            node=None,
            lineno=50,
            col=10,
            end_lineno=None,
            end_col=None,
        )
        report.add_message(issue)
        assert report.issues[0] == {
            "source": "some/path/file.robot",
            "line": 50,
            "end_line": 50,
            "column": 10,
            "end_column": 10,
            "rule_id": "0101",
            "rule_name": "some-message",
            "severity": "W",
            "description": "Some description",
        }

    def test_configure_output_dir(self):
        output_dir = "path/to/dir"
        report = JsonReport()
        report.configure("output_dir", output_dir)
        assert report.output_dir == Path(output_dir)

    def test_configure_filename(self):
        filename = ".robocop.json"
        report = JsonReport()
        report.configure("report_filename", filename)
        assert report.report_filename == filename

    def test_json_reports_saved_to_file(self, rule, rule2, tmp_path):
        config = Config(from_cli=False)
        rules = {m.rule_id: m for m in (rule, rule2)}
        source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
        source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
        source1 = str(config.root / source1_rel)
        source2 = str(config.root / source2_rel)

        report = JsonReport()
        report.configure("output_dir", tmp_path)

        issues = [
            Message(
                rule=r,
                msg=r.get_message(),
                source=source,
                node=None,
                lineno=line,
                col=col,
                end_lineno=end_line,
                end_col=end_col,
            )
            for r, source, line, end_line, col, end_col in [
                (rule, source1, 50, None, 10, None),
                (rule2, source1, 50, 51, 10, None),
                (rule, source2, 50, None, 10, 12),
                (rule2, source2, 11, 15, 10, 15),
            ]
        ]

        expected_report = [issue.to_json() for issue in issues]
        for issue in issues:
            report.add_message(issue)
        report.get_report()
        json_path = report.output_dir / "robocop.json"
        with open(json_path) as fp:
            json_report = json.load(fp)
        assert expected_report == json_report


class TestSarifReport:
    def test_configure_output_dir(self):
        output_dir = "path/to/dir"
        report = SarifReport()
        report.configure("output_dir", output_dir)
        assert report.output_dir == Path(output_dir)

    def test_configure_filename(self):
        filename = ".sarif"
        report = SarifReport()
        report.configure("report_filename", filename)
        assert report.report_filename == filename

    def test_sarif_report(self, rule, rule2, tmp_path):
        config = Config(from_cli=False)
        rules = {m.rule_id: m for m in (rule, rule2)}
        source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
        source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
        source1 = str(config.root / source1_rel)
        source2 = str(config.root / source2_rel)
        report = SarifReport()
        report.configure("output_dir", tmp_path)

        issues = [
            Message(
                rule=r,
                msg=r.get_message(),
                source=source,
                node=None,
                lineno=line,
                col=col,
                end_lineno=end_line,
                end_col=end_col,
            )
            for r, source, line, end_line, col, end_col in [
                (rule, source1, 50, None, 10, None),
                (rule2, source1, 50, 51, 10, None),
                (rule, source2, 50, None, 10, 12),
                (rule2, source2, 11, 15, 10, 15),
            ]
        ]

        def get_expected_result(message, level, source):
            return {
                "ruleId": message.rule_id,
                "level": level,
                "message": {"text": message.desc},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": source, "uriBaseId": "%SRCROOT%"},
                            "region": {
                                "startLine": message.line,
                                "endLine": message.end_line,
                                "startColumn": message.col,
                                "endColumn": message.end_col,
                            },
                        }
                    }
                ],
            }

        expected_report = {
            "$schema": report.SCHEMA,
            "version": report.SCHEMA_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Robocop",
                            "semanticVersion": __version__,
                            "informationUri": "https://robocop.readthedocs.io/",
                            "rules": [
                                {
                                    "id": r.rule_id,
                                    "name": r.name,
                                    "helpUri": f"https://robocop.readthedocs.io/en/stable/rules.html#{r.name}",
                                    "shortDescription": {"text": r.msg},
                                    "fullDescription": {"text": r.docs},
                                    "defaultConfiguration": {"level": r.default_severity.name.lower()},
                                    "help": {"text": r.docs, "markdown": r.docs},
                                }
                                for r in (rule, rule2)
                            ],
                        }
                    },
                    "automationDetails": {"id": "robocop/"},
                    "results": [
                        get_expected_result(issues[0], "warning", source1_rel),
                        get_expected_result(issues[1], "error", source1_rel),
                        get_expected_result(issues[2], "warning", source2_rel),
                        get_expected_result(issues[3], "error", source2_rel),
                    ],
                }
            ],
        }
        for issue in issues:
            report.add_message(issue)
        report.get_report(config, rules)
        sarif_path = report.output_dir / report.report_filename
        with open(sarif_path) as fp:
            sarif_report = json.load(fp)
        assert expected_report == sarif_report
