"""
Robocop rules are internally grouped into checkers. Each checker can scan for multiple related issues
(like ``LengthChecker`` checks both for minimum and maximum length of a keyword). You can refer to
specific rule reported by checkers by its name or id (for example `too-long-keyword` or `0501`).

Checkers are categorized into following categories with a corresponding ID:
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

Checkers have two basic types:

- ``VisitorChecker`` uses Robot Framework parsing API and Python `ast` module for traversing Robot code as nodes,

- ``RawFileChecker`` simply reads Robot file as normal file and scans every line.

Every rule has a `unique id` made of 4 digits where first 2 are `checker id` while 2 latter are `rule id`.
`Unique id` as well as `rule name` can be used to refer to the rule (e.g. in include/exclude statements,
configurations etc.). You can optionally configure rule severity or other parameters.
"""
import ast
import importlib.util
import inspect
from collections import defaultdict
from importlib import import_module
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from robot.api.parsing import ModelVisitor
except ImportError:
    from robot.parsing.model.visitor import ModelVisitor

from robot.utils import FileReader

from robocop.exceptions import (
    InvalidExternalCheckerError,
    RuleNotFoundError,
    RuleParamNotFoundError,
    RuleReportsNotFoundError,
)


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
            raise

    def report(
        self,
        rule,
        node=None,
        lineno=None,
        col=None,
        end_lineno=None,
        end_col=None,
        extended_disablers=None,
        sev_threshold_value=None,
        severity=None,
        **kwargs,
    ):
        rule_def = self.rules.get(rule, None)
        if rule_def is None:
            raise ValueError(f"Missing definition for message with name {rule}")
        rule_threshold = rule_def.config.get("severity_threshold", None)
        if rule_threshold and rule_threshold.substitute_value and rule_threshold.thresholds:
            threshold_trigger = rule_threshold.get_matching_threshold(sev_threshold_value)
            if threshold_trigger is None:
                return
            kwargs[rule_threshold.substitute_value] = threshold_trigger
        message = rule_def.prepare_message(
            source=self.source,
            node=node,
            lineno=lineno,
            col=col,
            end_lineno=end_lineno,
            end_col=end_col,
            extended_disablers=extended_disablers,
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


def is_checker(checker_class_def: Tuple) -> bool:
    return issubclass(checker_class_def[1], BaseChecker) and getattr(checker_class_def[1], "reports", False)


class RobocopImporter:
    def __init__(self, external_rules_paths=None):
        self.internal_checkers_dir = Path(__file__).parent
        self.external_rules_paths = external_rules_paths
        self.imported_modules = set()
        self.seen_modules = set()
        self.seen_checkers = defaultdict(list)

    def get_initialized_checkers(self):
        for module in self.modules_from_paths([self.internal_checkers_dir, *self.external_rules_paths]):
            if module in self.seen_modules:
                continue
            for _, submodule in inspect.getmembers(module, inspect.ismodule):
                if submodule not in self.seen_modules:
                    yield from self._get_initialized_checkers_from_module(submodule)
            yield from self._get_initialized_checkers_from_module(module)

    def _get_initialized_checkers_from_module(self, module):
        self.seen_modules.add(module)
        for checker_instance in self.get_checkers_from_module(module):
            if not self.is_checker_already_imported(checker_instance):
                yield checker_instance

    def is_checker_already_imported(self, checker):
        """Check if checker was already imported.

        Checker name does not have to be unique, but it should use different rules."""
        checker_name = checker.__class__.__name__
        if checker_name in self.seen_checkers:
            if sorted(checker.rules.keys()) in self.seen_checkers[checker_name]:
                return True
        self.seen_checkers[checker_name].append(sorted(checker.rules.keys()))
        return False

    def modules_from_paths(self, paths):
        for path in paths:
            path_object = Path(path)
            if path_object.exists():
                if path_object.is_dir():
                    if path_object.name in {".git", "__pycache__"}:
                        continue
                    yield from self.modules_from_paths(list(path_object.iterdir()))
                elif path_object.suffix == ".py":
                    yield self._import_module_from_file(path_object)
            else:
                # if it's not physical path, try to import from installed modules
                try:
                    mod = import_module(path)
                    yield from self._iter_imports(Path(mod.__file__))
                    yield mod
                except ImportError:
                    raise InvalidExternalCheckerError(path) from None

    @staticmethod
    def _import_module_from_file(file_path):
        """Import Python file as module.

        importlib does not support importing Python files directly, and we need to create module specification first."""
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    @staticmethod
    def _find_imported_modules(module: ast.Module):
        """Return modules imported using `import module.dot.submodule` syntax.

        `from . import` are ignored - they are later covered by exploring submodules in the same namespace.
        """
        for st in module.body:
            if isinstance(st, ast.Import):
                for n in st.names:
                    yield n.name

    def _iter_imports(self, file_path: Path):
        """Discover Python imports in the file using ast module."""
        try:
            parsed = ast.parse(file_path.read_bytes())
        except Exception:  # noqa
            return
        for import_name in self._find_imported_modules(parsed):
            if import_name not in self.imported_modules:
                self.imported_modules.add(import_name)
            try:
                yield import_module(import_name)
            except ImportError:
                pass

    def get_imported_rules(self):
        for module in self.modules_from_paths([self.internal_checkers_dir]):
            module_name = module.__name__.split(".")[-1]
            for rule in getattr(module, "rules", {}).values():
                yield module_name, rule

    @staticmethod
    def get_rules_from_module(module) -> Dict:
        module_rules = getattr(module, "rules", {})
        if not isinstance(module_rules, dict):
            return {}
        return {rule.name: rule for rule in getattr(module, "rules", {}).values()}

    def get_checkers_from_module(self, module) -> List:
        classes = inspect.getmembers(module, inspect.isclass)
        checkers = [checker for checker in classes if is_checker(checker)]
        module_rules = self.get_rules_from_module(module)
        checker_instances = []
        for checker in checkers:
            checker_instance = checker[1]()
            valid_checker = True
            for reported_rule in checker_instance.reports:
                if reported_rule not in module_rules:
                    valid_checker = False
                    if module_rules:
                        # empty rules are silently ignored when rules and checkers are imported separately
                        raise RuleReportsNotFoundError(reported_rule, checker_instance) from None
                    continue
                checker_instance.rules[reported_rule] = module_rules[reported_rule]
            if valid_checker:
                checker_instances.append(checker_instance)
        return checker_instances


def init(linter):
    robocop_importer = RobocopImporter(linter.config.ext_rules)
    for checker in robocop_importer.get_initialized_checkers():
        linter.register_checker(checker)


def get_rules():
    """Get only rules definitions for documentation generation."""
    robocop_importer = RobocopImporter()
    yield from robocop_importer.get_imported_rules()
