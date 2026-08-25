"""Checker for rules triggered by sections and section headers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.parsing.model.blocks import SettingSection, TestCaseSection, VariableSection

from robocop.linter.rules import VisitorChecker, duplications, lengths, misc, order, spacing

if TYPE_CHECKING:
    from robot.parsing.model import File
    from robot.parsing.model.blocks import Section
    from robot.parsing.model.statements import SectionHeader


class SectionsChecker(VisitorChecker):
    """Checker for rules reported for the sections and their headers."""

    can_be_resource_file: misc.CanBeResourceFileRule
    empty_section: lengths.EmptySectionRule
    too_many_test_cases: lengths.TooManyTestCasesRule
    variable_not_left_aligned: spacing.VariableNotLeftAlignedRule
    suite_setting_not_left_aligned: spacing.SuiteSettingNotLeftAlignedRule
    section_already_defined: duplications.SectionAlreadyDefinedRule
    both_tests_and_tasks: duplications.BothTestsAndTasksRule
    section_out_of_order: order.SectionOutOfOrderRule

    def __init__(self) -> None:
        self.sections_by_order: list[int] = []
        self.sections_by_existence: dict[str, int] = {}
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.sections_by_order = []
        self.sections_by_existence = {}
        self.can_be_resource_file.check(node, self.source_file.path.name)
        super().visit_File(node)

    def visit_Section(self, node: Section) -> None:  # noqa: N802
        """
        Visit every section type.

        Rules that used to live in their own checker relied on the ``ModelVisitor`` dispatch picking the most
        specific ``visit_<SectionType>`` method. They are dispatched with ``isinstance`` here instead so that a
        single visitor can serve all section types at once.
        """
        self.empty_section.check(node)
        if isinstance(node, VariableSection):
            self.variable_not_left_aligned.check(node)
        elif isinstance(node, SettingSection):
            self.suite_setting_not_left_aligned.check(node)
        elif isinstance(node, TestCaseSection):
            self.too_many_test_cases.check(node, self.templated_suite)
        self.generic_visit(node)

    def visit_SectionHeader(self, node: SectionHeader) -> None:  # noqa: N802
        section_name = node.type
        if section_name not in self.section_out_of_order.sections_order:
            return
        if section_name in (Token.TESTCASE_HEADER, "TASK HEADER"):
            # a bit awkward implementation because before RF 6.0 task header used TESTCASE_HEADER type
            if "task" in node.name.lower():
                section_name = "TASK HEADER"
                self.both_tests_and_tasks.check(node, Token.TESTCASE_HEADER in self.sections_by_existence)
            else:
                self.both_tests_and_tasks.check(node, "TASK HEADER" in self.sections_by_existence)
        order_id = self.section_out_of_order.sections_order[section_name]
        self.section_already_defined.check(node, self.sections_by_existence.get(section_name))
        if section_name not in self.sections_by_existence:
            self.sections_by_existence[section_name] = node.lineno
        self.section_out_of_order.check(node, self.sections_by_order, order_id)
        self.sections_by_order.append(order_id)
