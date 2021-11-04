"""
Miscellaneous checkers
"""
from pathlib import Path

from robot.api import Token
from robot.parsing.model.blocks import TestCaseSection
from robot.parsing.model.statements import KeywordCall, Return

try:
    from robot.api.parsing import Variable
except ImportError:
    from robot.parsing.model.statements import Variable

from robot.libraries import STDLIBS

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity
from robocop.utils import ROBOT_VERSION, AssignmentTypeDetector, normalize_robot_name, parse_assignment_sign_type, keyword_col

rules = {
    "0901": Rule(
        rule_id="0901",
        name="keyword-after-return",
        msg="[Return] is not defined at the end of keyword. "
        "Note that [Return] does not return from keyword but only set returned variables",
        severity=RuleSeverity.WARNING,
        docs="""
        To improve readability use `[Return]` setting at the end of the keyword. If you want to return immediately from 
        the keyword use `Return From Keyword` keyword instead (`[Return]` does not return until all steps in the 
        keyword are completed).
        
        Bad::
        
            Keyword
                Step
                [Return]    ${variable}
                ${variable}    Other Step
        
        Good::
        
            Keyword
                Step
                ${variable}    Other Step
                [Return]    ${variable}

        """,
    ),
    "0902": Rule(
        rule_id="0902",
        name="keyword-after-return-from",
        msg="Keyword call after 'Return From Keyword' keyword",
        severity=RuleSeverity.ERROR,
    ),
    "0903": Rule(rule_id="0903", name="empty-return", msg="[Return] is empty", severity=RuleSeverity.WARNING),
    "0907": Rule(
        rule_id="0907",
        name="nested-for-loop",
        msg="Nested for loops are not supported. You can use keyword with for loop instead",
        severity=RuleSeverity.ERROR,
        version="<4.0",
        docs="""
        Older versions of Robot Framework did not support nested for loops::
        
            FOR    ${var}    IN RANGE    10
                FOR   ${other_var}   IN    a  b
                    # Nesting supported from Robot Framework 4.0+
                END
            END

        """,
    ),
    "0908": Rule(
        rule_id="0908",
        name="if-can-be-used",
        msg="'{{ run_keyword }}' can be replaced with IF block since Robot Framework 4.0",
        severity=RuleSeverity.INFO,
        version=">=4.0",
    ),
    "0909": Rule(
        RuleParam(
            name="assignment_sign_type",
            default="autodetect",
            converter=parse_assignment_sign_type,
            desc="possible values: 'autodetect' (default), 'none' (''), "
            "'equal_sign' ('=') or space_and_equal_sign (' =')",
        ),
        rule_id="0909",
        name="inconsistent-assignment",
        msg="The assignment sign is not consistent within the file. Expected '{{ expected_sign }}' "
        "but got '{{ actual_sign }}' instead",
        severity=RuleSeverity.WARNING,
    ),
    "0910": Rule(
        RuleParam(
            name="assignment_sign_type",
            default="autodetect",
            converter=parse_assignment_sign_type,
            desc="possible values: 'autodetect' (default), 'none' (''), "
            "'equal_sign' ('=') or space_and_equal_sign (' =')",
        ),
        rule_id="0910",
        name="inconsistent-assignment-in-variables",
        msg="The assignment sign is not consistent inside the variables section. Expected '{{ expected_sign }}' "
        "but got '{{ actual_sign }}' instead",
        severity=RuleSeverity.WARNING,
    ),
    "0911": Rule(
        rule_id="0911",
        name="wrong-import-order",
        msg="BuiltIn library import '{{ builtin_import }}' should be placed before '{{ custom_import }}'",
        severity=RuleSeverity.WARNING,
    ),
    "0912": Rule(
        rule_id="0912",
        name="empty-variable",
        msg="Use built-in variable ${EMPTY} instead of leaving variable without value or using backslash",
        severity=RuleSeverity.INFO,
    ),
    "0913": Rule(
        rule_id="0913",
        name="can-be-resource-file",
        msg="No tests in '{{ file_name }}' file, consider renaming to '{{ file_name_stem }}.resource'",
        severity=RuleSeverity.INFO,
    ),
}


class ReturnChecker(VisitorChecker):
    """Checker for [Return] and Return From Keyword violations."""

    reports = (
        "keyword-after-return",
        "keyword-after-return-from",
        "empty-return",
    )

    def visit_Keyword(self, node):  # noqa
        return_setting_node = None
        keyword_after_return = False
        return_from = False
        for child in node.body:
            if isinstance(child, Return):
                return_setting_node = child
                if not child.values:
                    self.report("empty-return", node=child, col=child.end_col_offset)
            elif isinstance(child, KeywordCall):
                if return_setting_node is not None:
                    keyword_after_return = True
                if return_from:
                    token = child.data_tokens[0]
                    self.report(
                        "keyword-after-return-from",
                        node=token,
                        col=token.col_offset + 1,
                    )
                if normalize_robot_name(child.keyword) == "returnfromkeyword":
                    return_from = True
        if keyword_after_return:
            token = return_setting_node.data_tokens[0]
            self.report("keyword-after-return", node=token, col=token.col_offset + 1)


class NestedForLoopsChecker(VisitorChecker):
    """Checker for not supported nested FOR loops.

    Deprecated in RF 4.0
    """

    reports = ("nested-for-loop",)

    def visit_ForLoop(self, node):  # noqa
        # For RF 4.0 node is "For" but we purposely don't visit it because nested for loop is allowed in 4.0
        for child in node.body:
            if child.type == "FOR":
                self.report("nested-for-loop", node=child)


class IfBlockCanBeUsed(VisitorChecker):
    """Checker for potential IF block usage in Robot Framework 4.0

    Run Keyword variants (Run Keyword If, Run Keyword Unless) can be replaced with IF in RF 4.0
    """

    reports = ("if-can-be-used",)
    run_keyword_variants = {"runkeywordif", "runkeywordunless"}

    def visit_KeywordCall(self, node):  # noqa
        if not node.keyword:
            return
        if normalize_robot_name(node.keyword, remove_prefix='builtin.') in self.run_keyword_variants:
            col = keyword_col(node)
            self.report("if-can-be-used", run_keyword=node.keyword, node=node, col=col)


class ConsistentAssignmentSignChecker(VisitorChecker):
    """Checker for inconsistent assignment signs.

    By default this checker will try to autodetect most common assignment sign (separately for *** Variables *** section
    and (*** Test Cases ***, *** Keywords ***) sections and report any not consistent type of sign in particular file.

    To force one type of sign type you, can configure two rules::

        --configure inconsistent-assignment:assignment_sign_type:{sign_type}
        --configure inconsistent-assignment-in-variables:assignment_sign_type:{sign_type}

    ``${sign_type}` can be one of: ``autodetect`` (default), ``none`` (''), ``equal_sign`` ('='),
    ``space_and_equal_sign`` (' =').

    """

    reports = (
        "inconsistent-assignment",
        "inconsistent-assignment-in-variables",
    )

    def __init__(self):
        self.keyword_expected_sign_type = None
        self.variables_expected_sign_type = None
        super().__init__()

    def visit_File(self, node):  # noqa
        self.keyword_expected_sign_type = self.param("inconsistent-assignment", "assignment_sign_type")
        self.variables_expected_sign_type = self.param("inconsistent-assignment-in-variables", "assignment_sign_type")
        if "autodetect" in [
            self.param("inconsistent-assignment", "assignment_sign_type"),
            self.param("inconsistent-assignment-in-variables", "assignment_sign_type"),
        ]:
            auto_detector = self.auto_detect_assignment_sign(node)
            if self.param("inconsistent-assignment", "assignment_sign_type") == "autodetect":
                self.keyword_expected_sign_type = auto_detector.keyword_most_common
            if self.param("inconsistent-assignment-in-variables", "assignment_sign_type") == "autodetect":
                self.variables_expected_sign_type = auto_detector.variables_most_common
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        if self.keyword_expected_sign_type is None or not node.keyword:
            return
        if node.assign:  # if keyword returns any value
            assign_tokens = node.get_tokens(Token.ASSIGN)
            self.check_assign_type(
                assign_tokens[-1],
                self.keyword_expected_sign_type,
                "inconsistent-assignment",
            )
        return node

    def visit_VariableSection(self, node):  # noqa
        if self.variables_expected_sign_type is None:
            return
        for child in node.body:
            if not isinstance(child, Variable) or getattr(child, "errors", None) or getattr(child, "error", None):
                continue
            var_token = child.get_token(Token.VARIABLE)
            self.check_assign_type(
                var_token,
                self.variables_expected_sign_type,
                "inconsistent-assignment-in-variables",
            )
        return node

    def check_assign_type(self, token, expected, issue_name):
        sign = AssignmentTypeDetector.get_assignment_sign(token.value)
        if sign != expected:
            self.report(
                issue_name,
                expected_sign=expected,
                actual_sign=sign,
                lineno=token.lineno,
                col=token.end_col_offset + 1,
            )

    @staticmethod
    def auto_detect_assignment_sign(node):
        auto_detector = AssignmentTypeDetector()
        auto_detector.visit(node)
        return auto_detector


class SettingsOrderChecker(VisitorChecker):
    """Checker for settings order.

    BuiltIn libraries imports should always be placed before other libraries imports.
    """

    reports = ("wrong-import-order",)

    def __init__(self):
        self.libraries = []
        super().__init__()

    def visit_File(self, node):  # noqa
        self.libraries = []
        self.generic_visit(node)
        first_non_builtin = None
        for library in self.libraries:
            if first_non_builtin is None:
                if library.name not in STDLIBS:
                    first_non_builtin = library.name
            else:
                if library.name in STDLIBS:
                    self.report(
                        "wrong-import-order",
                        builtin_import=library.name,
                        custom_import=first_non_builtin,
                        node=library,
                    )

    def visit_LibraryImport(self, node):  # noqa
        if not node.name:
            return
        self.libraries.append(node)


class EmptyVariableChecker(VisitorChecker):
    """Checker for variables without value."""

    reports = ("empty-variable",)

    def visit_Variable(self, node):  # noqa
        if ROBOT_VERSION.major == 3:  # TODO refactor
            if node.error:
                return
        else:
            if node.errors:
                return
        if not node.value:  # catch variable declaration without any value
            self.report("empty-variable", node=node)
        for token in node.get_tokens(Token.ARGUMENT):
            if not token.value or token.value == "\\":
                self.report(
                    "empty-variable",
                    node=token,
                    lineno=token.lineno,
                    col=token.col_offset,
                )


class ResourceFileChecker(VisitorChecker):
    """Checker for resource files."""

    reports = ("can-be-resource-file",)

    def visit_File(self, node):  # noqa
        source = node.source if node.source else self.source
        if source:
            extension = Path(source).suffix
            file_name = Path(source).stem
            if (
                ".resource" not in extension
                and "__init__" not in file_name
                and node.sections
                and not any([isinstance(section, TestCaseSection) for section in node.sections])
            ):
                self.report("can-be-resource-file", file_name=Path(source).name, file_name_stem=file_name, node=node)
