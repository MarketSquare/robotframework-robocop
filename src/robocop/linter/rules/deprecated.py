import string

from robot.api import Token

try:
    from robot.api.parsing import ReturnStatement
except ImportError:
    ReturnStatement = None

from robocop.formatter.utils import misc as format_utils
from robocop.linter import sonar_qube
from robocop.linter.diagnostics import Diagnostic
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, Rule, RuleSeverity
from robocop.linter.utils import misc as utils
from robocop.source_file import StatementLinesCollector
from robocop.version_handling import ROBOT_VERSION


class IfCanBeUsedRule(Rule):
    """
    ``Run Keyword If`` or ``Run Keyword Unless`` used instead of IF.

    Starting from Robot Framework 4.0 IF block can be used instead of those keywords.

    Incorrect code example:

        *** Test Cases ***
        Test case
            Run Keyword If    ${condition}    Keyword Call    ELSE    Log    Condition did not match.
            Run Keyword Unless    ${something_happened}    Assert Results

    Correct code:

        *** Test Cases ***
        Test case
            IF    ${condition}
                Keyword Call
            ELSE
                Log    Condition did not match.
            END
            IF    not ${something_happened}
                Assert Results
            END

    """

    name = "if-can-be-used"
    rule_id = "DEPR01"
    message = "'{run_keyword}' can be replaced with IF block since Robot Framework 4.0"
    severity = RuleSeverity.INFO
    version = "==4.*"
    added_in_version = "1.4.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0908",)


class DeprecatedStatementRule(Rule):
    """
    Statement is deprecated.

    Detects any piece of code that is marked as deprecated but still works in RF.

    For example, ``Run Keyword`` and ``Continue For Loop`` keywords or ``[Return]`` setting.

    Changes in 8.0.0: Rule is now split into separate deprecated-* rules and the original rule is deprecated.

    """

    name = "deprecated-statement"
    rule_id = "DEPR02"
    message = "'{statement_name}' is deprecated since Robot Framework version {version}, use '{alternative}' instead"
    severity = RuleSeverity.WARNING
    added_in_version = "2.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0319",)
    deprecated = True


class DeprecatedWithNameRule(Rule):
    """
    Deprecated 'WITH NAME' alias marker used instead of 'AS'.

    ``WITH NAME`` marker used when giving an alias to an imported library is going to be renamed to ``AS``.
    The motivation is to be consistent with Python that uses ``as`` for a similar purpose.

    Incorrect code example:

        *** Settings ***
        Library    Collections    WITH NAME    AliasedName

    Correct code:

        *** Settings ***
        Library    Collections    AS    AliasedName

    """

    name = "deprecated-with-name"
    rule_id = "DEPR03"
    message = "Deprecated 'WITH NAME' alias marker used instead of 'AS'"
    severity = RuleSeverity.WARNING
    version = ">=6.0"
    added_in_version = "2.5.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0321",)

    def check(self, node) -> None:
        if not self.enabled:
            return
        with_name_token = node.get_token(Token.WITH_NAME)
        if not with_name_token or with_name_token.value == "AS":
            return
        self.report(
            node=with_name_token,
            col=with_name_token.col_offset + 1,
            end_col=with_name_token.end_col_offset + 1,
        )


class DeprecatedSingularHeaderRule(Rule):
    """
    Deprecated singular header used instead of plural form.

    Robot Framework 6.0 starts a deprecation period for singular headers forms. The rationale behind this change
    is available at https://github.com/robotframework/robotframework/issues/4431

    Incorrect code example:

        *** Setting ***
        *** Keyword ***

    Correct code:

        *** Settings ***
        *** Keywords ***

    """

    name = "deprecated-singular-header"
    rule_id = "DEPR04"
    message = "'{singular_header}' deprecated singular header used instead of '{plural_header}'"
    severity = RuleSeverity.WARNING
    version = ">=6.0"
    added_in_version = "2.6.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0322",)

    english_headers_singular = {
        "Comment",
        "Setting",
        "Variable",
        "Test Case",
        "Keyword",
    }
    english_headers_all = {
        "Comment",
        "Setting",
        "Variable",
        "Test Case",
        "Keyword",
        "Comments",
        "Settings",
        "Variables",
        "Test Cases",
        "Keywords",
    }

    def check(self, node) -> None:
        if not node.name:
            return
        normalized_name = string.capwords(node.name)
        # handle translated headers
        if normalized_name not in self.english_headers_all:
            return
        if normalized_name not in self.english_headers_singular:
            return
        header_node = node.data_tokens[0]
        self.report(
            singular_header=f"*** {node.name} ***",
            plural_header=f"*** {node.name}s ***",
            node=header_node,
            col=header_node.col_offset + 1,
            end_col=header_node.end_col_offset + 1,
        )


class ReplaceSetVariableWithVarRule(Rule):
    """
    Set X Variable used instead of VAR.

    Starting from Robot Framework 7.0, it is possible to create variables inside tests and user keywords using the
    VAR syntax. The VAR syntax is recommended over previously existing keywords.

    Incorrect code example:

        *** Keywords ***
        Set Variables To Different Scopes
            Set Local Variable    ${local}    value
            Set Test Variable    ${TEST_VAR}    value
            Set Task Variable    ${TASK_VAR}    value
            Set Suite Variable    ${SUITE_VAR}    value
            Set Global Variable    ${GLOBAL_VAR}    value

    Correct code:

        *** Keywords ***
        Set Variables To Different Scopes
            VAR    ${local}    value
            VAR    ${TEST_VAR}    value    scope=TEST
            VAR    ${TASK_VAR}    value    scope=TASK
            VAR    ${SUITE_VAR}    value    scope=SUITE
            VAR    ${GLOBAL_VAR}    value    scope=GLOBAL

    """

    name = "replace-set-variable-with-var"
    rule_id = "DEPR05"
    message = "{set_variable_keyword} used instead of VAR"
    severity = RuleSeverity.INFO
    version = ">=7.0"
    added_in_version = "5.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0327",)

    set_variable_keywords = {
        "setvariable",
        "setlocalvariable",
        "settestvariable",
        "settaskvariable",
        "setsuitevariable",
        "setglobalvariable",
    }

    def check(self, node, keyword_name: str, normalized_keyword_name: str) -> bool:
        """Check and return True if issue not found, otherwise return False."""
        if normalized_keyword_name in self.set_variable_keywords:
            col = utils.token_col(node, Token.NAME, Token.KEYWORD)
            self.report(
                set_variable_keyword=keyword_name,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )
            return False
        return True


class ReplaceCreateWithVarRule(Rule):
    """
    Create List/Dictionary used instead of VAR.

    Starting from Robot Framework 7.0, it is possible to create variables inside tests and user keywords using the
    VAR syntax. The VAR syntax is recommended over previously existing keywords.

    Incorrect code example:

        *** Keywords ***
        Create Variables
            @{list}    Create List    a  b
            &{dict}    Create Dictionary    key=value

    Correct code:

        *** Keywords ***
        Create Variables
            VAR    @{list}    a  b
            VAR    &{dict}    key=value

    """

    name = "replace-create-with-var"
    rule_id = "DEPR06"
    message = "{create_keyword} used instead of VAR"
    severity = RuleSeverity.INFO
    version = ">=7.0"
    added_in_version = "5.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0328",)

    create_keywords = {"createdictionary", "createlist"}

    def check(self, node, keyword_name: str, normalized_keyword_name: str) -> bool:
        """Check and return True if issue not found, otherwise return False."""
        if normalized_keyword_name in self.create_keywords:
            col = utils.token_col(node, Token.NAME, Token.KEYWORD)
            self.report(
                create_keyword=keyword_name,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )
            return False
        return True


class DeprecatedForceTagsRule(FixableRule):
    """
    Force Tags setting is deprecated.

    The following code is deprecated and will be removed in the future:

        *** Settings ***
        Force Tags      tag

    Use ``Test Tags`` instead:

        *** Settings ***
        Test Tags      tag

    """

    name = "deprecated-force-tags"
    rule_id = "DEPR07"
    message = "'Force Tags' is deprecated, use 'Test Tags' instead"
    severity = RuleSeverity.WARNING
    version = ">=6.0"
    added_in_version = "8.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    fix_availability = FixAvailability.ALWAYS

    def check(self, node) -> None:
        if ROBOT_VERSION.major < 6:
            return
        setting_name = node.data_tokens[0].value.lower()
        if setting_name == "force tags":
            self.report(
                node=node, col=utils.token_col(node, Token.FORCE_TAGS), end_col=node.col_offset + len(setting_name) + 1
            )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        return Fix(
            edits=[TextEdit.replace_at_range(self.rule_id, self.name, diag.range, "Test Tags")],
            message="Replace Force Tags with Test Tags",
            applicability=FixApplicability.SAFE,
        )


class DeprecatedRunKeywordIfRule(Rule):
    """
    ``Run Keyword If`` and ``Run Keyword Unless`` keywords are deprecated.

    The following code is deprecated and will be removed in the future:

        *** Test Cases ***
        Test with conditions
            Run Keyword If    ${GLOBAL_FLAG}    Conditional Keyword
            Run Keyword Unless    ${local_value} == "true"    Conditional Keyword
            Run Keyword If  ${condition}
                ...  Keyword  ${arg}
                ...  ELSE IF  ${condition2}  Keyword2
                ...  ELSE  Keyword3

    Use ``IF`` instead:

        *** Test Cases ***
        Test with conditions
            IF    ${GLOBAL_FLAG}    Conditional Keyword
            IF    not (${local_value} == "true")    Conditional Keyword
            Keyword
                IF    ${condition}
                    Keyword    ${arg}
                ELSE IF    ${condition2}
                    Keyword2
                ELSE
                    Keyword3
                END

    """

    name = "deprecated-run-keyword-if"
    rule_id = "DEPR07"
    message = "'{statement_name}' is deprecated, use 'IF' instead"
    severity = RuleSeverity.WARNING
    version = ">=4.0"
    added_in_version = "8.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    run_keyword_if_names = {"runkeywordif", "runkeywordunless"}

    def check(self, node, keyword_name: str, normalized_keyword_name: str) -> bool:
        """Check and return True if issue not found, otherwise return False."""
        if normalized_keyword_name in self.run_keyword_if_names:
            col = utils.token_col(node, Token.NAME, Token.KEYWORD)
            self.report(
                statement_name=keyword_name,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )
            return False
        return True


class DeprecatedLoopKeywordRule(Rule):
    """
    Loop keywords are deprecated.

    The following loop keywords are deprecated:

    - ``Continue For Loop``
    - ``Continue For Loop If``
    - ``Exit For Loop``
    - ``Exit For Loop If``

    Use ``CONTINUE`` and ``BREAK`` instead.

    Incorrect code example:

        *** Test Cases ***
        Test with loops
            WHILE    ${condition}
                Continue For Loop If    ${second_condition}
                Continue For Loop
            END
            FOR    ${var}    IN RANGE    10
                Exit For Loop If    ${var} = 5
                Exit For Loop
            END

    Correct code:

        *** Test Cases ***
        Test with loops
            WHILE    ${condition}
                First Keyword
                IF    ${second_condition}    CONTINUE
                CONTINUE
            END
            FOR    ${var}    IN RANGE    10
                IF    ${var} = 0    BREAK
                BREAK
            END

    """

    name = "deprecated-loop-keyword"
    rule_id = "DEPR08"
    message = "'{statement_name}' is deprecated, use '{alternative}' instead"
    severity = RuleSeverity.WARNING
    version = ">=5.0"
    added_in_version = "8.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    deprecated_names = {
        "exitforloop": "BREAK",
        "exitforloopif": "IF and BREAK",
        "continueforloop": "CONTINUE",
        "continueforloopif": "IF and CONTINUE",
    }

    def check(self, node, keyword_name: str, normalized_keyword_name: str) -> bool:
        """Check and return True if issue not found, otherwise return False."""
        if normalized_keyword_name in self.deprecated_names:
            col = utils.token_col(node, Token.NAME, Token.KEYWORD)
            alternative = self.deprecated_names[normalized_keyword_name]
            self.report(
                statement_name=keyword_name,
                alternative=alternative,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )
            return False
        return True


class DeprecatedReturnKeyword(FixableRule):
    """
    ``Return From Keyword`` and ``Return From Keyword If`` keywords are deprecated.

    Use ``RETURN`` or ``IF  <condition>  RETURN`` instead.
    """

    name = "deprecated-return-keyword"
    rule_id = "DEPR09"
    message = "'{statement_name}' is deprecated, use '{alternative}' instead"
    severity = RuleSeverity.WARNING
    version = ">=5.0"
    added_in_version = "8.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = {"returnfromkeyword": "RETURN", "returnfromkeywordif": "IF and RETURN"}
    fix_availability = FixAvailability.ALWAYS

    def check(self, node, keyword_name: str, normalized_keyword_name: str) -> bool:
        """Check and return True if issue not found, otherwise return False."""
        if normalized_keyword_name in self.deprecated_names:
            col = utils.token_col(node, Token.NAME, Token.KEYWORD)
            alternative = self.deprecated_names[normalized_keyword_name]
            self.report(
                statement_name=keyword_name,
                alternative=alternative,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )
            return False
        return True

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        """Fix Return From Keyword. Return From Keyword If is handled inside a rule check."""
        if "if" in diag.reported_arguments["statement_name"].lower():
            if diag.node is None or not ReturnStatement:
                return None
            replacement_node = format_utils.wrap_in_if_and_replace_statement(diag.node, ReturnStatement, "    ")
            if replacement_node is diag.node:  # no changes
                return None
            replacement_text = StatementLinesCollector(replacement_node).text
            return Fix(
                edits=[
                    TextEdit.replace_lines(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        start_line=diag.node.lineno,
                        end_line=diag.node.end_lineno,
                        replacement=replacement_text,
                    )
                ],
                message="Replace Return From Keyword If keyword with IF and RETURN",
                applicability=FixApplicability.SAFE,
            )
        return Fix(
            edits=[TextEdit.replace_at_range(self.rule_id, self.name, diag.range, "RETURN")],
            message="Replace Return From Keyword keyword with RETURN",
            applicability=FixApplicability.SAFE,
        )


class DeprecatedReturnSetting(FixableRule):
    """
    ``[Return]`` settings is deprecated.

    Use ``RETURN`` instead.

    Incorrect code example:

        *** Keywords ***
        Return One Value
            [Arguments]    ${arg}
            ${value}    Convert To Upper Case    ${arg}
            [Return]    ${value}

    Correct code:

        *** Keywords ***
        Return One Value
            [Arguments]    ${arg}
            ${value}    Convert To Upper Case    ${arg}
            RETURN    ${value}

    """

    name = "deprecated-return-setting"
    rule_id = "DEPR10"
    message = "'[Return]' is deprecated, use 'RETURN' instead"
    severity = RuleSeverity.WARNING
    version = ">=5.0"
    added_in_version = "8.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    fix_availability = FixAvailability.ALWAYS

    def check(self, node) -> None:
        """
        Check and report the deprecated [Return] setting and implement a fix.

        Since [Return] may be defined in any place of the keyword,
        we can't simply replace it with RETURN.
        The following code takes lines between [Return] and the last statement in keyword
        as lines under the fix (to avoid conflicts).
        Removes [Return] and add RETURN after the last statement.
        The formatting is preserved.

        """
        return_statement = StatementLinesCollector(node).text
        last_statement = self.checker.context.last_data_statement_in_keyword
        if last_statement and last_statement.type in ("RETURN STATEMENT", "RETURN SETTING"):
            # ignore duplicate [Return] or keywords with RETURN, it should be handled by a duplicate-return issue
            return
        replacement = self.checker.source_file.source_lines[node.end_lineno : last_statement.end_lineno]
        replacement = "".join(replacement) + return_statement.replace(node.data_tokens[0].value, "RETURN", 1)
        fix = Fix(
            edits=[
                TextEdit.replace_lines(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    start_line=node.lineno,
                    end_line=last_statement.end_lineno,
                    replacement=replacement,
                )
            ],
            message="Replace [Return] with RETURN",
            applicability=FixApplicability.SAFE,
        )
        self.report(
            node=node,
            col=utils.token_col(node, Token.RETURN),
            end_col=node.end_col_offset,
            fix=fix,
        )
