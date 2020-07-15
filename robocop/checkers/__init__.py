"""
Robocop lint rules are called checkers internally. Each checker can scan for multiple related issues
(like LengthChecker checks both for min and max length of keyword). You can refer to specific messages
reported by checkers by its name or id (for example `0501` or `too-long-keyword`).

Each message have configurable severity and optionally other parameters.
"""
import ast
import re
from pathlib import Path
from robot.parsing.model.statements import Comment
from importlib import import_module
import inspect
from robocop.messages import Message


"""
Message ids:
01: base
02: documentation
03: naming
04: errors
05: lengths
06: tags
07: comments
09: misc

"""


class BaseChecker:
    msgs = None

    def __init__(self, linter, configurable=None):
        self.linter = linter
        self.source = None
        self.messages = {}
        self.configurable = set() if configurable is None else configurable
        self.register_messages(self.msgs)

    def register_messages(self, msgs):
        for key, value in msgs.items():
            msg = Message(key, value)
            if msg.name in self.messages:
                raise ValueError("Duplicate message name in checker")  # TODO: add better handling for duplicate messages
            self.messages[msg.name] = msg

    def report(self, msg, *args, node=None, lineno=None, col=None):
        if msg not in self.messages:
            raise ValueError(f"Missing definition for message with name {msg}")
        message = self.messages[msg].prepare_message(*args, source=self.source, node=node, lineno=lineno, col=col)
        self.linter.report(message)

    def configure(self, param, value):
        self.__dict__[param] = value


class VisitorChecker(BaseChecker, ast.NodeVisitor):
    type = 'visitor_checker'

    def visit_File(self, node):
        self.generic_visit(node)


class RawFileChecker(BaseChecker):
    type = 'rawfile_checker'

    def parse_file(self):
        with open(self.source) as f:
            for lineno, line in enumerate(f):
                self.check_line(line, lineno + 1)

    def check_line(self, line, lineno):
        raise NotImplementedError

        
def init(linter):
    seen = set()
    for file in Path(__file__).parent.iterdir():
        if file.stem in seen or '__pycache__' in str(file):
            continue
        try:
            if file.is_dir() or (file.suffix in ('.py') and file.stem != '__init__'):
                linter.write_line(f"Importing rule file {file}")
                module = import_module('.' + file.stem, __name__)
                module.register(linter)
                seen.add(file.stem)
        except Exception as e:
            linter.write_line(e)


def get_docs():
    seen = set()
    for file in Path(__file__).parent.iterdir():
        if file.stem in seen or '__pycache__' in str(file):
            continue
        try:
            if file.is_dir() or (file.suffix in ('.py') and file.stem != '__init__'):
                module = import_module('.' + file.stem, __name__)
                classess = inspect.getmembers(module, inspect.isclass)
                for checker in classess:
                    if hasattr(checker[1], 'msgs') and checker[1].msgs:
                        yield checker[1]
                seen.add(file.stem)
        except Exception as e:
            print(e)
            pass