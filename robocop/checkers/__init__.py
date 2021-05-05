"""
Robocop rules are internally grouped into checkers. Each checker can scan for multiple related issues
(like ``LengthChecker`` checks both for minimum and maximum length of a keyword). You can refer to
specific rule reported by checkers by its name or id (for example `too-long-keyword` or `0501`).

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

- ``VisitorChecker`` uses Robot Framework parsing API and Python `ast` module for traversing Robot code as nodes,

- ``RawFileChecker`` simply reads Robot file as normal file and scans every line.

Every rule has a `unique id` made of 4 digits where first 2 are `checker id` while 2 latter are `rule id`.
`Unique id` as well as `rule name` can be used to refer to the rule (e.g. in include/exclude statements,
configurations etc.). You can optionally configure rule severity or other parameters.
"""
import inspect
from robocop.rules import Rule
from robocop.exceptions import DuplicatedRuleError
from robocop.utils import modules_in_current_dir, modules_from_paths
try:
    from robot.api.parsing import ModelVisitor
except ImportError:
    from robot.parsing.model.visitor import ModelVisitor


class BaseChecker:
    rules = None

    def __init__(self):
        self.disabled = False
        self.source = None
        self.lines = None
        self.rules_map = {}
        self.register_rules(self.rules)
        self.issues = []
        self.templated_suite = False

    def register_rules(self, rules):
        for key, value in rules.items():
            rule = Rule(key, value)
            if rule.name in self.rules_map:
                raise DuplicatedRuleError('name', rule.name, self, self)
            self.rules_map[rule.name] = rule

    def report(self, rule, *args, node=None, lineno=None, col=None, end_lineno=None, end_col=None):
        if rule not in self.rules_map:
            raise ValueError(f"Missing definition for message with name {rule}")
        message = self.rules_map[rule].prepare_message(
            *args,
            source=self.source,
            node=node,
            lineno=lineno,
            col=col,
            end_lineno=end_lineno,
            end_col=end_col
        )
        if message.enabled:
            self.issues.append(message)

    def configure(self, param, value):
        self.__dict__[param] = value

class VisitorChecker(BaseChecker, ModelVisitor):  # noqa
    type = 'visitor_checker'

    def scan_file(self, ast_model, filename, in_memory_content, templated=False):
        self.issues = []
        self.source = filename
        self.templated_suite = templated
        if in_memory_content is not None:
            self.lines = in_memory_content.splitlines(keepends=True)
        else:
            self.lines = None
        self.visit_File(ast_model)
        return self.issues

    def visit_File(self, node):  # noqa
        """ Perform generic ast visit on file node. """
        self.generic_visit(node)


class RawFileChecker(BaseChecker):  # noqa
    type = 'rawfile_checker'

    def scan_file(self, ast_model, filename, in_memory_content, templated=False):
        self.issues = []
        self.source = filename
        self.templated_suite = templated
        if in_memory_content is not None:
            self.lines = in_memory_content.splitlines(keepends=True)
        else:
            self.lines = None
        self.parse_file()
        return self.issues

    def parse_file(self):
        """ Read file line by line and for each call check_line method. """
        if self.lines is not None:
            self._parse_lines(self.lines)
        else:
            with open(self.source, encoding='utf-8') as file:
                self._parse_lines(file)

    def _parse_lines(self, lines):
        for lineno, line in enumerate(lines):
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
        module_name = module.__name__.split('.')[-1]
        classes = inspect.getmembers(module, inspect.isclass)
        for checker in classes:
            if not (hasattr(checker[1], 'rules') and checker[1].rules):
                continue
            for rule_body in checker[1].rules.values():
                yield module_name, rule_body[0]
