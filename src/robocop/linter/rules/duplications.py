"""Duplications checkers"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from robocop.linter import sonar_qube
from robocop.linter.fix import FixAvailability, remove_statement_fix
from robocop.linter.rules import FixableRule, Rule, RuleSeverity

if TYPE_CHECKING:
    from robot.parsing.model.statements import (
        Node,
        SectionHeader,
    )

    from robocop.linter.diagnostics import Diagnostic
    from robocop.linter.fix import Fix

NodeT = TypeVar("NodeT", bound="Node")


class DuplicatedImportRule(FixableRule):
    """
    Base class for the rules reporting the same import used more than once.

    The fix removes the duplicated import. Only imports that are exactly the same (including the arguments and
    the alias) are reported, so removing them does not change the behaviour. Comments are not removed.
    """

    fix_availability = FixAvailability.ALWAYS

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Remove the duplicated import."""
        if diag.node is None:
            return None
        return remove_statement_fix(self, diag.node, source_lines, "Remove the duplicated import")


class DuplicatedTestCaseRule(Rule):
    """
    Multiple test cases with the same name in the suite.

    It is not allowed to reuse the same name of the test case within the same suite in Robot Framework.
    Name matching is case-insensitive and ignores spaces and underscore characters.

    Incorrect code example:

        *** Test Cases ***
        Test with name
            No Operation

        test_with Name
            No Operation

    """

    name = "duplicated-test-case"
    rule_id = "DUP01"
    message = "Multiple test cases with name '{name}' (first occurrence in line {first_occurrence_line})"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0801",)


class DuplicatedKeywordRule(Rule):
    """
    Multiple keywords with the same name in the file.

    Do not define keywords with the same name inside the same file. Name matching is case-insensitive and
    ignores spaces and underscore characters.

    Incorrect code example:

        *** Keywords ***
        Keyword
            No Operation

        keyword
            No Operation

        K_eywor d
            No Operation

    """

    name = "duplicated-keyword"
    rule_id = "DUP02"
    message = "Multiple keywords with name '{name}' (first occurrence in line {first_occurrence_line})"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0802",)


class DuplicatedVariableRule(FixableRule):
    """
    Multiple variables with the same name in the file.

    Variable names in Robot Framework are case-insensitive and ignore spaces and underscores. Following variables
    are duplicates:

        *** Variables ***
        ${variable}    1
        ${VARIAble}    a
        @{variable}    a  b
        ${v ariabl e}  c
        ${v_ariable}   d

    Only the first definition is used by Robot Framework, so the duplicated definitions can be safely removed
    with the ``--fix`` option.

    """

    name = "duplicated-variable"
    rule_id = "DUP03"
    message = (
        "Multiple variables with name '{name}' in Variables section (first occurrence in line {first_occurrence_line})"
    )
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0803",)

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Remove the duplicated, and therefore ignored, variable definition."""
        if diag.node is None:
            return None
        return remove_statement_fix(self, diag.node, source_lines, "Remove the duplicated variable")


class DuplicatedResourceRule(DuplicatedImportRule):
    """
    Duplicated resource imports.

    Avoid re-importing the same imports.

    Incorrect code example:

        *** Settings ***
        Resource    path.resource
        Resource    other_path.resource
        Resource    path.resource

    The fix removes the duplicated import.

    """

    name = "duplicated-resource"
    rule_id = "DUP04"
    message = "Multiple resource imports with path '{name}' (first occurrence in line {first_occurrence_line})"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0804",)


class DuplicatedLibraryRule(DuplicatedImportRule):
    """
    Duplicated library imports.

    If you need to reimport library use alias:

        *** Settings ***
        Library  RobotLibrary
        Library  RobotLibrary  AS  OtherRobotLibrary

    The fix removes the duplicated import. Only imports with the same name, arguments and alias are reported.

    """

    name = "duplicated-library"
    rule_id = "DUP05"
    message = (
        "Multiple library imports with name '{name}' and identical arguments (first occurrence in line "
        "{first_occurrence_line})"
    )
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0805",)


class DuplicatedMetadataRule(Rule):
    """Duplicated metadata."""

    name = "duplicated-metadata"
    rule_id = "DUP06"
    message = "Duplicated metadata '{name}' (first occurrence in line {first_occurrence_line})"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0806",)


class DuplicatedVariablesImportRule(DuplicatedImportRule):
    """
    Duplicated variables import.

    The fix removes the duplicated import.
    """

    name = "duplicated-variables-import"
    rule_id = "DUP07"
    message = "Duplicated variables import with path '{name}' (first occurrence in line {first_occurrence_line})"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0807",)


class SectionAlreadyDefinedRule(Rule):
    """
    Section header already defined in the file.

    Duplicated section in the file. Robot Framework will handle repeated sections but it is recommended to not
    duplicate them.

    Incorrect code example:

        *** Test Cases ***
        My Test
            Keyword

        *** Keywords ***
        Keyword
            No Operation

        *** Test Cases ***  # duplicate
        Other Test
            Keyword

    """

    name = "section-already-defined"
    rule_id = "DUP08"
    message = (
        "'{section_name}' section header already defined in file (first occurrence in line {first_occurrence_line})"
    )
    severity = RuleSeverity.INFO
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0808",)

    def check(self, node: SectionHeader, first_occurrence_line: int | None) -> None:
        if not self.enabled or first_occurrence_line is None:
            return
        self.report(
            section_name=node.data_tokens[0].value,
            first_occurrence_line=first_occurrence_line,
            node=node,
            end_col=node.end_col_offset,
        )


class BothTestsAndTasksRule(Rule):
    """
    Both Task(s) and Test Case(s) section headers defined in file.

    The file contains both ``*** Test Cases ***`` and ``*** Tasks ***`` sections. Use only one of them. :

        *** Test Cases ***

        *** Tasks ***

    """

    name = "both-tests-and-tasks"
    rule_id = "DUP09"
    message = "Both Task(s) and Test Case(s) section headers defined in file"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0810",)

    def check(self, node: SectionHeader, other_kind_already_defined: bool) -> None:
        if not self.enabled or not other_kind_already_defined:
            return
        self.report(node=node, col=node.col_offset + 1, end_col=node.end_col_offset)


class DuplicatedSettingRule(Rule):
    """
    Duplicated setting.

    Some settings can be used only once in a file. Only the first value is used.

    Example:

        *** Settings ***
        Test Tags        F1
        Test Tags        F2  # this setting will be ignored

    """

    name = "duplicated-setting"
    rule_id = "DUP10"
    message = "{error_msg}"
    severity = RuleSeverity.WARNING
    added_in_version = "2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0813",)


class DuplicatedVariableInProjectRule(Rule):
    """
    Variable with the same name defined in multiple files visible together.

    Robot Framework does not report an error when the same variable is defined in a suite and in a resource file
    imported by it, or in two resource files imported by the same suite. The value used at runtime depends on the
    import order, which makes such duplications a common source of hard to debug problems.

    Example of rule violation:

        *** Settings ***
        Resource    variables.resource

        *** Variables ***
        ${BROWSER}    firefox  # variables.resource also defines ${BROWSER}

    Only variables defined in the ``*** Variables ***`` section are compared. Variable names are normalized, so
    ``${my var}``, ``${MY_VAR}`` and ``${myvar}`` are treated as the same variable.

    """

    name = "duplicated-variable-in-project"
    project_rule = True
    rule_id = "DUP11"
    message = "Variable '{name}' is also defined in '{first_source}' (line {first_occurrence_line})"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
