from pathlib import Path
from collections import Counter
from importlib import import_module
import importlib.util
import ast

from robocop.rules import RuleSeverity
from robocop.exceptions import InvalidExternalCheckerError

from robot.api import Token
try:
    from robot.api.parsing import Variable
except ImportError:
    from robot.parsing.model import Variable
from robot.version import VERSION


IS_RF4 = VERSION.startswith('4')
DISABLED_IN_4 = frozenset(('nested-for-loop', 'invalid-comment'))
ENABLED_IN_4 = frozenset(('if-can-be-used', 'else-not-upper-case'))


def modules_in_current_dir(path, module_name):
    """ Yield modules inside `path` parent directory """
    yield from modules_from_path(Path(path).parent, module_name)


def modules_from_paths(paths):
    for path in paths:
        path = Path(path)
        if not path.exists():
            raise InvalidExternalCheckerError(path)
        if path.is_dir():
            yield from modules_from_paths([file for file in path.iterdir() if '__pycache__' not in str(file)])
        else:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            mod = importlib.util.module_from_spec(spec)

            spec.loader.exec_module(mod)
            yield mod


def modules_from_path(path, module_name=None, relative='.'):
    """ Traverse current directory and yield python files imported as module """
    if path.is_file():
        yield import_module(relative + path.stem, module_name)
    elif path.is_dir():
        for file in path.iterdir():
            if '__pycache__' in str(file):
                continue
            if file.suffix == '.py' and file.stem != '__init__':
                yield from modules_from_path(file, module_name, relative)


def normalize_robot_name(name):
    return name.replace(' ', '').replace('_', '').lower()


def keyword_col(node):
    keyword_token = node.get_token(Token.KEYWORD)
    if keyword_token is None:
        return 0
    return keyword_token.col_offset


def rule_severity_to_diag_sev(severity):
    return {
        RuleSeverity.ERROR: 1,
        RuleSeverity.WARNING: 2,
        RuleSeverity.INFO: 3
    }.get(severity, 4)


def issues_to_lsp_diagnostic(issues):
    return [{
        'range': {
            'start': {
                'line': max(0, issue.line - 1),
                'character': issue.col
                },
            'end': {
                'line': max(0, issue.line - 1),
                'character': issue.col
            }
        },
        'severity': rule_severity_to_diag_sev(issue.severity),
        'code': issue.rule_id,
        'source': 'robocop',
        'message': issue.desc
    } for issue in issues]


class AssignmentTypeDetector(ast.NodeVisitor):
    """ Visitor for counting number and type of assignments """
    def __init__(self):
        self.keyword_sign_counter = Counter()
        self.keyword_most_common = None
        self.variables_sign_counter = Counter()
        self.variables_most_common = None

    def visit_File(self, node):  # noqa
        self.generic_visit(node)
        if len(self.keyword_sign_counter) >= 2:
            self.keyword_most_common = self.keyword_sign_counter.most_common(1)[0][0]
        if len(self.variables_sign_counter) >= 2:
            self.variables_most_common = self.variables_sign_counter.most_common(1)[0][0]

    def visit_KeywordCall(self, node):  # noqa
        if node.assign:  # if keyword returns any value
            sign = self.get_assignment_sign(node.assign[-1])
            self.keyword_sign_counter[sign] += 1

    def visit_VariableSection(self, node):  # noqa
        for child in node.body:
            if not isinstance(child, Variable):
                continue
            var_token = child.get_token(Token.VARIABLE)
            sign = self.get_assignment_sign(var_token.value)
            self.variables_sign_counter[sign] += 1
        return node

    @staticmethod
    def get_assignment_sign(token_value):
        return token_value[token_value.find('}')+1:]


def parse_equal_sign_type(value):
    types = {
        'remove': '',
        'equal_sign': '=',
        'space_and_equal_sign': ' =',
        'autodetect': None
    }
    # if value not in types: TODO
    #     raise click.BadOptionUsage(
    #         option_name='transform',
    #         message=f"Invalid configurable value: {value} for equal_sign_type for AssignmentNormalizer transformer."
    #                 f" Possible values:\n    remove\n    equal_sign\n    space_and_equal_sign"
    #     )
    return types[value]
