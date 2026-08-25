"""Custom reports used in the tests."""

from robocop.linter.reports import Report


class CustomReport(Report):
    """
    **Report name**: ``custom_report``

    Example custom report.
    """

    def __init__(self, config):
        self.name = "custom_report"
        self.description = "Example custom report"
        self.prefix = "Custom report"
        super().__init__(config)

    def configure(self, name, value):
        if name == "prefix":
            self.prefix = value
        else:
            super().configure(name, value)

    def generate_report(self, diagnostics, **kwargs):  # noqa: ARG002
        print(f"{self.prefix}: found {len(diagnostics.diagnostics)} issues")
