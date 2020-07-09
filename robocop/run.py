import sys
from robot.api import get_model
import os
from pathlib import Path
from robocop import checkers
from robocop.config import Config


SUPPORTED_FORMATS = ('.robot')


class Robocop:
    def __init__(self):
        self.checkers = []
        self.config = Config()
        self.config.parse_opts()
        self.load_checkers()

    def run(self):
        files = self.config.paths
        for file in self.get_files(files):
            print(f'Parsing {file}')
            model = get_model(str(file))
            for checker in self.checkers:
                checker.source = str(file)
                checker.visit(model)

    def report(self, msg):
        if not self.config.is_rule_enabled(msg):
            return
        print(f"{msg.source}:{msg.line}:{msg.col} [{msg.severity.value}] {msg.msg_id} {msg.desc}")

    def load_checkers(self):
        checkers.init(self)

    def register_checker(self, checker):
        if self.any_rule_enabled(checker):
            self.checkers.append(checker)

    def get_files(self, files_or_dirs):
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


def run_robocop():
    robocop = Robocop()
    robocop.run()
