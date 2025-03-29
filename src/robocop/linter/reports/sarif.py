from pathlib import Path

import robocop.linter.reports
from robocop import __version__
from robocop.config import Config, ConfigManager
from robocop.files import get_relative_path
from robocop.linter.diagnostics import Diagnostics
from robocop.linter.rules import Rule
from robocop.linter.utils.misc import ROBOCOP_RULES_URL


class SarifReport(robocop.linter.reports.JsonFileReport):
    """
    **Report name**: ``sarif``

    Report that generates SARIF output file.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports sarif`` or ``--reports all,sarif``.

    All fields required by GitHub Code Scanning are supported. The output file will be generated
    in the current working directory with the ``.sarif.json`` name.

    You can configure output path. It's relative path to file that will be produced by the report::

        robocop check --configure sarif.output_path=output/robocop_sarif.json

    Default path is ``.sarif.json`` .

    """

    NO_ALL = False
    SCHEMA_VERSION = "2.1.0"
    SCHEMA = f"https://json.schemastore.org/sarif-{SCHEMA_VERSION}.json"

    def __init__(self, config: Config):
        self.name = "sarif"
        self.description = "Generate SARIF output file"
        super().__init__(output_path=".sarif.json", config=config)

    @staticmethod
    def map_severity_to_level(severity):
        return {"WARNING": "warning", "ERROR": "error", "INFO": "note"}[severity.name]

    def get_rule_desc(self, rule):
        return {
            "id": rule.rule_id,
            "name": rule.name,
            "helpUri": f"{ROBOCOP_RULES_URL.format(version=__version__)}#{rule.name}",
            "shortDescription": {"text": rule.message},
            "fullDescription": {"text": rule.docs},
            "defaultConfiguration": {"level": self.map_severity_to_level(rule.default_severity)},
            "help": {"text": rule.docs, "markdown": rule.docs},
        }

    def generate_sarif_issues(self, diagnostics: Diagnostics, root: Path):
        sarif_issues = []
        for diagnostic in diagnostics:
            relative_uri = get_relative_path(diagnostic.source, root).as_posix()
            sarif_issue = {
                "ruleId": diagnostic.rule.rule_id,
                "level": self.map_severity_to_level(diagnostic.severity),
                "message": {"text": diagnostic.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": relative_uri, "uriBaseId": "%SRCROOT%"},
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
            sarif_issues.append(sarif_issue)
        return sarif_issues

    def generate_rules_config(self, rules: dict[str, Rule]):
        unique_enabled_rules = {rule.rule_id: rule for rule in rules.values() if rule.enabled}
        sorted_rules = sorted(unique_enabled_rules.values(), key=lambda x: x.rule_id)
        return [self.get_rule_desc(rule) for rule in sorted_rules]

    def generate_sarif_report(self, diagnostics: Diagnostics, root: Path, rules: dict[str, Rule]):
        return {
            "$schema": self.SCHEMA,
            "version": self.SCHEMA_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Robocop",
                            "semanticVersion": __version__,
                            "informationUri": "https://robocop.readthedocs.io/",
                            "rules": self.generate_rules_config(rules),
                        }
                    },
                    "automationDetails": {"id": "robocop/"},
                    "results": self.generate_sarif_issues(diagnostics, root),
                }
            ],
        }

    def generate_report(self, diagnostics: Diagnostics, config_manager: ConfigManager, **kwargs) -> str:  # noqa: ARG002
        # TODO: In case of several configs we may not have all rules in default config
        # instead, we could use diagnostic.rule and aggregate them
        report = self.generate_sarif_report(
            diagnostics, config_manager.root, config_manager.default_config.linter.rules
        )
        super().generate_report(report, "SARIF")
