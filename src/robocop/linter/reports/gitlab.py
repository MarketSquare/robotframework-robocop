from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import robocop.linter.reports
from robocop.files import get_relative_path
from robocop.formatter.utils.misc import StatementLinesCollector
from robocop.linter.rules import RuleSeverity

if TYPE_CHECKING:
    from robot.parsing import File

    from robocop.config import Config
    from robocop.linter.diagnostics import Diagnostic, Diagnostics


class GitlabReport(robocop.linter.reports.JsonFileReport):
    """
    **Report name**: ``gitlab``

    Report that generates Gitlab Code Quality output file.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports gitlab`` or ``--reports all,gitlab``.

    It allows to display issue information in the Gitlab, for example in the PR view.
    More information at https://docs.gitlab.com/ci/testing/code_quality/#code-quality-report-format .

    You can configure output path. It's relative path to file that will be produced by the report::

        robocop check --configure gitlab.output_path=output/robocop_code_quality.json

    Default path is ``robocop-code-quality.json`` .

    """

    NO_ALL = False

    def __init__(self, config: Config):
        self.name = "gitlab"
        self.description = "Generate Gitlab Code Quality output file"
        super().__init__(output_path="robocop-code-quality.json", config=config)

    def generate_report(self, diagnostics: Diagnostics, **kwargs) -> None:  # noqa: ARG002
        report = self.generate_gitlab_report(diagnostics)
        super().generate_report(report, "Gitlab Code Quality")

    def generate_gitlab_report(self, diagnostics: Diagnostics) -> list[dict]:
        report = []
        cwd = Path.cwd()
        for source, diag_by_source in diagnostics.diag_by_source.items():
            source_rel = str(get_relative_path(source, cwd).as_posix())
            source_lines = None
            fingerprints = set()
            for diagnostic in diag_by_source:
                if not source_lines:  # TODO: model should be coming from source, not diagnostics
                    source_lines = self._get_source_lines(diagnostic.model)
                content = self._get_line_content(diagnostic, source_lines)
                unique_id = 0
                while True:
                    fingerprint = self.get_fingerprint(diagnostic, source_rel, content, unique_id)
                    if fingerprint not in fingerprints:
                        fingerprints.add(fingerprint)
                        break
                    unique_id += 1
                report.append(
                    {
                        "description": diagnostic.message,
                        "check_name": diagnostic.rule.name,
                        "fingerprint": fingerprint,
                        "severity": self.get_severity(diagnostic),
                        "location": {"path": source_rel, "lines": {"begin": diagnostic.range.start.line}},
                    }
                )
        return report

    @staticmethod
    def _get_source_lines(model: File) -> list[str]:
        return StatementLinesCollector(model).text.splitlines()

    @staticmethod
    def _get_line_content(diagnostic: Diagnostic, lines: list[str]) -> str:
        if not lines:
            return ""
        line_pos = max(0, min(diagnostic.range.start.line - 1, len(lines) - 1))
        return lines[line_pos]

    @staticmethod
    def get_fingerprint(diagnostic: Diagnostic, source_rel: str, content: str, unique_id: int) -> str:
        """
        Generate unique identifier of the issue based on the rule message, name and line content.

        We are not using issue location to avoid marking issue as fixed and new issue raised when position of line
        changes. Since there could be several instances of the same line content in the same file, we are using
        unique_id to differentiate them.
        """
        issue = {
            "description": diagnostic.message,
            "check_name": diagnostic.rule.name,
            "severity": diagnostic.severity,
            "source": source_rel,
            "content": content,
            "unique_id": unique_id,
        }
        return hashlib.sha1(bytes(str(issue), "utf-8")).hexdigest()  # noqa: S324

    @staticmethod
    def get_severity(diagnostic: Diagnostic) -> str:
        """
        Map Robocop severity to Code Quality severity.

        Robocop uses three severity levels: info, warning and error.
        Code Quality uses: info, minor, major, critical, or blocker.
        """
        if diagnostic.severity == RuleSeverity.INFO:
            return "info"
        if diagnostic.severity == RuleSeverity.WARNING:
            return "minor"
        if diagnostic.rule.rule_id.startswith("ERR"):
            return "blocker"
        return "major"
