from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.libraries import STDLIBS

from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker

if TYPE_CHECKING:
    from robot.parsing.model import Statement


class WrongImportOrderRule(Rule):
    """
    Built-in imports placed after custom imports.

    To make code more readable it needs to be more consistent. That's why it is recommended to group known, built-in
    import before custom imports.

    Example of rule violation::

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


class BuiltinImportsNotSortedRule(Rule):
    """
    Built-in imports are not sorted in a alphabetical order.

    To increase readability sort the imports in a alphabetical order.

    Example of rule violation::

        *** Settings ***
        Library    OperatingSystem
        Library    Collections  # BuiltIn libraries imported not in alphabetical order

    """

    name = "builtin-imports-not-sorted"
    rule_id = "IMP02"
    message = "BuiltIn library import '{builtin_import}' should be placed before '{previous_builtin_import}'"
    severity = RuleSeverity.WARNING
    added_in_version = "5.2.0"


class NonBuiltinImportsNotSortedRule(Rule):
    """
    Custom imports are not sorted in alphabetical order.

    To increase readability sort the imports in alphabetical order. Beware that depending on your code, some of the
    custom imports may be depending on each other and the order of the imports.

    Example of rule violation::

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


class ResourcesImportsNotSortedRule(Rule):
    """
    Resources imports are not sorted in a alphabetical order.

    To increase readability sort the resources imports in a alphabetical order. Beware that depending on your code,
    some of the imports may be depending on each other and the order of the imports.

    Example of rule violation::

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


class SettingsOrderChecker(VisitorChecker):
    """Checker for settings order."""

    wrong_import_order: WrongImportOrderRule
    builtin_imports_not_sorted: BuiltinImportsNotSortedRule
    non_builtin_imports_not_sorted: NonBuiltinImportsNotSortedRule
    resources_imports_not_sorted: ResourcesImportsNotSortedRule

    def __init__(self):
        self.libraries = []
        self.non_builtin_libraries = []
        self.resources = []
        super().__init__()

    def visit_File(self, node) -> None:  # noqa: N802
        self.libraries = []
        self.resources = []
        self.generic_visit(node)
        built_in_libs = []
        non_builtin_libs = []

        for library in self.libraries:
            if library.name in STDLIBS:
                built_in_libs.append(library)
                if non_builtin_libs:
                    lib_name = library.get_token(Token.NAME)
                    self.report(
                        self.wrong_import_order,
                        builtin_import=library.name,
                        custom_import=non_builtin_libs[0].name,
                        node=library,
                        col=lib_name.col_offset + 1,
                        end_col=lib_name.end_col_offset + 1,
                    )
            else:
                non_builtin_libs.append(library)
        previous = None
        for library in built_in_libs:
            if previous and library.name < previous.name:
                lib_name = library.get_token(Token.NAME)
                self.report(
                    self.builtin_imports_not_sorted,
                    builtin_import=library.name,
                    previous_builtin_import=previous.name,
                    node=library,
                    col=lib_name.col_offset + 1,
                    end_col=lib_name.end_col_offset + 1,
                )
            previous = library
        previous = None
        for library in non_builtin_libs:
            if previous is not None and library.name < previous.name:
                lib_name = library.get_token(Token.NAME)
                self.report(
                    self.non_builtin_imports_not_sorted,
                    custom_import=library.name,
                    previous_custom_import=previous.name,
                    node=library,
                    col=lib_name.col_offset + 1,
                    end_col=lib_name.end_col_offset + 1,
                )
            previous = library
        previous = None
        for resource in self.resources:
            if previous is not None and resource.name < previous.name:
                resource_name = resource.get_token(Token.NAME)
                self.report(
                    self.resources_imports_not_sorted,
                    resource_import=resource.name,
                    previous_resource_import=previous.name,
                    node=resource,
                    col=resource_name.col_offset + 1,
                    end_col=resource_name.end_col_offset + 1,
                )
            previous = resource

    def visit_LibraryImport(self, node) -> None:  # noqa: N802
        if not node.name:
            return
        self.libraries.append(node)

    def visit_ResourceImport(self, node: type[Statement]) -> None:  # noqa: N802
        if not node.name:
            return
        self.resources.append(node)
