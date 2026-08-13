from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleSeverity

if TYPE_CHECKING:
    from robot.parsing.model.statements import LibraryImport, ResourceImport


class WrongImportOrderRule(Rule):
    """
    Built-in imports placed after custom imports.

    To make code more readable, it needs to be more consistent. That's why it is recommended to group known, built-in
    import before custom imports.

    Example of rule violation:

        *** Settings ***
        Library    Collections
        Library    CustomLibrary
        Library    OperatingSystem  # BuiltIn library defined after custom CustomLibrary

    """

    name = "wrong-import-order"
    rule_id = "IMP01"
    message = "BuiltIn library import '{builtin_import}' should be placed before '{custom_import}'"
    severity = RuleSeverity.WARNING
    added_in_version = "1.7.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0911",)

    def check(self, node: LibraryImport, custom_import: LibraryImport) -> None:
        lib_name = node.get_token(Token.NAME)
        self.report(
            builtin_import=node.name,
            custom_import=custom_import.name,
            node=node,
            col=lib_name.col_offset + 1,
            end_col=lib_name.end_col_offset + 1,
        )


class BuiltinImportsNotSortedRule(Rule):
    """
    Built-in imports are not sorted in alphabetical order.

    To increase readability, sort the imports in alphabetical order.

    Example of rule violation:

        *** Settings ***
        Library    OperatingSystem
        Library    Collections  # BuiltIn libraries imported not in alphabetical order

    """

    name = "builtin-imports-not-sorted"
    rule_id = "IMP02"
    message = "BuiltIn library import '{builtin_import}' should be placed before '{previous_builtin_import}'"
    severity = RuleSeverity.WARNING
    added_in_version = "5.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0926",)

    def check(self, node: LibraryImport, previous: LibraryImport | None) -> None:
        if not previous or node.name >= previous.name:
            return
        lib_name = node.get_token(Token.NAME)
        self.report(
            builtin_import=node.name,
            previous_builtin_import=previous.name,
            node=node,
            col=lib_name.col_offset + 1,
            end_col=lib_name.end_col_offset + 1,
        )


class NonBuiltinImportsNotSortedRule(Rule):
    """
    Custom imports are not sorted in alphabetical order.

    To increase readability, sort the imports in alphabetical order. Beware that depending on your code, some of the
    custom imports may be depending on each other and the order of the imports.

    Example of rule violation:

        *** Settings ***
        Library    Collections
        Library    CustomLibrary
        Library    AnotherCustomLibrary  # AnotherCustomLibrary library defined after custom CustomLibrary

    """

    name = "non-builtin-imports-not-sorted"
    rule_id = "IMP03"
    message = "Non builtin library import '{custom_import}' should be placed before '{previous_custom_import}'"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "5.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("10101",)

    def check(self, node: LibraryImport, previous: LibraryImport | None) -> None:
        if previous is None or node.name >= previous.name:
            return
        lib_name = node.get_token(Token.NAME)
        self.report(
            custom_import=node.name,
            previous_custom_import=previous.name,
            node=node,
            col=lib_name.col_offset + 1,
            end_col=lib_name.end_col_offset + 1,
        )


class ResourcesImportsNotSortedRule(Rule):
    """
    Resources imports are not sorted in alphabetical order.

    To increase readability, sort the resources imports in a alphabetical order. Beware that depending on your code,
    some imports may depend on each other and the order of the imports.

    Example of rule violation:

        *** Settings ***
        Resource   CustomResource.resource
        Resource   AnotherFile.resource

    """

    name = "resources-imports-not-sorted"
    rule_id = "IMP04"
    message = "Resource import '{resource_import}' should be placed before '{previous_resource_import}'"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "5.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("10102",)

    def check(self, node: ResourceImport, previous: ResourceImport | None) -> None:
        if previous is None or node.name >= previous.name:
            return
        resource_name = node.get_token(Token.NAME)
        self.report(
            resource_import=node.name,
            previous_resource_import=previous.name,
            node=node,
            col=resource_name.col_offset + 1,
            end_col=resource_name.end_col_offset + 1,
        )


class UnresolvedResourceImportRule(Rule):
    """
    Imported resource file does not exist.

    Reports resource imports that point to a file that cannot be found in the project. Such import makes the whole
    suite fail during the execution.

    Example of rule violation:

        *** Settings ***
        Resource    does_not_exist.resource  # file is not found next to the importing file

    Import paths are resolved relative to the file containing the import, exactly like Robot Framework does it.

    Variables used in the import path are resolved using variables defined in the ``*** Variables ***`` section
    of the importing file and variables provided with the ``--variable`` option::

        robocop check-project --variable RESOURCE_DIR:resources

    If the path contains a variable that cannot be resolved, the import is ignored and not reported. Thanks to that,
    dynamically built paths do not cause false positives.

    This rule is a project level rule and is only reported by the ``robocop check-project`` command.

    """

    name = "unresolved-resource-import"
    rule_id = "IMP07"
    message = "Imported resource file '{import_name}' does not exist"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "8.9.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class UnusedResourceImportRule(Rule):
    """
    Imported resource file is not used.

    Reports resource imports whose keywords and variables are never used in the importing file.

    Example of rule violation:

        *** Settings ***
        Resource    unused.resource  # nothing from this file is used

        *** Test Cases ***
        Test
            Keyword From Other Resource

    A resource is considered used when the file uses any keyword or variable defined in it, or in any resource it
    imports itself, since resource imports are transitive in Robot Framework.

    To avoid false positives, imports are not reported when:

    - the importing file calls a keyword using a name built from a variable, because such call may come from any
      resource,
    - the import path could not be resolved,
    - the imported resource defines no keywords and no variables, because it may be imported only for the imports
      it makes itself.

    This rule is a project level rule and is only reported by the ``robocop check-project`` command.

    """

    name = "unused-resource-import"
    rule_id = "IMP05"
    message = "Imported resource file '{import_name}' is not used"
    severity = RuleSeverity.INFO
    enabled = False
    added_in_version = "8.9.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
