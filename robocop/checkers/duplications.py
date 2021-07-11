"""
Duplications checkers
"""
from collections import defaultdict

from robot.api import Token

from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name


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
            'Multiple resource imports with path "%s" in suite',
            RuleSeverity.WARNING
        ),
        "0805": (
            "duplicated-library",
            'Multiple library imports with name "%s" and identical arguments in suite',
            RuleSeverity.WARNING
        ),
        "0806": (
            "duplicated-metadata",
            'Duplicated metadata "%s" in suite',
            RuleSeverity.WARNING
        ),
        "0807": (
            "duplicated-variables-import",
            'Duplicated variables import with path "%s" in suite',
            RuleSeverity.WARNING
        )
    }

    def __init__(self):
        self.test_cases = defaultdict(list)
        self.keywords = defaultdict(list)
        self.variables = defaultdict(list)
        self.resources = defaultdict(list)
        self.libraries = defaultdict(list)
        self.metadata = defaultdict(list)
        self.variable_imports = defaultdict(list)
        super().__init__()

    def visit_File(self, node):
        self.test_cases = defaultdict(list)
        self.keywords = defaultdict(list)
        self.variables = defaultdict(list)
        self.resources = defaultdict(list)
        self.libraries = defaultdict(list)
        self.metadata = defaultdict(list)
        self.variable_imports = defaultdict(list)
        super().visit_File(node)
        self.check_duplicates(self.test_cases, "duplicated-test-case")
        self.check_duplicates(self.keywords, "duplicated-keyword")
        self.check_duplicates(self.variables, "duplicated-variable")
        self.check_duplicates(self.resources, "duplicated-resource")
        self.check_duplicates(self.libraries, "duplicated-library")
        self.check_duplicates(self.metadata, "duplicated-metadata")
        self.check_duplicates(self.variable_imports, "duplicated-variables-import")

    def check_duplicates(self, container, rule):
        for nodes in container.values():
            if len(nodes) == 1:
                continue
            for duplicate in nodes:
                self.report(rule, duplicate.name, node=duplicate)

    def visit_TestCase(self, node):  # noqa
        testcase_name = normalize_robot_name(node.name)
        self.test_cases[testcase_name].append(node)

    def visit_Keyword(self, node):  # noqa
        keyword_name = normalize_robot_name(node.name)
        self.keywords[keyword_name].append(node)

    def visit_VariableSection(self, node):  # noqa
        self.generic_visit(node)

    def visit_Variable(self, node):  # noqa
        if not node.name:
            return
        var_name = normalize_robot_name(self.replace_chars(node.name, '${}@&'))
        self.variables[var_name].append(node)

    @staticmethod
    def replace_chars(name, chars):
        return ''.join(c for c in name if c not in chars)

    def visit_ResourceImport(self, node):  # noqa
        if node.name:
            self.resources[node.name].append(node)

    def visit_LibraryImport(self, node):  # noqa
        if not node.name:
            return
        name_with_args = node.name + ''.join(token.value for token in node.data_tokens[2:])
        self.libraries[name_with_args].append(node)

    def visit_Metadata(self, node):  # noqa
        if node.name is not None:
            self.metadata[node.name + node.value].append(node)

    def visit_VariablesImport(self, node): # noqa
        if node.name:
            self.variable_imports[node.name].append(node)


class SectionHeadersChecker(VisitorChecker):
    """ Checker for duplicated or out of order section headers. """
    rules = {
        "0808": (
            "section-already-defined",
            "'%s' section header already defined in file",
            RuleSeverity.WARNING
        ),
        "0809": (
            "section-out-of-order",
            "'%s' section header is defined in wrong order: "
            "Setting(s) > Variable(s) > Test Case(s) / Task(s) > Keyword(s)",
            RuleSeverity.WARNING
        ),
        "0810": (
            "both-tests-and-tasks",
            "Both Task(s) and Test Case(s) section headers defined in file",
            RuleSeverity.ERROR
        )
    }

    def __init__(self):
        self.sections_order = {
            Token.SETTING_HEADER: 0,
            Token.VARIABLE_HEADER: 1,
            Token.TESTCASE_HEADER: 2,
            'TASK HEADER': 2,
            Token.KEYWORD_HEADER: 4
        }
        self.sections_by_order = []
        self.sections_by_existence = set()
        super().__init__()

    def visit_File(self, node):
        self.sections_by_order = []
        self.sections_by_existence = set()
        super().visit_File(node)

    def visit_SectionHeader(self, node):  # noqa
        section_name = node.type
        if section_name not in self.sections_order:
            return
        if section_name == Token.TESTCASE_HEADER:
            if 'task' in node.name.lower():
                section_name = 'TASK HEADER'
                if Token.TESTCASE_HEADER in self.sections_by_existence:
                    self.report("both-tests-and-tasks", node=node)
            else:
                if 'TASK HEADER' in self.sections_by_existence:
                    self.report("both-tests-and-tasks", node=node)
        order_id = self.sections_order[section_name]
        if section_name in self.sections_by_existence:
            self.report("section-already-defined", node.data_tokens[0].value, node=node)
        if any(previous_id > order_id for previous_id in self.sections_by_order):
            self.report("section-out-of-order", node.data_tokens[0].value, node=node)
        self.sections_by_order.append(order_id)
        self.sections_by_existence.add(section_name)
