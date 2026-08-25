"""Naming checkers"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, Rule, RuleParam, RuleSeverity
from robocop.linter.utils import misc as utils
from robocop.parsing.string_operations import StringPart, get_unmasked_string, map_string_to_mask
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing import File
    from robot.parsing.model.blocks import InvalidSection, Keyword, TestCase
    from robot.parsing.model.statements import (
        KeywordCall,
        KeywordName,
        LibraryImport,
        Node,
        SectionHeader,
        TestCaseName,
    )

    from robocop.linter.diagnostics import Diagnostic

SECTION_NAME_PATTERN = re.compile(r"\*\*\*\s.+\s\*\*\*")
LETTER_PATTERN = re.compile(r"[^\w()-]|_", re.UNICODE)
ELSE_STATEMENTS = frozenset({"else", "else if"})
BDD_KEYWORDS = frozenset({"given", "when", "and", "but", "then"})
# reserved word followed by the RF version when it was introduced
RESERVED_WORDS = {
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


def normalize_keyword_name(keyword_name: str, pattern: re.Pattern[str], is_keyword_definition: bool) -> str:
    """Strip the parts of a keyword name that should not be taken into account when checking its case."""
    normalized = get_unmasked_string(keyword_name)
    normalized = pattern.sub("", normalized)
    if not is_keyword_definition and "." in normalized:
        # remove potential library import
        # Library.Keyword -> Keyword, Library.SubLibrary.Keyword -> Keyword
        # Library Space.Keyword -> Library Space.Keyword
        parts = normalized.split(".")
        for index, part in enumerate(parts):
            if " " in part:
                normalized = ".".join(parts[index:])
                break
        else:
            normalized = parts[-1]
    return normalized.replace("'", "")  # replace ' apostrophes


def report_wrong_case_in_keyword(rule: Rule, node: Node, keyword_name: str, normalized: str) -> None:
    words = LETTER_PATTERN.sub(" ", normalized).split(" ")
    if rule.convention == "first_word_capitalized":
        words = words[:1]
    if any(word[0].islower() for word in words if word):
        rule.report(
            keyword_name=keyword_name,
            node=node,
            col=node.col_offset + 1,
            end_col=node.col_offset + len(keyword_name) + 1,
        )


def capitalize_keyword_name(keyword_name: str, *, first_word_only: bool) -> str:
    """
    Capitalize the first letter of every word in the keyword name.

    Words are separated the same way as in the case convention check. Variables are not modified.
    With ``first_word_only`` only the first word of the name is capitalized.
    """
    capitalized: list[str] = []
    word_start = True
    first_word_done = False
    for part, part_type in map_string_to_mask(keyword_name):
        if part_type == StringPart.MASKED:
            capitalized.append(part)
            word_start = False
            continue
        for char in part:
            if LETTER_PATTERN.match(char):
                capitalized.append(char)
                word_start = True
                continue
            if word_start and not first_word_done:
                capitalized.append(char.upper())
                first_word_done = first_word_only
            else:
                capitalized.append(char)
            word_start = False
    return "".join(capitalized)


def keyword_name_start(keyword_name: str) -> int:
    """Return the index at which the keyword name starts, that is after the optional library name prefix."""
    if "." not in keyword_name:
        return 0
    parts = keyword_name.split(".")
    offset = 0
    for part in parts[:-1]:
        if " " in part:
            return offset
        offset += len(part) + 1
    return offset


def wrong_case_in_keyword_fix(
    rule: Rule, diag: Diagnostic, source_lines: list[str], *, is_keyword_call: bool
) -> Fix | None:
    """
    Create a fix that capitalizes the keyword name according to the configured convention.

    Keyword names are case-insensitive in Robot Framework, so renaming does not change the behaviour.
    Names matching the configured ``pattern`` are not fixed, since the pattern marks the words that are
    accepted as they are.
    """
    keyword_name = str(diag.reported_arguments["keyword_name"])
    if rule.pattern.pattern and rule.pattern.search(keyword_name):
        return None
    if diag.range.start.line != diag.range.end.line:
        return None
    line = source_lines[diag.range.start.line - 1]
    if line[diag.range.start.character - 1 : diag.range.end.character - 1] != keyword_name:
        return None
    start = keyword_name_start(keyword_name) if is_keyword_call else 0
    new_name = keyword_name[:start] + capitalize_keyword_name(
        keyword_name[start:], first_word_only=rule.convention == "first_word_capitalized"
    )
    if new_name == keyword_name:
        return None
    edit = TextEdit.replace_at_range(rule.rule_id, rule.name, diag.range, new_name)
    return Fix(
        edits=[edit],
        message=f"Rename '{keyword_name}' to '{new_name}'",
        applicability=FixApplicability.SAFE,
    )


# Separating alias values since RF 3 uses WITH_NAME instead of WITH NAME
ALIAS_TOKENS = [Token.WITH_NAME] if ROBOT_VERSION.major < 5 else ["WITH NAME", "AS"]
ALIAS_TOKENS_VALUES = ["WITH NAME"] if ROBOT_VERSION.major < 5 else ["WITH NAME", "AS"]
ALIAS_MARKER_PATTERN = re.compile(r"\s+(WITH NAME|AS)\s*$")


def remove_alias_fix(
    rule: Rule, diag: Diagnostic, source_lines: list[str], message: str, *, with_marker: bool
) -> Fix | None:
    """
    Create a fix removing the alias part of the library import.

    Everything from the end of the preceding value up to the end of the reported range is removed. With
    ``with_marker`` the alias marker (``AS`` or ``WITH NAME``) placed before the reported range is removed too.
    Imports with the alias split into multiple lines are not fixed.
    """
    reported_range = diag.range
    if reported_range.start.line != reported_range.end.line:
        return None
    line = source_lines[reported_range.start.line - 1]
    prefix = line[: reported_range.start.character - 1].rstrip()
    if with_marker:
        prefix, removed_marker = ALIAS_MARKER_PATTERN.subn("", prefix)
        if not removed_marker:  # the alias marker is placed in the previous line
            return None
    if prefix.strip() in ("", "..."):  # only the continuation mark would be left in the line
        return None
    replacement = prefix + line[reported_range.end.character - 1 :]
    return Fix(
        edits=[
            TextEdit.replace_lines(
                rule.rule_id, rule.name, reported_range.start.line, reported_range.start.line, replacement
            )
        ],
        message=message,
        applicability=FixApplicability.SAFE,
    )


def library_has_alias(node: LibraryImport) -> bool | None:
    """
    Determine whether a library import defines an alias.

    Returns ``None`` when the import should not be inspected at all: for RF < 6, ``AS`` passed as an argument is
    used to provide the library alias and is not reported.
    """
    if ROBOT_VERSION.major < 6:
        arg_nodes = node.get_tokens(Token.ARGUMENT)
        if arg_nodes and any(arg.value == "AS" for arg in arg_nodes):
            return None
        return bool(node.get_token(*ALIAS_TOKENS))
    return len(node.get_tokens(Token.NAME)) >= 2


class NotAllowedCharInNameRule(Rule):
    r"""
    Not allowed character found.

    Reports not allowed characters found in Test Case or Keyword names. By default, it's a dot (``.``). You can
    configure what patterns are reported by calling:

        robocop check --configure not-allowed-char-in-name.pattern=regex_pattern

    ``regex_pattern`` should define a regex pattern not allowed in names. For example, ``[@\[]`` pattern
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
            converter=utils.pattern_type,
            show_type="regex",
            desc="pattern defining characters (not) allowed in a name",
        )
    ]
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0301",)
    fix_suggestion = "Remove the not allowed character from the name."

    def check(self, node: TestCaseName | KeywordName, name_of_node: str, is_keyword: bool = False) -> None:
        """
        Search if regex pattern found from node name.

        Skips embedded variables from keyword name.
        """
        if not self.enabled:
            return
        node_name = node.name
        robot_vars = utils.find_robot_vars(node_name) if is_keyword else []
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
            match = self.pattern.search(tmp_node_name)
            if match:
                self.report(
                    character=match.group(),
                    block_name=f"'{node_name}' {name_of_node}",
                    node=node,
                    col=node.col_offset + match.start(0) + 1,
                    end_col=node.col_offset + match.end(0) + 1,
                )
            start_pos = variable[1]
        for not_allowed_char in self.pattern.finditer(node_name, start_pos):
            self.report(
                character=not_allowed_char.group(),
                block_name=f"'{node_name}' {name_of_node}",
                node=node,
                col=node.col_offset + not_allowed_char.start(0) + 1,
                end_col=node.col_offset + not_allowed_char.end(0) + 1,
            )


class WrongCaseInKeywordNameRule(FixableRule):
    r"""
    Keyword name does not follow case convention.

    Keyword names need to follow a specific case convention.
    The convention can be set using the `` convention `` parameter and accepts
    one of the 2 values: ``each_word_capitalized`` or ``first_word_capitalized``.

    By default, it's configured to ``each_word_capitalized``, which requires each keyword to follow such
    convention:

        *** Keywords ***
        Fill Out The Form
            Provide Shipping Address
            Provide Payment Method
            Click 'Next' Button
            [Teardown]  Log Form Data

    You can also set it to ``first_word_capitalized`` which requires capitalising the first word of the keyword:

        *** Keywords ***
        Fill out the form
            Provide shipping address
            Provide payment method
            Click 'Next' button
            [Teardown]  Log form data

    The rule also accepts another parameter ``pattern`` which can be used to configure words
    that are accepted in the keyword name, even though they violate the case convention.

    ``pattern`` parameter accepts a regex pattern. For example, configuring it to ``robocop\.readthedocs\.io``
    would make the following keyword legal:

        Go To robocop.readthedocs.io Page

    See the sibling rule [wrong-case-in-keyword-call](#name18-wrong-case-in-keyword-call) that checks keyword call
    naming convention.

    Keyword names are case-insensitive in Robot Framework, so the name can be capitalized automatically with the
    ``--fix`` option. Names matching the configured ``pattern`` are reported, but not fixed.
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
            converter=utils.pattern_type,
            show_type="regex",
            desc="pattern for accepted words in keyword",
        ),
    ]
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0302",)
    fix_suggestion = "Rename the keyword to use Title Case (e.g., 'My Keyword Name')."
    fix_availability = FixAvailability.SOMETIMES

    def check(self, node: Node, keyword_name: str, normalized: str) -> None:
        report_wrong_case_in_keyword(self, node, keyword_name, normalized)

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Capitalize the keyword name according to the configured convention."""
        return wrong_case_in_keyword_fix(self, diag, source_lines, is_keyword_call=False)


class KeywordNameIsReservedWordRule(Rule):
    """
    Keyword name is a reserved word.

    Do not use reserved names for keyword names. The following names are reserved:

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
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0303",)
    fix_suggestion = "Rename the keyword to avoid using a reserved word."

    def check(self, node: Node, keyword_name: str, inside_if_block: bool) -> bool:
        """
        Report a keyword name that is a reserved Robot Framework word.

        Returns whether the name is reserved. The other keyword naming rules are skipped in that case, so the
        result must not depend on whether this rule is enabled.
        """
        lower_name = keyword_name.lower()
        if lower_name not in RESERVED_WORDS:
            return False
        if lower_name in ELSE_STATEMENTS and inside_if_block:
            return False  # handled by else-not-upper-case
        if ROBOT_VERSION.major < RESERVED_WORDS[lower_name]:
            return False
        self.report(
            keyword_name=keyword_name,
            error_msg=uppercase_error_msg(lower_name),
            node=node,
            col=node.col_offset + 1,
            end_col=node.col_offset + 1 + len(keyword_name),
        )
        return True


class UnderscoreInKeywordNameRule(Rule):
    """
    Underscores in keyword name.

    You can replace underscores with spaces.

    Incorrect code example:

        keyword_with_underscores

    Correct code:

        Keyword Without Underscores

    """

    name = "underscore-in-keyword-name"
    rule_id = "NAME04"
    message = "Underscores in keyword name '{keyword_name}'"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0305",)
    fix_suggestion = "Replace underscores with spaces (e.g., 'My Keyword' instead of 'My_Keyword')."

    def check(self, node: Node, keyword_name: str, normalized: str) -> None:
        if "_" not in normalized:
            return
        self.report(
            keyword_name=keyword_name,
            node=node,
            col=node.col_offset + 1,
            end_col=node.col_offset + len(keyword_name.rstrip()) + 1,
        )


class SettingNameNotInTitleCaseRule(FixableRule):
    """
    Setting name not in the title or upper case.

    Incorrect code example:

        *** Settings ***
        resource    file.resource

        *** Test Cases ***
        Test
            [documentation]  Some documentation
            Step

    Correct code:

        *** Settings ***
        Resource    file.resource

        *** Test Cases ***
        Test
            [DOCUMENTATION]  Some documentation
            Step

    The setting name can be converted to the title case automatically with the ``--fix`` option.
    Use the ``NormalizeSettingName`` formatter (``robocop format``) if you also want to normalize
    the whitespace inside the setting name.

    """

    name = "setting-name-not-in-title-case"
    rule_id = "NAME05"
    message = "Setting name '{setting_name}' not in title or uppercase"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0306",)

    def check(self, node: Node, name: str) -> None:
        if name.istitle() or name.isupper():
            return
        col = node.tokens[0].end_col_offset if node.tokens[0].type == "SEPARATOR" else node.col_offset
        self.report(
            setting_name=name,
            node=node,
            col=col + 1,
            end_col=col + len(name) + 1,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        """Replace the setting name with its title case version."""
        setting_name = str(diag.reported_arguments["setting_name"])
        edit = TextEdit.replace_at_range(self.rule_id, self.name, diag.range, setting_name.title())
        return Fix(
            edits=[edit],
            message=f"Replace '{setting_name}' with '{setting_name.title()}'",
            applicability=FixApplicability.SAFE,
        )


class SectionNameInvalidRule(FixableRule):
    """
    Section name does not follow convention.

    Section name should use Title Case or CAP CASE case convention.

    Incorrect code example:

        *** settings ***
        *** KEYwords ***

    Correct code:

        *** SETTINGS ***
        *** Keywords ***

    The section name can be replaced with its title case version automatically with the ``--fix`` option.

    """

    name = "section-name-invalid"
    rule_id = "NAME06"
    message = "Section name should be in format '{section_title_case}' or '{section_upper_case}'"  # TODO: rename
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0307",)

    def check(self, node: SectionHeader) -> None:
        name = node.data_tokens[0].value
        if SECTION_NAME_PATTERN.match(name) and (name.istitle() or name.isupper()):
            return
        valid_name = f"*** {node.name.title()} ***"
        self.report(
            section_title_case=valid_name,
            section_upper_case=valid_name.upper(),
            node=node,
            end_col=node.col_offset + len(name) + 1,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        """Replace the section header with its title case version."""
        valid_name = str(diag.reported_arguments["section_title_case"])
        edit = TextEdit.replace_at_range(self.rule_id, self.name, diag.range, valid_name)
        return Fix(
            edits=[edit], message=f"Replace the section header with '{valid_name}'", applicability=FixApplicability.SAFE
        )


class NotCapitalizedTestCaseTitleRule(Rule):
    """
    Test case title does not start with a capital letter.

    Incorrect code example:

        *** Test Cases ***
        validate user details

    Correct code example:

        *** Test Cases ***
        Validate user details

    """

    name = "not-capitalized-test-case-title"
    rule_id = "NAME07"
    message = "Test case '{test_name}' title does not start with capital letter"
    severity = RuleSeverity.WARNING
    added_in_version = "1.4.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0308",)

    def check(self, node: TestCase) -> None:
        if not self.enabled:
            return
        for char in node.name:
            if not char.isalpha():
                continue
            if not char.isupper():
                self.report(
                    test_name=node.name,
                    node=node,
                    end_col=node.col_offset + len(node.name) + 1,
                )
            break


class SectionVariableNotUppercaseRule(Rule):
    """
    Section variable name is not uppercase.

    Incorrect code example:

        *** Variables ***
        ${section_variable}    value

    Correct code:

        *** Variables ***
        ${SECTION_VARIABLE}    value

    """

    name = "section-variable-not-uppercase"
    rule_id = "NAME08"
    message = "Section variable '{variable_name}' name is not uppercase"
    severity = RuleSeverity.WARNING
    added_in_version = "1.4.0"
    style_guide_ref = ["#variables-section", "#variable-scope-and-casing"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0309",)

    def check(self, token: Token, var_name: str) -> None:
        # in Variables section, everything needs to be in uppercase
        # because even when the variable is nested, it needs to be global
        if var_name.isupper():
            return
        self.report(
            variable_name=token.value.strip(),
            lineno=token.lineno,
            col=token.col_offset + 1,
            end_col=token.col_offset + len(token.value) + 1,
        )


class ElseNotUpperCaseRule(FixableRule):
    """
    ELSE and ELSE IF is not uppercase.

    Incorrect code example:

        *** Keywords ***
        Describe Temperature
            [Arguments]     ${degrees}
            If         ${degrees} > ${30}
                RETURN  Hot
            else if    ${degrees} > ${15}
                RETURN  Warm
            Else
                RETURN  Cold

    Correct code:

        *** Keywords ***
        Describe Temperature
            [Arguments]     ${degrees}
            IF         ${degrees} > ${30}
                RETURN  Hot
            ELSE IF    ${degrees} > ${15}
                RETURN  Warm
            ELSE
                RETURN  Cold

    The fix replaces the ``ELSE`` and ``ELSE IF`` names with their uppercase versions.

    """

    name = "else-not-upper-case"
    rule_id = "NAME09"
    message = "ELSE and ELSE IF is not uppercase"
    severity = RuleSeverity.ERROR
    added_in_version = "1.5.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0311",)
    fix_availability = FixAvailability.ALWAYS

    def check(self, node: KeywordCall) -> None:
        if not node.keyword or node.keyword.lower() not in ELSE_STATEMENTS:
            return
        col = utils.keyword_col(node)
        self.report(node=node, col=col, end_col=col + len(node.keyword))

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Replace the ELSE or ELSE IF name with its uppercase version."""
        line = source_lines[diag.range.start.line - 1]
        name = line[diag.range.start.character - 1 : diag.range.end.character - 1]
        if not name or name.isupper():
            return None
        edit = TextEdit.replace_at_range(self.rule_id, self.name, diag.range, name.upper())
        return Fix(
            edits=[edit],
            message=f"Replace '{name}' with '{name.upper()}'",
            applicability=FixApplicability.SAFE,
        )


class KeywordNameIsEmptyRule(Rule):
    """
    Keyword name is empty.

    Remember to always add a keyword name and avoid such code:

        *** Keywords ***
        # no keyword name here!!!
            Log To Console  hi

    """

    name = "keyword-name-is-empty"
    rule_id = "NAME10"
    message = "Keyword name is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.8.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0312",)

    def check(self, node: Keyword) -> None:
        if not node.name:
            self.report(node=node)


class TestCaseNameIsEmptyRule(Rule):
    """
    Test case name is empty.

    Remember to always add a test case name and avoid such code:

        *** Test Cases ***
        # no test case name here!!!
            Log To Console  hello

    """

    name = "test-case-name-is-empty"
    rule_id = "NAME11"
    message = "Test case name is empty"
    severity = RuleSeverity.ERROR
    added_in_version = "1.8.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0313",)

    def check(self, node: TestCase) -> None:
        if not self.enabled:
            return
        self.report(node=node)


class EmptyLibraryAliasRule(FixableRule):
    """
    Library alias is empty.

    Use a non-empty name when using library import with alias.

    Incorrect code example:

         *** Settings ***
         Library  CustomLibrary  AS

    Correct code:

        *** Settings ***
        Library  CustomLibrary  AS  AnotherName

    The fix removes the alias marker without the name. Imports with the alias split into multiple lines
    are not fixed.

    """

    name = "empty-library-alias"
    rule_id = "NAME12"
    message = "Library alias is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.10.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0314",)
    fix_availability = FixAvailability.SOMETIMES

    def check(self, node: LibraryImport) -> None:
        if library_has_alias(node) is not False:
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            if arg.value and arg.value in ALIAS_TOKENS_VALUES:
                col = arg.col_offset + 1
                self.report(node=arg, col=col, end_col=col + len(arg.value))

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Remove the alias marker that is not followed by the alias name."""
        return remove_alias_fix(self, diag, source_lines, "Remove the empty library alias", with_marker=False)


class DuplicatedLibraryAliasRule(FixableRule):
    """
    Library alias is the same as the original name.

    Examples of rule violation:

         *** Settings ***
         Library  CustomLibrary  AS  CustomLibrary   # same as library name
         Library  CustomLibrary  AS  Custom Library  # same as library name (spaces are ignored)

    The fix removes the redundant alias. Imports with the alias split into multiple lines are not fixed.

    """

    name = "duplicated-library-alias"
    rule_id = "NAME13"
    message = "Library alias is the same as original name"
    severity = RuleSeverity.WARNING
    added_in_version = "1.10.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0315",)
    fix_availability = FixAvailability.SOMETIMES

    def check(self, node: LibraryImport) -> None:
        if library_has_alias(node) is not True:
            return
        if node.alias.replace(" ", "") != node.name.replace(" ", ""):  # New Name == NewName
            return
        name_token = node.get_tokens(Token.NAME)[-1]
        self.report(node=name_token, col=name_token.col_offset + 1, end_col=name_token.end_col_offset + 1)

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Remove the alias that is the same as the library name."""
        return remove_alias_fix(self, diag, source_lines, "Remove the duplicated library alias", with_marker=True)


class BddWithoutKeywordCallRule(Rule):
    """
    BDD keyword isn't followed by any keyword.

    When using BDD reserved keywords (such as `GIVEN`, `WHEN`, `AND`, `BUT` or `THEN`) use them together with
    the name of the keyword to run.

    Incorrect code example:

        *** Test Cases ***
        Test case
            Given
            When User Log In
            Then User Should See Welcome Page

    Correct code:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0318",)

    def check(self, keyword_name: str | None, node: Node) -> None:
        if not keyword_name or keyword_name.lower() not in BDD_KEYWORDS:
            return
        arg = node.get_token(Token.ARGUMENT)
        suffix = f". Use one space between: '{keyword_name.title()} {arg.value}'" if arg else ""
        col = utils.token_col(node, Token.NAME, Token.KEYWORD)
        self.report(
            keyword_name=keyword_name,
            error_msg=suffix,
            node=node,
            col=col,
            end_col=col + len(keyword_name),
        )


class NotAllowedCharInFilenameRule(Rule):
    r"""
    Not allowed character found in filename.

    Reports not allowed pattern found in Suite names. By default, it's a dot (`.`).
    You can configure what characters are reported by running:

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
            converter=utils.pattern_type,
            show_type="regex",
            desc="pattern defining characters (not) allowed in a name",
        ),
    ]
    file_wide_rule = True
    added_in_version = "2.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0320",)

    def check(self, node: File, source_path: Path) -> None:
        if not self.enabled:
            return
        suite_name = source_path.stem
        if "__init__" in suite_name:
            suite_name = source_path.parent.name
        for match in self.pattern.finditer(suite_name):
            self.report(
                character=match.group(),
                block_name="suite",
                node=node,
                col=node.col_offset + match.start(0) + 1,
            )


class InvalidSectionRule(Rule):
    """
    Invalid section found.

    Robot Framework 6.1 detects unrecognized sections based on the language defined for the specific files.
    Consider using the `` -- language `` parameter if the file is defined with a different language.

    It is also possible to configure language in the file:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0325",)

    def check(self, node: InvalidSection) -> None:
        invalid_header = node.header.get_token(Token.INVALID_HEADER)
        if "Resource file with" in invalid_header.error:
            return
        if invalid_header:
            self.report(
                invalid_section=node.header.data_tokens[0].value,
                node=node,
                col=node.header.col_offset + 1,
                end_col=node.header.end_col_offset,
            )


class MixedTaskTestSettingsRule(Rule):
    """
    Task related setting used with ``*** Test Cases ***`` or Test related setting used with the `` *** Tasks ***``
    section.

    If the `` *** Tasks ***`` section is present in the file, use task-related settings like ``Task Setup``,
    ``Task Teardown``, ``Task Template``, ``Task Tags`` and ``Task Timeout`` instead of their `Test` variants.

    Similarly, use test-related settings when using the `` *** Test Cases ***`` section.

    """

    name = "mixed-task-test-settings"
    rule_id = "NAME17"
    message = "Use {task_or_test}-related setting '{setting}' if {tasks_or_tests} section is used"  # TODO: Rename
    severity = RuleSeverity.WARNING
    added_in_version = "3.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0326",)

    def check(self, node: Node, name: str, task_section: bool | None) -> None:
        name_normalized = name.lower()
        end_col = node.col_offset + 1 + len(name)
        if "test" in name_normalized and task_section:
            self.report(
                setting="Task " + name.split()[1],
                task_or_test="task",
                tasks_or_tests="Tasks",
                node=node,
                end_col=end_col,
            )
        elif "task" in name_normalized and not task_section:
            self.report(
                setting="Test " + name.split()[1],
                task_or_test="test",
                tasks_or_tests="Test Cases",
                node=node,
                end_col=end_col,
            )


class WrongCaseInKeywordCallRule(FixableRule):
    r"""
    Keyword call name does not follow case convention.

    Keyword names need to follow a specific case convention.
    The convention can be set using the `` convention `` parameter and accepts
    one of the 2 values: ``each_word_capitalized`` or ``first_word_capitalized``.

    By default, it's configured to ``each_word_capitalized``, which requires each keyword to follow such
    convention:

        *** Keywords ***
        Fill out the form
            Provide Shipping Address
            Provide Payment Method
            Click 'Next' Button
            [Teardown]  Log Form Data

    You can also set it to ``first_word_capitalized`` which requires capitalising the first word of the keyword:

        *** Keywords ***
        Fill out the form
            Provide shipping address
            Provide payment method
            Click 'Next' button
            [Teardown]  Log form data

    The rule also accepts another parameter ``pattern`` which can be used to configure words
    that are accepted in the keyword name, even though they violate the case convention.

    ``pattern`` parameter accepts a regex pattern. For example, configuring it to ``robocop\.readthedocs\.io``
    would make the following keyword legal:

        Go To robocop.readthedocs.io Page

    See the sibling rule [wrong-case-in-keyword-name](#name02-wrong-case-in-keyword-name) that checks keyword definition
    naming convention.

    Keyword names are case-insensitive in Robot Framework, so the name can be capitalized automatically with the
    ``--fix`` option. The optional library name prefix is not modified. Names matching the configured ``pattern``
    are reported, but not fixed.
    """

    name = "wrong-case-in-keyword-call"
    rule_id = "NAME18"
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
            converter=utils.pattern_type,
            show_type="regex",
            desc="pattern for accepted words in keyword",
        ),
    ]
    added_in_version = "7.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.IDENTIFIABLE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    fix_availability = FixAvailability.SOMETIMES

    def check(self, node: Node, keyword_name: str, normalized: str) -> None:
        report_wrong_case_in_keyword(self, node, keyword_name, normalized)

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Capitalize the keyword call name according to the configured convention."""
        return wrong_case_in_keyword_fix(self, diag, source_lines, is_keyword_call=True)


SET_VARIABLE_VARIANTS = {
    "settaskvariable",
    "settestvariable",
    "setsuitevariable",
    "setglobalvariable",
}


def uppercase_error_msg(name: str) -> str:
    return f". It must be in uppercase ({name.upper()}) when used as a statement"
