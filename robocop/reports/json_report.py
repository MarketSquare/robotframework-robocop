from robocop.reports import Report
from robocop.rules import Message


class JsonReport(Report):
    """
    Report name: ``json_report``

    Report that returns list of found issues in JSON format.
    """

    DEFAULT = False
    INTERNAL = True

    def __init__(self):
        self.name = "json_report"
        self.description = "Accumulates found issues in JSON format"
        self.issues = []

    def add_message(self, message: Message):
        self.issues.append(message.to_json())

    def get_report(self):
        return None
