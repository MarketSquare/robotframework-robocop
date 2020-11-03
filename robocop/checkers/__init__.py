"""
Robocop lint rules are internally grouped into similar groups called checkers. Each checker can scan for multiple
related issues (like ``LengthChecker`` checks both for min and max length of keyword). You can refer to specific
rules reported by checkers by its name or id (for example `0501` or `too-long-keyword`).

Checkers are categorized into following groups:
 * 01: base
 * 02: documentation
 * 03: naming
 * 04: errors
 * 05: lengths
 * 06: tags
 * 07: comments
 * 08: duplications
 * 09: misc
 * 10: spacing
 * 11-50: not yet used: reserved for future internal checkers
 * 51-99: reserved for external checkers

Checker has two basic types:

- ``VisitorChecker`` uses Robot Framework parsing api and Python `ast` module for traversing Robot code as nodes

- ``RawFileChecker`` simply reads Robot file as normal file and scans every line

Every rule has a `unique id` made of 4 digits where first 2 are `group id` while 2 latter are `rule id`.
`Unique id` as well as `rule name` can be used to refer to the rule (e.g. in include/exclude statements,
configurations etc.) You can optionally configure rule severity or other parameters.
"""
import ast
import inspect
from robocop.rules import Rule
from robocop.exceptions import DuplicatedRuleError
from robocop.utils import modules_in_current_dir, modules_from_paths


class BaseChecker:
    rules = None

    def __init__(self, configurable=None):
        self.disabled = False
        self.source = None
        self.rules_map = {}
        self.configurable = set() if configurable is None else configurable
        self.register_rules(self.rules)
        self.issues = []

    def register_rules(self, rules):
        for key, value in rules.items():
            rule = Rule(key, value)
            if rule.name in self.rules_map:
                raise DuplicatedRuleError('name', rule.name, self, self)
            self.rules_map[rule.name] = rule

    def report(self, rule, *args, node=None, lineno=None, col=None):
        if rule not in self.rules_map:
            raise ValueError(f"Missing definition for message with name {rule}")
        message = self.rules_map[rule].prepare_message(*args, source=self.source, node=node, lineno=lineno, col=col)
        self.issues.append(message)

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


def get_modules(linter):
    yield from modules_in_current_dir(__file__, __name__)
    yield from modules_from_paths(linter.config.ext_rules)


def init(linter):
    for module in get_modules(linter):
        classes = inspect.getmembers(module, inspect.isclass)
        for checker in classes:
            if issubclass(checker[1], BaseChecker) and hasattr(checker[1], 'rules') and checker[1].rules:
                linter.register_checker(checker[1]())


def get_docs():
    for module in modules_in_current_dir(__file__, __name__):
        classes = inspect.getmembers(module, inspect.isclass)
        for checker in classes:
            if hasattr(checker[1], 'rules') and checker[1].rules:
                yield checker[1]


def get_rules_for_atest():
    for module in modules_in_current_dir(__file__, __name__):
        classes = inspect.getmembers(module, inspect.isclass)
        for checker in classes:
            if not (hasattr(checker[1], 'rules') and checker[1].rules):
                continue
            for rule_id, rule_body in checker[1].rules.items():
                yield rule_body[0]
