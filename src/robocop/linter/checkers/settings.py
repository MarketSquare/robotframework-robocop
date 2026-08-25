"""Checker for rules triggered by settings: their names, values and order."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.libraries import STDLIBS
from robot.parsing.model.blocks import SettingSection, TestCaseSection

from robocop.linter.rules import VisitorChecker, deprecated, documentation, errors, imports, lengths, naming
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model.blocks import InvalidSection, Keyword, TestCase
    from robot.parsing.model.statements import (
        Arguments,
        LibraryImport,
        Node,
        ResourceImport,
        Return,
        SectionHeader,
        Statement,
        Template,
        VariablesImport,
    )


class SettingsChecker(VisitorChecker):
    """
    Checker for rules reported for the suite, test case and keyword settings.

    Handles settings from three angles at once: whether the setting has a value, whether its name follows the
    naming conventions and whether the imports are placed in the recommended order.
    """

    empty_metadata: lengths.EmptyMetadataRule
    metadata_without_value: lengths.MetadataWithoutValueRule
    empty_documentation: lengths.EmptyDocumentationRule
    variable_in_documentation: documentation.VariableInDocumentationRule
    empty_force_tags: lengths.EmptyForceTagsRule
    empty_default_tags: lengths.EmptyDefaultTagsRule
    empty_keyword_tags: lengths.EmptyKeywordTagsRule
    empty_variables_import: lengths.EmptyVariablesImport
    empty_resource_import: lengths.EmptyResourceImport
    empty_library_import: lengths.EmptyLibraryImport
    empty_setup: lengths.EmptySetupRule
    empty_suite_setup: lengths.EmptySuiteSetupRule
    empty_test_setup: lengths.EmptyTestSetupRule
    empty_teardown: lengths.EmptyTeardownRule
    empty_suite_teardown: lengths.EmptySuiteTeardownRule
    empty_test_teardown: lengths.EmptyTestTeardownRule
    empty_timeout: lengths.EmptyTimeoutRule
    empty_test_timeout: lengths.EmptyTestTimeoutRule
    empty_template: lengths.EmptyTemplateRule
    empty_test_template: lengths.EmptyTestTemplateRule
    empty_arguments: lengths.EmptyArgumentsRule
    setting_name_not_in_title_case: naming.SettingNameNotInTitleCaseRule
    section_name_invalid: naming.SectionNameInvalidRule
    empty_library_alias: naming.EmptyLibraryAliasRule
    duplicated_library_alias: naming.DuplicatedLibraryAliasRule
    invalid_section: naming.InvalidSectionRule
    mixed_task_test_settings: naming.MixedTaskTestSettingsRule
    wrong_import_order: imports.WrongImportOrderRule
    builtin_imports_not_sorted: imports.BuiltinImportsNotSortedRule
    non_builtin_imports_not_sorted: imports.NonBuiltinImportsNotSortedRule
    resources_imports_not_sorted: imports.ResourcesImportsNotSortedRule
    variables_import_with_args: errors.VariablesImportWithArgsRule
    deprecated_with_name: deprecated.DeprecatedWithNameRule
    deprecated_singular_header: deprecated.DeprecatedSingularHeaderRule
    deprecated_force_tags: deprecated.DeprecatedForceTagsRule
    deprecated_return_setting: deprecated.DeprecatedReturnSetting

    def __init__(self) -> None:
        self.parent_node_name = ""
        self.task_section: bool | None = None
        self.libraries: list[LibraryImport] = []
        self.resources: list[ResourceImport] = []
        self.in_test_case = False
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
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
        self.libraries = []
        self.resources = []
        self.in_test_case = False
        self.generic_visit(node)
        self.check_import_order()

    def overwrites_suite_setting(self) -> bool:
        """
        Check if the empty setting can overwrite the suite setting.

        Test case settings such as ``[Timeout]`` are used with an empty value to overwrite the suite setting.
        The suite setting can be defined in the same file, but also in the ``__init__.robot`` file of the parent
        suite. Because of that such settings should not be removed, but replaced with the explicit ``NONE`` value.
        Keyword settings can never overwrite the suite settings and can be safely removed.
        """
        return self.in_test_case

    def check_import_order(self) -> None:
        built_in_libs: list[LibraryImport] = []
        non_builtin_libs: list[LibraryImport] = []
        for library in self.libraries:
            if library.name in STDLIBS:
                built_in_libs.append(library)
                if non_builtin_libs:
                    self.wrong_import_order.check(library, non_builtin_libs[0])
            else:
                non_builtin_libs.append(library)
        previous: LibraryImport | None = None
        for library in built_in_libs:
            self.builtin_imports_not_sorted.check(library, previous)
            previous = library
        previous = None
        for library in non_builtin_libs:
            self.non_builtin_imports_not_sorted.check(library, previous)
            previous = library
        previous_resource: ResourceImport | None = None
        for resource in self.resources:
            self.resources_imports_not_sorted.check(resource, previous_resource)
            previous_resource = resource

    def check_setting_name(self, node: Node) -> None:
        """Validate the name of the setting and its consistency with the test/task terminology used in the file."""
        name = node.data_tokens[0].value
        self.setting_name_not_in_title_case.check(node, name)
        # if there is no task/test section, determine by first setting in the file
        name_normalized = name.lower()
        if self.task_section is None and ("test" in name_normalized or "task" in name_normalized):
            self.task_section = "task" in name_normalized
        self.mixed_task_test_settings.check(node, name, self.task_section)

    def visit_InvalidSection(self, node: InvalidSection) -> None:  # noqa: N802
        # deliberately not descending: the header would otherwise be reported as an invalid section name as well,
        # and the body of an invalid section only ever holds comments
        self.invalid_section.check(node)

    def visit_SectionHeader(self, node: SectionHeader) -> None:  # noqa: N802
        self.section_name_invalid.check(node)
        self.deprecated_singular_header.check(node)

    def visit_SettingSection(self, node: SettingSection) -> None:  # noqa: N802
        self.parent_node_name = "Test Suite"
        self.generic_visit(node)

    def visit_TestCaseName(self, node: Statement) -> None:  # noqa: N802
        self.parent_node_name = f"'{node.name}' Test Case" if node.name else ""
        self.generic_visit(node)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.in_test_case = True
        self.generic_visit(node)
        self.in_test_case = False

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.parent_node_name = f"'{node.name}' Keyword" if node.name else ""
        self.context.keyword = node
        self.generic_visit(node)
        self.context.keyword = None

    def visit_Metadata(self, node: Statement) -> None:  # noqa: N802
        self.empty_metadata.check(node)
        self.metadata_without_value.check(node)
        self.check_setting_name(node)

    def visit_Documentation(self, node: Statement) -> None:  # noqa: N802
        self.empty_documentation.check(node, self.parent_node_name)
        self.variable_in_documentation.check(node)
        self.check_setting_name(node)

    def visit_ForceTags(self, node: Statement) -> None:  # noqa: N802
        self.empty_force_tags.check(node)
        self.check_setting_name(node)
        self.deprecated_force_tags.check(node)

    visit_TestTags = visit_ForceTags  # noqa: N815

    def visit_DefaultTags(self, node: Statement) -> None:  # noqa: N802
        self.empty_default_tags.check(node)
        self.check_setting_name(node)

    def visit_KeywordTags(self, node: Statement) -> None:  # noqa: N802
        # keyword tags are deliberately not passed to check_setting_name to keep the previous behaviour
        self.empty_keyword_tags.check(node)

    def visit_Tags(self, node: Statement) -> None:  # noqa: N802
        self.check_setting_name(node)

    def visit_VariablesImport(self, node: VariablesImport) -> None:  # noqa: N802
        self.empty_variables_import.check(node)
        self.check_setting_name(node)
        self.variables_import_with_args.check(node)

    def visit_ResourceImport(self, node: ResourceImport) -> None:  # noqa: N802
        self.empty_resource_import.check(node)
        self.check_setting_name(node)
        if node.name:
            self.resources.append(node)

    def visit_LibraryImport(self, node: LibraryImport) -> None:  # noqa: N802
        self.empty_library_import.check(node)
        self.setting_name_not_in_title_case.check(node, node.data_tokens[0].value)
        self.empty_library_alias.check(node)
        self.duplicated_library_alias.check(node)
        self.deprecated_with_name.check(node)
        if node.name:
            self.libraries.append(node)

    def visit_Setup(self, node: Statement) -> None:  # noqa: N802
        self.empty_setup.check(node, self.parent_node_name, self.overwrites_suite_setting())
        self.check_setting_name(node)

    def visit_SuiteSetup(self, node: Statement) -> None:  # noqa: N802
        self.empty_suite_setup.check(node)
        self.check_setting_name(node)

    def visit_TestSetup(self, node: Statement) -> None:  # noqa: N802
        self.empty_test_setup.check(node)
        self.check_setting_name(node)

    def visit_Teardown(self, node: Statement) -> None:  # noqa: N802
        self.empty_teardown.check(node, self.parent_node_name, self.overwrites_suite_setting())
        self.check_setting_name(node)

    def visit_SuiteTeardown(self, node: Statement) -> None:  # noqa: N802
        self.empty_suite_teardown.check(node)
        self.check_setting_name(node)

    def visit_TestTeardown(self, node: Statement) -> None:  # noqa: N802
        self.empty_test_teardown.check(node)
        self.check_setting_name(node)

    def visit_Timeout(self, node: Statement) -> None:  # noqa: N802
        self.empty_timeout.check(node, self.parent_node_name, self.overwrites_suite_setting())
        self.check_setting_name(node)

    def visit_TestTimeout(self, node: Statement) -> None:  # noqa: N802
        self.empty_test_timeout.check(node)
        self.check_setting_name(node)

    def visit_Template(self, node: Template) -> None:  # noqa: N802
        self.empty_template.check(node, self.parent_node_name, self.overwrites_suite_setting())
        self.check_setting_name(node)

    def visit_TestTemplate(self, node: Statement) -> None:  # noqa: N802
        self.empty_test_template.check(node)
        self.check_setting_name(node)

    def visit_Arguments(self, node: Arguments) -> None:  # noqa: N802
        self.empty_arguments.check(node, self.parent_node_name)
        self.check_setting_name(node)

    def visit_ReturnSetting(self, node: Statement) -> None:  # noqa: N802
        self.check_setting_name(node)
        self.deprecated_return_setting.check(node)

    def visit_Return(self, node: Return) -> None:  # noqa: N802
        """For RETURN use visit_ReturnStatement - visit_Return will most likely visit RETURN in the future"""
        self.check_setting_name(node)
        if ROBOT_VERSION.major in (5, 6):
            self.deprecated_return_setting.check(node)
