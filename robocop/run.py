"""
Main class of Robocop module. Gather files for scan, checkers and parse cli arguments and scan files.
"""
import sys
from pathlib import Path
from robot.api import get_model
from robocop import checkers
from robocop.config import Config
from robocop import reports
from robocop.utils import DisablersFinder, FileType, FileTypeChecker


class Robocop:
    def __init__(self):
        self.files = {}
        self.checkers = []
        self.out = sys.stdout
        self.messages = {}
        self.reports = []
        self.disabler = None
        self.config = Config()
        self.config.parse_opts()
        self.set_output()
        self.load_checkers()
        self.configure_checkers()
        self.load_reports()

    def set_output(self):
        """ Set output for printing to file if configured. Else use standard output """
        self.out = self.config.output or sys.stdout

    def write_line(self, line):
        """ Print line using file=self.out parameter (set in `set_output` method) """
        print(line, file=self.out)

    def run(self):
        """ Entry point for running scans """
        self.recognize_file_types()
        self.run_checks()
        self.make_reports()

    def recognize_file_types(self):
        """
        Preparse files to recognize types. If the filename is "__init__.robot" file type is INIT.
        If the file is imported somewhere then file type is RESOURCE. Otherwise file type is GENERAL.
        Those types are important since are used to define parsing class for robot API.
        """
        files = self.config.paths
        for file in self.get_files(files, True):
            if file.name == '__init__.robot':
                self.files[file] = FileType.INIT
            else:
                self.files[file] = FileType.GENERAL
        file_type_checker = FileTypeChecker(self.files)
        for file in self.files:
            file_type_checker.source = file
            model = get_model(file)
            file_type_checker.visit(model)

    def run_checks(self):
        for file in self.files:
            self.write_line(f"Parsing {file}")
            self.register_disablers(file)
            if self.disabler.file_disabled:
                continue
            model = self.files[file].get_parser()(str(file))
            for checker in self.checkers:
                checker.source = str(file)
                if checker.type == 'visitor_checker':
                    checker.visit(model)
                elif checker.type == 'rawfile_checker':
                    checker.parse_file()

    def register_disablers(self, file):
        """ Parse content of file to find any disabler statements like # robocop: disable=rulename """
        self.disabler = DisablersFinder(file, self)

    def report(self, msg):
        if not self.config.is_rule_enabled(msg):  # disabled from cli
            return
        if self.disabler.is_msg_disabled(msg):  # disabled from source code
            return
        for report in self.reports:
            report.add_message(msg)
        self.log_message(source=msg.source,
                         line=msg.line,
                         col=msg.col,
                         severity=msg.severity.value,
                         msg_id=msg.msg_id,
                         desc=msg.desc,
                         msg_name=msg.name)

    def log_message(self, **kwargs):
        self.write_line(self.config.format.format(**kwargs))

    def load_checkers(self):
        checkers.init(self)

    def load_reports(self):
        reports.init(self)

    def register_checker(self, checker):
        if self.any_rule_enabled(checker):
            for msg_name, msg in checker.messages.items():
                self.messages[msg_name] = (msg, checker)
                self.messages[msg.msg_id] = (msg, checker)
            self.checkers.append(checker)

    def register_report(self, report):
        if report.name in self.config.reports:
            self.reports.append(report)

    def make_reports(self):
        for report in self.reports:
            self.write_line(report.get_report())

    def get_files(self, files_or_dirs, recursive=False):
        for file in files_or_dirs:
            yield from self.get_absolute_path(Path(file), recursive)

    def get_absolute_path(self, path, recursive):
        if not path.exists():
            return
        if path.is_file():
            if self.should_parse(path):
                yield path.absolute()
        elif path.is_dir():
            for file in path.iterdir():
                if file.is_dir() and not recursive:
                    continue
                yield from self.get_absolute_path(file, recursive)

    def should_parse(self, file):
        """ Check if file extension is in list of supported file types (can be configured from cli) """
        return file.suffix and file.suffix in self.config.filetypes

    def any_rule_enabled(self, checker):
        return any(self.config.is_rule_enabled(msg) for msg in checker.messages.values())

    def configure_checkers(self):
        for config in self.config.configure:
            # TODO: handle wrong format, not existing checker
            rule, param, value = config.split(':')
            if rule not in self.messages:
                continue
            msg, checker = self.messages[rule]
            if param == 'severity':
                self.messages[rule] = (msg.change_severity(value), checker)
            else:
                configurable = msg.get_configurable(param)
                if configurable is None:
                    continue
                checker.configure(configurable[1], configurable[2](value))

    def find_checker(self, msg_id_or_name):
        for checker in self.checkers:
            if msg_id_or_name in checker.messages:
                return checker
            for msg in checker.messages.values():
                if msg_id_or_name == msg.msg_id:
                    return checker
        return None


def run_robocop():
    robocop = Robocop()
    robocop.run()
