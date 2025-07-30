from pathlib import Path

import robocop.linter.reports
from robocop.config import Config, ConfigManager
from robocop.errors import ConfigurationError
from robocop.files import get_relative_path
from robocop.linter import sonar_qube
from robocop.linter.diagnostics import Diagnostic, Diagnostics
from robocop.linter.rules import Rule, RuleSeverity


class SonarQubeReport(robocop.linter.reports.JsonFileReport):
    """
    **Report name**: ``sonarqube``

    Report that generates SonarQube report.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports sonarqube`` or ``--reports all,sonarqube``.

    Implements all mandatory field of Sonar Qube `Generic formatted issue report`.

    Currently, Robocop supports 2 major minimal Sonar Qube versions:

    - up to 9.9
    - 10.3 onwards (default)

    If your SonarQube instance requires 9.9 format (which for example doesn't have impacts field), you can configure it
    using ``sonar_version`` parameter::

        robocop check --configure sonarqube.sonar_version=9.9

    You can configure output path. It's relative path to file that will be produced by the report::

        robocop check --configure sonarqube.output_path=output/robocop_sonar_qube.json

    Default path is ``robocop_sonar_qube.json`` .

    """

    NO_ALL = False
    SUPPORTED_MIN_VERSIONS = {"9.9", "10.3"}

    def __init__(self, config: Config):
        self.name = "sonarqube"
        self.description = "Generate SonarQube report"
        self.sonar_version = "10.3"
        super().__init__(output_path="robocop_sonar_qube.json", config=config)

    @property
    def report_generator(self):
        return {
            "9.9": SonarQubeDescriptor99,
            "10.3": SonarQubeDescriptor103,
        }[self.sonar_version]

    def configure(self, name: str, value: str) -> None:
        if name == "sonar_version":
            if value not in self.SUPPORTED_MIN_VERSIONS:
                versions = ", ".join(self.SUPPORTED_MIN_VERSIONS)
                raise ConfigurationError(f"Not supported minimal version: {value}. Supported versions: {versions}")
            self.sonar_version = value
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

    def generate_report(self, diagnostics: Diagnostics, config_manager: ConfigManager, **kwargs) -> None:  # noqa: ARG002
        report = self.report_generator().generate_sonarqube_report(diagnostics, config_manager.root)
        super().generate_report(report, "SonarQube")


class SonarQubeGenerator:
    def get_code_attributes(self, rule: Rule) -> dict:
        raise NotImplementedError

    @staticmethod
    def get_sonar_qube_range(diagnostic: Diagnostic) -> dict:
        text_range = diagnostic.range
        # reports on empty lines
        if diagnostic.rule.rule_id in {"SPC03", "SPC04", "SPC05", "SPC09", "SPC12"}:
            return {"startLine": text_range.start.line, "endLine": text_range.end.line}
        if text_range.start == text_range.end:
            return {"startLine": text_range.start.line}
        return {
            "startLine": text_range.start.line,
            "startColumn": max(text_range.start.character - 1, 0),
            "endLine": text_range.end.line,
            "endColumn": max(text_range.end.character - 1, 0),
        }

    def get_issue_description(self, diagnostic: Diagnostic, source_rel: str) -> dict:
        return {
            "ruleId": diagnostic.rule.rule_id,
            "primaryLocation": {
                "message": diagnostic.message,
                "filePath": source_rel,
                "textRange": self.get_sonar_qube_range(diagnostic),
            },
        }

    def get_rule_description(self, diagnostic: Diagnostic) -> dict:
        return {
            "id": diagnostic.rule.rule_id,
            "name": diagnostic.rule.name,
            "description": diagnostic.rule.docs,
            "engineId": "robocop",
            **self.get_code_attributes(diagnostic.rule),
        }

    def generate_sonarqube_report(self, diagnostics: Diagnostics, root: Path) -> dict:
        report = {"rules": [], "issues": []}
        seen_rules = set()
        for source, diag_by_source in diagnostics.diag_by_source.items():
            source_rel = str(get_relative_path(source, root).as_posix())
            for diagnostic in diag_by_source:
                if diagnostic.rule.rule_id not in seen_rules:
                    seen_rules.add(diagnostic.rule.rule_id)
                    report["rules"].append(self.get_rule_description(diagnostic))
                report["issues"].append(self.get_issue_description(diagnostic, source_rel))
        return report


class SonarQubeDescriptor99(SonarQubeGenerator):
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


class SonarQubeDescriptor103(SonarQubeGenerator):
    @staticmethod
    def map_severity(rule_severity: RuleSeverity) -> str:
        return {
            RuleSeverity.INFO: "LOW",
            RuleSeverity.WARNING: "MEDIUM",
            RuleSeverity.ERROR: "HIGH",
        }[rule_severity]

    def get_code_attributes(self, rule: Rule) -> dict:
        if rule.sonar_qube_attrs:
            clean_code_attr = rule.sonar_qube_attrs.clean_code.value
        else:
            clean_code_attr = sonar_qube.CleanCodeAttribute.CONVENTIONAL.value
        severity = self.map_severity(rule.severity)
        return {
            "cleanCodeAttribute": clean_code_attr,
            "impacts": [{"softwareQuality": "MAINTAINABILITY", "severity": severity}],
        }
