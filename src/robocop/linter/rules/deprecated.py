from robocop.linter import sonar_qube
from robocop.linter.diagnostics import Diagnostic
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, Rule, RuleSeverity


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


class DeprecatedStatementRule(Rule):  # TODO: Split rule
    """
    Statement is deprecated.

    Detects any piece of code that is marked as deprecated but still works in RF.

    For example, ``Run Keyword`` and ``Continue For Loop`` keywords or ``[Return]`` setting.

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

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        return Fix(
            edits=[TextEdit.replace_at_range(self.rule_id, self.name, diag.range, "Test Tags")],
            message="Replace Force Tags with Test Tags",
            applicability=FixApplicability.SAFE,
        )


class DeprecatedRunKeywordIfRule(Rule):
    """
    Run Keyword If and Run Keyword Unless are deprecated.

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
