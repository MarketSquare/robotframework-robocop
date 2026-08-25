from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, Rule, RuleSeverity

if TYPE_CHECKING:
    from robot.parsing.model.statements import LibraryImport, ResourceImport

    from robocop.linter.diagnostics import Diagnostic


def move_import_fix(rule: Rule, diag: Diagnostic, source_lines: list[str], message: str) -> Fix | None:
    """
    Create a fix that moves the reported import before the import it should be placed before.

    Whole affected region is replaced with a single edit to make sure the import is never duplicated,
    even if other imports from the same file are reported at the same time.
    """
    node = diag.node
    target_lineno = diag.reported_arguments.get("target_lineno")
    if node is None or not isinstance(target_lineno, int) or not 0 < target_lineno < node.lineno:
        return None
    moved = source_lines[node.lineno - 1 : node.end_lineno]
    preceding = source_lines[target_lineno - 1 : node.lineno - 1]
    if not moved:
        return None
    ends_with_newline = moved[-1].endswith("\n")
    replacement = "".join(line if line.endswith("\n") else f"{line}\n" for line in moved + preceding)
    if not ends_with_newline:
        replacement = replacement[:-1]
    edit = TextEdit.replace_lines(rule.rule_id, rule.name, target_lineno, node.end_lineno, replacement)
    return Fix(edits=[edit], message=message, applicability=FixApplicability.SAFE)


class WrongImportOrderRule(FixableRule):
    """
    Built-in imports placed after custom imports.

    To make code more readable, it needs to be more consistent. That's why it is recommended to group known, built-in
    import before custom imports.

    Example of rule violation:

        *** Settings ***
        Library    Collections
        Library    CustomLibrary
        Library    OperatingSystem  # BuiltIn library defined after custom CustomLibrary

    The import can be moved before the first custom import automatically with the ``--fix`` option.

    """

    name = "wrong-import-order"
    rule_id = "IMP01"
    message = "BuiltIn library import '{builtin_import}' should be placed before '{custom_import}'"
    severity = RuleSeverity.INFO
    added_in_version = "1.7.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0911",)

    def check(self, node: LibraryImport, custom_import: LibraryImport) -> None:
        lib_name = node.get_token(Token.NAME)
        self.report(
            builtin_import=node.name,
            custom_import=custom_import.name,
            target_lineno=custom_import.lineno,
            node=node,
            col=lib_name.col_offset + 1,
            end_col=lib_name.end_col_offset + 1,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Move the BuiltIn library import before the first custom library import."""
        custom_import = diag.reported_arguments["custom_import"]
        return move_import_fix(
            self, diag, source_lines, f"Move '{diag.reported_arguments['builtin_import']}' before '{custom_import}'"
        )


class BuiltinImportsNotSortedRule(FixableRule):
    """
    Built-in imports are not sorted in alphabetical order.

    To increase readability, sort the imports in alphabetical order.

    Example of rule violation:

        *** Settings ***
        Library    OperatingSystem
        Library    Collections  # BuiltIn libraries imported not in alphabetical order

    The imports can be sorted automatically with the ``--fix`` option.

    """

    name = "builtin-imports-not-sorted"
    rule_id = "IMP02"
    message = "BuiltIn library import '{builtin_import}' should be placed before '{previous_builtin_import}'"
    severity = RuleSeverity.INFO
    added_in_version = "5.2.0"
    fix_availability = FixAvailability.ALWAYS
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
            target_lineno=previous.lineno,
            node=node,
            col=lib_name.col_offset + 1,
            end_col=lib_name.end_col_offset + 1,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Move the BuiltIn library import before the previous, not sorted BuiltIn library import."""
        previous = diag.reported_arguments["previous_builtin_import"]
        return move_import_fix(
            self, diag, source_lines, f"Move '{diag.reported_arguments['builtin_import']}' before '{previous}'"
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

        robocop check --variable RESOURCE_DIR:resources

    If the path contains a variable that cannot be resolved, the import is ignored and not reported. Thanks to that,
    dynamically built paths do not cause false positives.

    """

    name = "unresolved-resource-import"
    project_rule = True
    rule_id = "IMP07"
    message = "Imported resource file '{import_name}' does not exist"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "9.0.0"
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

    """

    name = "unused-resource-import"
    project_rule = True
    rule_id = "IMP05"
    message = "Imported resource file '{import_name}' is not used"
    severity = RuleSeverity.INFO
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


class UnusedLibraryImportRule(Rule):
    """
    Imported library is not used.

    Reports library imports whose keywords are never used in the importing file.

    Example of rule violation:

        *** Settings ***
        Library    Collections  # no keyword from this library is used

        *** Test Cases ***
        Test
            Log    message

    Keywords from a library imported in a resource file are available in every file importing that resource,
    so the import is reported only when none of those files use any of its keywords.

    The library is imported to find out what keywords it provides, which means this rule is only reported when
    the library analysis is enabled (see the ``analyze-libraries`` option).

    To avoid false positives, imports are not reported when:

    - the library could not be imported, or is excluded with the ``ignored-libraries`` option,
    - the library provides no keywords, since it may be imported for its side effects, for example to register
      a listener,
    - the importing file calls a keyword using a name built from a variable, because such call may come from any
      library,
    - the import path or arguments could not be resolved.

    Libraries used only through ``Get Library Instance`` or imported dynamically with ``Import Library`` are
    reported, since such usage cannot be detected from the source code.

    """

    name = "unused-library-import"
    project_rule = True
    rule_id = "IMP06"
    message = "Imported library '{import_name}' is not used"
    severity = RuleSeverity.INFO
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


class CircularImportRule(Rule):
    """
    Resource file is a part of a circular import.

    Reports resource imports that import, directly or indirectly, the file they are used in.

    Example of rule violation:

        # keywords.resource
        *** Settings ***
        Resource    helpers.resource

        # helpers.resource
        *** Settings ***
        Resource    keywords.resource  # keywords.resource imports this file already

    Robot Framework does not fail on circular imports, but they make it harder to tell where a keyword comes from
    and often mean that the files should be split differently. Move the shared keywords to a separate resource file
    imported by both files to break the cycle.

    Every import taking part in the cycle is reported, together with the path leading back to the importing file.
    A file importing itself is reported as well.

    Imports that could not be resolved are not reported, since it is not known what they point to.

    """

    name = "circular-import"
    project_rule = True
    rule_id = "IMP08"
    message = "Circular import: {cycle}"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.MODULAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


class UnresolvedLibraryImportRule(Rule):
    """
    Imported library could not be imported.

    Reports library imports that Robot Framework would not be able to import during the execution.

    Example of rule violation:

        *** Settings ***
        Library    libs/does_not_exist.py  # file is not found next to the importing file
        Library    NotInstalledLibrary  # module is not installed and is not found in the search paths

    Library imports pointing to a file are always validated. Imports using a module name are only validated when
    Robocop imports the libraries, which it does by default and which can be disabled with the
    ``--no-analyze-libraries`` option::

        robocop check --no-analyze-libraries

    Extra directories with the libraries can be provided with the ``--pythonpath`` option::

        robocop check --pythonpath libs

    Following imports are never reported, since it is not known if they can be imported:

    - imports with a name or arguments containing a variable that cannot be resolved,
    - libraries excluded from the analysis with the ``--ignored-library`` option,
    - the ``Remote`` library, which connects to the remote server already during the import.

    Libraries that require a running service or a special environment can be excluded from the analysis::

        robocop check --ignored-library CustomServiceLibrary

    """

    name = "unresolved-library-import"
    project_rule = True
    rule_id = "IMP09"
    message = "Imported library '{import_name}' could not be imported: {error}"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
