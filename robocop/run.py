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
import robocop.exceptions


class Robocop:
    def __init__(self, from_cli=False):
        self.files = {}
        self.checkers = []
        self.out = sys.stdout
        self.messages = {}
        self.reports = []
        self.disabler = None
        self.config = Config()
        if from_cli:
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
        if not self.out.closed:
            self.out.close()

    def recognize_file_types(self):
        """
        Pre-parse files to recognize their types. If the filename is `__init__.robot`, the type is `INIT`.
        If the file is imported somewhere then file type is `RESOURCE`. Otherwise file type is `GENERAL`.
        These types are important since they are used to define parsing class for robot API.
        """
        files = self.config.paths
        for file in self.get_files(files, True):
            if file.name == '__init__.robot':
                self.files[file] = FileType.INIT
            else:
                self.files[file] = FileType.GENERAL
        file_type_checker = FileTypeChecker(self.files, self.config.exec_dir)
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
                checker.scan_file(model)

    def register_disablers(self, file):
        """ Parse content of file to find any disabler statements like # robocop: disable=rulename """
        self.disabler = DisablersFinder(file, self)

    def report(self, msg):
        if not msg.enabled:  # disabled from cli
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
                if msg_name in self.messages:
                    (_, checker_prev) = self.messages[msg_name]
                    raise robocop.exceptions.DuplicatedMessageError('name', msg_name, checker, checker_prev)
                if msg.msg_id in self.messages:
                    (_, checker_prev) = self.messages[msg.msg_id]
                    raise robocop.exceptions.DuplicatedMessageError('id', msg.msg_id, checker, checker_prev)
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
            raise robocop.exceptions.FileError(path)
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
        for name, msg in checker.messages.items():
            msg.enabled = self.config.is_rule_enabled(msg)
            checker.messages[name] = msg
        return any(msg.enabled for msg in checker.messages.values())

    def configure_checkers(self):
        for config in self.config.configure:
            if config.count(':') != 2:
                raise robocop.exceptions.ConfigGeneralError(
                    f'Provided invalid config: \'{config}\' (pattern: <rule>:<param>:<value>)')
            rule, param, value = config.split(':')
            if rule not in self.messages:
                raise robocop.exceptions.ConfigGeneralError(f'Provided rule \'{rule}\' does not exists')
            msg, checker = self.messages[rule]
            if param == 'severity':
                self.messages[rule] = (msg.change_severity(value), checker)
            else:
                configurable = msg.get_configurable(param)
                if configurable is None:
                    raise robocop.exceptions.ConfigGeneralError(
                        f'Provided param \'{param}\' for rule \'{rule}\' does not exists')
                checker.configure(configurable[1], configurable[2](value))


def run_robocop():
    linter = Robocop(from_cli=True)
    linter.run()
