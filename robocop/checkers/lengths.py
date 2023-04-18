"""
Lengths checkers
"""
import re

from robot.api import Token
from robot.parsing.model.blocks import CommentSection, TestCase
from robot.parsing.model.statements import (
    Arguments,
    Comment,
    Documentation,
    EmptyLine,
    KeywordCall,
    Template,
    TemplateArguments,
)

try:
    from robot.api.parsing import Break, Continue, ReturnStatement
except ImportError:
    ReturnStatement, Break, Continue = None, None, None

from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity, SeverityThreshold
from robocop.utils import get_section_name, normalize_robot_name, pattern_type, str2bool

rules = {
    "0501": Rule(
        RuleParam(name="max_len", default=40, converter=int, desc="number of lines allowed in a keyword"),
        RuleParam(name="ignore_docs", default=False, converter=str2bool, show_type="bool", desc="Ignore documentation"),
        SeverityThreshold("max_len", compare_method="greater"),
        rule_id="0501",
        name="too-long-keyword",
        msg="Keyword '{{ keyword_name }}' is too long ({{ keyword_length }}/{{ allowed_length}})",
        severity=RuleSeverity.WARNING,
    ),
    "0502": Rule(
        RuleParam(name="min_calls", default=1, converter=int, desc="number of keyword calls required in a keyword"),
        SeverityThreshold("min_calls", compare_method="less"),
        rule_id="0502",
        name="too-few-calls-in-keyword",
        msg="Keyword '{{ keyword_name }}' has too few keywords inside ({{ keyword_count }}/{{ min_allowed_count }})",
        severity=RuleSeverity.WARNING,
    ),
    "0503": Rule(
        RuleParam(name="max_calls", default=10, converter=int, desc="number of keyword calls allowed in a keyword"),
        SeverityThreshold("max_calls", compare_method="greater"),
        rule_id="0503",
        name="too-many-calls-in-keyword",
        msg="Keyword '{{ keyword_name }}' has too many keywords inside ({{ keyword_count }}/{{ max_allowed_count }})",
        severity=RuleSeverity.WARNING,
    ),
    "0504": Rule(
        RuleParam(name="max_len", default=20, converter=int, desc="number of lines allowed in a test case"),
        RuleParam(name="ignore_docs", default=False, converter=str2bool, show_type="bool", desc="Ignore documentation"),
        SeverityThreshold("max_len", compare_method="greater"),
        rule_id="0504",
        name="too-long-test-case",
        msg="Test case '{{ test_name }}' is too long ({{ test_length }}/{{ allowed_length }})",
        severity=RuleSeverity.WARNING,
    ),
    "0505": Rule(
        RuleParam(name="max_calls", default=10, converter=int, desc="number of keyword calls allowed in a test case"),
        RuleParam(
            name="ignore_templated", default=False, converter=str2bool, show_type="bool", desc="Ignore templated tests"
        ),
        SeverityThreshold("max_calls", compare_method="greater"),
        rule_id="0505",
        name="too-many-calls-in-test-case",
        msg="Test case '{{ test_name }}' has too many keywords inside ({{ keyword_count }}/{{ max_allowed_count }})",
        docs="Redesign the test and move complex logic to separate keywords to increase readability.",
        severity=RuleSeverity.WARNING,
    ),
    "0506": Rule(
        RuleParam(name="max_lines", default=400, converter=int, desc="number of lines allowed in a file"),
        SeverityThreshold("max_lines", compare_method="greater"),
        rule_id="0506",
        name="file-too-long",
        msg="File has too many lines ({{ lines_count }}/{{max_allowed_count }})",
        severity=RuleSeverity.WARNING,
    ),
    "0507": Rule(
        RuleParam(name="max_args", default=5, converter=int, desc="number of lines allowed in a file"),
        SeverityThreshold("max_args", compare_method="greater"),
        rule_id="0507",
        name="too-many-arguments",
        msg="Keyword '{{ keyword_name }}' has too many arguments ({{ arguments_count }}/{{ max_allowed_count }})",
        severity=RuleSeverity.WARNING,
    ),
    "0508": Rule(
        RuleParam(name="line_length", default=120, converter=int, desc="number of characters allowed in line"),
        RuleParam(
            name="ignore_pattern",
            default=re.compile(r"https?://\S+"),
            converter=pattern_type,
            show_type="regex",
            desc="ignore lines that contain configured pattern",
        ),
        SeverityThreshold("line_length"),
        rule_id="0508",
        name="line-too-long",
        msg="Line is too long ({{ line_length }}/{{ allowed_length }})",
        severity=RuleSeverity.WARNING,
        docs="""
        It is possible to ignore lines that match regex pattern. Configure it using following option::

            robocop --configure line-too-long:ignore_pattern:pattern

        The default pattern is ``https?://\S+`` that ignores the lines that look like an URL.

        """,
    ),
    "0509": Rule(
        rule_id="0509", name="empty-section", msg="Section '{{ section_name }}' is empty", severity=RuleSeverity.WARNING
    ),
    "0510": Rule(
        RuleParam(
            name="max_returns", default=4, converter=int, desc="allowed number of returned values from a keyword"
        ),
        SeverityThreshold("max_returns", compare_method="greater"),
        rule_id="0510",
        name="number-of-returned-values",
        msg="Too many return values ({{ return_count }}/{{ max_allowed_count }})",
        severity=RuleSeverity.WARNING,
    ),
    "0511": Rule(
        rule_id="0511",
        name="empty-metadata",
        msg="Metadata settings does not have any value set",
        severity=RuleSeverity.WARNING,
    ),
    "0512": Rule(
        rule_id="0512",
        name="empty-documentation",
        msg="Documentation of {{ block_name }} is empty",
        severity=RuleSeverity.WARNING,
    ),
    "0513": Rule(rule_id="0513", name="empty-force-tags", msg="Force Tags are empty", severity=RuleSeverity.WARNING),
    "0514": Rule(
        rule_id="0514", name="empty-default-tags", msg="Default Tags are empty", severity=RuleSeverity.WARNING
    ),
    "0515": Rule(
        rule_id="0515", name="empty-variables-import", msg="Import variables path is empty", severity=RuleSeverity.ERROR
    ),
    "0516": Rule(
        rule_id="0516", name="empty-resource-import", msg="Import resource path is empty", severity=RuleSeverity.ERROR
    ),
    "0517": Rule(
        rule_id="0517", name="empty-library-import", msg="Import library path is empty", severity=RuleSeverity.ERROR
    ),
    "0518": Rule(
        rule_id="0518",
        name="empty-setup",
        msg="Setup of {{ block_name }} does not have any keywords",
        severity=RuleSeverity.ERROR,
    ),
    "0519": Rule(
        rule_id="0519",
        name="empty-suite-setup",
        msg="Suite Setup does not have any keywords",
        severity=RuleSeverity.ERROR,
    ),
    "0520": Rule(
        rule_id="0520",
        name="empty-test-setup",
        msg="Test Setup does not have any keywords",
        severity=RuleSeverity.ERROR,
    ),
    "0521": Rule(
        rule_id="0521",
        name="empty-teardown",
        msg="Teardown of {{ block_name }} does not have any keywords",
        severity=RuleSeverity.ERROR,
    ),
    "0522": Rule(
        rule_id="0522",
        name="empty-suite-teardown",
        msg="Suite Teardown does not have any keywords",
        severity=RuleSeverity.ERROR,
    ),
    "0523": Rule(
        rule_id="0523",
        name="empty-test-teardown",
        msg="Test Teardown does not have any keywords",
        severity=RuleSeverity.ERROR,
    ),
    "0524": Rule(
        rule_id="0524", name="empty-timeout", msg="Timeout of {{ block_name }} is empty", severity=RuleSeverity.WARNING
    ),
    "0525": Rule(rule_id="0525", name="empty-test-timeout", msg="Test Timeout is empty", severity=RuleSeverity.WARNING),
    "0526": Rule(
        rule_id="0526",
        name="empty-arguments",
        msg="Arguments of {{ block_name }} are empty",
        severity=RuleSeverity.ERROR,
    ),
    "0527": Rule(
        RuleParam(name="max_testcases", default=50, converter=int, desc="number of test cases allowed in a suite"),
        RuleParam(
            name="max_templated_testcases",
            default=100,
            converter=int,
            desc="number of test cases allowed in a templated suite",
        ),
        SeverityThreshold("max_testcases or max_templated_testcases"),
        rule_id="0527",
        name="too-many-test-cases",
        msg="Too many test cases ({{ test_count }}/{{ max_allowed_count }})",
        severity=RuleSeverity.WARNING,
    ),
    "0528": Rule(
        RuleParam(name="min_calls", default=1, converter=int, desc="number of keyword calls required in a test case"),
        RuleParam(
            name="ignore_templated", default=False, converter=str2bool, show_type="bool", desc="Ignore templated tests"
        ),
        rule_id="0528",
        name="too-few-calls-in-test-case",
        msg="Test case '{{ test_name }}' has too few keywords inside ({{ keyword_count }}/{{ min_allowed_count }})",
        docs="""
        Test without keywords will fail. Add more keywords or set results using Fail, Pass, Skip keywords::

            *** Test Cases ***
            Test case
                [Tags]    smoke
                Skip    Test case draft

        """,
        severity=RuleSeverity.ERROR,
    ),
    "0529": Rule(
        rule_id="0529",
        name="empty-test-template",
        msg="Test Template is empty",
        docs="""
        ``Test Template`` sets the template to all tests in a suite. Empty value is considered an error
        because it leads the users to wrong impression on how the suite operates.
        Without value, the setting is ignored and the tests are not templated.
        """,
        severity=RuleSeverity.ERROR,
    ),
    "0530": Rule(
        rule_id="0530",
        name="empty-template",
        msg="Template of {{ block_name }} is empty. "
        "To overwrite suite Test Template use more explicit [Template]  NONE",
        docs="""
        The ``[Template]`` setting overrides the possible template set in the Setting section, and an empty value for 
        ``[Template]`` means that the test has no template even when Test Template is used.
        
        If it is intended behaviour, use more explicit ``NONE`` value to indicate that you want to overwrite suite 
        Test Template::
        
            *** Settings ***
            Test Template    Template Keyword
            
            *** Test Cases ***
            Templated test
                argument
            
            Not templated test
                [Template]    NONE

        """,
        severity=RuleSeverity.WARNING,
    ),
}


def is_data_statement(node):
    return not isinstance(node, (EmptyLine, Comment))


def is_not_standalone_comment(node):
    return isinstance(node, Comment) and node.tokens[0].type == Token.SEPARATOR


def check_node_length(node, ignore_docs):
    last_node = node
    for child in node.body[::-1]:
        if is_data_statement(child) or is_not_standalone_comment(child):
            last_node = child
            break
    if ignore_docs:
        return (last_node.end_lineno - node.lineno - get_documentation_length(node)), last_node.end_lineno
    return (last_node.end_lineno - node.lineno), last_node.end_lineno


def get_documentation_length(node):
    doc_len = 0
    for child in node.body:
        if isinstance(child, Documentation):
            doc_len += child.end_lineno - child.lineno + 1
    return doc_len


class LengthChecker(VisitorChecker):
    """Checker for max and min length of keyword or test case. It analyses number of lines and also number of
    keyword calls (as you can have just few keywords but very long ones or vice versa).
    """

    reports = (
        "too-few-calls-in-keyword",
        "too-few-calls-in-test-case",
        "too-many-calls-in-keyword",
        "too-many-calls-in-test-case",
        "too-long-keyword",
        "too-long-test-case",
        "file-too-long",
        "too-many-arguments",
    )

    def visit_File(self, node):
        if node.end_lineno > self.param("file-too-long", "max_lines"):
            self.report(
                "file-too-long",
                lines_count=node.end_lineno,
                max_allowed_count=self.param("file-too-long", "max_lines"),
                node=node,
                lineno=node.end_lineno,
                end_col=node.end_col_offset,
                sev_threshold_value=node.end_lineno,
            )
        super().visit_File(node)

    def visit_Keyword(self, node):  # noqa
        if node.name.lstrip().startswith("#"):
            return
        for child in node.body:
            if isinstance(child, Arguments):
                args_number = len(child.values)
                if args_number > self.param("too-many-arguments", "max_args"):
                    self.report(
                        "too-many-arguments",
                        keyword_name=node.name,
                        arguments_count=args_number,
                        max_allowed_count=self.param("too-many-arguments", "max_args"),
                        node=node,
                        end_col=node.col_offset + len(node.name) + 1,
                        sev_threshold_value=args_number,
                    )
                break
        length, node_end_line = check_node_length(node, ignore_docs=self.param("too-long-keyword", "ignore_docs"))
        if length > self.param("too-long-keyword", "max_len"):
            self.report(
                "too-long-keyword",
                keyword_name=node.name,
                keyword_length=length,
                allowed_length=self.param("too-long-keyword", "max_len"),
                node=node,
                end_col=node.col_offset + len(node.name) + 1,
                ext_disablers=(node.lineno, node_end_line),
                sev_threshold_value=length,
            )
            return
        key_calls = LengthChecker.count_keyword_calls(node)
        if key_calls < self.param("too-few-calls-in-keyword", "min_calls"):
            self.report(
                "too-few-calls-in-keyword",
                keyword_name=node.name,
                keyword_count=key_calls,
                min_allowed_count=self.param("too-few-calls-in-keyword", "min_calls"),
                node=node,
                end_col=node.col_offset + len(node.name) + 1,
                sev_threshold_value=key_calls,
            )
        elif key_calls > self.param("too-many-calls-in-keyword", "max_calls"):
            self.report(
                "too-many-calls-in-keyword",
                keyword_name=node.name,
                keyword_count=key_calls,
                max_allowed_count=self.param("too-many-calls-in-keyword", "max_calls"),
                node=node,
                end_col=node.col_offset + len(node.name) + 1,
                sev_threshold_value=key_calls,
            )

    def test_is_templated(self, node):
        if self.templated_suite:
            return True
        if not node.body:
            return False
        for statement in node.body:
            if isinstance(statement, Template):
                return True
        return False

    def visit_TestCase(self, node):  # noqa
        length, _ = check_node_length(node, ignore_docs=self.param("too-long-test-case", "ignore_docs"))
        if length > self.param("too-long-test-case", "max_len"):
            self.report(
                "too-long-test-case",
                test_name=node.name,
                test_length=length,
                allowed_length=self.param("too-long-test-case", "max_len"),
                node=node,
                end_col=node.col_offset + len(node.name) + 1,
                sev_threshold_value=length,
            )
        test_is_templated = self.test_is_templated(node)
        skip_too_many = test_is_templated and self.param("too-many-calls-in-test-case", "ignore_templated")
        skip_too_few = test_is_templated and self.param("too-few-calls-in-test-case", "ignore_templated")
        if skip_too_few and skip_too_many:
            return
        key_calls = LengthChecker.count_keyword_calls(node)
        if not skip_too_many and (key_calls > self.param("too-many-calls-in-test-case", "max_calls")):
            self.report(
                "too-many-calls-in-test-case",
                test_name=node.name,
                keyword_count=key_calls,
                max_allowed_count=self.param("too-many-calls-in-test-case", "max_calls"),
                node=node,
                sev_threshold_value=key_calls,
                end_col=node.col_offset + len(node.name) + 1,
            )
        elif not skip_too_few and (key_calls < self.param("too-few-calls-in-test-case", "min_calls")):
            self.report(
                "too-few-calls-in-test-case",
                test_name=node.name,
                keyword_count=key_calls,
                min_allowed_count=self.param("too-few-calls-in-test-case", "min_calls"),
                node=node,
                sev_threshold_value=key_calls,
                end_col=node.col_offset + len(node.name) + 1,
            )

    @staticmethod
    def count_keyword_calls(node):
        # ReturnStatement is imported and evaluates to true in RF 5.0+, we don't need to also check Break/Continue
        if (
            isinstance(node, (KeywordCall, TemplateArguments))
            or ReturnStatement
            and isinstance(node, (Break, Continue, ReturnStatement))
        ):
            return 1
        if not hasattr(node, "body"):
            return 0
        calls = sum(LengthChecker.count_keyword_calls(child) for child in node.body)
        while node and getattr(node, "orelse", None):
            node = node.orelse
            calls += sum(LengthChecker.count_keyword_calls(child) for child in node.body)
        while node and getattr(node, "next", None):
            node = node.next
            calls += sum(LengthChecker.count_keyword_calls(child) for child in node.body)
        return calls


class LineLengthChecker(RawFileChecker):
    """Checker for maximum length of a line."""

    reports = ("line-too-long",)
    # replace `# noqa` or `# robocop`, `# robocop: enable`, `# robocop: disable=optional,rule,names`
    disabler_pattern = re.compile(r"(# )+(noqa|robocop: ?(?P<disabler>disable|enable)=?(?P<rules>[\w\-,]*))")

    def check_line(self, line, lineno):
        if self.param("line-too-long", "ignore_pattern") and self.param("line-too-long", "ignore_pattern").search(line):
            return
        line = self.disabler_pattern.sub("", line)
        line = line.rstrip().expandtabs(4)
        if len(line) > self.param("line-too-long", "line_length"):
            self.report(
                "line-too-long",
                line_length=len(line),
                allowed_length=self.param("line-too-long", "line_length"),
                lineno=lineno,
                end_col=len(line) + 1,
                sev_threshold_value=len(line),
            )


class EmptySectionChecker(VisitorChecker):
    """Checker for detecting empty sections."""

    reports = ("empty-section",)

    def check_if_empty(self, node):
        if not node.header:
            return
        anything_but = EmptyLine if isinstance(node, CommentSection) else (Comment, EmptyLine)
        if all(isinstance(child, anything_but) for child in node.body):
            self.report(
                "empty-section",
                section_name=get_section_name(node),
                node=node,
                col=node.col_offset + 1,
                end_col=node.header.end_col_offset,
            )

    def visit_Section(self, node):  # noqa
        self.check_if_empty(node)


class NumberOfReturnedArgsChecker(VisitorChecker):
    """Checker for number of returned values from a keyword."""

    reports = ("number-of-returned-values",)

    def visit_Return(self, node):  # noqa
        self.check_node_returns(len(node.values), node)

    visit_ReturnStatement = visit_Return

    def visit_KeywordCall(self, node):  # noqa
        if not node.keyword:
            return

        normalized_name = normalize_robot_name(node.keyword, remove_prefix="builtin.")
        if normalized_name == "returnfromkeyword":
            self.check_node_returns(len(node.args), node)
        elif normalized_name == "returnfromkeywordif":
            self.check_node_returns(len(node.args) - 1, node)

    def check_node_returns(self, return_count, node):
        if return_count > self.param("number-of-returned-values", "max_returns"):
            self.report(
                "number-of-returned-values",
                return_count=return_count,
                max_allowed_count=self.param("number-of-returned-values", "max_returns"),
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.data_tokens[0].end_col_offset + 1,
                sev_threshold_value=return_count,
            )


class EmptySettingsChecker(VisitorChecker):
    """Checker for detecting empty settings."""

    reports = (
        "empty-metadata",
        "empty-documentation",
        "empty-force-tags",
        "empty-default-tags",
        "empty-variables-import",
        "empty-resource-import",
        "empty-library-import",
        "empty-setup",
        "empty-suite-setup",
        "empty-test-setup",
        "empty-teardown",
        "empty-suite-teardown",
        "empty-test-teardown",
        "empty-timeout",
        "empty-test-timeout",
        "empty-template",
        "empty-test-template",
        "empty-arguments",
    )

    def __init__(self):
        self.parent_node_name = ""
        super().__init__()

    def visit_SettingSection(self, node):  # noqa
        self.parent_node_name = "Test Suite"
        self.generic_visit(node)

    def visit_TestCaseName(self, node):  # noqa
        if node.name:
            self.parent_node_name = f"'{node.name}' Test Case"
        else:
            self.parent_node_name = ""
        self.generic_visit(node)

    def visit_Keyword(self, node):  # noqa
        if node.name:
            self.parent_node_name = f"'{node.name}' Keyword"
        else:
            self.parent_node_name = ""
        self.generic_visit(node)

    def visit_Metadata(self, node):  # noqa
        if node.name is None:
            self.report("empty-metadata", node=node, col=node.col_offset + 1)

    def visit_Documentation(self, node):  # noqa
        if not node.value:
            self.report(
                "empty-documentation",
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_ForceTags(self, node):  # noqa
        if not node.values:
            self.report("empty-force-tags", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_DefaultTags(self, node):  # noqa
        if not node.values:
            self.report("empty-default-tags", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_VariablesImport(self, node):  # noqa
        if not node.name:
            self.report("empty-variables-import", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_ResourceImport(self, node):  # noqa
        if not node.name:
            self.report("empty-resource-import", node=node, col=node.col_offset + 1)

    def visit_LibraryImport(self, node):  # noqa
        if not node.name:
            self.report("empty-library-import", node=node, col=node.col_offset + 1)

    def visit_Setup(self, node):  # noqa
        if not node.name:
            self.report(
                "empty-setup",
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_SuiteSetup(self, node):  # noqa
        if not node.name:
            self.report("empty-suite-setup", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_TestSetup(self, node):  # noqa
        if not node.name:
            self.report("empty-test-setup", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_Teardown(self, node):  # noqa
        if not node.name:
            self.report(
                "empty-teardown",
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_SuiteTeardown(self, node):  # noqa
        if not node.name:
            self.report("empty-suite-teardown", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_TestTeardown(self, node):  # noqa
        if not node.name:
            self.report("empty-test-teardown", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_TestTemplate(self, node):  # noqa
        if not node.value:
            self.report("empty-test-template", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_Template(self, node):  # noqa
        if len(node.data_tokens) < 2:
            self.report(
                "empty-template",
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_Timeout(self, node):  # noqa
        if not node.value:
            self.report(
                "empty-timeout",
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset,
            )

    def visit_TestTimeout(self, node):  # noqa
        if not node.value:
            self.report("empty-test-timeout", node=node, col=node.col_offset + 1, end_col=node.end_col_offset)

    def visit_Arguments(self, node):  # noqa
        if not node.values:
            self.report(
                "empty-arguments",
                block_name=self.parent_node_name,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.end_col_offset + 1,
            )


class TestCaseNumberChecker(VisitorChecker):
    """Checker for counting number of test cases depending on suite type"""

    reports = ("too-many-test-cases",)

    def visit_TestCaseSection(self, node):  # noqa
        max_testcases = (
            self.param("too-many-test-cases", "max_templated_testcases")
            if self.templated_suite
            else self.param("too-many-test-cases", "max_testcases")
        )
        discovered_testcases = sum([isinstance(child, TestCase) for child in node.body])
        if discovered_testcases > max_testcases:
            self.report(
                "too-many-test-cases",
                test_count=discovered_testcases,
                max_allowed_count=max_testcases,
                node=node,
                end_col=node.header.end_col_offset,
                sev_threshold_value=discovered_testcases,
            )
