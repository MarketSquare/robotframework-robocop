from robot.api import Token
from robot.libraries import STDLIBS

from robocop.checkers import VisitorChecker
from robocop.rules import CommunityRule, RuleSeverity

RULE_CATEGORY_ID = "01"


rules = {
    "10101": CommunityRule(
        rule_id="10101",
        name="non-builtin-imports-not-sorted",
        msg="Non builtin library import '{{ custom_import }}' should be placed before '{{ previous_custom_import }}'",
        severity=RuleSeverity.WARNING,
        added_in_version="5.2.0",
        enabled=False,
        docs="""
        Example of rule violation::

            *** Settings ***
            Library    Collections
            Library    CustomLibrary
            Library    AnotherCustomLibrary  # AnotherCustomLibrary library defined after custom CustomLibrary

        """,
    ),
    "10102": CommunityRule(
        rule_id="10102",
        name="resources-imports-not-sorted",
        msg="Resource import '{{ resource_import }}' should be placed before '{{ previous_resource_import }}'",
        severity=RuleSeverity.WARNING,
        added_in_version="5.2.0",
        enabled=False,
        docs="""
        Example of rule violation::

            *** Settings ***
            Resource   CustomResource.resource
            Resource   AnotherFile.resource

        """,
    ),
}


class NonBuiltinLibrariesImportOrderChecker(VisitorChecker):
    """Find and report Non Builtin Libraries or Resources imported not in alphabetical order."""

    reports = (
        "non-builtin-imports-not-sorted",
        "resources-imports-not-sorted",
    )

    def __init__(self):
        self.non_builtin_libraries = []
        self.resources = []
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.non_builtin_libraries = []
        self.resources = []
        self.generic_visit(node)
        previous = None
        for library in self.non_builtin_libraries:
            if previous is not None and library.name < previous.name:
                lib_name = library.get_token(Token.NAME)
                self.report(
                    "non-builtin-imports-not-sorted",
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
                    "resources-imports-not-sorted",
                    resource_import=resource.name,
                    previous_resource_import=previous.name,
                    node=resource,
                    col=resource_name.col_offset + 1,
                    end_col=resource_name.end_col_offset + 1,
                )
            previous = resource

    def visit_LibraryImport(self, node):  # noqa: N802
        if node.name and node.name not in STDLIBS:
            self.non_builtin_libraries.append(node)

    def visit_ResourceImport(self, node):  # noqa: N802
        if not node.name:
            return
        self.resources.append(node)
