"""
Robocop lint rules are internally grouped into similar groups called checkers.
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
use Python ast module for traversing Robot code as nodes. ``RawFileChecker`` simply reads Robot file as normal file
and scan every line.

Rules are defines as messages. Every rule have unique id (group id + message id) and rule name and both can be use
to refer to rule (in include/exclude statements, configurations etc).
You can configure rule severity and optionally other parameters.
"""
import ast
import inspect
from robocop.messages import Message
from robocop.utils import modules_in_current_dir


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

    def scan_file(self, *args):
        raise NotImplementedError


class VisitorChecker(BaseChecker, ast.NodeVisitor):  # noqa
    type = 'visitor_checker'

    def scan_file(self, *args):
        self.visit_File(*args)

    def visit_File(self, node):  # noqa
        """ Perform generic ast visit on file node. """
        self.generic_visit(node)


class RawFileChecker(BaseChecker):  # noqa
    type = 'rawfile_checker'

    def scan_file(self, *args):
        self.parse_file()

    def parse_file(self):
        """ Read file line by line and for each call check_line method. """
        with open(self.source) as file:
            for lineno, line in enumerate(file):
                self.check_line(line, lineno + 1)

    def check_line(self, line, lineno):
        raise NotImplementedError


def init(linter):
    for module in modules_in_current_dir(__file__, __name__):
        try:
            module.register(linter)
        except AttributeError as err:
            linter.write_line(err)


def get_docs():
    for module in modules_in_current_dir(__file__, __name__):
        classes = inspect.getmembers(module, inspect.isclass)
        for checker in classes:
            if hasattr(checker[1], 'msgs') and checker[1].msgs:
                yield checker[1]
