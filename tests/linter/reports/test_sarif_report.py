import json
from pathlib import Path
from unittest.mock import Mock

from robocop import __version__
from robocop.linter.diagnostics import Diagnostic, Diagnostics
from robocop.linter.reports.sarif import SarifReport
from tests.linter.reports import generate_issues


class TestSarifReport:
    def test_configure_output_path(self, config):
        output_path = "path/to/dir/.sarif.json"
        report = SarifReport(config)
        report.configure("output_path", output_path)
        assert report.output_path == output_path

    def test_sarif_report(self, rule, rule2, tmp_path, config):
        root = Path.cwd()
        output_file = tmp_path / "sarif.json"
        rules = {m.rule_id: m for m in (rule, rule2)}
        source1_rel = "tests/atest/rules/comments/ignored-data/test.robot"
        source2_rel = "tests/atest/rules/misc/empty-return/test.robot"
        report = SarifReport(config)
        report.configure("output_path", str(output_file))

        issues = generate_issues(rule, rule2)

        def get_expected_result(diagnostic: Diagnostic, level, source):
            return {
                "ruleId": diagnostic.rule.rule_id,
                "level": level,
                "message": {"text": diagnostic.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": source, "uriBaseId": "%SRCROOT%"},
                            "region": {
                                "startLine": diagnostic.range.start.line,
                                "endLine": diagnostic.range.end.line,
                                "startColumn": diagnostic.range.start.character,
                                "endColumn": diagnostic.range.end.character,
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
                            "informationUri": "https://robocop.dev/",
                            "rules": [
                                {
                                    "id": r.rule_id,
                                    "name": r.name,
                                    "helpUri": f"https://robocop.dev/v{__version__}/rules_list/#{r.rule_id.lower()}-{r.name}",
                                    "shortDescription": {"text": r.message},
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
        config_manager = Mock()
        config_manager.root = root
        config_manager.default_config.linter.rules = rules
        report.generate_report(Diagnostics(issues), config_manager)
        with open(output_file) as fp:
            sarif_report = json.load(fp)
        assert expected_report == sarif_report

    def test_empty_results(self, config, tmp_path):
        # Arrange
        output_file = tmp_path / "report.json"
        report = SarifReport(config)
        report.configure("output_path", str(output_file))
        diagnostics = Diagnostics([])
        config_manager = Mock()
        config_manager.root = Path.cwd()
        config_manager.default_config.linter.rules = {}

        # Act
        report.generate_report(diagnostics, config_manager)

        # Assert
        assert output_file.exists()
        assert json.loads(output_file.read_text()) == {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "automationDetails": {"id": "robocop/"},
                    "results": [],
                    "tool": {
                        "driver": {
                            "informationUri": "https://robocop.dev/",
                            "name": "Robocop",
                            "rules": [],
                            "semanticVersion": __version__,
                        }
                    },
                }
            ],
            "version": "2.1.0",
        }
