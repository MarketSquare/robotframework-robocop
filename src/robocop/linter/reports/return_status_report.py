from collections import defaultdict

import robocop.linter.reports
from robocop.config import Config
from robocop.linter.diagnostics import Diagnostics


class ReturnStatusReport(robocop.linter.reports.Report):
    """
    **Report name**: ``return_status``

    Report that checks if number of returned rules messages for given severity value does not exceed preset threshold.
    If the report is enabled, it will be used as a return status from Robocop.
    """

    NO_ALL = False

    def __init__(self, config: Config):
        self.name = "return_status"
        self.description = "Checks if number of specific issues exceed quality gate limits"
        self.return_status = 0
        self.quality_gate = {"E": 0, "W": 0, "I": -1}
        super().__init__(config)

    def configure(self, name: str, value: str) -> None:
        if name not in ["quality_gate", "quality_gates"]:
            super().configure(name, value)
        for val in value.split(":"):
            try:
                name, count = val.split("=", maxsplit=1)
                if name.upper() in self.quality_gate:
                    self.quality_gate[name.upper()] = int(count)
            except ValueError:
                continue

    def generate_report(self, diagnostics: Diagnostics, **kwargs) -> None:  # noqa: ARG002
        severity_counter = defaultdict(int)
        for diagnostic in diagnostics:
            severity_counter[diagnostic.severity] += 1
        for severity, count in severity_counter.items():
            threshold = self.quality_gate.get(severity.value, 0)
            if -1 < threshold < count:
                self.return_status += count - threshold
        self.return_status = min(self.return_status, 255)
