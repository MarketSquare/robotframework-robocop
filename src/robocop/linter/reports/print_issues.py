import robocop.linter.reports
from robocop.config import Config
from robocop.linter.diagnostics import Diagnostic


class PrintIssuesReport(robocop.linter.reports.Report):
    """
    **Report name**: ``print_issues``

    This report is always enabled.
    Report that collect diagnostic messages and print them at the end of the execution.
    """

    DEFAULT = False
    ENABLED = True

    def __init__(self, config: Config):
        self.name = "print_issues"
        self.description = "Collect and print rules messages"
        self.diagn_by_source: dict[str, list[Diagnostic]] = {}
        super().__init__(config)

    def add_message(self, message: Diagnostic) -> None:
        if message.source not in self.diagn_by_source:
            self.diagn_by_source[message.source] = []
        self.diagn_by_source[message.source].append(message)

    def get_report(self) -> None:
        for source, diagnostics in self.diagn_by_source.items():
            diagnostics.sort()
            for diagnostic in diagnostics:
                print(
                    self.config.linter.issue_format.format(
                        source=diagnostic.source,
                        line=diagnostic.range.start.line,
                        col=diagnostic.range.start.character,
                        end_line=diagnostic.range.end.line,
                        end_col=diagnostic.range.end.character,
                        severity=diagnostic.severity.value,
                        rule_id=diagnostic.rule.rule_id,
                        desc=diagnostic.message,
                        name=diagnostic.rule.name,
                    )
                )

            # try:
            #     # TODO: reimplement with Path
            #     # TODO: lazy evaluation in case source_rel is not used
            #     source_rel = os.path.relpath(os.path.expanduser(rule_msg.source), self.config_manager.root)
            # except ValueError:
            #     source_rel = rule_msg.source
