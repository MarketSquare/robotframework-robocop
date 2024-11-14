import json
from pathlib import Path

import robocop.reports
from robocop.rules import Message
from robocop.version import __version__


class SarifReport(robocop.reports.Report):
    """
    **Report name**: ``sarif``

    Report that generates SARIF output file.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports sarif`` or ``--reports all,sarif``.

    All fields required by GitHub Code Scanning are supported. The output file will be generated
    in the current working directory with the ``.sarif.json`` name.

    You can configure output directory and report filename::

        robocop --configure sarif:output_dir:C:/sarif_reports --configure sarif:report_filename:.sarif

    """

    DEFAULT = False
    SCHEMA_VERSION = "2.1.0"
    SCHEMA = f"https://json.schemastore.org/sarif-{SCHEMA_VERSION}.json"

    def __init__(self):
        self.name = "sarif"
        self.description = "Generate SARIF output file"
        self.output_dir = None
        self.report_filename = ".sarif.json"
        self.issues = []

    def configure(self, name, value):
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
            "helpUri": rule.help_url or "",
            "shortDescription": {"text": rule.msg},
            "fullDescription": {"text": rule.docs},
            "defaultConfiguration": {"level": self.map_severity_to_level(rule.default_severity)},
            "help": {"text": rule.docs, "markdown": rule.docs},
        }

    def add_message(self, message: Message):
        self.issues.append(message)

    def generate_sarif_issues(self, config):
        sarif_issues = []
        for issue in self.issues:
            relative_uri = Path(issue.source).relative_to(config.root)
            sarif_issue = {
                "ruleId": issue.rule_id,
                "level": self.map_severity_to_level(issue.severity),
                "message": {"text": issue.desc},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": relative_uri.as_posix(), "uriBaseId": "%SRCROOT%"},
                            "region": {
                                "startLine": issue.line,
                                "endLine": issue.end_line,
                                "startColumn": issue.col,
                                "endColumn": issue.end_col,
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

    def generate_sarif_report(self, config, rules):
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
                    "results": self.generate_sarif_issues(config),
                }
            ],
        }

    def get_report(self, config, rules) -> str:
        report = self.generate_sarif_report(config, rules)
        if self.output_dir is not None:
            output_path = self.output_dir / self.report_filename
        else:
            output_path = Path(self.report_filename)
        with open(output_path, "w") as fp:
            json_string = json.dumps(report, indent=4)
            fp.write(json_string)
        return f"Generated SARIF report in {output_path}"
