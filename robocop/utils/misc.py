from pathlib import Path
from collections import Counter, defaultdict
from importlib import import_module
import importlib.util
import ast
import difflib
import re

from robot.api import Token
try:
    from robot.api.parsing import Variable
except ImportError:
    from robot.parsing.model.statements import Variable
from robot.version import VERSION

from robocop.rules import RuleSeverity
from robocop.exceptions import InvalidExternalCheckerError


IS_RF4 = VERSION.startswith('4')
DISABLED_IN_4 = frozenset(('nested-for-loop', 'invalid-comment'))
ENABLED_IN_4 = frozenset(('if-can-be-used', 'else-not-upper-case', 'variable-should-left-aligned'))


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
    return name.replace(' ', '').replace('_', '').lower() if name else ''


def keyword_col(node):
    return token_col(node, Token.KEYWORD)


def token_col(node, token_type):
    token = node.get_token(token_type)
    if token is None:
        return 1
    return token.col_offset + 1


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
                'line': max(0, issue.end_line - 1),
                'character': issue.end_col
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


def parse_assignment_sign_type(value):
    types = {
        'none': '',
        'equal_sign': '=',
        'space_and_equal_sign': ' =',
        'autodetect': 'autodetect'
    }
    if value not in types:
        raise ValueError(
            f"Expected one of ('none', 'equal_sign', 'space_and_equal_sign', 'autodetect') but got '{value}' instead")
    return types[value]


class RecommendationFinder:
    def find_similar(self, name, candidates):
        norm_name = self.normalize(name)
        norm_cand = self.get_normalized_candidates(candidates)
        matches = []
        for norm in norm_name:
            matches += self.find(norm, norm_cand.keys())
        if not matches:
            return ''
        matches = self.get_original_candidates(matches, norm_cand)
        suggestion = ' Did you mean:\n'
        suggestion += '\n'.join(f'    {match}' for match in matches)
        return suggestion

    def find(self, name, candidates, max_matches=5):
        """ Return a list of close matches to `name` from `candidates`. """
        if not name or not candidates:
            return []
        cutoff = self._calculate_cutoff(name)
        return difflib.get_close_matches(
            name, candidates, n=max_matches, cutoff=cutoff
        )

    @staticmethod
    def _calculate_cutoff(string, min_cutoff=.5, max_cutoff=.85,
                          step=.03):
        """ The longer the string the bigger required cutoff. """
        cutoff = min_cutoff + len(string) * step
        return min(cutoff, max_cutoff)

    @staticmethod
    def normalize(name):
        """
        Return tuple where first element is string created from sorted words in name,
        and second element is name without `-` and `_`.
        """
        norm = re.split('[-_ ]+', name)
        return ' '.join(sorted(norm)), name.replace('-', '').replace('_', '')

    @staticmethod
    def get_original_candidates(candidates, norm_candidates):
        """ Map found normalized candidates to unique original candidates. """
        return sorted(list(set(c for cand in candidates for c in norm_candidates[cand])))

    def get_normalized_candidates(self, candidates):
        """
        Thanks for normalizing and sorting we can find cases like this-is, thisis, this-is1 instead of is-this.
        Normalized names form dictionary that point to original names - we're using list because several names can
        have one common normalized name.
        Different normalization methods try to imitate possible mistakes done when typing name - different order,
        missing `-` etc.
        """
        norm = defaultdict(list)
        for cand in candidates:
            for norm_cand in self.normalize(cand):
                norm[norm_cand].append(cand)
        return norm


class TestTemplateFinder(ast.NodeVisitor):
    def __init__(self):
        self.templated = False

    def visit_TestTemplate(self, node):
        self.templated = bool(node.value)


def is_suite_templated(model):
    finder = TestTemplateFinder()
    finder.visit(model)
    return finder.templated
