import json
from pathlib import Path

import robocop.linter.reports
from robocop import __version__
from robocop.config import Config
from robocop.linter.diagnostics import Diagnostic
from robocop.linter.utils.misc import ROBOCOP_RULES_URL


class SarifReport(robocop.linter.reports.Report):
    """
    **Report name**: ``sarif``

    Report that generates SARIF output file.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports sarif`` or ``--reports all,sarif``.

    All fields required by GitHub Code Scanning are supported. The output file will be generated
    in the current working directory with the ``.sarif.json`` name.

    You can configure output directory and report filename::

        robocop check --configure sarif.output_dir=C:/sarif_reports --configure sarif.report_filename=.sarif

    """

    NO_ALL = False
    SCHEMA_VERSION = "2.1.0"
    SCHEMA = f"https://json.schemastore.org/sarif-{SCHEMA_VERSION}.json"

    def __init__(self, config: Config):
        self.name = "sarif"
        self.description = "Generate SARIF output file"
        self.output_dir = None
        self.report_filename = ".sarif.json"
        self.issues: list[Diagnostic] = []
        super().__init__(config)

    def configure(self, name, value) -> None:
        if name == "output_dir":
            self.output_dir = Path(value)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        elif name == "report_filename":
            self.report_filename = value
        else:
            super().configure(name, value)

    @staticmethod
    def map_severity_to_level(severity):
        return {"WARNING": "warning", "ERROR": "error", "INFO": "note"}[severity.name]

    def get_rule_desc(self, rule):
        return {
            "id": rule.rule_id,
            "name": rule.name,
            "helpUri": f"{ROBOCOP_RULES_URL.format(version=__version__)}#{rule.name}",
            "shortDescription": {"text": rule.message},
            "fullDescription": {"text": rule.__doc__},
            "defaultConfiguration": {"level": self.map_severity_to_level(rule.default_severity)},
            "help": {"text": rule.__doc__, "markdown": rule.__doc__},
        }

    def add_message(self, message: Diagnostic) -> None:
        self.issues.append(message)

    def generate_sarif_issues(self, root: Path):
        sarif_issues = []
        for diagnostic in self.issues:
            relative_uri = Path(diagnostic.source).relative_to(root)
            sarif_issue = {
                "ruleId": diagnostic.rule.rule_id,
                "level": self.map_severity_to_level(diagnostic.severity),
                "message": {"text": diagnostic.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": relative_uri.as_posix(), "uriBaseId": "%SRCROOT%"},
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

    def generate_rules_config(self, rules):
        unique_enabled_rules = {rule.rule_id: rule for rule in rules.values() if rule.enabled}
        sorted_rules = sorted(unique_enabled_rules.values(), key=lambda x: x.rule_id)
        return [self.get_rule_desc(rule) for rule in sorted_rules]

    def generate_sarif_report(self, root: Path, rules):
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
                    "results": self.generate_sarif_issues(root),
                }
            ],
        }

    def get_report(self, root: Path, rules) -> str:
        report = self.generate_sarif_report(root, rules)
        if self.output_dir is not None:
            output_path = self.output_dir / self.report_filename
        else:
            output_path = Path(self.report_filename)
        with open(output_path, "w") as fp:
            json_string = json.dumps(report, indent=4)
            fp.write(json_string)
        return f"Generated SARIF report in {output_path}"
