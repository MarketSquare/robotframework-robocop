import sys
from robot.api import get_model
import os
from pathlib import Path
from robocop import checkers

SUPPORTED_FORMATS = ('.robot')


class Robocop:
    def __init__(self):
        self.checkers = []
        self.load_checkers()

    def run(self):
        files = sys.argv[1]
        for file in self.get_files(files):
            print(f'Parsing {file}')
            model = get_model(str(file))
            for checker in self.checkers:
                checker.source = str(file)
                checker.visit(model)

    def report(self, msg):
        print(f"{msg.source}:{msg.line}:{msg.col} [{msg.severity.value}] {msg.msg_id} {msg.desc}")

    def load_checkers(self):
        checkers.init(self)

    def register_checker(self, checker):
        self.checkers.append(checker)

    def get_files(self, files_or_dirs):
        if isinstance(files_or_dirs, list):
            for path in files_or_dirs:
                yield from self.get_files(path)
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


def run_robocop():
    robocop = Robocop()
    robocop.run()
