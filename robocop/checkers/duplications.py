"""
Duplications checkers
"""
from collections import defaultdict
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name


def register(linter):
    linter.register_checker(DuplicationsChecker(linter))
    pass


class DuplicationsChecker(VisitorChecker):
    """ Checker for duplicated names. """
    rules = {
        "0801": (
            "duplicated-test-case",
            'Multiple test cases with name "%s" in suite',
            RuleSeverity.ERROR
        ),
        "0802": (
            "duplicated-keyword",
            'Multiple keywords with name "%s" in file',
            RuleSeverity.ERROR
        ),
        "0803": (
            "duplicated-variable",
            'Multiple variables with name "%s" in Variables section. Note that Robot Framework is case insensitive',
            RuleSeverity.ERROR
        ),
        "0804": (
            "duplicated-resource",
            'Multiple resource imports with name "%s" in suite',
            RuleSeverity.WARNING
        ),
        "0805": (
            "duplicated-library",
            'Multiple library imports with name "%s" and identical arguments in suite',
            RuleSeverity.WARNING
        )
    }

    def __init__(self, *args):
        self.test_cases = defaultdict(list)
        self.keywords = defaultdict(list)
        self.variables = defaultdict(list)
        self.resources = defaultdict(list)
        self.libraries = defaultdict(list)
        super().__init__(*args)

    def visit_File(self, node):
        self.test_cases = defaultdict(list)
        self.keywords = defaultdict(list)
        self.variables = defaultdict(list)
        self.resources = defaultdict(list)
        self.libraries = defaultdict(list)
        super().visit_File(node)
        self.check_duplicates(self.test_cases, "duplicated-test-case")
        self.check_duplicates(self.keywords, "duplicated-keyword")
        self.check_duplicates(self.variables, "duplicated-variable")
        self.check_duplicates(self.resources, "duplicated-resource")
        self.check_duplicates(self.libraries, "duplicated-library")

    def check_duplicates(self, container, rule):
        for name, nodes in container.items():
            if len(nodes) == 1:
                continue
            for duplicate in nodes:
                self.report(rule, duplicate.name, node=duplicate)

    def visit_TestCase(self, node):  # noqa
        self.test_cases[node.name].append(node)

    def visit_Keyword(self, node):  # noqa
        keyword_name = normalize_robot_name(node.name)
        self.keywords[keyword_name].append(node)

    def visit_VariableSection(self, node):  # noqa
        self.generic_visit(node)

    def visit_Variable(self, node):  # noqa
        if node.error is not None:
            return
        var_name = normalize_robot_name(self.replace_chars(node.name, '${}@&'))
        self.variables[var_name].append(node)

    @staticmethod
    def replace_chars(name, chars):
        return ''.join(c for c in name if c not in chars)

    def visit_ResourceImport(self, node):  # noqa
        self.resources[node.name].append(node)

    def visit_LibraryImport(self, node):  # noqa
        name_with_args = node.name + ''.join(token.value for token in node.data_tokens[2:])
        self.libraries[name_with_args].append(node)
