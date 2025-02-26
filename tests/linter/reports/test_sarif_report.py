import json
from pathlib import Path

import pytest

from robocop.config import Config
from robocop.linter.reports.sarif_report import SarifReport
from robocop.linter.rules import Message
from robocop import __version__


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

    @pytest.mark.parametrize("compare_runs", [True, False])
    def test_sarif_report(self, rule, rule2, compare_runs, tmp_path):
        root = Path(".").resolve()
        rules = {m.rule_id: m for m in (rule, rule2)}
        source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
        source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
        source1 = str(root / source1_rel)
        source2 = str(root / source2_rel)
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
                                    "helpUri": f"https://robocop.readthedocs.io/en/{__version__}/rules_list.html#{r.name}",
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
        report.get_report(root, rules)
        sarif_path = report.output_dir / report.report_filename
        with open(sarif_path) as fp:
            sarif_report = json.load(fp)
        assert expected_report == sarif_report
