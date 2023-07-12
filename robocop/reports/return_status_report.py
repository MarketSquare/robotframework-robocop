import robocop.reports
from robocop.reports.rules_by_severity_report import RulesBySeverityReport
from robocop.rules import Message


class ReturnStatusReport(robocop.reports.Report):
    """
    **Report name**: ``return_status``

    This report is always enabled.
    Report that checks if number of returned rules messages for given severity value does not exceed preset threshold.
    That information is later used as a return status from Robocop.
    """

    INTERNAL = True

    def __init__(self):
        self.name = "return_status"
        self.description = "Checks if number of specific issues exceed quality gate limits"
        self.return_status = 0
        self.counter = RulesBySeverityReport(compare_runs=False)
        self.quality_gate = {"E": 0, "W": 0, "I": -1}

    def configure(self, name, value):
        if name not in ["quality_gate", "quality_gates"]:
            super().configure(name, value)
        for val in value.split(":"):
            try:
                name, count = val.split("=", maxsplit=1)
                if name.upper() in self.quality_gate:
                    self.quality_gate[name.upper()] = int(count)
            except ValueError:
                continue

    def add_message(self, message: Message):
        self.counter.add_message(message)

    def get_report(self):
        for severity, count in self.counter.severity_counter.items():
            threshold = self.quality_gate.get(severity.value, 0)
            if -1 < threshold < count:
                self.return_status += count - threshold
        self.return_status = min(self.return_status, 255)
