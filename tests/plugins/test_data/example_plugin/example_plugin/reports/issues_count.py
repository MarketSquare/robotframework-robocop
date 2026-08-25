from robocop.linter.reports import Report


class IssuesCountReport(Report):
    """
    **Report name**: ``issues_count``

    Report shipped with the example plugin. Prints the number of the found issues.
    """

    def __init__(self, config):
        self.name = "issues_count"
        self.description = "Returns number of found issues"
        self.prefix = "Plugin report"
        super().__init__(config)

    def configure(self, name, value):
        if name == "prefix":
            self.prefix = value
        else:
            super().configure(name, value)

    def generate_report(self, diagnostics, **kwargs):  # noqa: ARG002
        print(f"{self.prefix}: found {len(diagnostics.diagnostics)} issues")
