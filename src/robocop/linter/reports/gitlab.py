from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer

import robocop.linter.reports
from robocop.formatter.utils.misc import StatementLinesCollector
from robocop.linter.rules import RuleSeverity

if TYPE_CHECKING:
    from robot.parsing import File

    from robocop.config import Config
    from robocop.linter.diagnostics import Diagnostic


class GitlabReport(robocop.linter.reports.Report):
    """
    **Report name**: ``gitlab``

    Report that generates Gitlab Code Quality output file.

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
        self.output_path = "robocop-code-quality.json"
        self.diagn_by_source: dict[str, list[Diagnostic]] = {}
        super().__init__(config)

    def add_message(self, message: Diagnostic) -> None:
        if message.source not in self.diagn_by_source:
            self.diagn_by_source[message.source] = []
        self.diagn_by_source[message.source].append(message)

    def configure(self, name, value) -> None:
        if name == "output_path":
            self.output_path = value
        else:
            super().configure(name, value)

    def get_report(self) -> str:
        report = self.generate_gitlab_report()
        output_path = Path(self.output_path)
        try:
            output_path.parent.mkdir(exist_ok=True, parents=True)
            with open(output_path, "w") as fp:
                json.dump(report, fp, indent=4)
        except OSError as err:
            print(f"Failed to write Gitlab report to {output_path}: {err}")
            raise typer.Exit(code=1) from None
        return f"Generated Gitlab Code Quality report at {self.output_path}"

    def generate_gitlab_report(self) -> list[dict]:
        report = []
        cwd = Path.cwd()
        for source, diagnostics in self.diagn_by_source.items():
            diagnostics.sort()
            source_rel = Path(source).relative_to(cwd).as_posix()
            source_lines = None
            fingerprints = set()
            for diagnostic in diagnostics:
                if not source_lines:  # TODO: model should be coming from source, not diagnostics
                    source_lines = self._get_source_lines(diagnostic.model)
                content = self._get_line_content(diagnostic, source_lines)
                unique_id = 0
                while True:
                    fingerprint = self.get_fingerprint(diagnostic, str(source_rel), content, unique_id)
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
                        "location": {"path": str(source_rel), "lines": {"begin": diagnostic.range.start.line}},
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
