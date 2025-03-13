import robocop.linter.reports
from robocop.config import Config
from robocop.linter.diagnostics import Diagnostic
from robocop.linter.reports.rules_by_severity_report import RulesBySeverityReport


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
        self.counter = RulesBySeverityReport(config)
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

    def add_message(self, message: Diagnostic) -> None:
        self.counter.add_message(message)

    def get_report(self) -> None:
        for severity, count in self.counter.severity_counter.items():
            threshold = self.quality_gate.get(severity.value, 0)
            if -1 < threshold < count:
                self.return_status += count - threshold
        self.return_status = min(self.return_status, 255)
