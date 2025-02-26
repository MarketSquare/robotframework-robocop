from typing import Optional

from robot.api.parsing import CommentSection, EmptyLine, Token

try:
    from robot.api.parsing import Config  # from RF 6.0
except ImportError:
    Config = None

from robotidy.disablers import skip_section_if_disabled
from robotidy.skip import Skip
from robotidy.transformers import Transformer
from robotidy.utils.misc import is_suite_templated


class NormalizeNewLines(Transformer):
    """
    Normalize new lines.

    Ensure that there is exactly:
    - ``section_lines = 1`` empty lines between sections,
    - ``test_case_lines = 1`` empty lines between test cases,
    - ``keyword_lines = test_case_lines`` empty lines between keywords.

    Removes empty lines after section (and before any data) and appends 1 empty line at the end of file.

    Consecutive empty lines inside settings, variables, keywords and test cases are also removed
    (configurable via ``consecutive_lines = 1``). If set to 0 all empty lines will be removed.

    If the suite contains Test Template tests will not be separated by empty lines unless ``separate_templated_tests``
    is set to True.
    """

    HANDLES_SKIP = frozenset({"skip_sections"})
    WHITESPACE_TOKENS = {Token.EOL, Token.SEPARATOR}

    def __init__(
        self,
        test_case_lines: int = 1,
        # | was added in Python 3.10. We can't use it with from __future__ import annotations because of RF
        # auto conversion - future annotations replaces everything to string
        keyword_lines: Optional[int] = None,
        section_lines: int = 2,
        separate_templated_tests: bool = False,
        consecutive_lines: int = 1,
        skip: Skip = None,
    ):
        super().__init__(skip)
        self.test_case_lines = test_case_lines
        self.keyword_lines = keyword_lines if keyword_lines is not None else test_case_lines
        self.section_lines = section_lines
        self.separate_templated_tests = separate_templated_tests
        self.consecutive_lines = consecutive_lines
        self.last_section = None
        self.last_test = None
        self.last_keyword = None
        self.templated = False

    def visit_File(self, node):  # noqa
        self.templated = not self.separate_templated_tests and is_suite_templated(node)
        self.last_section = node.sections[-1] if node.sections else None
        return self.generic_visit(node)

    def should_be_trimmed(self, node):
        """
        Check whether given section should have empty lines trimmed.
        Section should not be trimmed if it contains only language marker and there is no more than
        allowed section empty lines.
        """
        if not isinstance(node, CommentSection) or not Config:
            return True
        language_marker_only = False
        empty_lines = 0
        for statement in node.body:
            if isinstance(statement, Config):
                language_marker_only = True
            elif isinstance(statement, EmptyLine):
                empty_lines += 1
                if empty_lines > self.section_lines:
                    return True
            else:
                return True
        return not language_marker_only

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa
        should_be_trimmed = self.should_be_trimmed(node)
        if should_be_trimmed:
            self.trim_empty_lines(node)
        if node is self.last_section:
            return self.generic_visit(node)
        if should_be_trimmed:
            empty_line = EmptyLine.from_params()
            node.body.extend([empty_line] * self.section_lines)
        return self.generic_visit(node)

    def visit_TestCaseSection(self, node):  # noqa
        self.last_test = node.body[-1] if node.body else None
        return self.visit_Section(node)

    def visit_KeywordSection(self, node):  # noqa
        self.last_keyword = node.body[-1] if node.body else None
        return self.visit_Section(node)

    def visit_TestCase(self, node):  # noqa
        self.trim_empty_lines(node)
        if node is not self.last_test and not self.templated:
            node.body.extend([EmptyLine.from_params()] * self.test_case_lines)
        return self.generic_visit(node)

    def visit_Keyword(self, node):  # noqa
        self.trim_empty_lines(node)
        if node is not self.last_keyword:
            node.body.extend([EmptyLine.from_params()] * self.keyword_lines)
        return self.generic_visit(node)

    def visit_If(self, node):  # noqa
        self.trim_empty_lines(node)
        return self.generic_visit(node)

    visit_For = visit_While = visit_Try = visit_If

    def visit_Statement(self, node):  # noqa
        tokens = []
        cont = node.get_token(Token.CONTINUATION)
        for line in node.lines:
            if cont and all(token.type in self.WHITESPACE_TOKENS for token in line):
                continue
            if line[-1].type == Token.EOL:
                line[-1].value = "\n"
            tokens.extend(line)
        node.tokens = tokens
        return node

    def trim_empty_lines(self, node):
        self.trim_leading_empty_lines(node)
        self.trim_trailing_empty_lines(node)
        self.trim_consecutive_empty_lines(node)

    @staticmethod
    def trim_trailing_empty_lines(node):
        if not hasattr(node, "body"):
            return
        while node.body and isinstance(node.body[-1], EmptyLine):
            node.body.pop()

    @staticmethod
    def trim_leading_empty_lines(node):
        while node.body and isinstance(node.body[0], EmptyLine):
            node.body.pop(0)

    def trim_consecutive_empty_lines(self, node):
        empty_count = 0
        nodes = []
        for child in node.body:
            if isinstance(child, EmptyLine):
                empty_count += 1
            else:
                empty_count = 0
            if empty_count <= self.consecutive_lines:
                nodes.append(child)
        node.body = nodes
