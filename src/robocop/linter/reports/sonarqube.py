import json
from pathlib import Path

import robocop.linter.reports
from robocop.config import Config, ConfigManager
from robocop.errors import FatalError
from robocop.linter import sonar_qube
from robocop.linter.diagnostics import Diagnostic, Diagnostics
from robocop.linter.rules import Rule, RuleSeverity


class SonarQubeReport(robocop.linter.reports.Report):
    """
    **Report name**: ``sonarqube``

    Report that generates SonarQube report.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports sonarqube`` or ``--reports all,sonarqube``.

    Implements all mandatory field of Sonar Qube `Generic formatted issue report`. Each Robocop rule can be assigned
    with Sonar Qube code attribute or issue type for that purpose. If rule doesn't have such attribute assigned,
    ``cleanCodeAttribute`` will be set to ``CONVENTIONAL`` and ``issueType`` will be set to ``CODE SMELL``.
    Severity is mapped in a following way:

    - parsing errors and bugs as ``BLOCKER``
    - errors as ``MAJOR``
    - warnings as ``MINOR``
    - infos as ``INFO``

    You can configure output path. It's relative path to file that will be produced by the report::

        robocop check --configure sonarqube.output_path=output/robocop_sonar_qube.json

    Default path is ``robocop_sonar_qube.json`` .

    """

    NO_ALL = False

    def __init__(self, config: Config):
        self.name = "sonarqube"
        self.description = "Generate SonarQube report"
        self.output_path = "robocop_sonar_qube.json"
        super().__init__(config)

    def configure(self, name, value) -> None:
        if name == "output_path":
            self.output_path = value
        else:
            super().configure(name, value)

    def get_rule_description(self, diagnostic: Diagnostic) -> dict:
        return {
            "id": diagnostic.rule.rule_id,
            "name": diagnostic.rule.name,
            "description": diagnostic.rule.docs,
            "engineId": "robocop",
            **self.get_code_attributes(diagnostic.rule),
        }

    def get_issue_description(self, diagnostic: Diagnostic, source_rel: str) -> dict:
        return {
            "ruleId": diagnostic.rule.rule_id,
            "primaryLocation": {
                "message": diagnostic.message,
                "filePath": source_rel,
                "textRange": {
                    "startLine": diagnostic.range.start.line,
                    "startColumn": diagnostic.range.start.character,
                    "endLine": diagnostic.range.end.line,
                    "endColumn": diagnostic.range.end.character,
                },
            },
        }

    @staticmethod
    def map_severity(rule_severity: RuleSeverity) -> str:
        return {
            RuleSeverity.INFO: "INFO",
            RuleSeverity.WARNING: "MINOR",
            RuleSeverity.ERROR: "MAJOR",
        }[rule_severity]

    def get_code_attributes(self, rule: Rule) -> dict:
        if rule.sonar_qube_attrs:
            issue_type = rule.sonar_qube_attrs.issue_type.value
            clean_code_attr = rule.sonar_qube_attrs.clean_code.value
            if issue_type == sonar_qube.SonarQubeIssueType.BUG:
                severity = "BLOCKER"
            else:
                severity = self.map_severity(rule.severity)
        else:
            issue_type = sonar_qube.SonarQubeIssueType.CODE_SMELL.value
            clean_code_attr = sonar_qube.CleanCodeAttribute.CONVENTIONAL.value
            severity = self.map_severity(rule.severity)
        return {"type": issue_type, "cleanCodeAttribute": clean_code_attr, "severity": severity}

    def generate_sonarqube_report(self, diagnostics: Diagnostics, root: Path) -> dict:
        report = {"rules": [], "issues": []}
        seen_rules = set()
        for source, diag_by_source in diagnostics.diag_by_source.items():
            source_rel = str(Path(source).relative_to(root).as_posix())
            for diagnostic in diag_by_source:
                if diagnostic.rule.rule_id not in seen_rules:
                    seen_rules.add(diagnostic.rule.rule_id)
                    report["rules"].append(self.get_rule_description(diagnostic))
                report["issues"].append(self.get_issue_description(diagnostic, source_rel))
        return report

    def generate_report(self, diagnostics: Diagnostics, config_manager: ConfigManager, **kwargs) -> None:  # noqa: ARG002
        report = self.generate_sonarqube_report(diagnostics, config_manager.root)
        output_path = Path(self.output_path)
        try:
            output_path.parent.mkdir(exist_ok=True, parents=True)
            with open(output_path, "w") as fp:
                json.dump(report, fp, indent=4)
        except OSError as err:
            raise FatalError(f"Failed to write SonarQube report to {output_path}: {err}") from None
        print(f"Generated SonarQube report in {self.output_path}")
