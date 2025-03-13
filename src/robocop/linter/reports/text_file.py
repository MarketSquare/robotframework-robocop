from pathlib import Path

import robocop.linter.reports
from robocop.config import Config
from robocop.linter.diagnostics import Diagnostic


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

    def add_message(self, message: Diagnostic) -> None:
        if message.source not in self.diagn_by_source:
            self.diagn_by_source[message.source] = []
        self.diagn_by_source[message.source].append(message)

    def get_report(self) -> str:
        cwd = Path.cwd()
        messages = []
        for source, diagnostics in self.diagn_by_source.items():
            diagnostics.sort()
            source_rel = Path(source).relative_to(cwd)
            messages.extend(
                self.config.linter.issue_format.format(
                    source=source_rel,
                    source_abs=diagnostic.source,
                    line=diagnostic.range.start.line,
                    col=diagnostic.range.start.character,
                    end_line=diagnostic.range.end.line,
                    end_col=diagnostic.range.end.character,
                    severity=diagnostic.severity.value,
                    rule_id=diagnostic.rule.rule_id,
                    desc=diagnostic.message,
                    name=diagnostic.rule.name,
                )
                for diagnostic in diagnostics
            )
        with open(self.output_path, "w") as text_file:
            text_file.write("\n".join(messages))
        return f"\nGenerated text file report at {self.output_path}"

    def configure(self, name: str, value: str) -> None:
        if name == "output_path":
            self.output_path = Path(value)
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            super().configure(name, value)
