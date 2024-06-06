from robot.api import Token
from robot.libraries import STDLIBS

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity

RULE_CATEGORY_ID = "01"


rules = {
    "10101": Rule(
        rule_id="10101",
        name="non-builtin-imports-not-sorted",
        msg="Non builtin library import '{{ custom_import }}' should be placed before '{{ previous_custom_import }}'",
        severity=RuleSeverity.WARNING,
        enabled=False,
        docs="""
        Example of rule violation:

            *** Settings ***
            Library    Collections
            Library    CustomLibrary
            Library    AnotherCustomLibrary  # AnotherCustomLibrary library defined after custom CustomLibrary

        """,
        added_in_version="5.2.0",
    ),
}


class NonBuiltinLibrariesImportOrderChecker(VisitorChecker):
    """
    Find and report Non Builtin Libraries imported not in alphabetical order.
    """

    reports = ("non-builtin-imports-not-sorted",)

    def __init__(self):
        self.non_builtin_libraries = []
        super().__init__()

    def visit_File(self, node):  # noqa
        self.non_builtin_libraries = []
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

    def visit_LibraryImport(self, node):  # noqa
        if node.name and node.name not in STDLIBS:
            self.non_builtin_libraries.append(node)
