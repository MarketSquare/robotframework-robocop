"""
Spacing checkers
"""
import re
from collections import Counter

from robot.api import Token
from robot.parsing.model.blocks import Keyword, TestCase
from robot.parsing.model.statements import Comment, EmptyLine
from robot.parsing.model.visitor import ModelVisitor

from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity, SeverityThreshold
from robocop.utils import get_errors, get_section_name, token_col

rules = {
    "1001": Rule(
        rule_id="1001",
        name="trailing-whitespace",
        msg="Trailing whitespace at the end of line",
        severity=RuleSeverity.WARNING,
    ),
    "1002": Rule(
        rule_id="1002",
        name="missing-trailing-blank-line",
        msg="Missing trailing blank line at the end of file",
        severity=RuleSeverity.WARNING,
    ),
    "1003": Rule(
        RuleParam(
            name="empty_lines",
            default=2,
            converter=int,
            desc="number of empty lines required between sections",
        ),
        rule_id="1003",
        name="empty-lines-between-sections",
        msg="Invalid number of empty lines between sections ({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
    ),
    "1004": Rule(
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of empty lines required between test cases",
        ),
        rule_id="1004",
        name="empty-lines-between-test-cases",
        msg="Invalid number of empty lines between test cases ({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
    ),
    "1005": Rule(
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of empty lines required between keywords",
        ),
        rule_id="1005",
        name="empty-lines-between-keywords",
        msg="Invalid number of empty lines between keywords ({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
    ),
    "1006": Rule(
        rule_id="1006",
        name="mixed-tabs-and-spaces",
        msg="Inconsistent use of tabs and spaces in file",
        severity=RuleSeverity.WARNING,
    ),
    "1007": Rule(
        rule_id="1007",
        name="uneven-indent",
        msg="Line is {{ over_or_under }}-indented",
        severity=RuleSeverity.WARNING,
        docs="""
        Reported when line does not follow indent from the current block. 
        Example of rule violation::
        
            Keyword With Over Indented Setting
                [Documentation]  this is doc
                 [Arguments]  ${arg}  # over-indented
                   No Operation  # over-indented
                Pass
                No Operation
                Fail
        
        """,
    ),
    "1008": Rule(
        rule_id="1008",
        name="bad-indent",
        msg="Indent expected",
        severity=RuleSeverity.ERROR,
        docs="""
        Expecting indent. Example of rule violation::
        
             FOR  ${elem}  IN  ${list}
            Log  stuff  # content of FOR blocks should use bigger indentation than FOR header
             END
        
        """,
    ),
    "1009": Rule(
        RuleParam(
            name="empty_lines",
            default=0,
            converter=int,
            desc="number of empty lines allowed after section header",
        ),
        SeverityThreshold("empty_lines"),
        rule_id="1009",
        name="empty-line-after-section",
        msg="Too many empty lines after '{{ section_name }}' section header "
        "({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
        docs="""
        Empty lines after the section header are not allowed by default. Example of rule violation::
        
             *** Test Cases ***
             
             Resource  file.resource
        
        It can be configured using `empty_lines` parameter.
        """,
    ),
    "1010": Rule(
        rule_id="1010",
        name="too-many-trailing-blank-lines",
        msg="Too many blank lines at the end of file",
        severity=RuleSeverity.WARNING,
        docs="""There should be exactly one blank line at the end of the file""",
    ),
    "1011": Rule(
        rule_id="1011",
        name="misaligned-continuation",
        msg="Continuation marker should be aligned with starting row",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::
        
                Default Tags       default tag 1    default tag 2    default tag 3
            ...                default tag 4    default tag 5
            
                *** Test Cases ***
                Example
                    Do X    first argument    second argument    third argument
                  ...    fourth argument    fifth argument    sixth argument
        
        """,
    ),
    "1012": Rule(
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of allowed consecutive empty lines",
        ),
        SeverityThreshold("empty_lines", compare_method="greater"),
        rule_id="1012",
        name="consecutive-empty-lines",
        msg="Too many consecutive empty lines ({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::
        
            Keyword
                Step 1
                
                
                Step 2

        """,
    ),
    "1013": Rule(
        rule_id="1013",
        name="empty-lines-in-statement",
        msg="Multi-line statement with empty lines",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::
        
             Keyword
             ...  1
             # empty line in-between multiline statement
             ...  2
        
        """,
    ),
    "1014": Rule(
        rule_id="1014",
        name="variable-should-be-left-aligned",
        msg="Variable in Variable section should be left aligned",
        severity=RuleSeverity.ERROR,
        version=">=4.0",
        docs="""
        Example of rule violation::
        
            *** Variables ***
             ${VAR}  1
              ${VAR2}  2
        
        """,
    ),
    "1015": Rule(
        rule_id="1015",
        name="misaligned-continuation-row",
        msg="Each next continuation line should be aligned with the previous one",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::
        
            *** Settings ***
            Documentation      Here we have documentation for this suite.
            ...                Documentation is often quite long.
            ...
            ...            It can also contain multiple paragraphs.  # misaligned
            
            *** Test Cases ***
            Test
            [Tags]    you    probably    do    not    have    this    many
            ...      tags    in    real    life  # misaligned
        
        """,
    ),
    "1016": Rule(
        rule_id="1016",
        name="suite-setting-should-be-left-aligned",
        msg="Setting in Settings section should be left aligned",
        severity=RuleSeverity.ERROR,
        version=">=4.0",
        docs="""
        Example of rule violation::
        
            *** Settings ***
                Library  Collections
                Resource  data.resource
                Variables  vars.robot
        
        """,
    ),
}


class InvalidSpacingChecker(RawFileChecker):
    """Checker for trailing spaces and lines."""

    reports = (
        "trailing-whitespace",
        "missing-trailing-blank-line",
        "too-many-trailing-blank-lines",
    )

    def __init__(self):
        self.raw_lines = []
        super().__init__()

    def parse_file(self):
        self.raw_lines = []
        super().parse_file()
        if self.raw_lines:
            last_line = self.raw_lines[-1]
            if last_line in ["\n", "\r", "\r\n"]:
                self.report("too-many-trailing-blank-lines", lineno=len(self.raw_lines) + 1)
                return
            empty_lines = 0
            for line in self.raw_lines[::-1]:
                if not line.strip():
                    empty_lines += 1
                else:
                    break
                if empty_lines > 1:
                    self.report("too-many-trailing-blank-lines", lineno=len(self.raw_lines))
                    return
            if not empty_lines and not last_line.endswith(("\n", "\r")):
                self.report("missing-trailing-blank-line", lineno=len(self.raw_lines))

    def check_line(self, line, lineno):
        self.raw_lines.append(line)

        stripped_line = line.rstrip("\n\r")
        if stripped_line and stripped_line[-1] in [" ", "\t"]:
            self.report("trailing-whitespace", lineno=lineno, col=len(stripped_line))


class EmptyLinesChecker(VisitorChecker):
    """Checker for invalid spacing."""

    reports = (
        "empty-lines-between-sections",
        "empty-lines-between-test-cases",
        "empty-lines-between-keywords",
        "empty-line-after-section",
        "consecutive-empty-lines",
        "empty-lines-in-statement",
    )

    def verify_consecutive_empty_lines(self, lines, check_leading=True, check_trailing=False):
        allowed_consecutive = self.param("consecutive-empty-lines", "empty_lines")
        empty_lines = 0
        last_empty_line = None
        data_found = check_leading
        for line in lines:
            if isinstance(line, EmptyLine):
                if not data_found:
                    continue
                empty_lines += 1
                last_empty_line = line
            else:
                data_found = True
                if empty_lines > allowed_consecutive:
                    self.report(
                        "consecutive-empty-lines",
                        empty_lines=empty_lines,
                        allowed_empty_lines=allowed_consecutive,
                        node=last_empty_line,
                        sev_threshold_value=empty_lines,
                    )
                empty_lines = 0
        if check_trailing:
            if empty_lines > allowed_consecutive:
                self.report(
                    "consecutive-empty-lines",
                    empty_lines=empty_lines,
                    allowed_empty_lines=allowed_consecutive,
                    node=last_empty_line,
                    sev_threshold_value=empty_lines,
                )
        return empty_lines

    def check_empty_lines_in_keyword_test(self, node):
        """
        Verify number of consecutive empty lines inside keyword or test.
        Return number of trailing empty lines.
        """
        # split node and trailing empty lines/comments
        end_found = False
        node_lines, trailing_lines = [], []
        for child in node.body[::-1]:
            if not end_found and isinstance(child, (EmptyLine, Comment)):
                trailing_lines.append(child)
            else:
                end_found = True
                node_lines.append(child)
        node_lines = node_lines[::-1]
        trailing_lines = trailing_lines[::-1]
        self.verify_consecutive_empty_lines(node_lines)
        return self.verify_consecutive_empty_lines(trailing_lines)

    def visit_Statement(self, node):  # noqa
        prev_token = None
        for token in node.tokens:
            if token.type == Token.EOL:
                if prev_token:
                    self.report("empty-lines-in-statement", node=token)
                prev_token = token
            else:
                prev_token = None

    def visit_VariableSection(self, node):  # noqa
        self.verify_consecutive_empty_lines(node.body, check_leading=False)
        self.generic_visit(node)

    def visit_SettingSection(self, node):  # noqa
        self.verify_consecutive_empty_lines(node.body, check_leading=False)
        self.generic_visit(node)

    def verify_empty_lines_between_nodes(self, node, node_type, issue_name, allowed_empty_lines):
        last_index = len(node.body) - 1
        for index, child in enumerate(node.body):
            if not isinstance(child, node_type):
                continue
            empty_lines = self.check_empty_lines_in_keyword_test(child)
            if allowed_empty_lines not in (empty_lines, -1) and index < last_index:
                self.report(
                    issue_name,
                    empty_lines=empty_lines,
                    allowed_empty_lines=allowed_empty_lines,
                    lineno=child.end_lineno,
                )
        self.generic_visit(node)

    def visit_TestCaseSection(self, node):  # noqa
        allowed_lines = -1 if self.templated_suite else self.param("empty-lines-between-test-cases", "empty_lines")
        self.verify_empty_lines_between_nodes(node, TestCase, "empty-lines-between-test-cases", allowed_lines)

    def visit_KeywordSection(self, node):  # noqa
        self.verify_empty_lines_between_nodes(
            node,
            Keyword,
            "empty-lines-between-keywords",
            self.param("empty-lines-between-keywords", "empty_lines"),
        )

    def visit_For(self, node):  # noqa
        self.verify_consecutive_empty_lines(node.body, check_trailing=True)
        self.generic_visit(node)

    visit_ForLoop = visit_While = visit_Try = visit_If = visit_For

    def visit_File(self, node):  # noqa
        for section in node.sections:
            self.check_empty_lines_after_section(section)
        for section in node.sections[:-1]:
            if not section.header:  # for comment section
                continue
            empty_lines = 0
            for child in reversed(section.body):
                if isinstance(child, (Keyword, TestCase)):
                    for statement in reversed(child.body):
                        if isinstance(statement, EmptyLine):
                            empty_lines += 1
                        else:
                            break
                if isinstance(child, EmptyLine):
                    empty_lines += 1
                elif isinstance(child, Comment):
                    continue
                else:
                    break
            if empty_lines != self.param("empty-lines-between-sections", "empty_lines"):
                self.report(
                    "empty-lines-between-sections",
                    empty_lines=empty_lines,
                    allowed_empty_lines=self.param("empty-lines-between-sections", "empty_lines"),
                    lineno=section.end_lineno,
                )
        super().visit_File(node)

    def check_empty_lines_after_section(self, section):
        empty_lines = []
        for child in section.body:
            if not isinstance(child, EmptyLine):
                break
            empty_lines.append(child)
        else:
            return
        if len(empty_lines) > self.param("empty-line-after-section", "empty_lines"):
            self.report(
                "empty-line-after-section",
                section_name=get_section_name(section),
                empty_lines=len(empty_lines),
                allowed_empty_lines=self.param("empty-line-after-section", "empty_lines"),
                node=empty_lines[-1],
                sev_threshold_value=len(empty_lines),
            )


class InconsistentUseOfTabsAndSpacesChecker(VisitorChecker, ModelVisitor):
    """Checker for inconsistent use of tabs and spaces."""

    reports = ("mixed-tabs-and-spaces",)

    def __init__(self):
        self.found, self.tabs, self.spaces = False, False, False
        super().__init__()

    def visit_File(self, node):  # noqa
        self.found, self.tabs, self.spaces = False, False, False
        super().visit_File(node)

    def visit_Statement(self, node):  # noqa
        if self.found:
            return
        for token in node.get_tokens(Token.SEPARATOR):
            self.tabs = "\t" in token.value or self.tabs
            self.spaces = " " in token.value or self.spaces

            if self.tabs and self.spaces:
                self.report("mixed-tabs-and-spaces", node=node, lineno=1)
                self.found = True
                break


class UnevenIndentChecker(VisitorChecker):
    """Checker for indentation violations."""

    reports = (
        "uneven-indent",
        "bad-indent",
    )

    HEADERS = {
        Token.ARGUMENTS,
        Token.DOCUMENTATION,
        Token.SETUP,
        Token.TIMEOUT,
        Token.TEARDOWN,
        Token.TEMPLATE,
        Token.TAGS,
    }

    def visit_TestCaseSection(self, node):  # noqa
        self.check_standalone_comments_indent(node)

    def visit_KeywordSection(self, node):  # noqa
        self.check_standalone_comments_indent(node)

    def check_standalone_comments_indent(self, node):
        # comments before first test case / keyword
        for child in node.body:
            if (
                getattr(child, "type", "") == Token.COMMENT
                and getattr(child, "tokens", None)
                and child.tokens[0].type == Token.SEPARATOR
            ):
                self.report(
                    "uneven-indent",
                    over_or_under="over",
                    node=child,
                    col=token_col(child, Token.COMMENT),
                )
        self.generic_visit(node)

    def visit_TestCase(self, node):  # noqa
        self.check_indents(node)
        self.generic_visit(node)

    def visit_Keyword(self, node):  # noqa
        if not node.name.lstrip().startswith("#"):
            self.check_indents(node)
        self.generic_visit(node)

    def visit_ForLoop(self, node):  # noqa
        column_index = 2 if node.end is not None else 0
        self.check_indents(node, node.header.tokens[1].col_offset + 1, column_index)

    visit_For = visit_If = visit_While = visit_ForLoop

    def visit_Try(self, node):  # noqa
        column_index = 2 if node.end is not None else 0
        self.check_indents(node, node.header.tokens[1].col_offset + 1, column_index)
        while node.next:
            node = node.next
            self.check_indents(node, node.header.tokens[1].col_offset + 1, column_index)

    @staticmethod
    def get_indent(node):
        tokens = node.tokens if hasattr(node, "tokens") else node.header.tokens
        indent_len = 0
        for token in tokens:
            if token.type != Token.SEPARATOR:
                break
            indent_len += len(token.value.expandtabs(4))
        return indent_len

    def check_indents(self, node, req_indent=0, column_index=0, previous_indent=None):
        indents = []
        header_indents = []
        templated = self.is_templated(node)
        end_of_block = self.find_block_end(node) if not column_index else len(node.body)
        for index, child in enumerate(node.body):
            if index == end_of_block:
                break
            if child.lineno == node.lineno or isinstance(child, EmptyLine):
                continue
            indent_len = self.get_indent(child)
            if indent_len is None:
                continue
            if hasattr(child, "type") and child.type in UnevenIndentChecker.HEADERS:
                if templated:
                    header_indents.append((indent_len, child))
                else:
                    indents.append((indent_len, child))
            else:
                if indent_len < req_indent:
                    self.report("bad-indent", node=child)
                else:
                    indents.append((indent_len, child))
        if not column_index:
            self.validate_standalone_comments(node.body[end_of_block:])
        previous_indent = self.validate_indent_lists(indents, previous_indent)
        if templated:
            self.validate_indent_lists(header_indents)
        if getattr(node, "orelse", None):
            self.check_indents(node.orelse, req_indent, column_index, previous_indent)

    def validate_indent_lists(self, indents, previous_indent=None):
        counter = Counter(indent[0] for indent in indents)
        if previous_indent:  # in case of continuing blocks, ie if else blocks, remember the indent
            counter = previous_indent + counter
        elif len(indents) < 2:
            return counter
        if len(counter) == 1:  # everything have the same indent
            return counter
        common_indent = counter.most_common(1)[0][0]
        for indent in indents:
            if indent[0] != common_indent:
                self.report(
                    "uneven-indent",
                    over_or_under="over" if indent[0] > common_indent else "under",
                    node=indent[1],
                    col=indent[0] + 1,
                )
        return counter

    def validate_standalone_comments(self, comments_and_eols):
        """
        Report any comment that does not start from col 1.

        :param comments_and_eols: list of comments and empty lines (outside keyword and test case definitions)
        """
        for child in comments_and_eols:
            if getattr(child, "type", "invalid") != Token.COMMENT:
                continue
            col = token_col(child, Token.COMMENT)
            if col != 1:
                self.report("uneven-indent", over_or_under="over", node=child, col=col)

    @staticmethod
    def find_block_end(node):
        """
        Find where the keyword/test case/block ends. If there are only comments and new lines left, the
        first comment that starts from col 1 is considered outside your block::

            Keyword
                Line
                # comment
                Other Line
               # comment belonging to Keyword

            # This should not belong to Keyword
              # Since there was comment starting from col 1, this comment is also outside block
        """
        for index, child in reversed(list(enumerate(node.body))):
            node_type = getattr(child, "type", "")
            if not node_type:
                return len(node.body) - 1
            if node_type not in (Token.COMMENT, Token.EOL):
                break
        else:
            return len(node.body) - 1
        for block_index, child in enumerate(node.body[index + 1 :]):
            if getattr(child, "type", "invalid") == Token.COMMENT and token_col(child, Token.COMMENT) == 1:
                return block_index + index + 1
        return len(node.body) - 1

    @staticmethod
    def is_templated(node):
        if not isinstance(node, TestCase):
            return False
        for child in node.body:
            if hasattr(child, "type") and child.type == "TEMPLATE":
                return True
        return False


class MisalignedContinuation(VisitorChecker, ModelVisitor):
    """Checker for misaligned continuation line markers."""

    reports = (
        "misaligned-continuation",
        "misaligned-continuation-row",
    )

    def visit_Statement(self, node):  # noqa
        if not node.data_tokens:
            return
        starting_row = self.get_indent(node.tokens)
        first_column, indent = 0, 0
        for index, line in enumerate(node.lines):
            if index == 0:
                starting_row = self.get_indent(line)
                if node.type == Token.TAGS:
                    first_column = self.first_line_indent(line, node.type, Token.ARGUMENT)
                continue
            indent = 0
            for token in line:
                if token.type == Token.SEPARATOR:  # count possible indent before or after ...
                    indent += len(token.value.expandtabs(4))
                elif token.type == Token.CONTINUATION:
                    if indent != starting_row:
                        self.report(
                            "misaligned-continuation",
                            lineno=token.lineno,
                            col=token.col_offset + 1,
                        )
                        break
                    indent = 0
                elif token.type != Token.EOL and token.value.strip():  # ignore trailing whitespace
                    if first_column:
                        if indent != first_column:
                            self.report(
                                "misaligned-continuation-row",
                                node=token,
                                col=token.col_offset + 1,
                            )
                    else:
                        first_column = indent
                    break  # check only first value

    @staticmethod
    def get_indent(tokens):
        indent_len = 0
        for token in tokens:
            if token.type != Token.SEPARATOR:
                break
            indent_len += len(token.value.expandtabs(4))
        return indent_len

    @staticmethod
    def first_line_indent(tokens, from_tok, search_for):
        """
        Find indent required for other lines to match indentation of first line.

        [from_token]     <search_for>
        ...<-   pos   ->

        :param tokens: statement first line tokens
        :param from_tok: start counting separator after finding from_tok token
        :param search_for: stop counting after finding search_for token
        :return: pos: length of indent
        """
        pos = 0
        found = False
        for token in tokens:
            if not found:
                if token.type == from_tok:
                    found = True
                    # subtract 3 to adjust for ... length in 2nd line
                    pos += len(token.value) - 3
            elif token.type == Token.SEPARATOR:
                pos += len(token.value.expandtabs(4))
            elif token.type == search_for:
                return pos
        return 0  # 0 will ignore first line indent and compare to 2nd line only


class LeftAlignedChecker(VisitorChecker):
    """Checker for left align."""

    reports = (
        "variable-should-be-left-aligned",
        "suite-setting-should-be-left-aligned",
    )

    suite_settings = {
        "documentation": "Documentation",
        "suitesetup": "Suite Setup",
        "suiteteardown": "Suite Teardown",
        "metadata": "Metadata",
        "testsetup": "Test Setup",
        "testteardown": "Test Teardown",
        "testtemplate": "Test Template",
        "testtimeout": "Test Timeout",
        "forcetags": "Force Tags",
        "defaulttags": "Default Tags",
        "library": "Library",
        "resource": "Resource",
        "variables": "Variables",
    }

    def visit_VariableSection(self, node):  # noqa
        for child in node.body:
            if not child.data_tokens:
                continue
            token = child.data_tokens[0]
            if token.type == Token.VARIABLE and (token.value == "" or token.value.startswith(" ")):
                if token.value or not child.get_token(Token.ARGUMENT):
                    pos = len(token.value) - len(token.value.lstrip()) + 1
                else:
                    pos = child.get_token(Token.ARGUMENT).col_offset + 1
                self.report("variable-should-be-left-aligned", lineno=token.lineno, col=pos)

    def visit_SettingSection(self, node):  # noqa
        for child in node.body:
            for error in get_errors(child):
                if "Non-existing setting" in error:
                    self.parse_error(child, error)

    def parse_error(self, node, error):
        setting_error = re.search("Non-existing setting '(.*)'.", error)
        if not setting_error:
            return
        setting_error = setting_error.group(1)
        if not setting_error:
            setting_cand = node.get_token(Token.COMMENT)
            if setting_cand and setting_cand.value.replace(" ", "").lower() in self.suite_settings:
                self.report(
                    "suite-setting-should-be-left-aligned",
                    node=setting_cand,
                    col=setting_cand.col_offset + 1,
                )
        elif not setting_error[0].strip():  # starts with space/tab
            suite_sett_cand = setting_error.replace(" ", "").lower()
            for setting in self.suite_settings:
                if suite_sett_cand.startswith(setting):
                    indent = len(setting_error) - len(setting_error.lstrip())
                    self.report(
                        "suite-setting-should-be-left-aligned",
                        node=node,
                        col=indent + 1,
                    )
                    break
