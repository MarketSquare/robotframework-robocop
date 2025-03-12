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

from robocop.linter.rules import Rule, RuleParam, RuleSeverity, VisitorChecker, deprecated, variables
from robocop.linter.utils import (
    ROBOT_VERSION,
    find_robot_vars,
    keyword_col,
    normalize_robot_name,
    normalize_robot_var_name,
    pattern_type,
    remove_robot_vars,
    token_col,
)
from robocop.linter.utils.misc import _is_var_scope_local, remove_nested_variables
from robocop.linter.utils.run_keywords import iterate_keyword_names
from robocop.linter.utils.variable_matcher import VariableMatches

if TYPE_CHECKING:
    from collections.abc import Iterable


class NotAllowedCharInNameRule(Rule):
    r"""
    Not allowed character found.

    Reports not allowed characters found in Test Case or Keyword names. By default it's a dot (``.``). You can
    configure what patterns are reported by calling::

        robocop check --configure not-allowed-char-in-name.pattern=regex_pattern

    ``regex_pattern`` should define regex pattern not allowed in names. For example ``[@\[]`` pattern
    would report any occurrence of ``@[`` characters.

    """

    name = "not-allowed-char-in-name"
    rule_id = "NAME01"
    message = "Not allowed character '{character}' found in {block_name} name"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="pattern",
            default=re.compile(r"[\.\?]"),
            converter=pattern_type,
            show_type="regex",
            desc="pattern defining characters (not) allowed in a name",
        )
    ]
    added_in_version = "1.0.0"


class WrongCaseInKeywordNameRule(Rule):
    r"""
    Keyword name does not follow case convention.

    Keyword names need to follow a specific case convention.
    The convention can be set using ``convention`` parameter and accepts
    one of the 2 values: ``each_word_capitalized`` or ``first_word_capitalized``.

    By default, it's configured to ``each_word_capitalized``, which requires each keyword to follow such
    convention::

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

    ``pattern`` parameter accepts a regex pattern. For example, configuring it to ``robocop\.readthedocs\.io``
    would make such keyword legal::

        Go To robocop.readthedocs.io Page

    """

    name = "wrong-case-in-keyword-name"
    rule_id = "NAME02"
    message = "Keyword name '{keyword_name}' does not follow case convention"
    severity = RuleSeverity.WARNING
    parameters = [
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
    ]
    added_in_version = "1.0.0"


class KeywordNameIsReservedWordRule(Rule):
    """
    Keyword name is a reserved word.

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

    """

    name = "keyword-name-is-reserved-word"
    rule_id = "NAME03"
    message = "'{keyword_name}' is a reserved keyword{error_msg}"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"


class UnderscoreInKeywordNameRule(Rule):
    """
    Underscores in keyword name.

    You can replace underscores with spaces.

    Incorrect code example::

        keyword_with_underscores

    Correct code::

        Keyword Without Underscores

    """

    name = "underscore-in-keyword-name"
    rule_id = "NAME04"
    message = "Underscores in keyword name '{keyword_name}'"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"


class SettingNameNotInTitleCaseRule(Rule):
    """
    Setting name not in title or upper case.

    Incorrect code example::

        *** Settings ***
        resource    file.resource

        *** Test Cases ***
        Test
            [documentation]  Some documentation
            Step

    Correct code::

        *** Settings ***
        Resource    file.resource

        *** Test Cases ***
        Test
            [DOCUMENTATION]  Some documentation
            Step


    """

    name = "setting-name-not-in-title-case"
    rule_id = "NAME05"
    message = "Setting name '{setting_name}' not in title or uppercase"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"


class SectionNameInvalidRule(Rule):
    """
    Section name does not follow convention.

    Section name should use Title Case or CAP CASE case convention.

    Incorrect code example::

        *** settings ***
        *** KEYwords ***

    Correct code::

        *** SETTINGS ***
        *** Keywords ***

    """

    name = "section-name-invalid"
    rule_id = "NAME06"
    message = "Section name should be in format '{section_title_case}' or '{section_upper_case}'"  # TODO: rename
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"


class NotCapitalizedTestCaseTitleRule(Rule):
    """
    Test case title does not start with capital letter.

    Incorrect code example::

        *** Test Cases ***
        validate user details

    Correct code example::

        *** Test Cases ***
        Validate user details

    """

    name = "not-capitalized-test-case-title"
    rule_id = "NAME07"
    message = "Test case '{test_name}' title does not start with capital letter"
    severity = RuleSeverity.WARNING
    added_in_version = "1.4.0"


class SectionVariableNotUppercaseRule(Rule):
    """
    Section variable name is not uppercase.

    Incorrect code example::

        *** Variables ***
        ${section_variable}    value

    Correct code::

        *** Variables ***
        ${SECTION_VARIABLE}    value

    """

    name = "section-variable-not-uppercase"
    rule_id = "NAME08"
    message = "Section variable '{variable_name}' name is not uppercase"
    severity = RuleSeverity.WARNING
    added_in_version = "1.4.0"
    style_guide_ref = ["#variables-section", "#variable-scope-and-casing"]


class ElseNotUpperCaseRule(Rule):
    """
    ELSE and ELSE IF is not uppercase.

    Incorrect code example::

        *** Keywords ***
        Describe Temperature
            [Arguments]     ${degrees}
            If         ${degrees} > ${30}
                RETURN  Hot
            else if    ${degrees} > ${15}
                RETURN  Warm
            Else
                RETURN  Cold

    Correct code::

        *** Keywords ***
        Describe Temperature
            [Arguments]     ${degrees}
            IF         ${degrees} > ${30}
                RETURN  Hot
            ELSE IF    ${degrees} > ${15}
                RETURN  Warm
            ELSE
                RETURN  Cold

    """

    name = "else-not-upper-case"
    rule_id = "NAME09"
    message = "ELSE and ELSE IF is not uppercase"
    severity = RuleSeverity.ERROR
    added_in_version = "1.5.0"


class KeywordNameIsEmptyRule(Rule):
    """
    Keyword name is empty.

    Remember to always add a keyword name and avoid such code::

        *** Keywords ***
        # no keyword name here!!!
            Log To Console  hi

    """

    name = "keyword-name-is-empty"
    rule_id = "NAME10"
    message = "Keyword name is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.8.0"


class TestCaseNameIsEmptyRule(Rule):
    """
    Test case name is empty.

    Remember to always add a test case name and avoid such code::

        *** Test Cases ***
        # no test case name here!!!
            Log To Console  hello

    """

    name = "test-case-name-is-empty"
    rule_id = "NAME11"
    message = "Test case name is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.8.0"


class EmptyLibraryAliasRule(Rule):
    """
    Library alias is empty.

    Use non-empty name when using library import with alias.

    Incorrect code example::

         *** Settings ***
         Library  CustomLibrary  AS

    Correct code::

        *** Settings ***
        Library  CustomLibrary  AS  AnotherName

    """

    name = "empty-library-alias"
    rule_id = "NAME12"
    message = "Library alias is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.10.0"


class DuplicatedLibraryAliasRule(Rule):
    """
    Library alias is the same as original name.

    Examples of rule violation::

         *** Settings ***
         Library  CustomLibrary  AS  CustomLibrary   # same as library name
         Library  CustomLibrary  AS  Custom Library  # same as library name (spaces are ignored)

    """

    name = "duplicated-library-alias"
    rule_id = "NAME13"
    message = "Library alias is the same as original name"
    severity = RuleSeverity.WARNING
    added_in_version = "1.10.0"


class BddWithoutKeywordCallRule(Rule):
    """
    BDD keyword not followed by any keyword.

    When using BDD reserved keywords (such as `GIVEN`, `WHEN`, `AND`, `BUT` or `THEN`) use them together with
    name of the keyword to run.

    Incorrect code example::

        *** Test Cases ***
        Test case
            Given
            When User Log In
            Then User Should See Welcome Page

    Correct code::

        *** Test Cases ***
        Test case
            Given Setup Is Complete
            When User Log In
            Then User Should See Welcome Page

    Since those words are used for BDD style, it's also recommended not to use them within the user keyword name.

    """

    name = "bdd-without-keyword-call"
    rule_id = "NAME14"
    message = "BDD reserved keyword '{keyword_name}' not followed by any keyword{error_msg}"
    severity = RuleSeverity.WARNING
    added_in_version = "1.11.0"


class NotAllowedCharInFilenameRule(Rule):
    r"""
    Not allowed character found in filename.

    Reports not allowed pattern found in Suite names. By default, it's a dot (`.`).
    You can configure what characters are reported by running::

         robocop check --configure not-allowed-char-in-filename.pattern=regex_pattern .

    where ``regex_pattern`` should define regex pattern for characters not allowed in names. For example `[@\[]`
    pattern would report any occurrence of ``@[`` characters.

    """

    name = "not-allowed-char-in-filename"
    rule_id = "NAME15"
    message = "Not allowed character '{character}' found in {block_name} name"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="pattern",
            default=re.compile(r"[\.\?]"),
            converter=pattern_type,
            show_type="regex",
            desc="pattern defining characters (not) allowed in a name",
        ),
    ]
    added_in_version = "2.1.0"


class InvalidSectionRule(Rule):
    """
    Invalid section found.

    Robot Framework 6.1 detects unrecognized sections based on the language defined for the specific files.
    Consider using ``--language`` parameter if the file is defined with different language.

    It is also possible to configure language in the file::

        language: pl

        *** Przypadki Testowe ***
        Wypisz dyrektywę 4
            Log   Błąd dostępu

    """

    name = "invalid-section"
    rule_id = "NAME16"
    message = "Invalid section '{invalid_section}'"
    severity = RuleSeverity.ERROR
    version = ">=6.1"
    added_in_version = "3.2.0"


class MixedTaskTestSettingsRule(Rule):
    """
    Task related setting used with ``*** Test Cases ***`` or Test related setting used with ``*** Tasks ***`` section.

    If ``*** Tasks ***`` section is present in the file, use task-related settings like ``Task Setup``,
    ``Task Teardown``, ``Task Template``, ``Task Tags`` and ``Task Timeout`` instead of their `Test` variants.

    Similarly, use test-related settings when using ``*** Test Cases ***`` section.

    """

    name = "mixed-task-test-settings"
    rule_id = "NAME17"
    message = "Use {task_or_test}-related setting '{setting}' if {tasks_or_tests} section is used"  # TODO: Rename
    severity = RuleSeverity.WARNING
    added_in_version = "3.3.0"


SET_VARIABLE_VARIANTS = {
    "settaskvariable",
    "settestvariable",
    "setsuitevariable",
    "setglobalvariable",
}


class InvalidCharactersInNameChecker(VisitorChecker):
    """Checker for invalid characters in suite, test case or keyword name."""

    not_allowed_char_in_filename: NotAllowedCharInFilenameRule
    not_allowed_char_in_name: NotAllowedCharInNameRule

    def visit_File(self, node) -> None:  # noqa: N802
        source = node.source if node.source else self.source
        if source:
            suite_name = Path(source).stem
            if "__init__" in suite_name:
                suite_name = Path(source).parent.name
            for match in self.not_allowed_char_in_filename.pattern.finditer(suite_name):
                self.report(
                    self.not_allowed_char_in_filename,
                    character=match.group(),
                    block_name="suite",
                    node=node,
                    col=node.col_offset + match.start(0) + 1,
                )
        super().visit_File(node)

    def check_if_pattern_in_node_name(self, node, name_of_node, is_keyword=False) -> None:
        """
        Search if regex pattern found from node name.
        Skips embedded variables from keyword name
        """
        node_name = node.name
        robot_vars = find_robot_vars(node_name) if is_keyword else []
        start_pos = 0
        for variable in robot_vars:
            # Loop and skip variables:
            # Search pattern from start_pos to variable starting position
            # example `Keyword With ${em.bedded} Two ${second.Argument} Argument`
            # is split to:
            #   1. `Keyword With `
            #   2. ` Two `
            #   3. ` Argument` - last part is searched in finditer part after this loop
            tmp_node_name = node_name[start_pos : variable[0]]
            match = self.not_allowed_char_in_name.pattern.search(tmp_node_name)
            if match:
                self.report(
                    self.not_allowed_char_in_name,
                    character=match.group(),
                    block_name=f"'{node_name}' {name_of_node}",
                    node=node,
                    col=node.col_offset + match.start(0) + 1,
                    end_col=node.col_offset + match.end(0) + 1,
                )
            start_pos = variable[1]

        for not_allowed_char in self.not_allowed_char_in_name.pattern.finditer(node_name, start_pos):
            self.report(
                self.not_allowed_char_in_name,
                character=not_allowed_char.group(),
                block_name=f"'{node.name}' {name_of_node}",
                node=node,
                col=node.col_offset + not_allowed_char.start(0) + 1,
                end_col=node.col_offset + not_allowed_char.end(0) + 1,
            )

    def visit_TestCaseName(self, node) -> None:  # noqa: N802
        self.check_if_pattern_in_node_name(node, "test case")

    def visit_KeywordName(self, node) -> None:  # noqa: N802
        self.check_if_pattern_in_node_name(node, "keyword", is_keyword=True)


def uppercase_error_msg(name) -> str:
    return f". It must be in uppercase ({name.upper()}) when used as a statement"


class KeywordNamingChecker(VisitorChecker):
    """Checker for keyword naming violations."""

    wrong_case_in_keyword_name: WrongCaseInKeywordNameRule
    keyword_name_is_reserved_word: KeywordNameIsReservedWordRule
    underscore_in_keyword_name: UnderscoreInKeywordNameRule
    else_not_upper_case: ElseNotUpperCaseRule
    keyword_name_is_empty: KeywordNameIsEmptyRule
    bdd_without_keyword_call: BddWithoutKeywordCallRule

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

    def check_keyword_naming_with_subkeywords(self, node, name_token_type) -> None:
        for keyword in iterate_keyword_names(node, name_token_type):
            self.check_keyword_naming(keyword.value, keyword)

    def visit_Setup(self, node) -> None:  # noqa: N802
        self.check_bdd_keywords(node.name, node)
        self.check_keyword_naming_with_subkeywords(node, Token.NAME)

    visit_TestTeardown = visit_SuiteTeardown = visit_Teardown = visit_TestSetup = visit_SuiteSetup = visit_Setup  # noqa: N815

    def visit_Template(self, node) -> None:  # noqa: N802
        if node.value:
            name_token = node.get_token(Token.NAME)
            self.check_keyword_naming(node.value, name_token)
        self.generic_visit(node)

    visit_TestTemplate = visit_Template  # noqa: N815

    def visit_Keyword(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.keyword_name_is_empty, node=node)
        else:
            self.check_keyword_naming(node.name, node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        if self.inside_if_block and node.keyword and node.keyword.lower() in self.else_statements:
            col = keyword_col(node)
            end_col = col + len(node.keyword)
            self.report(self.else_not_upper_case, node=node, col=col, end_col=end_col)
        self.check_keyword_naming_with_subkeywords(node, Token.KEYWORD)
        self.check_bdd_keywords(node.keyword, node)

    def visit_If(self, node) -> None:  # noqa: N802
        self.inside_if_block = True
        self.generic_visit(node)
        self.inside_if_block = False

    def check_keyword_naming(self, keyword_name, node) -> None:
        if not keyword_name or keyword_name.lstrip().startswith("#"):
            return
        if keyword_name == r"/":  # old for loop, / are interpreted as keywords
            return
        if self.check_if_keyword_is_reserved(keyword_name, node):
            return
        normalized = remove_robot_vars(keyword_name)
        normalized = self.wrong_case_in_keyword_name.pattern.sub("", normalized)
        normalized = normalized.split(".")[-1]  # remove any imports ie ExternalLib.SubLib.Log -> Log
        normalized = normalized.replace("'", "")  # replace ' apostrophes
        if "_" in normalized:
            self.report(
                self.underscore_in_keyword_name,
                keyword_name=keyword_name,
                node=node,
                col=node.col_offset + 1,
                end_col=node.end_col_offset + 1,
            )
        words = self.letter_pattern.sub(" ", normalized).split(" ")
        if self.wrong_case_in_keyword_name.convention == "first_word_capitalized":
            words = words[:1]
        if any(word[0].islower() for word in words if word):
            self.report(
                self.wrong_case_in_keyword_name,
                keyword_name=keyword_name,
                node=node,
                col=node.col_offset + 1,
                end_col=node.col_offset + len(keyword_name) + 1,
            )

    def check_bdd_keywords(self, keyword_name, node) -> None:
        if not keyword_name or keyword_name.lower() not in self.bdd:
            return
        arg = node.get_token(Token.ARGUMENT)
        suffix = f". Use one space between: '{keyword_name.title()} {arg.value}'" if arg else ""
        col = token_col(node, Token.NAME, Token.KEYWORD)
        end_col = col + len(keyword_name)
        self.report(
            self.bdd_without_keyword_call,
            keyword_name=keyword_name,
            error_msg=suffix,
            node=node,
            col=col,
            end_col=end_col,
        )

    def check_if_keyword_is_reserved(self, keyword_name, node) -> bool:
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
            self.keyword_name_is_reserved_word,
            keyword_name=keyword_name,
            error_msg=error_msg,
            node=node,
            col=node.col_offset + 1,
            end_col=node.end_col_offset + 1,
        )
        return True


class SettingsNamingChecker(VisitorChecker):
    """Checker for settings and sections naming violations."""

    setting_name_not_in_title_case: SettingNameNotInTitleCaseRule
    section_name_invalid: SectionNameInvalidRule
    empty_library_alias: EmptyLibraryAliasRule
    duplicated_library_alias: DuplicatedLibraryAliasRule
    invalid_section: InvalidSectionRule
    mixed_task_test_settings: MixedTaskTestSettingsRule

    ALIAS_TOKENS = [Token.WITH_NAME] if ROBOT_VERSION.major < 5 else ["WITH NAME", "AS"]
    # Separating alias values since RF 3 uses WITH_NAME instead of WITH NAME
    ALIAS_TOKENS_VALUES = ["WITH NAME"] if ROBOT_VERSION.major < 5 else ["WITH NAME", "AS"]

    def __init__(self):
        self.section_name_pattern = re.compile(r"\*\*\*\s.+\s\*\*\*")
        self.task_section: bool | None = None
        super().__init__()

    def visit_InvalidSection(self, node) -> None:  # noqa: N802
        name = node.header.data_tokens[0].value
        invalid_header = node.header.get_token(Token.INVALID_HEADER)
        if "Resource file with" in invalid_header.error:
            return
        if invalid_header:
            self.report(
                self.invalid_section,
                invalid_section=name,
                node=node,
                col=node.header.col_offset + 1,
                end_col=node.header.end_col_offset + 1,
            )

    def visit_SectionHeader(self, node) -> None:  # noqa: N802
        name = node.data_tokens[0].value
        if not self.section_name_pattern.match(name) or not (name.istitle() or name.isupper()):
            valid_name = f"*** {node.name.title()} ***"
            self.report(
                self.section_name_invalid,
                section_title_case=valid_name,
                section_upper_case=valid_name.upper(),
                node=node,
                end_col=node.col_offset + len(name) + 1,
            )

    def visit_File(self, node) -> None:  # noqa: N802
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

    def visit_Setup(self, node) -> None:  # noqa: N802
        self.check_setting_name(node.data_tokens[0].value, node)
        self.check_settings_consistency(node.data_tokens[0].value, node)

    visit_SuiteSetup = visit_TestSetup = visit_Teardown = visit_SuiteTeardown = visit_TestTeardown = (  # noqa: N815
        visit_TestTimeout  # noqa: N815
    ) = visit_TestTemplate = visit_TestTags = visit_ForceTags = visit_DefaultTags = visit_ResourceImport = (  # noqa: N815
        visit_VariablesImport  # noqa: N815
    ) = visit_Documentation = visit_Tags = visit_Timeout = visit_Template = visit_Arguments = visit_ReturnSetting = (  # noqa: N815
        visit_Return  # noqa: N815
    ) = visit_Setup

    def visit_LibraryImport(self, node) -> None:  # noqa: N802
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
                    col = arg.col_offset + 1
                    self.report(
                        self.empty_library_alias, node=arg, col=arg.col_offset + 1, end_col=col + len(arg.value)
                    )
        elif node.alias.replace(" ", "") == node.name.replace(" ", ""):  # New Name == NewName
            name_token = node.get_tokens(Token.NAME)[-1]
            self.report(
                self.duplicated_library_alias,
                node=name_token,
                col=name_token.col_offset + 1,
                end_col=name_token.end_col_offset + 1,
            )

    def check_setting_name(self, name, node) -> None:
        if not (name.istitle() or name.isupper()):
            col = node.tokens[0].end_col_offset if node.tokens[0].type == "SEPARATOR" else node.col_offset
            self.report(
                self.setting_name_not_in_title_case,
                setting_name=name,
                node=node,
                col=col + 1,
                end_col=col + len(name) + 1,
            )

    def check_settings_consistency(self, name: str, node) -> None:
        name_normalized = name.lower()
        # if there is no task/test section, determine by first setting in the file
        if self.task_section is None and ("test" in name_normalized or "task" in name_normalized):
            self.task_section = "task" in name_normalized
        if "test" in name_normalized and self.task_section:
            end_col = node.col_offset + 1 + len(name)
            self.report(
                self.mixed_task_test_settings,
                setting="Task " + name.split()[1],
                task_or_test="task",
                tasks_or_tests="Tasks",
                node=node,
                end_col=end_col,
            )
        elif "task" in name_normalized and not self.task_section:
            end_col = node.col_offset + 1 + len(name)
            self.report(
                self.mixed_task_test_settings,
                setting="Test " + name.split()[1],
                task_or_test="test",
                tasks_or_tests="Test Cases",
                node=node,
                end_col=end_col,
            )


class TestCaseNamingChecker(VisitorChecker):
    """Checker for test case naming violations."""

    not_capitalized_test_case_title: NotCapitalizedTestCaseTitleRule
    test_case_name_is_empty: TestCaseNameIsEmptyRule

    def visit_TestCase(self, node) -> None:  # noqa: N802
        if not node.name:
            self.report(self.test_case_name_is_empty, node=node)
        else:
            for c in node.name:
                if not c.isalpha():
                    continue
                if not c.isupper():
                    self.report(
                        self.not_capitalized_test_case_title,
                        test_name=node.name,
                        node=node,
                        end_col=node.col_offset + len(node.name) + 1,
                    )
                break


class VariableNamingChecker(VisitorChecker):
    """Checker for variable naming violations."""

    section_variable_not_uppercase: SectionVariableNotUppercaseRule
    non_local_variables_should_be_uppercase: variables.NonLocalVariablesShouldBeUppercaseRule
    hyphen_in_variable_name: variables.HyphenInVariableNameRule
    overwriting_reserved_variable: variables.OverwritingReservedVariableRule

    RESERVED_VARIABLES = {  # TODO could be part of the rule class
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

    def visit_Keyword(self, node) -> None:  # noqa: N802
        name_token = node.header.get_token(Token.KEYWORD_NAME)
        self.parse_embedded_arguments(name_token)
        self.generic_visit(node)

    def visit_Variable(self, node) -> None:  # noqa: N802
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
                self.section_variable_not_uppercase,
                variable_name=token.value.strip(),
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.col_offset + len(token.value) + 1,
            )
        self.check_for_reserved_naming_or_hyphen(token, "Variable")

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        for token in node.get_tokens(Token.ASSIGN):
            self.check_for_reserved_naming_or_hyphen(token, "Variable")
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

    def check_non_local_variable(self, variable_name: str, node, token) -> None:
        normalized_var_name = remove_nested_variables(variable_name)
        if not normalized_var_name:
            return
        # a variable as a keyword argument can contain lowercase nested variable
        # because the actual value of it may be uppercase
        if not normalized_var_name.isupper():
            self.report(
                self.non_local_variables_should_be_uppercase,
                node=node,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )

    def visit_Var(self, node) -> None:  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        variable = node.get_token(Token.VARIABLE)
        if not variable:
            return
        self.check_for_reserved_naming_or_hyphen(variable, "Variable")
        # TODO: Check supported syntax for variable, ie ${{var}}?
        if not _is_var_scope_local(node):
            self.check_non_local_variable(search_variable(variable.value).base, node, variable)

    def visit_If(self, node) -> None:  # noqa: N802
        for token in node.header.get_tokens(Token.ASSIGN):
            self.check_for_reserved_naming_or_hyphen(token, "Variable")
        self.generic_visit(node)

    def visit_Arguments(self, node) -> None:  # noqa: N802
        for arg in node.get_tokens(Token.ARGUMENT):
            self.check_for_reserved_naming_or_hyphen(arg, "Argument")

    def parse_embedded_arguments(self, name_token) -> None:
        """Store embedded arguments from keyword name. Ignore embedded variables patterns like (${var:pattern})."""
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    self.check_for_reserved_naming_or_hyphen(token, "Embedded argument", has_pattern=True)
        except VariableError:
            pass

    def check_for_reserved_naming_or_hyphen(self, token, var_or_arg, has_pattern=False) -> None:
        """Check if variable name is a reserved Robot Framework name or uses hyphen in the name."""
        variable_match = search_variable(token.value, ignore_errors=True)
        name = variable_match.base
        if has_pattern:
            name, *_ = name.split(":", maxsplit=1)  # var:pattern -> var
        if not name:
            return
        if "-" in name:
            self.report(
                self.hyphen_in_variable_name,
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
                self.overwriting_reserved_variable,
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

    possible_variable_overwriting: variables.PossibleVariableOverwritingRule
    inconsistent_variable_name: variables.InconsistentVariableNameRule

    def __init__(self):
        self.assigned_variables = defaultdict(list)
        self.parent_name = ""
        self.parent_type = ""
        super().__init__()

    def visit_Keyword(self, node) -> None:  # noqa: N802
        self.assigned_variables = defaultdict(list)
        self.parent_name = node.name
        self.parent_type = type(node).__name__
        name_token = node.header.get_token(Token.KEYWORD_NAME)
        self.parse_embedded_arguments(name_token)
        self.visit_vars_and_find_similar(node)
        self.generic_visit(node)

    def visit_TestCase(self, node) -> None:  # noqa: N802
        self.assigned_variables = defaultdict(list)
        self.parent_name = node.name
        self.parent_type = type(node).__name__
        self.generic_visit(node)

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
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

    def visit_Var(self, node) -> None:  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(arg, arg.value, is_var=False)
        variable = node.get_token(Token.VARIABLE)
        if variable:
            self.find_similar_variables([variable], node, ignore_overwriting=not _is_var_scope_local(node))

    def visit_If(self, node) -> None:  # noqa: N802
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

    def visit_For(self, node) -> None:  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token, token.value, is_var=False)
        for var in self.for_assign_vars(node):
            self.assigned_variables[normalize_robot_var_name(var)].append(var)
        self.generic_visit(node)

    visit_ForLoop = visit_For  # noqa: N815

    def visit_Return(self, node) -> None:  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token, token.value, is_var=False)

    visit_ReturnStatement = visit_Teardown = visit_Timeout = visit_Return  # noqa: N815

    def parse_embedded_arguments(self, name_token) -> None:
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

    def check_inconsistent_naming(self, token, value: str, offset: int) -> None:
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
                self.inconsistent_variable_name,
                name=name,
                first_use=latest_assign,
                node=token,
                lineno=token.lineno,
                col=token.col_offset + offset + 1,
                end_col=token.col_offset + offset + len(name) + 1,
            )

    def find_not_nested_variable(self, token, value, is_var: bool, offset: int = 0) -> None:
        r"""
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

    def visit_vars_and_find_similar(self, node) -> None:
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

    def find_similar_variables(self, tokens, node, ignore_overwriting: bool = False) -> None:
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
                    self.possible_variable_overwriting,
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

    deprecated_statement: deprecated.DeprecatedStatementRule
    deprecated_with_name: deprecated.DeprecatedWithNameRule
    deprecated_singular_header: deprecated.DeprecatedSingularHeaderRule
    replace_set_variable_with_var: deprecated.ReplaceSetVariableWithVarRule
    replace_create_with_var: deprecated.ReplaceCreateWithVarRule

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

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        self.check_if_keyword_is_deprecated(node.keyword, node)
        self.check_keyword_can_be_replaced_with_var(node.keyword, node)

    def visit_SuiteSetup(self, node) -> None:  # noqa: N802
        self.check_if_keyword_is_deprecated(node.name, node)

    visit_TestSetup = visit_Setup = visit_SuiteTeardown = visit_TestTeardown = visit_Teardown = visit_SuiteSetup  # noqa: N815

    def visit_Template(self, node) -> None:  # noqa: N802
        if not node.value:
            return
        self.check_if_keyword_is_deprecated(node.value, node)

    visit_TestTemplate = visit_Template  # noqa: N815

    def visit_Return(self, node) -> None:  # noqa: N802
        """For RETURN use visit_ReturnStatement - visit_Return will most likely visit RETURN in the future"""
        if ROBOT_VERSION.major not in (5, 6):
            return
        self.check_deprecated_return(node)

    def visit_ReturnSetting(self, node) -> None:  # noqa: N802
        self.check_deprecated_return(node)

    def check_deprecated_return(self, node) -> None:
        self.report(
            self.deprecated_statement,
            statement_name="[Return]",
            alternative="RETURN",
            node=node,
            col=token_col(node, Token.RETURN),
            end_col=node.end_col_offset,
            version="5.*",
        )

    def visit_ForceTags(self, node) -> None:  # noqa: N802
        if ROBOT_VERSION.major < 6:
            return
        setting_name = node.data_tokens[0].value.lower()
        if setting_name == "force tags":
            self.report(
                self.deprecated_statement,
                statement_name="Force Tags",
                alternative="Test Tags",
                node=node,
                col=token_col(node, Token.FORCE_TAGS),
                end_col=node.col_offset + len(setting_name) + 1,
                version="6.0",
            )

    def check_if_keyword_is_deprecated(self, keyword_name, node) -> None:
        normalized_keyword_name = normalize_robot_name(keyword_name, remove_prefix="builtin.")
        if normalized_keyword_name not in self.deprecated_keywords:
            return
        version, alternative = self.deprecated_keywords[normalized_keyword_name]
        if version > ROBOT_VERSION.major:
            return
        col = token_col(node, Token.NAME, Token.KEYWORD)
        self.report(
            self.deprecated_statement,
            statement_name=keyword_name,
            alternative=alternative,
            node=node,
            col=col,
            end_col=col + len(keyword_name),
            version=f"{version}.*",
        )

    def check_keyword_can_be_replaced_with_var(self, keyword_name, node) -> None:
        if ROBOT_VERSION.major < 7:
            return
        normalized = normalize_robot_name(keyword_name, remove_prefix="builtin.")
        col = token_col(node, Token.NAME, Token.KEYWORD)
        if normalized in self.set_variable_keywords:
            self.report(
                self.replace_set_variable_with_var,
                set_variable_keyword=keyword_name,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )
        elif normalized in self.create_keywords:
            self.report(
                self.replace_create_with_var,
                create_keyword=keyword_name,
                node=node,
                col=col,
                end_col=col + len(keyword_name),
            )

    def visit_LibraryImport(self, node) -> None:  # noqa: N802
        if ROBOT_VERSION.major < 5 or (ROBOT_VERSION.major == 5 and ROBOT_VERSION.minor == 0):
            return
        with_name_token = node.get_token(Token.WITH_NAME)
        if not with_name_token or with_name_token.value == "AS":
            return
        self.report(
            self.deprecated_with_name,
            node=with_name_token,
            col=with_name_token.col_offset + 1,
            end_col=with_name_token.end_col_offset + 1,
        )

    def visit_SectionHeader(self, node) -> None:  # noqa: N802
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
            self.deprecated_singular_header,
            singular_header=f"*** {node.name} ***",
            plural_header=f"*** {node.name}s ***",
            node=header_node,
            col=header_node.col_offset + 1,
            end_col=header_node.end_col_offset + 1,
        )
