from pathlib import Path

import robocop.linter.reports
from robocop.config import Config
from robocop.errors import FatalError
from robocop.files import get_relative_path
from robocop.linter.diagnostics import Diagnostic, Diagnostics


class TextFile(robocop.linter.reports.Report):
    """
    **Report name**: ``text_file``

    Report that output issues in the file. Issues format follow PrintIssues simple report format.

    You can configure output path::

        robocop check --configure text_file.output_path=output/robocop.txt

    ``text_file`` report supports only ``simple`` issue output format.
    """

    NO_ALL = False

    def __init__(self, config: Config):
        self.name = "text_file"
        self.description = "Print rules messages to the file"
        self.output_path = Path("robocop.txt")
        self.diagn_by_source: dict[str, list[Diagnostic]] = {}
        super().__init__(config)

    def generate_report(self, diagnostics: Diagnostics, **kwargs) -> None:  # noqa: ARG002
        cwd = Path.cwd()
        messages = []
        for source, diag_by_source in diagnostics.diag_by_source.items():
            source_rel = get_relative_path(source, cwd)
            messages.extend(
                self.config.linter.issue_format.format(
                    source=source_rel,
                    source_abs=Path(source).resolve(),
                    line=diagnostic.range.start.line,
                    col=diagnostic.range.start.character,
                    end_line=diagnostic.range.end.line,
                    end_col=diagnostic.range.end.character,
                    severity=diagnostic.severity.value,
                    rule_id=diagnostic.rule.rule_id,
                    desc=diagnostic.message,
                    name=diagnostic.rule.name,
                )
                for diagnostic in diag_by_source
            )
        output_path = Path(self.output_path)
        try:
            output_path.parent.mkdir(exist_ok=True, parents=True)
            with open(output_path, "w") as text_file:
                text_file.write("\n".join(messages))
        except OSError as err:
            raise FatalError(f"Failed to write TextFile report to {output_path}: {err}") from None

    def configure(self, name: str, value: str) -> None:
        if name == "output_path":
            self.output_path = Path(value)
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            super().configure(name, value)
