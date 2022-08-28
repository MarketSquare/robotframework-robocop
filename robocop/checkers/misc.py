"""
Miscellaneous checkers
"""
from pathlib import Path

from robot.api import Token
from robot.parsing.model.blocks import TestCaseSection
from robot.parsing.model.statements import KeywordCall, Return, Teardown

try:
    from robot.api.parsing import Comment, EmptyLine, If, Variable
except ImportError:
    from robot.parsing.model.statements import Comment, EmptyLine, Variable
try:
    from robot.api.parsing import Break, Continue, InlineIfHeader, ReturnStatement
except ImportError:
    ReturnStatement, InlineIfHeader, Break, Continue = None, None, None, None
from robot.libraries import STDLIBS

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity, SeverityThreshold
from robocop.utils import (
    ROBOT_VERSION,
    AssignmentTypeDetector,
    get_errors,
    keyword_col,
    normalize_robot_name,
    parse_assignment_sign_type,
    token_col,
)

rules = {
    "0901": Rule(
        rule_id="0901",
        name="keyword-after-return",
        msg="{{ error_msg }}",
        severity=RuleSeverity.WARNING,
        docs="""
        To improve readability use `[Return]` setting at the end of the keyword. If you want to return immediately from 
        the keyword use `RETURN` statement instead (`[Return]` does not return until all steps in the 
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
    "0903": Rule(
        rule_id="0903",
        name="empty-return",
        msg="[Return] is empty",
        severity=RuleSeverity.WARNING,
        docs="""
        `[Return]` statement is used to define variables returned from keyword. If you don't return anything from 
        keyword,  don't use `[Return]`.
        """,
    ),
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
        version="==4.*",
        docs="""
        Starting from Robot Framework 4.0 `Run Keyword If` and `Run Keyword Unless` can be replaced by IF block.
        """,
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
        docs="""
        Use only one type of assignment sign in a file. 
        
        Example of rule violation::
        
            *** Keywords ***
            Keyword
                ${var} =  Other Keyword
                No Operation
            
            Keyword 2
                No Operation
                ${var}  ${var2}  Some Keyword  # this assignment doesn't use equal sign while the previous one uses ` =`
        
        By default Robocop looks for most popular assignment sign in the file. It is possible to define expected 
        assignment sign by running::
        
            robocop --configure inconsistent-assignment:assignment_sign_type:equal_sign
        
        You can choose between following signs: 'autodetect' (default), 'none' (''), 'equal_sign' ('=') or 
        space_and_equal_sign (' =').
    
        """,
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
        docs="""
        Use one type of assignment sign in Variables section. 
        
        Example of rule violation::
        
            *** Variables ***
            ${var} =    1
            ${var2}=    2
            ${var3} =   3
            ${var4}     a
            ${var5}     b
        
        By default Robocop looks for most popular assignment sign in the file. It is possible to define expected 
        assignment sign by running::
        
            robocop --configure inconsistent-assignment-in-variables:assignment_sign_type:equal_sign
        
        You can choose between following signs: 'autodetect' (default), 'none' (''), 'equal_sign' ('=') or 
        space_and_equal_sign (' =').
        
        """,
    ),
    "0911": Rule(
        rule_id="0911",
        name="wrong-import-order",
        msg="BuiltIn library import '{{ builtin_import }}' should be placed before '{{ custom_import }}'",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::
        
            *** Settings ***
            Library    Collections
            Library    CustomLibrary
            Library    OperatingSystem  # BuiltIn library defined after custom CustomLibrary

        """,
    ),
    "0912": Rule(
        rule_id="0912",
        name="empty-variable",
        msg="Use built-in variable {{ var_type }}{EMPTY} instead of leaving variable without value or using backslash",
        severity=RuleSeverity.INFO,
        docs="""
        Example of rule violation::
        
            *** Variables ***
            ${VAR_NO_VALUE}                   # missing value
            ${VAR_WITH_EMPTY}       ${EMPTY}
            @{MULTILINE_FIRST_EMPTY}
            ...                               # missing value
            ...  value
            ${EMPTY_WITH_BACKSLASH}  \        # used backslash

        """,
    ),
    "0913": Rule(
        rule_id="0913",
        name="can-be-resource-file",
        msg="No tests in '{{ file_name }}' file, consider renaming to '{{ file_name_stem }}.resource'",
        severity=RuleSeverity.INFO,
        docs="""
        If the Robot file contains only keywords or variables it's a good practice to use `.resource` extension.
        """,
    ),
    "0914": Rule(
        rule_id="0914",
        name="if-can-be-merged",
        msg="IF statement can be merged with previous IF (defined in line {{ line }})",
        severity=RuleSeverity.INFO,
        version=">=4.0",
        docs="""
        IF statement follows another IF with identical conditions. It can be possibly merged into one.
        
        Example of rule violation::
        
            IF  ${var} == 4
                Keyword
            END
            # comments are ignored
            IF  ${var}  == 4
                Keyword 2
            END
        
        IF statement is considered identical only if all branches have identical conditions. 
        
        Similar but not identical IF::
        
            IF  ${variable}
                Keyword
            ELSE
                Other Keyword
            END
            IF  ${variable}
                Keyword
            END

        """,
    ),
    "0915": Rule(
        rule_id="0915",
        name="statement-outside-loop",
        msg="{{ name }} {{ statement_type }} used outside a loop",
        severity=RuleSeverity.ERROR,
        version=">=5.0",
        docs="""
        Following keywords and statements should only be used inside loop (``WHILE`` or ``FOR``):
            - ``Exit For Loop``,
            - ``Exit For Loop If``,
            - ``Continue For Loop``,
            - ``Continue For Loop If ``
            - ``CONTINUE``,
            - ``BREAK``
        
        """,
    ),
    "0916": Rule(
        RuleParam(
            name="max_width",
            default=80,
            converter=int,
            desc="maximum width of IF (in characters) below which it will be recommended to use inline IF",
        ),
        SeverityThreshold("max_width", compare_method="less"),
        rule_id="0916",
        name="inline-if-can-be-used",
        msg="IF can be replaced with inline IF",
        severity=RuleSeverity.INFO,
        version=">=5.0",
        docs="""
        Short and simple IFs can be replaced with inline IF.
        
        Following IF::
        
            IF    $condition
                BREAK
            END
        
        can be replaced with::
        
            IF    $condition    BREAK

        """,
    ),
}


class ReturnChecker(VisitorChecker):
    """Checker for [Return] and Return From Keyword violations."""

    reports = (
        "keyword-after-return",
        "empty-return",
    )

    def visit_Keyword(self, node):  # noqa
        return_setting_node = None
        keyword_after_return = False
        return_from = False
        error = ""
        for child in node.body:
            if isinstance(child, Return):
                return_setting_node = child
                error = (
                    "[Return] is not defined at the end of keyword. "
                    "Note that [Return] does not quit from keyword but only set variables to be returned"
                )
                if not child.values:
                    self.report("empty-return", node=child, col=child.end_col_offset)
            elif ReturnStatement and isinstance(child, ReturnStatement):  # type: ignore[arg-type]
                return_setting_node = child
                error = "RETURN is not defined at the end of keyword"
            elif not isinstance(child, (EmptyLine, Comment, Teardown)):
                if return_setting_node is not None:
                    keyword_after_return = True

            if isinstance(child, KeywordCall):
                if return_from:
                    keyword_after_return = True
                    return_setting_node = child
                    error = "Keyword call after 'Return From Keyword'"
                elif normalize_robot_name(child.keyword, remove_prefix="builtin.") == "returnfromkeyword":
                    return_from = True
        if keyword_after_return:
            token = return_setting_node.data_tokens[0]
            self.report("keyword-after-return", error_msg=error, node=token, col=token.col_offset + 1)
        self.generic_visit(node)

    visit_If = visit_For = visit_While = visit_Try = visit_Keyword


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
        if normalize_robot_name(node.keyword, remove_prefix="builtin.") in self.run_keyword_variants:
            col = keyword_col(node)
            self.report("if-can-be-used", run_keyword=node.keyword, node=node, col=col)


class ConsistentAssignmentSignChecker(VisitorChecker):
    """Checker for inconsistent assignment signs.

    By default, this checker will try to autodetect most common assignment sign (separately for *** Variables ***
    section and *** Test Cases ***, *** Keywords *** sections) and report any inconsistent type of sign in particular
    file.

    To force one type of sign type you, can configure two rules::

        --configure inconsistent-assignment:assignment_sign_type:{sign_type}
        --configure inconsistent-assignment-in-variables:assignment_sign_type:{sign_type}

    ``${sign_type}`` can be one of: ``autodetect`` (default), ``none`` (''), ``equal_sign`` ('='),
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
            if not isinstance(child, Variable) or get_errors(child):
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
        if get_errors(node):
            return
        if not node.value:  # catch variable declaration without any value
            self.report("empty-variable", var_type=node.name[0], node=node)
        for token in node.get_tokens(Token.ARGUMENT):
            if not token.value or token.value == "\\":
                self.report(
                    "empty-variable",
                    var_type="$",
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


class IfChecker(VisitorChecker):
    """Checker for IF blocks"""

    reports = (
        "if-can-be-merged",
        "inline-if-can-be-used",
    )

    def visit_TestCase(self, node):  # noqa
        if get_errors(node):
            return
        self.check_adjacent_ifs(node)

    visit_For = visit_If = visit_Keyword = visit_TestCase  # TODO  While, Try Except?

    @staticmethod
    def is_if_inline(node):
        return isinstance(node.header, InlineIfHeader)

    def check_adjacent_ifs(self, node):
        previous_if = None
        for child in node.body:
            if isinstance(child, If):
                if child.header.errors:
                    continue
                self.check_whether_if_should_be_inline(child)
                if previous_if and child.header and self.compare_conditions(child, previous_if):
                    token = child.header.get_token(child.header.type)
                    self.report("if-can-be-merged", line=previous_if.lineno, node=token, col=token.col_offset + 1)
                previous_if = child
            elif not isinstance(child, (Comment, EmptyLine)):
                previous_if = None
        self.generic_visit(node)

    def compare_conditions(self, if_node, other_if_node):
        if not self.compare_assign_tokens(if_node, other_if_node):
            return False
        while if_node is not None and other_if_node is not None:
            if if_node.condition != other_if_node.condition:
                return False
            if_node = if_node.orelse
            other_if_node = other_if_node.orelse
        return if_node is None and other_if_node is None

    @staticmethod
    def normalize_var_name(name):
        return name.lower().replace("_", "").replace(" ", "").replace("=", "")

    def compare_assign_tokens(self, if_node, other_if_node):
        assign_1 = getattr(if_node, "assign", None)
        assign_2 = getattr(other_if_node, "assign", None)
        if assign_1 is None or assign_2 is None:
            return all(assign is None for assign in (assign_1, assign_2))
        if len(assign_1) != len(assign_2):
            return False
        for var1, var2 in zip(assign_1, assign_2):
            if self.normalize_var_name(var1) != self.normalize_var_name(var2):
                return False
        return True

    @staticmethod
    def tokens_length(tokens):
        return sum(len(token.value) for token in tokens)

    def check_whether_if_should_be_inline(self, node):
        if ROBOT_VERSION.major < 5:
            return
        if self.is_if_inline(node):
            return
        if (
            len(node.body) != 1
            or node.orelse
            or not isinstance(node.body[0], (KeywordCall, ReturnStatement, Break, Continue))  # type: ignore[arg-type]
        ):
            return
        min_possible = self.tokens_length(node.header.tokens) + self.tokens_length(node.body[0].tokens[1:]) + 2
        if min_possible > self.param("inline-if-can-be-used", "max_width"):
            return
        token = node.header.get_token(node.header.type)
        self.report("inline-if-can-be-used", node=node, col=token.col_offset + 1, sev_threshold_value=min_possible)


class LoopStatementsChecker(VisitorChecker):
    """Checker for loop keywords and statements such as CONTINUE or Exit For Loop"""

    reports = ("statement-outside-loop",)
    for_keyword = {"continueforloop", "continueforloopif", "exitforloop", "exitforloopif"}

    def __init__(self):
        self.loops = 0
        super().__init__()

    def visit_File(self, node):  # noqa
        self.loops = 0
        self.generic_visit(node)

    def visit_For(self, node):  # noqa
        self.loops += 1
        self.generic_visit(node)
        self.loops -= 1

    visit_While = visit_For

    def visit_KeywordCall(self, node):  # noqa
        if node.errors or self.loops:
            return
        if normalize_robot_name(node.keyword, remove_prefix="builtin.") in self.for_keyword:
            self.report(
                "statement-outside-loop",
                name=f"'{node.keyword}'",
                statement_type="keyword",
                node=node,
                col=keyword_col(node),
            )

    def visit_Continue(self, node):  # noqa
        self.check_statement_in_loop(node, "CONTINUE")  # type: ignore[arg-type]

    def visit_Break(self, node):  # noqa
        self.check_statement_in_loop(node, "BREAK")  # type: ignore[arg-type]

    def check_statement_in_loop(self, node, token_type):
        if self.loops or node.errors and f"{token_type} can only be used inside a loop." not in node.errors:
            return
        self.report(
            "statement-outside-loop",
            name=token_type,
            statement_type="statement",
            node=node,
            col=token_col(node, token_type),
        )
