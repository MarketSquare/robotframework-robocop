"""Naming checkers"""

from __future__ import annotations

import re
import string
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import VariableError
from robot.parsing.model.blocks import TestCaseSection
from robot.parsing.model.statements import Arguments
from robot.variables.search import search_variable

from robocop.checkers import VisitorChecker
from robocop.rules import DefaultRule, RuleParam, RuleSeverity
from robocop.utils import (
    ROBOT_VERSION,
    find_robot_vars,
    keyword_col,
    normalize_robot_name,
    normalize_robot_var_name,
    pattern_type,
    remove_robot_vars,
    token_col,
)
from robocop.utils.misc import _is_var_scope_local, remove_nested_variables
from robocop.utils.run_keywords import iterate_keyword_names
from robocop.utils.variable_matcher import VariableMatches

if TYPE_CHECKING:
    from collections.abc import Iterable

RULE_CATEGORY_ID = "03"

rules = {
    "0301": DefaultRule(
        RuleParam(
            name="pattern",
            default=re.compile(r"[\.\?]"),
            converter=pattern_type,
            show_type="regex",
            desc="pattern defining characters (not) allowed in a name",
        ),
        rule_id="0301",
        name="not-allowed-char-in-name",
        msg="Not allowed character '{{ character }}' found in {{ block_name }} name",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
        docs="""
        Reports not allowed characters found in Test Case or Keyword names. By default it's a dot (``.``). You can
        configure what patterns are reported by calling::

            robocop --configure not-allowed-char-in-name:pattern:regex_pattern

        ``regex_pattern`` should define regex pattern not allowed in names. For example ``[@\\[]`` pattern
        would report any occurrence of ``@[`` characters.
        """,
    ),
    "0302": DefaultRule(
        RuleParam(
            name="convention",
            default="each_word_capitalized",
            converter=str,
            desc="possible values: 'each_word_capitalized' (default) or 'first_word_capitalized'",
        ),
        RuleParam(
            name="pattern",
            default=re.compile(r""),
            converter=pattern_type,
            show_type="regex",
            desc="pattern for accepted words in keyword",
        ),
        rule_id="0302",
        name="wrong-case-in-keyword-name",
        msg="Keyword name '{{ keyword_name }}' does not follow case convention",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
        docs="""
        Keyword names need to follow a specific case convention.
        The convention can be set using ``convention`` parameter and accepts
        one of the 2 values: ``each_word_capitalized`` or ``first_word_capitalized``.

        By default, it's configured to ``each_word_capitalized``, which requires each keyword to follow such convention::

            *** Keywords ***
            Fill Out The Form
                Provide Shipping Address
                Provide Payment Method
                Click 'Next' Button
                [Teardown]  Log Form Data

        You can also set it to ``first_word_capitalized`` which requires first word to have first letter capital::

            *** Keywords ***
            Fill out the form
                Provide shipping address
                Provide payment method
                Click 'Next' button
                [Teardown]  Log form data

        The rule also accepts another parameter ``pattern`` which can be used to configure words
        that are accepted in the keyword name, even though they violate the case convention.

        ``pattern`` parameter accepts a regex pattern. For example, configuring it to ``robocop\\.readthedocs\\.io``
        would make such keyword legal::

            Go To robocop.readthedocs.io Page
        """,
    ),
    "0303": DefaultRule(
        rule_id="0303",
        name="keyword-name-is-reserved-word",
        msg="'{{ keyword_name }}' is a reserved keyword{{ error_msg }}",
        severity=RuleSeverity.ERROR,
        added_in_version="1.0.0",
        docs="""
        Do not use reserved names for keyword names. Following names are reserved:

          - IF
          - ELSE IF
          - ELSE
          - FOR
          - END
          - WHILE
          - CONTINUE
          - RETURN
          - TRY
          - EXCEPT
          - FINALLY
        """,
    ),
    "0305": DefaultRule(
        rule_id="0305",
        name="underscore-in-keyword-name",
        msg="Underscores in keyword name '{{ keyword_name }}' can be replaced with spaces",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
        docs="""
        Bad |:x:|

        ..  code-block:: none

            keyword_with_underscores

        Good |:white_check_mark:|

        ..  code-block:: none

            Keyword Without Underscores
        """,
    ),
    "0306": DefaultRule(
        rule_id="0306",
        name="setting-name-not-in-title-case",
        msg="Setting name '{{ setting_name }}' should use title or upper case",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
        docs="""
        Good |:white_check_mark:| ::

            *** Settings ***
            Resource    file.resource

            *** Test Cases ***
            Test
                [DOCUMENTATION]  Some documentation
                Step

        Bad |:x:| ::

            *** Settings ***
            resource    file.resource

            *** Test Cases ***
            Test
                [documentation]  Some documentation
                Step
        """,
    ),
    "0307": DefaultRule(
        rule_id="0307",
        name="section-name-invalid",
        msg="Section name should be in format '{{ section_title_case }}' or '{{ section_upper_case }}'",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
        docs="""
        Good |:white_check_mark:| ::

            *** SETTINGS ***
            *** Keywords ***

        Bad |:x:| ::

            *** keywords ***

        """,
    ),
    "0308": DefaultRule(
        rule_id="0308",
        name="not-capitalized-test-case-title",
        msg="Test case '{{ test_name }}' title should start with capital letter",
        severity=RuleSeverity.WARNING,
        added_in_version="1.4.0",
        docs="""
        Good |:white_check_mark:| ::

            *** Test Cases ***
            Validate user details

        Bad |:x:| ::

            *** Test Cases ***
            validate user details
        """,
    ),
    "0309": DefaultRule(
        rule_id="0309",
        name="section-variable-not-uppercase",
        msg="Section variable '{{ variable_name }}' name should be uppercase",
        severity=RuleSeverity.WARNING,
        added_in_version="1.4.0",
    ),
    "0310": DefaultRule(
        rule_id="0310",
        name="non-local-variables-should-be-uppercase",
        msg="Test, suite and global variables should be uppercase",
        severity=RuleSeverity.WARNING,
        added_in_version="1.4.0",
        docs="""
        Good |:white_check_mark:|

        ..  code-block:: none

            Set Task Variable    ${MY_VAR}           1
            Set Suite Variable   ${MY VAR}           1
            Set Test Variable    ${MY_VAR}           1
            Set Global Variable  ${MY VAR${nested}}  1

        Bad |:x:|

        ..  code-block:: none

            Set Task Variable    ${my_var}           1
            Set Suite Variable   ${My Var}           1
            Set Test Variable    ${myvar}            1
            Set Global Variable  ${my_var${NESTED}}  1
        """,
    ),
    "0311": DefaultRule(
        rule_id="0311",
        name="else-not-upper-case",
        msg="ELSE and ELSE IF should be upper case",
        severity=RuleSeverity.ERROR,
        added_in_version="1.5.0",
        docs="""
        Good |:white_check_mark:| ::

            *** Keywords ***
            Describe Temperature
                [Arguments]     ${degrees}
                IF         ${degrees} > ${30}
                    RETURN  Hot
                ELSE IF    ${degrees} > ${15}
                    RETURN  Warm
                ELSE
                    RETURN  Cold

        Bad |:x:| ::

            *** Keywords ***
            Describe Temperature
                [Arguments]     ${degrees}
                If         ${degrees} > ${30}
                    RETURN  Hot
                else if    ${degrees} > ${15}
                    RETURN  Warm
                Else
                    RETURN  Cold
        """,
    ),
    "0312": DefaultRule(
        rule_id="0312",
        name="keyword-name-is-empty",
        msg="Keyword name should not be empty",
        severity=RuleSeverity.ERROR,
        added_in_version="1.8.0",
        docs="""
        Remember to always add a keyword name and avoid such code::

            *** Keywords ***
            # no keyword name here!!!
                Log To Console  hi
        """,
    ),
    "0313": DefaultRule(
        rule_id="0313",
        name="test-case-name-is-empty",
        msg="Test case name should not be empty",
        severity=RuleSeverity.ERROR,
        added_in_version="1.8.0",
        docs="""
        Remember to always add a test case name and avoid such code::

            *** Test Cases ***
            # no test case name here!!!
                Log To Console  hello
        """,
    ),
    "0314": DefaultRule(
        rule_id="0314",
        name="empty-library-alias",
        msg="Library alias should not be empty",
        severity=RuleSeverity.ERROR,
        added_in_version="1.10.0",
        docs="""
        Use non-empty name when using library import with alias.

        Good |:white_check_mark:| ::

            *** Settings ***
            Library  CustomLibrary  AS  AnotherName

        Bad |:x:| ::

             *** Settings ***
             Library  CustomLibrary  AS
        """,
    ),
    "0315": DefaultRule(
        rule_id="0315",
        name="duplicated-library-alias",
        msg="Library alias should not be the same as original name",
        severity=RuleSeverity.WARNING,
        added_in_version="1.10.0",
        docs="""
        Examples of rule violation::

             *** Settings ***
             Library  CustomLibrary  AS  CustomLibrary   # same as library name
             Library  CustomLibrary  AS  Custom Library  # same as library name (spaces are ignored)
        """,
    ),
    "0316": DefaultRule(
        rule_id="0316",
        name="possible-variable-overwriting",
        msg="Variable '{{ variable_name }}' may overwrite similar variable inside '{{ block_name }}' {{ block_type }}. "
        "Note that variables are case-insensitive, and also spaces and underscores are ignored.",
        severity=RuleSeverity.INFO,
        added_in_version="1.10.0",
        docs="""
        Following assignments overwrite the same variable::

            *** Keywords ***
            Retrieve Usernames
                ${username}      Get Username       id=1
                ${User Name}     Get Username       id=2
                ${user_name}     Get Username       id=3

        Use consistent variable naming guidelines to avoid unintended variable overwriting.
        Remember that variable names in Robot Framework are case-insensitive and
        underscores and whitespaces are ignored.
        """,
    ),
    "0317": DefaultRule(
        rule_id="0317",
        name="hyphen-in-variable-name",
        msg="Use underscore in variable name '{{ variable_name }}' instead of hyphens to "
        "avoid treating them like minus sign",
        severity=RuleSeverity.INFO,
        added_in_version="1.10.0",
        docs="""
        Robot Framework supports evaluation of Python code inside ${ } brackets. For example:

        ..  code-block: none

            ${var2}  Set Variable  ${${var}-${var2}}

        That's why there is a possibility that hyphen in name is not recognized as part of the name but as a minus sign.
        Better to use underscore instead:

        ..  code-block: none

            ${var2}  Set Variable  ${${var}_${var2}}
        """,
    ),
    "0318": DefaultRule(
        rule_id="0318",
        name="bdd-without-keyword-call",
        msg="BDD reserved keyword '{{ keyword_name }}' not followed by any keyword{{ error_msg }}",
        severity=RuleSeverity.WARNING,
        added_in_version="1.11.0",
        docs="""
        When using BDD reserved keywords (such as `GIVEN`, `WHEN`, `AND`, `BUT` or `THEN`) use them together with
        name of the keyword to run.

        Good |:white_check_mark:| ::

            Given Setup Is Complete
            When User Log In
            Then User Should See Welcome Page

        Bad |:x:| ::

            Given
            When User Log In
            Then User Should See Welcome Page

        Since those words are used for BDD style, it's also recommended not to use them within the user keyword name.
        """,
    ),
    "0319": DefaultRule(
        rule_id="0319",
        name="deprecated-statement",
        msg="'{{ statement_name }}' is deprecated since Robot Framework version "
        "{{ version }}, use '{{ alternative }}' instead",
        severity=RuleSeverity.WARNING,
        added_in_version="2.0.0",
        docs="""
        This rule detects any piece of code that is marked as deprecated but still works in RF.

        For example, ``Run Keyword`` and ``Continue For Loop`` keywords or ``[Return]`` setting.
        """,
    ),
    "0320": DefaultRule(
        RuleParam(
            name="pattern",
            default=re.compile(r"[\.\?]"),
            converter=pattern_type,
            show_type="regex",
            desc="pattern defining characters (not) allowed in a name",
        ),
        rule_id="0320",
        name="not-allowed-char-in-filename",
        msg="Not allowed character '{{ character }}' found in {{ block_name }} name",
        severity=RuleSeverity.WARNING,
        added_in_version="2.1.0",
        docs="""
        Reports not allowed pattern found in Suite names. By default, it's a dot (`.`).
        You can configure what characters are reported by running::

             robocop --configure not-allowed-char-in-filename:pattern:regex_pattern .

        where ``regex_pattern`` should define regex pattern for characters not allowed in names. For example `[@\\[]`
        pattern would report any occurrence of ``@[`` characters.
        """,
    ),
    "0321": DefaultRule(
        rule_id="0321",
        name="deprecated-with-name",
        msg=(
            "'WITH NAME' alias marker is deprecated since Robot Framework 6.0 version "
            "and will be removed in the future release. Use 'AS' instead"
        ),
        severity=RuleSeverity.WARNING,
        version=">=6.0",
        added_in_version="2.5.0",
        docs="""
        ``WITH NAME`` marker that is used when giving an alias to an imported library is going to be renamed to ``AS``.
        The motivation is to be consistent with Python that uses ``as`` for similar purpose.

        Code with the deprecated marker::

            *** Settings ***
            Library    Collections    WITH NAME    AliasedName

        Code with the supported marker::

            *** Settings ***
            Library    Collections    AS    AliasedName
        """,
    ),
    "0322": DefaultRule(
        rule_id="0322",
        name="deprecated-singular-header",
        msg="'{{ singular_header }}' singular header form is deprecated since RF 6.0 and "
        "will be removed in the future releases. Use '{{ plural_header }}' instead",
        severity=RuleSeverity.WARNING,
        version=">=6.0",
        added_in_version="2.6.0",
        docs="""
        Robot Framework 6.0 starts deprecation period for singular headers forms. The rationale behind this change
        is available at https://github.com/robotframework/robotframework/issues/4431
        """,
    ),
    "0323": DefaultRule(
        rule_id="0323",
        name="inconsistent-variable-name",
        msg="Variable '{{ name }}' has inconsistent naming. First used as '{{ first_use }}'",
        severity=RuleSeverity.WARNING,
        added_in_version="3.2.0",
        docs="""
        Variable names are case-insensitive and ignore underscores and spaces. It is possible to
        write the variable in multiple ways and it will be a valid Robot Framework code. However,
        it makes it harder to maintain the code that does not follow the consistent naming.

        Example::

            *** Keywords ***
            Check If User Is Admin
                [Arguments]    ${username}
                ${role}    Get User Role     ${username}
                IF    '${ROLE}' == 'Admin'   # inconsistent name with ${role}
                    Log    ${Username} is an admin  # inconsistent name with ${username}
                ELSE
                    Log    ${user name} is not an admin  # inconsistent name
                END
        """,
    ),
    "0324": DefaultRule(
        rule_id="0324",
        name="overwriting-reserved-variable",
        msg="{{ var_or_arg }} '{{ variable_name }}' overwrites reserved variable '{{ reserved_variable }}'",
        severity=RuleSeverity.WARNING,
        added_in_version="3.2.0",
        docs="""
        Overwriting reserved variables may bring unexpected results.
        For example, overwriting variable with name ``${LOG_LEVEL}`` can break Robot Framework logging.
        See the full list of reserved variables at
        `Robot Framework User Guide <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#automatic-variables>`_
        """,
    ),
    "0325": DefaultRule(
        rule_id="0325",
        name="invalid-section",
        msg="Invalid section '{{ invalid_section }}'. Consider using --language parameter if the file is defined with different language",
        severity=RuleSeverity.ERROR,
        version=">=6.1",
        added_in_version="3.2.0",
        docs="""
        Robot Framework 6.1 detects unrecognized sections based on the language defined for the specific files.
        Consider using ``--language`` parameter if the file is defined with different language.

        It is also possible to configure language in the file::

            language: pl

            *** Przypadki Testowe ***
            Wypisz dyrektywę 4
                Log   Błąd dostępu
        """,
    ),
    "0326": DefaultRule(
        rule_id="0326",
        name="mixed-task-test-settings",
        msg="Use {{ task_or_test }}-related setting '{{ setting }}' if {{ tasks_or_tests }} section is used",
        severity=RuleSeverity.WARNING,
        added_in_version="3.3.0",
        docs="""
        If ``*** Tasks ***`` section is present in the file, use task-related settings like ``Task Setup``,
        ``Task Teardown``, ``Task Template``, ``Task Tags`` and ``Task Timeout`` instead of their `Test` variants.

        Similarly, use test-related settings when using ``*** Test Cases ***`` section.
        """,
    ),
    "0327": DefaultRule(
        rule_id="0327",
        name="replace-set-variable-with-var",
        msg="{{ set_variable_keyword }} can be replaced with VAR",
        severity=RuleSeverity.INFO,
        version=">=7.0",
        added_in_version="5.0.0",
        docs="""
        Starting from Robot Framework 7.0, it is possible to create variables inside tests and user keywords using the
        VAR syntax. The VAR syntax is recommended over previously existing keywords.

        Example with Set Variable keywords::

          *** Keywords ***
          Set Variables To Different Scopes
              Set Local Variable    ${local}    value
              Set Test Variable    ${TEST_VAR}    value
              Set Task Variable    ${TASK_VAR}    value
              Set Suite Variable    ${SUITE_VAR}    value
              Set Global Variable    ${GLOBAL_VAR}    value

        Can be now rewritten to::

          *** Keywords ***
          Set Variables To Different Scopes
              VAR    ${local}    value
              VAR    ${TEST_VAR}    value    scope=TEST
              VAR    ${TASK_VAR}    value    scope=TASK
              VAR    ${SUITE_VAR}    value    scope=SUITE
              VAR    ${GLOBAL_VAR}    value    scope=GLOBAL

        """,
    ),
    "0328": DefaultRule(
        rule_id="0328",
        name="replace-create-with-var",
        msg="{{ create_keyword }} can be replaced with VAR",
        severity=RuleSeverity.INFO,
        version=">=7.0",
        added_in_version="5.0.0",
        docs="""
        Starting from Robot Framework 7.0, it is possible to create variables inside tests and user keywords using the
        VAR syntax. The VAR syntax is recommended over previously existing keywords.

        Example with Create keywords::

          *** Keywords ***
          Create Variables
              @{list}    Create List    a  b
              &{dict}    Create Dictionary    key=value

        Can be now rewritten to::

          *** Keywords ***
          Create Variables
              VAR    @{list}    a  b
              VAR    &{dict}    key=value

        """,
    ),
}

SET_VARIABLE_VARIANTS = {
    "settaskvariable",
    "settestvariable",
    "setsuitevariable",
    "setglobalvariable",
}


class InvalidCharactersInNameChecker(VisitorChecker):
    """Checker for invalid characters in suite, test case or keyword name."""

    reports = (
        "not-allowed-char-in-filename",
        "not-allowed-char-in-name",
    )

    def visit_File(self, node):  # noqa: N802
        source = node.source if node.source else self.source
        if source:
            suite_name = Path(source).stem
            if "__init__" in suite_name:
                suite_name = Path(source).parent.name
            for match in self.param("not-allowed-char-in-filename", "pattern").finditer(suite_name):
                self.report(
                    "not-allowed-char-in-filename",
                    character=match.group(),
                    block_name="suite",
                    node=node,
                    col=node.col_offset + match.start(0) + 1,
                )
        super().visit_File(node)

    def check_if_pattern_in_node_name(self, node, name_of_node, is_keyword=False):
        """
        Search if regex pattern found from node name.
        Skips embedded variables from keyword name
        """
        node_name = node.name
        variables = find_robot_vars(node_name) if is_keyword else []
        start_pos = 0
        for variable in variables:
            # Loop and skip variables:
            # Search pattern from start_pos to variable starting position
            # example `Keyword With ${em.bedded} Two ${second.Argument} Argument``
            # is split to:
            #   1. `Keyword With `
            #   2. ` Two `
            #   3. ` Argument` - last part is searched in finditer part after this loop
            tmp_node_name = node_name[start_pos : variable[0]]
            match = self.param("not-allowed-char-in-name", "pattern").search(tmp_node_name)
            if match:
                self.report(
                    "not-allowed-char-in-name",
                    character=match.group(),
                    block_name=f"'{node_name}' {name_of_node}",
                    node=node,
                    col=node.col_offset + match.start(0) + 1,
                    end_col=node.col_offset + match.end(0) + 1,
                )
            start_pos = variable[1]

        for iter in self.param("not-allowed-char-in-name", "pattern").finditer(node_name, start_pos):
            self.report(
                "not-allowed-char-in-name",
                character=iter.group(),
                block_name=f"'{node.name}' {name_of_node}",
                node=node,
                col=node.col_offset + iter.start(0) + 1,
                end_col=node.col_offset + iter.end(0) + 1,
            )

    def visit_TestCaseName(self, node):  # noqa: N802
        self.check_if_pattern_in_node_name(node, "test case")

    def visit_KeywordName(self, node):  # noqa: N802
        self.check_if_pattern_in_node_name(node, "keyword", is_keyword=True)


def uppercase_error_msg(name):
    return f". It must be in uppercase ({name.upper()}) when used as a statement"


class KeywordNamingChecker(VisitorChecker):
    """Checker for keyword naming violations."""

    reports = (
        "wrong-case-in-keyword-name",
        "keyword-name-is-reserved-word",
        "underscore-in-keyword-name",
        "else-not-upper-case",
        "keyword-name-is-empty",
        "bdd-without-keyword-call",
    )
    # reserved word followed by the RF version when it was introduced
    reserved_words = {
        "for": 3,
        "end": 3,
        "if": 4,
        "else if": 4,
        "else": 4,
        "while": 5,
        "continue": 5,
        "return": 5,
        "try": 5,
        "except": 5,
        "finally": 5,
    }
    else_statements = {"else", "else if"}
    bdd = {"given", "when", "and", "but", "then"}

    def __init__(self):
        self.letter_pattern = re.compile(r"[^\w()-]|_", re.UNICODE)
        self.inside_if_block = False
        super().__init__()

    def check_keyword_naming_with_subkeywords(self, node, name_token_type):
        for keyword in iterate_keyword_names(node, name_token_type):
            self.check_keyword_naming(keyword.value, keyword)

    def visit_Setup(self, node):  # noqa: N802
        self.check_bdd_keywords(node.name, node)
        self.check_keyword_naming_with_subkeywords(node, Token.NAME)

    visit_TestTeardown = visit_SuiteTeardown = visit_Teardown = visit_TestSetup = visit_SuiteSetup = visit_Setup  # noqa: N815

    def visit_Template(self, node):  # noqa: N802
        if node.value:
            name_token = node.get_token(Token.NAME)
            self.check_keyword_naming(node.value, name_token)
        self.generic_visit(node)

    visit_TestTemplate = visit_Template  # noqa: N815

    def visit_Keyword(self, node):  # noqa: N802
        if not node.name:
            self.report("keyword-name-is-empty", node=node)
        else:
            self.check_keyword_naming(node.name, node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa: N802
        if self.inside_if_block and node.keyword and node.keyword.lower() in self.else_statements:
            self.report("else-not-upper-case", node=node, col=keyword_col(node))
        self.check_keyword_naming_with_subkeywords(node, Token.KEYWORD)
        self.check_bdd_keywords(node.keyword, node)

    def visit_If(self, node):  # noqa: N802
        self.inside_if_block = True
        self.generic_visit(node)
        self.inside_if_block = False

    def check_keyword_naming(self, keyword_name, node):
        if not keyword_name or keyword_name.lstrip().startswith("#"):
            return
        if keyword_name == r"/":  # old for loop, / are interpreted as keywords
            return
        if self.check_if_keyword_is_reserved(keyword_name, node):
            return
        normalized = remove_robot_vars(keyword_name)
        normalized = self.param("wrong-case-in-keyword-name", "pattern").sub("", normalized)
        normalized = normalized.split(".")[-1]  # remove any imports ie ExternalLib.SubLib.Log -> Log
        normalized = normalized.replace("'", "")  # replace ' apostrophes
        if "_" in normalized:
            self.report(
                "underscore-in-keyword-name",
                keyword_name=keyword_name,
                node=node,
                col=node.col_offset + 1,
                end_col=node.end_col_offset + 1,
            )
        words = self.letter_pattern.sub(" ", normalized).split(" ")
        if self.param("wrong-case-in-keyword-name", "convention") == "first_word_capitalized":
            words = words[:1]
        if any(word[0].islower() for word in words if word):
            self.report(
                "wrong-case-in-keyword-name",
                keyword_name=keyword_name,
                node=node,
                col=node.col_offset + 1,
                end_col=node.col_offset + len(keyword_name) + 1,
            )

    def check_bdd_keywords(self, keyword_name, node):
        if not keyword_name or keyword_name.lower() not in self.bdd:
            return
        arg = node.get_token(Token.ARGUMENT)
        suffix = f". Use one space between: '{keyword_name.title()} {arg.value}'" if arg else ""
        col = token_col(node, Token.NAME, Token.KEYWORD)
        self.report("bdd-without-keyword-call", keyword_name=keyword_name, error_msg=suffix, node=node, col=col)

    def check_if_keyword_is_reserved(self, keyword_name, node):
        # if there is typo in syntax, it is interpreted as keyword
        lower_name = keyword_name.lower()
        if lower_name not in self.reserved_words:
            return False
        if lower_name in self.else_statements and self.inside_if_block:
            return False  # handled by else-not-upper-case
        min_ver = self.reserved_words[lower_name]
        if ROBOT_VERSION.major < min_ver:
            return False
        error_msg = uppercase_error_msg(lower_name)
        self.report(
            "keyword-name-is-reserved-word",
            keyword_name=keyword_name,
            error_msg=error_msg,
            node=node,
            col=node.col_offset + 1,
            end_col=node.end_col_offset + 1,
        )
        return True


class SettingsNamingChecker(VisitorChecker):
    """Checker for settings and sections naming violations."""

    reports = (
        "setting-name-not-in-title-case",
        "section-name-invalid",
        "empty-library-alias",
        "duplicated-library-alias",
        "invalid-section",
        "mixed-task-test-settings",
    )
    ALIAS_TOKENS = [Token.WITH_NAME] if ROBOT_VERSION.major < 5 else ["WITH NAME", "AS"]
    # Separating alias values since RF 3 uses WITH_NAME instead of WITH NAME
    ALIAS_TOKENS_VALUES = ["WITH NAME"] if ROBOT_VERSION.major < 5 else ["WITH NAME", "AS"]

    def __init__(self):
        self.section_name_pattern = re.compile(r"\*\*\*\s.+\s\*\*\*")
        self.task_section: bool | None = None
        super().__init__()

    def visit_InvalidSection(self, node):  # noqa: N802
        name = node.header.data_tokens[0].value
        invalid_header = node.header.get_token(Token.INVALID_HEADER)
        if "Resource file with" in invalid_header.error:
            return
        if invalid_header:
            self.report(
                "invalid-section",
                invalid_section=name,
                node=node,
                col=node.header.col_offset + 1,
                end_col=node.header.end_col_offset + 1,
            )

    def visit_SectionHeader(self, node):  # noqa: N802
        name = node.data_tokens[0].value
        if not self.section_name_pattern.match(name) or not (name.istitle() or name.isupper()):
            valid_name = f"*** {node.name.title()} ***"
            self.report(
                "section-name-invalid",
                section_title_case=valid_name,
                section_upper_case=valid_name.upper(),
                node=node,
                end_col=node.col_offset + len(name) + 1,
            )

    def visit_File(self, node):  # noqa: N802
        self.task_section = None
        for section in node.sections:
            if isinstance(section, TestCaseSection):
                if (ROBOT_VERSION.major < 6 and "task" in section.header.name.lower()) or (
                    ROBOT_VERSION.major >= 6 and section.header.type == Token.TASK_HEADER
                ):
                    self.task_section = True
                else:
                    self.task_section = False
                break
        super().visit_File(node)

    def visit_Setup(self, node):  # noqa: N802
        self.check_setting_name(node.data_tokens[0].value, node)
        self.check_settings_consistency(node.data_tokens[0].value, node)

    visit_SuiteSetup = visit_TestSetup = visit_Teardown = visit_SuiteTeardown = visit_TestTeardown = (  # noqa: N815
        visit_TestTimeout  # noqa: N815
    ) = visit_TestTemplate = visit_TestTags = visit_ForceTags = visit_DefaultTags = visit_ResourceImport = (  # noqa: N815
        visit_VariablesImport  # noqa: N815
    ) = visit_Documentation = visit_Tags = visit_Timeout = visit_Template = visit_Arguments = visit_ReturnSetting = (  # noqa: N815
        visit_Return  # noqa: N815
    ) = visit_Setup

    def visit_LibraryImport(self, node):  # noqa: N802
        self.check_setting_name(node.data_tokens[0].value, node)
        if ROBOT_VERSION.major < 6:
            arg_nodes = node.get_tokens(Token.ARGUMENT)
            # ignore cases where 'AS' is used to provide library alias for RF < 5
            if arg_nodes and any(arg.value == "AS" for arg in arg_nodes):
                return
            with_name = bool(node.get_token(*self.ALIAS_TOKENS))
        else:
            with_name = len(node.get_tokens(Token.NAME)) >= 2
        if not with_name:
            for arg in node.get_tokens(Token.ARGUMENT):
                if arg.value and arg.value in self.ALIAS_TOKENS_VALUES:
                    self.report("empty-library-alias", node=arg, col=arg.col_offset + 1)
        elif node.alias.replace(" ", "") == node.name.replace(" ", ""):  # New Name == NewName
            name_token = node.get_tokens(Token.NAME)[-1]
            self.report(
                "duplicated-library-alias",
                node=name_token,
                col=name_token.col_offset + 1,
                end_col=name_token.end_col_offset + 1,
            )

    def check_setting_name(self, name, node):
        if not (name.istitle() or name.isupper()):
            col = node.tokens[0].end_col_offset if node.tokens[0].type == "SEPARATOR" else node.col_offset
            self.report(
                "setting-name-not-in-title-case", setting_name=name, node=node, col=col + 1, end_col=col + len(name) + 1
            )

    def check_settings_consistency(self, name: str, node):
        name_normalized = name.lower()
        # if there is no task/test section, determine by first setting in the file
        if self.task_section is None and ("test" in name_normalized or "task" in name_normalized):
            self.task_section = "task" in name_normalized
        if "test" in name_normalized and self.task_section:
            self.report(
                "mixed-task-test-settings",
                setting="Task " + name.split()[1],
                task_or_test="task",
                tasks_or_tests="Tasks",
                node=node,
            )
        elif "task" in name_normalized and not self.task_section:
            self.report(
                "mixed-task-test-settings",
                setting="Test " + name.split()[1],
                task_or_test="test",
                tasks_or_tests="Test Cases",
                node=node,
            )


class TestCaseNamingChecker(VisitorChecker):
    """Checker for test case naming violations."""

    reports = (
        "not-capitalized-test-case-title",
        "test-case-name-is-empty",
    )

    def visit_TestCase(self, node):  # noqa: N802
        if not node.name:
            self.report("test-case-name-is-empty", node=node)
        else:
            for c in node.name:
                if not c.isalpha():
                    continue
                if not c.isupper():
                    self.report(
                        "not-capitalized-test-case-title",
                        test_name=node.name,
                        node=node,
                        end_col=node.col_offset + len(node.name) + 1,
                    )
                break


class VariableNamingChecker(VisitorChecker):
    """Checker for variable naming violations."""

    reports = (
        "section-variable-not-uppercase",
        "non-local-variables-should-be-uppercase",
        "hyphen-in-variable-name",
        "overwriting-reserved-variable",
    )
    RESERVED_VARIABLES = {
        "testname": "${TEST_NAME}",
        "testtags": "@{TEST_TAGS}",
        "testdocumentation": "${TEST_DOCUMENTATION}",
        "teststatus": "${TEST_STATUS}",
        "testmessage": "${TEST_MESSAGE}",
        "prevtestname": "${PREV_TEST_NAME}",
        "prevteststatus": "${PREV_TEST_STATUS}",
        "prevtestmessage": "${PREV_TEST_MESSAGE}",
        "suitename": "${SUITE_NAME}",
        "suitesource": "${SUITE_SOURCE}",
        "suitedocumentation": "${SUITE_DOCUMENTATION}",
        "suitemetadata": "&{SUITE_METADATA}",
        "suitestatus": "${SUITE_STATUS}",
        "suitemessage": "${SUITE_MESSAGE}",
        "keywordstatus": "${KEYWORD_STATUS}",
        "keywordmessage": "${KEYWORD_MESSAGE}",
        "loglevel": "${LOG_LEVEL}",
        "outputfile": "${OUTPUT_FILE}",
        "logfile": "${LOG_FILE}",
        "reportfile": "${REPORT_FILE}",
        "debugfile": "${DEBUG_FILE}",
        "outputdir": "${OUTPUT_DIR}",
        # "options": "&{OPTIONS}", This variable is widely used and is relatively safe to overwrite
    }

    def visit_Keyword(self, node):  # noqa: N802
        name_token = node.header.get_token(Token.KEYWORD_NAME)
        self.parse_embedded_arguments(name_token)
        self.generic_visit(node)

    def visit_Variable(self, node):  # noqa: N802
        token = node.data_tokens[0]
        try:
            var_name = search_variable(token.value).base
        except VariableError:
            return  # TODO: Ignore for now, for example ${not  closed in variables will throw it
        if var_name is None:
            return  # in RF<=5, a continuation mark ` ...` is wrongly considered a variable
        # in Variables section, everything needs to be in uppercase
        # because even when the variable is nested, it needs to be global
        if not var_name.isupper():
            self.report(
                "section-variable-not-uppercase",
                variable_name=token.value.strip(),
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.col_offset + len(token.value) + 1,
            )
        self.check_for_reserved_naming_or_hyphen(token, "Variable")

    def visit_KeywordCall(self, node):  # noqa: N802
        for token in node.get_tokens(Token.ASSIGN):
            self.check_for_reserved_naming_or_hyphen(token, "Variable", is_assign=True)
        if not node.keyword:
            return
        if normalize_robot_name(node.keyword, remove_prefix="builtin.") in SET_VARIABLE_VARIANTS:
            if len(node.data_tokens) < 2:
                return
            token = node.data_tokens[1]
            if not token.value:
                return
            try:
                var_name = search_variable(token.value).base
            except VariableError:
                return  # TODO: Ignore for now, for example ${not  closed in variables will throw it
            if var_name is None:  # possibly $escaped or \${escaped}, or invalid variable name
                return
            self.check_non_local_variable(var_name, node, token)

    def check_non_local_variable(self, variable_name: str, node, token):
        normalized_var_name = remove_nested_variables(variable_name)
        # a variable as a keyword argument can contain lowercase nested variable
        # because the actual value of it may be uppercase
        if not normalized_var_name.isupper():
            self.report(
                "non-local-variables-should-be-uppercase",
                node=node,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )

    def visit_Var(self, node):  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        variable = node.get_token(Token.VARIABLE)
        if not variable:
            return
        self.check_for_reserved_naming_or_hyphen(variable, "Variable", is_assign=True)
        # TODO: Check supported syntax for variable, ie ${{var}}?
        if not _is_var_scope_local(node):
            self.check_non_local_variable(search_variable(variable.value).base, node, variable)

    def visit_If(self, node):  # noqa: N802
        for token in node.header.get_tokens(Token.ASSIGN):
            self.check_for_reserved_naming_or_hyphen(token, "Variable")
        self.generic_visit(node)

    def visit_Arguments(self, node):  # noqa: N802
        for arg in node.get_tokens(Token.ARGUMENT):
            self.check_for_reserved_naming_or_hyphen(arg, "Argument")

    def parse_embedded_arguments(self, name_token):
        """Store embedded arguments from keyword name. Ignore embedded variables patterns like (${var:pattern})."""
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    self.check_for_reserved_naming_or_hyphen(token, "Embedded argument", has_pattern=True)
        except VariableError:
            pass

    def check_for_reserved_naming_or_hyphen(self, token, var_or_arg, has_pattern=False, is_assign=False):
        """Check if variable name is a reserved Robot Framework name or uses hyphen in the name."""
        variable_match = search_variable(token.value, ignore_errors=True)
        name = variable_match.base
        if has_pattern:
            name, *_ = name.split(":", maxsplit=1)  # var:pattern -> var
        if is_assign and "-" in variable_match.base:
            self.report(
                "hyphen-in-variable-name",
                variable_name=token.value,
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )
        if variable_match.items:  # item assignments ${dict}[key] =
            return
        normalized_name = normalize_robot_name(name)
        if normalized_name in self.RESERVED_VARIABLES:
            reserved_variable = self.RESERVED_VARIABLES[normalized_name]
            self.report(
                "overwriting-reserved-variable",
                var_or_arg=var_or_arg,
                variable_name=variable_match.match,
                reserved_variable=reserved_variable,
                node=token,
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.col_offset + len(variable_match.match) + 1,
            )


class SimilarVariableChecker(VisitorChecker):
    """Checker for finding same variables with similar names."""

    reports = ("possible-variable-overwriting", "inconsistent-variable-name")

    def __init__(self):
        self.assigned_variables = defaultdict(list)
        self.parent_name = ""
        self.parent_type = ""
        super().__init__()

    def visit_Keyword(self, node):  # noqa: N802
        self.assigned_variables = defaultdict(list)
        self.parent_name = node.name
        self.parent_type = type(node).__name__
        name_token = node.header.get_token(Token.KEYWORD_NAME)
        self.parse_embedded_arguments(name_token)
        self.visit_vars_and_find_similar(node)
        self.generic_visit(node)

    def visit_TestCase(self, node):  # noqa: N802
        self.assigned_variables = defaultdict(list)
        self.parent_name = node.name
        self.parent_type = type(node).__name__
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa: N802
        if normalize_robot_name(node.keyword, remove_prefix="builtin.") in SET_VARIABLE_VARIANTS:
            normalized, assign_value = "", ""
            for index, token in enumerate(node.data_tokens[1:]):
                if index == 0:  # First argument is assign-like
                    normalized = normalize_robot_var_name(token.value)
                    assign_value = token.value  # process assign last, cache for now
                else:
                    self.find_not_nested_variable(token, token.value, is_var=False)
            self.assigned_variables[normalized].append(assign_value)
        else:
            for token in node.get_tokens(Token.ARGUMENT, Token.KEYWORD):  # argument can be used in keyword name
                self.find_not_nested_variable(token, token.value, is_var=False)
        tokens = node.get_tokens(Token.ASSIGN)
        self.find_similar_variables(tokens, node)

    def visit_Var(self, node):  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(arg, arg.value, is_var=False)
        variable = node.get_token(Token.VARIABLE)
        if variable:
            self.find_similar_variables([variable], node, ignore_overwriting=not _is_var_scope_local(node))

    def visit_If(self, node):  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token, token.value, is_var=False)
        tokens = node.header.get_tokens(Token.ASSIGN)
        self.find_similar_variables(tokens, node)
        self.generic_visit(node)

    def visit_While(self, node):  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token, token.value, is_var=False)
        return self.generic_visit(node)

    @staticmethod
    def for_assign_vars(for_node) -> Iterable[str]:
        if ROBOT_VERSION.major < 7:
            yield from for_node.variables
        else:
            yield from for_node.assign

    def visit_For(self, node):  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token, token.value, is_var=False)
        for var in self.for_assign_vars(node):
            self.assigned_variables[normalize_robot_var_name(var)].append(var)
        self.generic_visit(node)

    visit_ForLoop = visit_For  # noqa: N815

    def visit_Return(self, node):  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token, token.value, is_var=False)

    visit_ReturnStatement = visit_Teardown = visit_Timeout = visit_Return  # noqa: N815

    def parse_embedded_arguments(self, name_token):
        """Store embedded arguments from keyword name. Ignore embedded variables patterns (${var:pattern})."""
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    var_name, *pattern = token.value.split(":", maxsplit=1)
                    if pattern:
                        var_name = var_name + "}"  # recreate, so it handles ${variable:pattern} -> ${variable} matching
                    normalized_name = normalize_robot_var_name(var_name)
                    self.assigned_variables[normalized_name].append(var_name)
        except VariableError:
            pass

    def check_inconsistent_naming(self, token, value: str, offset: int):
        """
        Check if variable name ``value`` was already defined under matching but not the same name.
        :param token: ast token representing the string with variable
        :param value: name of variable found in token value string
        :param offset: starting position of variable in token value string
        """
        normalized = normalize_robot_name(value)
        if normalized not in self.assigned_variables:
            return  # we could handle attr access here, ignoring now
        latest_assign = self.assigned_variables[normalized][-1]
        assign_normalized = latest_assign.lstrip("$@%&").lstrip("{").rstrip("}")
        if value != assign_normalized:
            name = "${" + value + "}"
            self.report(
                "inconsistent-variable-name",
                name=name,
                first_use=latest_assign,
                node=token,
                lineno=token.lineno,
                col=token.col_offset + offset + 1,
                end_col=token.col_offset + offset + len(name) + 1,
            )

    def find_not_nested_variable(self, token, value, is_var: bool, offset: int = 0):
        """
        Find and process not nested variable.

        Search `value` string until there is ${variable} without other variables inside.
        Unescaped escaped syntax ($var or \\${var}) is ignored.
        Offset is to determine position of the variable in the string.
        For example 'This is ${var}' contains ${var} at 8th position.
        """
        try:
            variables = list(VariableMatches(value))
        except VariableError:  # for example ${variable which wasn't closed properly
            return
        if not variables:
            if is_var:
                self.check_inconsistent_naming(token, value, offset)
            return
        if is_var:
            offset += 2  # handle ${var_${var}} case
        for match in variables:
            if match.before:
                offset += len(match.before)
            # match = search_variable(variable, ignore_errors=True)
            if match.base and match.base.startswith("{") and match.base.endswith("}"):  # inline val
                self.find_not_nested_variable(token, match.base[1:-1].strip(), is_var=False, offset=offset + 1)
            else:
                self.find_not_nested_variable(token, match.base, is_var=True, offset=offset)
            offset += len(match.match)
            for item in match.items:
                self.find_not_nested_variable(token, item, is_var=False, offset=offset)
                offset += len(item)

    def visit_vars_and_find_similar(self, node):
        """
        Update a dictionary `assign_variables` with normalized variable name as a key
        and ads a list of all detected variations of this variable in the node as a value,
        then it checks if similar variable was found.
        """
        for child in node.body:
            # read arguments from Keywords
            if isinstance(child, Arguments):
                for token in child.get_tokens(Token.ARGUMENT):
                    variable_match = search_variable(token.value, ignore_errors=True)
                    name = variable_match.name
                    normalized = normalize_robot_name(variable_match.base)
                    self.assigned_variables[normalized].append(name)

    def find_similar_variables(self, tokens, node, ignore_overwriting: bool = False):
        for token in tokens:
            variable_match = search_variable(token.value, ignore_errors=True)
            name = variable_match.name
            normalized = normalize_robot_name(variable_match.base)
            if (
                not ignore_overwriting
                and normalized in self.assigned_variables
                and name not in self.assigned_variables[normalized]
            ):
                self.report(
                    "possible-variable-overwriting",
                    variable_name=name,
                    block_name=self.parent_name,
                    block_type=self.parent_type,
                    node=node,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset + 1,
                )
            self.assigned_variables[normalized].append(name)


class DeprecatedStatementChecker(VisitorChecker):
    """Checker for deprecated statements."""

    reports = (
        "deprecated-statement",
        "deprecated-with-name",
        "deprecated-singular-header",
        "replace-set-variable-with-var",
        "replace-create-with-var",
    )
    deprecated_keywords = {
        "runkeywordunless": (5, "IF"),
        "runkeywordif": (5, "IF"),
        "exitforloop": (5, "BREAK"),
        "exitforloopif": (5, "IF and BREAK"),
        "continueforloop": (5, "CONTINUE"),
        "continueforloopif": (5, "IF and CONTINUE"),
        "returnfromkeyword": (5, "RETURN"),
        "returnfromkeywordif": (5, "IF and RETURN"),
    }
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
    set_variable_keywords = {
        "setlocalvariable",
        "settestvariable",
        "settaskvariable",
        "setsuitevariable",
        "setglobalvariable",
    }
    create_keywords = {"createdictionary", "createlist"}

    def visit_KeywordCall(self, node):  # noqa: N802
        self.check_if_keyword_is_deprecated(node.keyword, node)
        self.check_keyword_can_be_replaced_with_var(node.keyword, node)

    def visit_SuiteSetup(self, node):  # noqa: N802
        self.check_if_keyword_is_deprecated(node.name, node)

    visit_TestSetup = visit_Setup = visit_SuiteTeardown = visit_TestTeardown = visit_Teardown = visit_SuiteSetup  # noqa: N815

    def visit_Template(self, node):  # noqa: N802
        if not node.value:
            return
        self.check_if_keyword_is_deprecated(node.value, node)

    visit_TestTemplate = visit_Template  # noqa: N815

    def visit_Return(self, node):  # noqa: N802
        """For RETURN use visit_ReturnStatement - visit_Return will most likely visit RETURN in the future"""
        if ROBOT_VERSION.major not in (5, 6):
            return
        self.check_deprecated_return(node)

    def visit_ReturnSetting(self, node):  # noqa: N802
        self.check_deprecated_return(node)

    def check_deprecated_return(self, node):
        self.report(
            "deprecated-statement",
            statement_name="[Return]",
            alternative="RETURN",
            node=node,
            col=token_col(node, Token.RETURN),
            end_col=node.end_col_offset,
            version="5.*",
        )

    def visit_ForceTags(self, node):  # noqa: N802
        if ROBOT_VERSION.major < 6:
            return
        setting_name = node.data_tokens[0].value.lower()
        if setting_name == "force tags":
            self.report(
                "deprecated-statement",
                statement_name="Force Tags",
                alternative="Test Tags",
                node=node,
                col=token_col(node, Token.FORCE_TAGS),
                end_col=node.col_offset + len(setting_name) + 1,
                version="6.0",
            )

    def check_if_keyword_is_deprecated(self, keyword_name, node):
        normalized_keyword_name = normalize_robot_name(keyword_name, remove_prefix="builtin.")
        if normalized_keyword_name not in self.deprecated_keywords:
            return
        version, alternative = self.deprecated_keywords[normalized_keyword_name]
        if version > ROBOT_VERSION.major:
            return
        col = token_col(node, Token.NAME, Token.KEYWORD)
        self.report(
            "deprecated-statement",
            statement_name=keyword_name,
            alternative=alternative,
            node=node,
            col=col,
            end_col=col + len(keyword_name),
            version=f"{version}.*",
        )

    def check_keyword_can_be_replaced_with_var(self, keyword_name, node):
        if ROBOT_VERSION.major < 7:
            return
        normalized = normalize_robot_name(keyword_name, remove_prefix="builtin.")
        col = token_col(node, Token.NAME, Token.KEYWORD)
        if normalized in self.set_variable_keywords:
            self.report(
                "replace-set-variable-with-var",
                set_variable_keyword=keyword_name,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )
        elif normalized in self.create_keywords:
            self.report(
                "replace-create-with-var",
                create_keyword=keyword_name,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )

    def visit_LibraryImport(self, node):  # noqa: N802
        if ROBOT_VERSION.major < 5 or (ROBOT_VERSION.major == 5 and ROBOT_VERSION.minor == 0):
            return
        with_name_token = node.get_token(Token.WITH_NAME)
        if not with_name_token or with_name_token.value == "AS":
            return
        self.report(
            "deprecated-with-name",
            node=with_name_token,
            col=with_name_token.col_offset + 1,
            end_col=with_name_token.end_col_offset + 1,
        )

    def visit_SectionHeader(self, node):  # noqa: N802
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
            "deprecated-singular-header",
            singular_header=f"*** {node.name} ***",
            plural_header=f"*** {node.name}s ***",
            node=header_node,
            col=header_node.col_offset + 1,
            end_col=header_node.end_col_offset + 1,
        )
