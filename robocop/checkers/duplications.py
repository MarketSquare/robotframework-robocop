"""
Duplications checkers
"""
from collections import defaultdict

from robot.api import Token

from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name
from robocop.exceptions import InvalidRuleConfigurableError


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
            'Multiple variables with name "%s" in Variables section. Note that Robot Framework is case-insensitive',
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

    def visit_File(self, node):  # noqa
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
            "%s",
            RuleSeverity.WARNING,
            (
                'sections_order',
                'sections_order',
                str,
                'order of sections in comma separated list. For example: settings,variables,testcases,keywords'
            )
        ),
        "0810": (
            "both-tests-and-tasks",
            "Both Task(s) and Test Case(s) section headers defined in file",
            RuleSeverity.ERROR
        )
    }

    def __init__(self):
        self.sections_order = {}
        self.section_order_str = None
        self.configure('sections_order', 'settings,variables,testcases,keywords')
        self.sections_by_order = []
        self.sections_by_existence = set()
        super().__init__()

    def configure(self, param, value):
        section_map = {
            'settings': Token.SETTING_HEADER,
            'variables': Token.VARIABLE_HEADER,
            'testcase': Token.TESTCASE_HEADER,
            'testcases': Token.TESTCASE_HEADER,
            'task': 'TASK HEADER',
            'tasks': 'TASK HEADER',
            'keyword': Token.KEYWORD_HEADER,
            'keywords': Token.KEYWORD_HEADER
        }
        sections_order = {}
        for index, name in enumerate(value.split(',')):
            if name.lower() not in section_map or section_map[name.lower()] in sections_order:
                raise InvalidRuleConfigurableError('0809', value)
            sections_order[section_map[name.lower()]] = index
        if Token.TESTCASE_HEADER in sections_order:
            sections_order['TASK HEADER'] = sections_order[Token.TESTCASE_HEADER]
        super().configure(param, sections_order)
        self.section_order_str = self.section_order_to_str(value)

    @staticmethod
    def section_order_to_str(value):
        name_map = {
            'settings': 'Settings',
            'variables': 'Variables',
            'testcase': 'Test Cases / Tasks',
            'testcases': 'Test Cases / Tasks',
            'tasks': 'Test Cases / Tasks',
            'task': 'Test Cases / Tasks',
            'keyword': 'Keywords',
            'keywords': 'Keywords'
        }
        order = []
        for name in value.split(','):
            mapped_name = name_map[name.lower()]
            if mapped_name not in order:
                order.append(mapped_name)
        return ' > '.join(order)

    def visit_File(self, node):  # noqa
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
            self.report("section-out-of-order", node.data_tokens[0].value, self.section_order_str, node=node)
        self.sections_by_order.append(order_id)
        self.sections_by_existence.add(section_name)
