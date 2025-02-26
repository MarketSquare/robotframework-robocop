from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.libraries import STDLIBS

from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker

if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model import Statement


class NonBuiltinImportsNotSortedRule(Rule):
    """

    Example of rule violation:

        *** Settings ***
        Library    Collections
        Library    CustomLibrary
        Library    AnotherCustomLibrary  # AnotherCustomLibrary library defined after custom CustomLibrary


    """

    name = "non-builtin-imports-not-sorted"
    rule_id = "10101"
    message = "Non builtin library import '{custom_import}' should be placed before '{previous_custom_import}'"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "5.2.0"


class ResourcesImportsNotSortedRule(Rule):
    """

    Example of rule violation:

        *** Settings ***
        Resource   CustomResource.resource
        Resource   AnotherFile.resource


    """

    name = "resources-imports-not-sorted"
    rule_id = "10102"
    message = "Resource import '{resource_import}' should be placed before '{previous_resource_import}'"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "5.2.0"


class NonBuiltinLibrariesImportOrderChecker(VisitorChecker):  # TODO could be together with BuiltIn sorted one
    """Find and report Non Builtin Libraries or Resources imported not in alphabetical order."""

    non_builtin_imports_not_sorted: NonBuiltinImportsNotSortedRule
    resources_imports_not_sorted: ResourcesImportsNotSortedRule

    def __init__(self):
        self.non_builtin_libraries = []
        self.resources = []
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.non_builtin_libraries = []
        self.resources = []
        self.generic_visit(node)
        previous = None
        for library in self.non_builtin_libraries:
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

    def visit_LibraryImport(self, node: type[Statement]) -> None:  # noqa: N802
        if node.name and node.name not in STDLIBS:
            self.non_builtin_libraries.append(node)

    def visit_ResourceImport(self, node: type[Statement]) -> None:  # noqa: N802
        if not node.name:
            return
        self.resources.append(node)
