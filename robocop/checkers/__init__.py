"""
Robocop lint rules are interally grouped into similar groups called checkers.
Each checker can scan for multiple related issues (like LengthChecker checks both for min and max length of keyword).
You can refer to specific messages reported by checkers by its name or id (for example `0501` or `too-long-keyword`).

Each message have configurable severity and optionally other parameters.

Checkers are categorized into following groups:
 * 01: base
 * 02: documentation
 * 03: naming
 * 04: errors
 * 05: lengths
 * 06: tags
 * 07: comments
 * 09: misc

Group id is prefix of message id.

Checker have two basic types ``VisitorChecker`` uses Robot Framework parsing api and
use Python ast modoule for traversing Robot code as nodes. ``RawFileChecker`` simply reads Robot file as normal file
and scan every line.

Rules are defines as messages. Every rule have unique id (group id + message id) and rule name and both can be use
to refer to rule (in include/exclude statements, configurations etc).
You can configure rule severity and optionally other parameters.
"""
import ast
import inspect
from pathlib import Path
from importlib import import_module
from robocop.messages import Message


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
                raise ValueError("Duplicate message name in checker")
                # TODO: add better handling for duplicate messages
            self.messages[msg.name] = msg

    def report(self, msg, *args, node=None, lineno=None, col=None):
        if msg not in self.messages:
            raise ValueError(f"Missing definition for message with name {msg}")
        message = self.messages[msg].prepare_message(*args, source=self.source, node=node, lineno=lineno, col=col)
        self.linter.report(message)

    def configure(self, param, value):
        self.__dict__[param] = value


class VisitorChecker(BaseChecker, ast.NodeVisitor):  # noqa
    type = 'visitor_checker'

    def visit_File(self, node):  # noqa
        """ Perform generic ast visit on file node. """
        self.generic_visit(node)


class RawFileChecker(BaseChecker):  # noqa
    type = 'rawfile_checker'

    def parse_file(self):
        """ Read file line by line and for each call check_line method. """
        with open(self.source) as file:
            for lineno, line in enumerate(file):
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
        except Exception as err:
            linter.write_line(err)


def get_docs():
    seen = set()
    for file in Path(__file__).parent.iterdir():
        if file.stem in seen or '__pycache__' in str(file):
            continue
        if file.is_dir() or (file.suffix in ('.py') and file.stem != '__init__'):
            module = import_module('.' + file.stem, __name__)
            classess = inspect.getmembers(module, inspect.isclass)
            for checker in classess:
                if hasattr(checker[1], 'msgs') and checker[1].msgs:
                    yield checker[1]
            seen.add(file.stem)
