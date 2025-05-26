import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from robocop.linter.diagnostics import Diagnostics
from robocop.linter.reports.sonarqube import SonarQubeReport
from tests.linter.reports import generate_issues


class TestSonarQubeReport:
    @pytest.mark.parametrize(
        ("sonar_version", "expected"),
        [
            (
                "9.9",
                {
                    "rules": [
                        {
                            "cleanCodeAttribute": "CONVENTIONAL",
                            "description": "",
                            "engineId": "robocop",
                            "id": "0101",
                            "name": "some-message",
                            "severity": "MINOR",
                            "type": "CODE_SMELL",
                        },
                        {
                            "cleanCodeAttribute": "CONVENTIONAL",
                            "description": "",
                            "engineId": "robocop",
                            "id": "0902",
                            "name": "other-message",
                            "severity": "MAJOR",
                            "type": "CODE_SMELL",
                        },
                    ],
                    "issues": [
                        {
                            "primaryLocation": {
                                "filePath": "tests/atest/rules/comments/ignored-data/test.robot",
                                "message": "Some description",
                                "textRange": {"startLine": 50},
                            },
                            "ruleId": "0101",
                        },
                        {
                            "primaryLocation": {
                                "filePath": "tests/atest/rules/comments/ignored-data/test.robot",
                                "message": "Some description. Example",
                                "textRange": {"endColumn": 9, "endLine": 51, "startColumn": 9, "startLine": 50},
                            },
                            "ruleId": "0902",
                        },
                        {
                            "primaryLocation": {
                                "filePath": "tests/atest/rules/misc/empty-return/test.robot",
                                "message": "Some description. Example",
                                "textRange": {"endColumn": 14, "endLine": 15, "startColumn": 9, "startLine": 11},
                            },
                            "ruleId": "0902",
                        },
                        {
                            "primaryLocation": {
                                "filePath": "tests/atest/rules/misc/empty-return/test.robot",
                                "message": "Some description",
                                "textRange": {"endColumn": 11, "endLine": 50, "startColumn": 9, "startLine": 50},
                            },
                            "ruleId": "0101",
                        },
                    ],
                },
            ),
            (
                "10.3",
                {
                    "rules": [
                        {
                            "cleanCodeAttribute": "CONVENTIONAL",
                            "description": "",
                            "engineId": "robocop",
                            "id": "0101",
                            "name": "some-message",
                            "impacts": [{"softwareQuality": "MAINTAINABILITY", "severity": "MEDIUM"}],
                        },
                        {
                            "cleanCodeAttribute": "CONVENTIONAL",
                            "description": "",
                            "engineId": "robocop",
                            "id": "0902",
                            "name": "other-message",
                            "impacts": [{"softwareQuality": "MAINTAINABILITY", "severity": "HIGH"}],
                        },
                    ],
                    "issues": [
                        {
                            "primaryLocation": {
                                "filePath": "tests/atest/rules/comments/ignored-data/test.robot",
                                "message": "Some description",
                                "textRange": {"startLine": 50},
                            },
                            "ruleId": "0101",
                        },
                        {
                            "primaryLocation": {
                                "filePath": "tests/atest/rules/comments/ignored-data/test.robot",
                                "message": "Some description. Example",
                                "textRange": {"endColumn": 9, "endLine": 51, "startColumn": 9, "startLine": 50},
                            },
                            "ruleId": "0902",
                        },
                        {
                            "primaryLocation": {
                                "filePath": "tests/atest/rules/misc/empty-return/test.robot",
                                "message": "Some description. Example",
                                "textRange": {"endColumn": 14, "endLine": 15, "startColumn": 9, "startLine": 11},
                            },
                            "ruleId": "0902",
                        },
                        {
                            "primaryLocation": {
                                "filePath": "tests/atest/rules/misc/empty-return/test.robot",
                                "message": "Some description",
                                "textRange": {"endColumn": 11, "endLine": 50, "startColumn": 9, "startLine": 50},
                            },
                            "ruleId": "0101",
                        },
                    ],
                },
            ),
        ],
    )
    def test_sonarqube_report(self, rule, rule2, tmp_path, config, sonar_version, expected):
        output_file = tmp_path / "reports" / "sonarqube.json"
        report = SonarQubeReport(config)
        report.configure("output_path", str(output_file))
        report.configure("sonar_version", sonar_version)

        issues = generate_issues(rule, rule2)

        config_manager = Mock()
        config_manager.root = Path.cwd()
        report.generate_report(Diagnostics(issues), config_manager)
        with open(output_file) as fp:
            sonarqube_report = json.load(fp)
        assert expected == sonarqube_report

    def test_configure_output_path(self, config):
        output_path = "path/to/dir/file.json"
        report = SonarQubeReport(config)
        report.configure("output_path", output_path)
        assert report.output_path == output_path
