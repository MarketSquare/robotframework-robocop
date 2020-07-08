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

    def report(self, key, msg, node, source, lineno=None, col=None):
        if lineno is None:
            lineno = node.lineno
        if col is None:
            col = 0
        severity = key[0]
        print(f"{source}:{lineno}:{col} [{severity}] {key} {msg}")

    def load_checkers(self):
        checkers.init(self)

    def register_checker(self, checker):
        self.checkers.append(checker)

    def get_files(self, files_or_dirs):
        if isinstance(files_or_dirs, list):
            for path in files_or_dirs:
                yield from self.get_files(path)
        if Path(files_or_dirs).is_file():
            yield Path(files_or_dirs).absolute()
        for root, dirs, files in os.walk(files_or_dirs):
            for name in files:
                yield Path(root, name).absolute()

    @staticmethod
    def should_parse(file):
        return file.suffix in SUPPORTED_FORMATS


def run_robocop():
    robocop = Robocop()
    robocop.run()
