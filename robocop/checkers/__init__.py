"""
Robocop rules are internally grouped into checkers. Each checker can scan for multiple related issues
(like ``LengthChecker`` checks both for minimum and maximum length of a keyword). You can refer to
specific rule reported by checkers by its name or id (for example `too-long-keyword` or `0501`).

.. dropdown:: Checker groups IDs:

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

try:
    from robot.api.parsing import ModelVisitor
except ImportError:
    from robot.parsing.model.visitor import ModelVisitor

from robot.utils import FileReader

from robocop.exceptions import RuleNotFoundError, RuleParamNotFoundError, RuleReportsNotFoundError
from robocop.utils import modules_from_paths, modules_in_current_dir


class BaseChecker:
    rules = None

    def __init__(self):
        self.disabled = False
        self.source = None
        self.lines = None
        self.issues = []
        self.rules = {}
        self.templated_suite = False

    def param(self, rule, param_name):
        try:
            return self.rules[rule].config[param_name].value
        except KeyError:
            if rule not in self.rules:
                raise RuleNotFoundError(rule, self) from None
            if param_name not in self.rules[rule].config:
                raise RuleParamNotFoundError(self.rules[rule], param_name, self) from None

    def report(
        self,
        rule,
        node=None,
        lineno=None,
        col=None,
        end_lineno=None,
        end_col=None,
        ext_disablers=None,
        sev_threshold_value=None,
        severity=None,
        **kwargs,
    ):
        if rule not in self.rules:
            raise ValueError(f"Missing definition for message with name {rule}")
        message = self.rules[rule].prepare_message(
            source=self.source,
            node=node,
            lineno=lineno,
            col=col,
            end_lineno=end_lineno,
            end_col=end_col,
            ext_disablers=ext_disablers,
            sev_threshold_value=sev_threshold_value,
            severity=severity,
            **kwargs,
        )
        if message.enabled:
            self.issues.append(message)


class VisitorChecker(BaseChecker, ModelVisitor):  # noqa
    type = "visitor_checker"

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
        """Perform generic ast visit on file node."""
        self.generic_visit(node)


class RawFileChecker(BaseChecker):  # noqa
    type = "rawfile_checker"

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
        """Read file line by line and for each call check_line method."""
        if self.lines is not None:
            for lineno, line in enumerate(self.lines):
                self.check_line(line, lineno + 1)
        else:
            with FileReader(self.source) as file_reader:
                for lineno, line in enumerate(file_reader.readlines()):
                    self.check_line(line, lineno + 1)

    def check_line(self, line, lineno):
        raise NotImplementedError


def init(linter):
    """For each module get `rules` dictionary and visitors. Instantiate each visitor and map it to the
    rule class instance using `reports` visitor attribute."""
    for module in get_modules(linter.config.ext_rules):
        classes = inspect.getmembers(module, inspect.isclass)
        module_rules = {rule.name: rule for rule in getattr(module, "rules", {}).values()}
        for checker in classes:
            if issubclass(checker[1], BaseChecker) and getattr(checker[1], "reports", False):
                checker_instance = checker[1]()
                for reported_rule in checker_instance.reports:
                    if reported_rule not in module_rules:
                        raise RuleReportsNotFoundError(reported_rule, checker_instance) from None
                    checker_instance.rules[reported_rule] = module_rules[reported_rule]
                linter.register_checker(checker_instance)


def get_modules(ext_rules):
    yield from modules_in_current_dir(__file__, __name__)
    yield from modules_from_paths(ext_rules)


def get_rules():
    for module in modules_in_current_dir(__file__, __name__):
        module_name = module.__name__.split(".")[-1]
        for rule in getattr(module, "rules", {}).values():
            yield module_name, rule
