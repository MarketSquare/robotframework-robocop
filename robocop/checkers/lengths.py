"""
Lengths checkers
"""
import re

from robot.parsing.model.blocks import CommentSection, TestCase
from robot.parsing.model.statements import Arguments, Comment, EmptyLine, KeywordCall

from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity
from robocop.utils import last_non_empty_line, normalize_robot_name, pattern_type

rules = {
    "0501": Rule(
        RuleParam(name="max_len", default=40, converter=int, desc="number of lines allowed in a keyword"),
        rule_id="0501",
        name="too-long-keyword",
        msg="Keyword is too long (%d/%d)",
        severity=RuleSeverity.WARNING,
        docs_args=(
            "keyword length",
            "allowed length",
        ),
    ),
    "0502": Rule(
        RuleParam(name="min_calls", default=1, converter=int, desc="number of keyword calls required in a keyword"),
        rule_id="0502",
        name="too-few-calls-in-keyword",
        msg="Keyword has too few keywords inside (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
    "0503": Rule(
        RuleParam(name="max_calls", default=10, converter=int, desc="number of keyword calls allowed in a keyword"),
        rule_id="0503",
        name="too-many-calls-in-keyword",
        msg="Keyword has too many keywords inside (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
    "0504": Rule(
        RuleParam(name="max_len", default=20, converter=int, desc="number of lines allowed in a test case"),
        rule_id="0504",
        name="too-long-test-case",
        msg="Test case is too long (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
    "0505": Rule(
        RuleParam(name="max_calls", default=10, converter=int, desc="number of keyword calls allowed in a test case"),
        rule_id="0505",
        name="too-many-calls-in-test-case",
        msg="Test case has too many keywords inside (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
    "0506": Rule(
        RuleParam(name="max_lines", default=400, converter=int, desc="number of lines allowed in a file"),
        rule_id="0506",
        name="file-too-long",
        msg="File has too many lines (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
    "0507": Rule(
        RuleParam(name="max_args", default=5, converter=int, desc="number of lines allowed in a file"),
        rule_id="0507",
        name="too-many-arguments",
        msg="Keyword has too many arguments (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
    "0508": Rule(
        RuleParam(name="line_length", default=120, converter=int, desc="number of lines allowed in a file"),
        RuleParam(
            name="ignore_pattern",
            default=re.compile(r"https?://\S+"),
            converter=pattern_type,
            desc="ignore lines that contain configured pattern",
        ),
        rule_id="0508",
        name="line-too-long",
        msg="Line is too long (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
    "0509": Rule(rule_id="0509", name="empty-section", msg="Section is empty", severity=RuleSeverity.WARNING),
    "0510": Rule(
        RuleParam(
            name="max_returns", default=4, converter=int, desc="allowed number of returned values from a keyword"
        ),
        rule_id="0510",
        name="number-of-returned-values",
        msg="Too many return values (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
    "0511": Rule(
        rule_id="0511",
        name="empty-metadata",
        msg="Metadata settings does not have any value set",
        severity=RuleSeverity.WARNING,
    ),
    "0512": Rule(
        rule_id="0512", name="empty-documentation", msg="Documentation is empty", severity=RuleSeverity.WARNING
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
        rule_id="0518", name="empty-setup", msg="Setup does not have any keywords", severity=RuleSeverity.ERROR
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
        rule_id="0521", name="empty-teardown", msg="Teardown does not have any keywords", severity=RuleSeverity.ERROR
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
    "0524": Rule(rule_id="0524", name="empty-timeout", msg="Timeout is empty", severity=RuleSeverity.WARNING),
    "0525": Rule(rule_id="0525", name="empty-test-timeout", msg="Test Timeout is empty", severity=RuleSeverity.WARNING),
    "0526": Rule(rule_id="0526", name="empty-arguments", msg="Arguments are empty", severity=RuleSeverity.ERROR),
    "0527": Rule(
        RuleParam(name="max_testcases", default=50, converter=int, desc="number of test cases allowed in a suite"),
        RuleParam(
            name="max_templated_testcases",
            default=100,
            converter=int,
            desc="number of test cases allowed in a templated suite",
        ),
        rule_id="0527",
        name="too-many-test-cases",
        msg="Too many test cases (%d/%d)",
        severity=RuleSeverity.WARNING,
    ),
}


class LengthChecker(VisitorChecker):
    """Checker for max and min length of keyword or test case. It analyses number of lines and also number of
    keyword calls (as you can have just few keywords but very long ones or vice versa).
    """

    reports = (
        "too-long-keyword",
        "too-few-calls-in-keyword",
        "too-many-calls-in-keyword",
        "too-long-test-case",
        "too-many-calls-in-test-case",
        "file-too-long",
        "too-many-arguments",
    )

    def visit_File(self, node):
        if node.end_lineno > self.param("file-too-long", "max_lines"):
            self.report(
                "file-too-long",
                node.end_lineno,
                self.param("file-too-long", "max_lines"),
                node=node,
                lineno=node.end_lineno,
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
                        args_number,
                        self.param("too-many-arguments", "max_args"),
                        node=node,
                    )
                break
        length = LengthChecker.check_node_length(node)
        if length > self.param("too-long-keyword", "max_len"):
            self.report(
                "too-long-keyword",
                length,
                self.param("too-long-keyword", "max_len"),
                node=node,
                lineno=node.end_lineno,
                ext_disablers=(node.lineno, last_non_empty_line(node)),
            )
            return
        key_calls = LengthChecker.count_keyword_calls(node)
        if key_calls < self.param("too-few-calls-in-keyword", "min_calls"):
            self.report(
                "too-few-calls-in-keyword", key_calls, self.param("too-few-calls-in-keyword", "min_calls"), node=node
            )
            return
        if key_calls > self.param("too-many-calls-in-keyword", "max_calls"):
            self.report(
                "too-many-calls-in-keyword",
                key_calls,
                self.param("too-many-calls-in-keyword", "max_calls"),
                node=node,
            )
            return

    def visit_TestCase(self, node):  # noqa
        length = LengthChecker.check_node_length(node)
        if length > self.param("too-long-test-case", "max_len"):
            self.report("too-long-test-case", length, self.param("too-long-test-case", "max_len"), node=node)
        key_calls = LengthChecker.count_keyword_calls(node)
        if key_calls > self.param("too-many-calls-in-test-case", "max_calls"):
            self.report(
                "too-many-calls-in-test-case",
                key_calls,
                self.param("too-many-calls-in-test-case", "max_calls"),
                node=node,
            )
            return

    @staticmethod
    def check_node_length(node):
        return node.end_lineno - node.lineno

    @staticmethod
    def count_keyword_calls(node):
        if isinstance(node, KeywordCall):
            return 1
        if not hasattr(node, "body"):
            return 0
        return sum(LengthChecker.count_keyword_calls(child) for child in node.body)


class LineLengthChecker(RawFileChecker):
    """Checker for maximum length of a line."""

    reports = ("line-too-long",)
    # replace # noqa or # robocop, # robocop: enable, # robocop: disable=optional,rule,names
    disabler_pattern = re.compile(r"(# )+(noqa|robocop: ?(?P<disabler>disable|enable)=?(?P<rules>[\w\-,]*))")

    def check_line(self, line, lineno):
        if self.param("line-too-long", "ignore_pattern") and self.param("line-too-long", "ignore_pattern").search(line):
            return
        line = self.disabler_pattern.sub("", line)
        line = line.rstrip().expandtabs(4)
        if len(line) > self.param("line-too-long", "line_length"):
            self.report("line-too-long", len(line), self.param("line-too-long", "line_length"), lineno=lineno)


class EmptySectionChecker(VisitorChecker):
    """Checker for detecting empty sections."""

    reports = ("empty-section",)

    def check_if_empty(self, node):
        anything_but = EmptyLine if isinstance(node, CommentSection) else (Comment, EmptyLine)
        if all(isinstance(child, anything_but) for child in node.body):
            self.report("empty-section", node=node)

    def visit_SettingSection(self, node):  # noqa
        self.check_if_empty(node)

    def visit_VariableSection(self, node):  # noqa
        self.check_if_empty(node)

    def visit_TestCaseSection(self, node):  # noqa
        self.check_if_empty(node)

    def visit_KeywordSection(self, node):  # noqa
        self.check_if_empty(node)

    def visit_CommentSection(self, node):  # noqa
        self.check_if_empty(node)


class NumberOfReturnedArgsChecker(VisitorChecker):
    """Checker for number of returned values from a keyword."""

    reports = ("number-of-returned-values",)

    def visit_Keyword(self, node):  # noqa
        self.generic_visit(node)

    def visit_ForLoop(self, node):  # noqa
        self.generic_visit(node)

    def visit_For(self, node):  # noqa
        self.generic_visit(node)

    def visit_Return(self, node):  # noqa
        self.check_node_returns(len(node.values), node)

    def visit_KeywordCall(self, node):  # noqa
        if not node.keyword:
            return

        normalized_name = normalize_robot_name(node.keyword)
        if normalized_name == "returnfromkeyword":
            self.check_node_returns(len(node.args), node)
        elif normalized_name == "returnfromkeywordif":
            self.check_node_returns(len(node.args) - 1, node)

    def check_node_returns(self, return_count, node):
        if return_count > self.param("number-of-returned-values", "max_returns"):
            self.report(
                "number-of-returned-values",
                return_count,
                self.param("number-of-returned-values", "max_returns"),
                node=node,
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
        "empty-arguments",
    )

    def visit_Metadata(self, node):  # noqa
        if node.name is None:
            self.report("empty-metadata", node=node, col=node.end_col_offset)

    def visit_Documentation(self, node):  # noqa
        if not node.value:
            self.report("empty-documentation", node=node, col=node.end_col_offset)

    def visit_ForceTags(self, node):  # noqa
        if not node.values:
            self.report("empty-force-tags", node=node, col=node.end_col_offset)

    def visit_DefaultTags(self, node):  # noqa
        if not node.values:
            self.report("empty-default-tags", node=node, col=node.end_col_offset)

    def visit_VariablesImport(self, node):  # noqa
        if not node.name:
            self.report("empty-variables-import", node=node, col=node.end_col_offset)

    def visit_ResourceImport(self, node):  # noqa
        if not node.name:
            self.report("empty-resource-import", node=node, col=node.end_col_offset)

    def visit_LibraryImport(self, node):  # noqa
        if not node.name:
            self.report("empty-library-import", node=node, col=node.end_col_offset)

    def visit_Setup(self, node):  # noqa
        if not node.name:
            self.report("empty-setup", node=node, col=node.end_col_offset + 1)

    def visit_SuiteSetup(self, node):  # noqa
        if not node.name:
            self.report("empty-suite-setup", node=node, col=node.end_col_offset)

    def visit_TestSetup(self, node):  # noqa
        if not node.name:
            self.report("empty-test-setup", node=node, col=node.end_col_offset)

    def visit_Teardown(self, node):  # noqa
        if not node.name:
            self.report("empty-teardown", node=node, col=node.end_col_offset + 1)

    def visit_SuiteTeardown(self, node):  # noqa
        if not node.name:
            self.report("empty-suite-teardown", node=node, col=node.end_col_offset)

    def visit_TestTeardown(self, node):  # noqa
        if not node.name:
            self.report("empty-test-teardown", node=node, col=node.end_col_offset)

    def visit_Timeout(self, node):  # noqa
        if not node.value:
            self.report("empty-timeout", node=node, col=node.end_col_offset + 1)

    def visit_TestTimeout(self, node):  # noqa
        if not node.value:
            self.report("empty-test-timeout", node=node, col=node.end_col_offset)

    def visit_Arguments(self, node):  # noqa
        if not node.values:
            self.report("empty-arguments", node=node, col=node.end_col_offset + 1)


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
            self.report("too-many-test-cases", discovered_testcases, max_testcases, node=node)
