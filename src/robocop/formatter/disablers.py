from __future__ import annotations

import functools
import re

from robot.api.parsing import Comment, CommentSection, ModelVisitor, Token

ALL_FORMATTERS = "all"


def skip_if_disabled(func):
    """
    Skip node if it is disabled.

    Do not format node if it's not within passed ``start_line`` and ``end_line`` or
    it does match any ``# robocop: fmt: off`` disabler
    """

    @functools.wraps(func)
    def wrapper(self, node, *args, **kwargs):  # noqa: ANN202
        class_name = self.__class__.__name__
        if self.disablers.is_node_disabled(class_name, node):
            return node
        return func(self, node, *args, **kwargs)

    return wrapper


def get_section_name_from_header_type(node):
    header_type = node.header.type if node.header else "COMMENT HEADER"
    return {
        "SETTING HEADER": "settings",
        "VARIABLE HEADER": "variables",
        "TESTCASE HEADER": "testcases",
        "TASK HEADER": "tasks",
        "KEYWORD HEADER": "keywords",
        "COMMENT HEADER": "comments",
    }.get(header_type, "invalid")


def skip_section_if_disabled(func):
    """
    Skip section if it is disabled.

    Does the same checks as ``skip_if_disabled`` and additionally checks if the section header does not contain
    disabler.
    """

    @functools.wraps(func)
    def wrapper(self, node, *args, **kwargs):  # noqa: ANN202
        class_name = self.__class__.__name__
        if self.disablers.is_node_disabled(class_name, node):
            return node
        if self.disablers.is_header_disabled(class_name, node.lineno):
            return node
        if self.skip:
            section_name = get_section_name_from_header_type(node)
            if self.skip.section(section_name):
                return node
        return func(self, node, *args, **kwargs)

    return wrapper


def is_line_start(node):
    for token in node.tokens:
        if token.type == Token.SEPARATOR:
            continue
        return token.col_offset == 0
    return False


class DisablersInFile:
    def __init__(self, start_line: int | None, end_line: int | None, file_end: int | None = None):
        self.start_line = start_line
        self.end_line = end_line
        self.file_end = file_end
        self.disablers = {ALL_FORMATTERS: DisabledLines(start_line, end_line, file_end)}

    @property
    def file_disabled(self):
        return self.is_disabled_in_file(ALL_FORMATTERS)

    def parse_global_disablers(self):
        self.disablers[ALL_FORMATTERS].parse_global_disablers()

    def sort_disablers(self):
        for disabled_lines in self.disablers.values():
            disabled_lines.sort_disablers()

    def add_disabler(self, formatter: str, start_line: int, end_line: int, file_level: bool = False):
        if formatter not in self.disablers:
            self.disablers[formatter] = DisabledLines(self.start_line, self.end_line, self.file_end)
        self.disablers[formatter].add_disabler(start_line, end_line)
        if file_level:
            self.disablers[formatter].disabled_whole = file_level

    def add_disabled_header(self, formatter: str, lineno):
        if formatter not in self.disablers:
            self.disablers[formatter] = DisabledLines(self.start_line, self.end_line, self.file_end)
        self.disablers[formatter].add_disabled_header(lineno)

    def is_disabled_in_file(self, formatter_name: str) -> bool:
        if self.disablers[ALL_FORMATTERS].disabled_whole:
            return True
        if formatter_name not in self.disablers:
            return False
        return self.disablers[formatter_name].disabled_whole

    def is_header_disabled(self, formatter_name: str, line) -> bool:
        if self.disablers[ALL_FORMATTERS].is_header_disabled(line):
            return True
        if formatter_name not in self.disablers:
            return False
        return self.disablers[formatter_name].is_header_disabled(line)

    def is_node_disabled(self, formatter_name: str, node, full_match=True) -> bool:
        if self.disablers[ALL_FORMATTERS].is_node_disabled(node, full_match):
            return True
        if formatter_name not in self.disablers:
            return False
        return self.disablers[formatter_name].is_node_disabled(node, full_match)


class DisabledLines:
    def __init__(self, start_line, end_line, file_end):
        self.start_line = start_line
        self.end_line = end_line
        self.file_end = file_end
        self.lines = []
        self.disabled_headers = set()
        self.disabled_whole = False

    def add_disabler(self, start_line, end_line):
        self.lines.append((start_line, end_line))

    def add_disabled_header(self, lineno):
        self.disabled_headers.add(lineno)

    def parse_global_disablers(self):
        if not self.start_line:
            return
        end_line = self.end_line if self.end_line else self.start_line
        if self.start_line > 1:
            self.add_disabler(1, self.start_line - 1)
        if end_line < self.file_end:
            self.add_disabler(end_line + 1, self.file_end)

    def sort_disablers(self):
        self.lines = sorted(self.lines, key=lambda x: x[0])

    def is_header_disabled(self, line):
        return line in self.disabled_headers

    def is_node_disabled(self, node, full_match=True):
        if not node or not self.lines:
            return False
        end_lineno = max(node.lineno, node.end_lineno)  # workaround for formatters setting -1 as end_lineno
        if full_match:
            for start_line, end_line in self.lines:
                # lines are sorted on start_line, so we can return on first match
                if end_line >= end_lineno:
                    return start_line <= node.lineno
        else:
            for start_line, end_line in self.lines:
                if node.lineno <= end_line and end_lineno >= start_line:
                    return True
        return False


class RegisterDisablers(ModelVisitor):
    def __init__(self, start_line, end_line):
        self.start_line = start_line
        self.end_line = end_line
        self.disablers = DisablersInFile(start_line, end_line)
        self.disabler_pattern = re.compile(r"#\s(?:robocop:\s)?fmt: (?P<disabler>on|off) ?=?(?P<formatters>[\w,\s]+)?")
        self.disablers_in_scope: list[dict[str, int]] = []
        self.file_level_disablers = False

    def is_disabled_in_file(self, formatter_name: str = ALL_FORMATTERS) -> bool:
        return self.disablers.is_disabled_in_file(formatter_name)

    def get_disabler(self, comment: Token) -> re.Match | None:
        if not comment.value:
            return None
        return self.disabler_pattern.search(comment.value)

    def close_disabler(self, end_line):
        disabler = self.disablers_in_scope.pop()
        for formatter_name, start_line in disabler.items():
            if not start_line:
                continue
            self.disablers.add_disabler(formatter_name, start_line, end_line, self.file_level_disablers)

    def visit_File(self, node):  # noqa: N802
        self.file_level_disablers = False
        self.disablers = DisablersInFile(self.start_line, self.end_line, node.end_lineno)
        self.disablers.parse_global_disablers()
        self.stack = []
        for index, section in enumerate(node.sections):
            self.file_level_disablers = index == 0 and isinstance(section, CommentSection)
            self.visit_Section(section)
        self.disablers.sort_disablers()

    @staticmethod
    def get_disabler_formatters(match) -> list[str]:
        if not match.group("formatters") or "=" not in match.group(0):  # robocop: fmt: off or fmt: off comment
            return [ALL_FORMATTERS]
        # fmt: off=Formatter1, Formatter2
        return [formatter.strip() for formatter in match.group("formatters").split(",") if formatter.strip()]

    def visit_SectionHeader(self, node):  # noqa: N802
        for comment in node.get_tokens(Token.COMMENT):
            disabler = self.get_disabler(comment)
            if not disabler or disabler.group("disabler") != "off":
                continue
            formatters = self.get_disabler_formatters(disabler)
            for formatter in formatters:
                self.disablers.add_disabled_header(formatter, node.lineno)
            break
        return self.generic_visit(node)

    def visit_TestCase(self, node):  # noqa: N802
        self.disablers_in_scope.append({ALL_FORMATTERS: 0})
        self.generic_visit(node)
        self.close_disabler(node.end_lineno)

    def visit_Try(self, node):  # noqa: N802
        self.generic_visit(node.header)
        self.disablers_in_scope.append({ALL_FORMATTERS: 0})
        for statement in node.body:
            self.visit(statement)
        self.close_disabler(node.end_lineno)
        tail = node
        while tail.next:
            self.generic_visit(tail.header)
            self.disablers_in_scope.append({ALL_FORMATTERS: 0})
            for statement in tail.body:
                self.visit(statement)
            end_line = tail.next.lineno - 1 if tail.next else tail.end_lineno
            self.close_disabler(end_line=end_line)
            tail = tail.next

    visit_Keyword = visit_Section = visit_For = visit_ForLoop = visit_If = visit_While = visit_TestCase  # noqa: N815

    def visit_Statement(self, node):  # noqa: N802
        if isinstance(node, Comment):
            comment = node.get_token(Token.COMMENT)
            disabler = self.get_disabler(comment)
            if not disabler:
                return
            formatters = self.get_disabler_formatters(disabler)
            index = 0 if is_line_start(node) else -1
            disabler_start = disabler.group("disabler") == "on"
            for formatter in formatters:
                if disabler_start:
                    start_line = self.disablers_in_scope[index].get(formatter)
                    if not start_line:  # no disabler open
                        continue
                    self.disablers.add_disabler(formatter, start_line, node.lineno)
                    self.disablers_in_scope[index][formatter] = 0
                elif not self.disablers_in_scope[index].get(formatter):
                    self.disablers_in_scope[index][formatter] = node.lineno
        else:
            # inline disabler
            for comment in node.get_tokens(Token.COMMENT):
                disabler = self.get_disabler(comment)
                if not disabler:
                    continue
                formatters = self.get_disabler_formatters(disabler)
                if disabler.group("disabler") == "off":
                    for formatter in formatters:
                        self.disablers.add_disabler(formatter, node.lineno, node.end_lineno)
