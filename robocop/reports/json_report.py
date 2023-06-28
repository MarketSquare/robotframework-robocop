import json
from pathlib import Path

from robocop.reports import Report
from robocop.rules import Message


class JsonReport(Report):
    """
    Report name: ``json_report``

    Report that returns a list of found issues in a JSON format. The output file will be generated
    in the current working directory with the ``robocop_output.json`` name.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports json_report`` or ``--reports all,json_report``.

    You can configure output directory and report filename::

        robocop --configure json_report:output_dir:C:/json_reports
        robocop --configure json_report:report_filename:robocop.json

    """

    DEFAULT = False

    def __init__(self):
        self.name = "json_report"
        self.description = "Produces JSON file with found issues"
        self.output_dir = None
        self.report_filename = "robocop_output.json"
        self.issues = []

    def add_message(self, message: Message):
        self.issues.append(message.to_json())

    def get_report(self):
        if self.output_dir is not None:
            output_path = self.output_dir / self.report_filename
        else:
            output_path = Path(self.report_filename)
        with open(output_path, "w") as fp:
            json_string = json.dumps(self.issues, indent=4)
            fp.write(json_string)
        return f"Generated JSON report at {output_path}"

    def configure(self, name, value):
        if name == "output_dir":
            self.output_dir = Path(value)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        elif name == "report_filename":
            self.report_filename = value
        else:
            super().configure(name, value)


class InternalJsonReport(Report):
    """
    Report name: ``internal_json_report``

    Report that returns list of found issues in JSON format.
    """

    DEFAULT = False
    INTERNAL = True

    def __init__(self):
        self.name = "internal_json_report"
        self.description = "Accumulates found issues in JSON format"
        self.issues = []

    def add_message(self, message: Message):
        self.issues.append(message.to_json())

    def get_report(self):
        return None
