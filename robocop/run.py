import sys
from robot.api import get_model
import os
from pathlib import Path
from robocop import checkers
from robocop.config import Config
from robocop import reports
from robocop.utils import DisablersFinder, FileType, FileTypeChecker


SUPPORTED_FORMATS = ('.robot')


class Robocop:
    def __init__(self):
        self.files = dict()
        self.checkers = []
        self.messages = dict()
        self.reports = []
        self.disabler = None
        self.config = Config()
        self.config.parse_opts()
        self.load_checkers()
        self.configure_checkers()
        self.load_reports()

    def run(self):
        self.recognize_file_types()
        self.run_checks()
        self.make_reports()

    def recognize_file_types(self):
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
            print(f"Parsing {file}")
            self.register_disablers(file)
            if self.disabler.file_disabled:
                continue
            model = self.files[file].get_parser()(str(file))
            for checker in self.checkers:
                checker.source = str(file)
                checker.visit(model)

    def register_disablers(self, file):
        self.disabler = DisablersFinder(file, self)

    def report(self, msg):
        if not self.config.is_rule_enabled(msg):
            return
        if self.disabler.is_msg_disabled(msg):
            return
        for report in self.reports:
            report.add_message(msg)
        self.log_message(source=msg.source, line=msg.line, col=msg.col, severity=msg.severity.value,
                         msg_id=msg.msg_id, desc=msg.desc)

    def log_message(self, **kwargs):
        print(self.config.format.format(**kwargs))

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
            print(report.get_report())

    def get_files(self, files_or_dirs, recursive=False):
        for file in files_or_dirs:
            yield from self.get_absolute_path(Path(file), recursive)

    def get_absolute_path(self, path, recursive):
        if not path.exists():
            raise StopIteration
        if path.is_file():
            if Robocop.should_parse(path):
                yield path.absolute()
        elif path.is_dir():
            for file in path.iterdir():
                if file.is_dir() and not recursive:
                    continue
                yield from self.get_absolute_path(file, recursive)

    def get_files1(self, files_or_dirs):
        if isinstance(files_or_dirs, list):
            for path in files_or_dirs:
                yield from self.get_files(path)
        else:
            path = Path(files_or_dirs)
            if path.is_file() and Robocop.should_parse(path):
                yield path.absolute()
            for root, dirs, files in os.walk(files_or_dirs):
                for name in files:
                    path = Path(root, name)
                    if Robocop.should_parse(path):
                        yield path.absolute()

    @staticmethod
    def should_parse(file):
        return file.suffix in SUPPORTED_FORMATS

    def any_rule_enabled(self, checker):
        for msg_name, msg in checker.messages.items():
            if self.config.is_rule_enabled(msg):
                return True
        else:
            return False

    def configure_checkers(self):
        for config in self.config.configure:
            # TODO: handle wrong format, not existing checker
            rule, param, value = config.split(':')
            if rule not in self.messages:
                continue
            msg, checker = self.messages[rule]
            configurable = msg.get_configurable(param)
            if configurable is None:
                continue
            checker.configure(configurable[1], configurable[2](value))

    def find_checker(self, msg_id_or_name):
        for checker in self.checkers:
            if msg_id_or_name in checker.messages:
                return checker
            for msg_name, msg in checker.messages.items():
                if msg_id_or_name == msg.msg_id:
                    return checker
        else:
            return None


def run_robocop():
    robocop = Robocop()
    robocop.run()
