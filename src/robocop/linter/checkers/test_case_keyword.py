"""Checker for rules triggered by test case and keyword definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import VisitorChecker, documentation, lengths, naming, order
from robocop.linter.rules.lengths import count_keyword_calls, is_templated_test

if TYPE_CHECKING:
    from robot.parsing.model import File, Keyword, SettingSection, TestCase
    from robot.parsing.model.statements import KeywordName, TestCaseName


class TestCaseKeywordChecker(VisitorChecker):
    """Checker for rules reported for the whole test case or keyword definition."""

    missing_doc_keyword: documentation.MissingDocKeywordRule
    missing_doc_test_case: documentation.MissingDocTestCaseRule
    missing_doc_test_suite: documentation.MissingDocTestSuiteRule
    missing_doc_resource_file: documentation.MissingDocResourceFileRule
    file_too_long: lengths.FileTooLongRule
    too_long_keyword: lengths.TooLongKeywordRule
    too_few_calls_in_keyword: lengths.TooFewCallsInKeywordRule
    too_many_calls_in_keyword: lengths.TooManyCallsInKeywordRule
    too_long_test_case: lengths.TooLongTestCaseRule
    too_few_calls_in_test_case: lengths.TooFewCallsInTestCaseRule
    too_many_calls_in_test_case: lengths.TooManyCallsInTestCaseRule
    too_many_arguments: lengths.TooManyArgumentsRule
    not_allowed_char_in_filename: naming.NotAllowedCharInFilenameRule
    not_allowed_char_in_name: naming.NotAllowedCharInNameRule
    not_capitalized_test_case_title: naming.NotCapitalizedTestCaseTitleRule
    test_case_name_is_empty: naming.TestCaseNameIsEmptyRule
    test_case_section_out_of_order: order.TestCaseSectionOutOfOrderRule
    keyword_section_out_of_order: order.KeywordSectionOutOfOrderRule

    def __init__(self) -> None:
        self.is_resource = False
        self.settings_section_exists = False
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        path = self.source_file.path
        self.is_resource = bool(path.name) and ".resource" in path.suffix
        self.settings_section_exists = False
        self.file_too_long.check(node)
        self.not_allowed_char_in_filename.check(node, path)
        self.generic_visit(node)
        if not self.settings_section_exists:
            if self.is_resource:
                self.missing_doc_resource_file.check_missing_settings_section(node)
            else:
                self.missing_doc_test_suite.check_missing_settings_section(node)

    def visit_SettingSection(self, node: SettingSection) -> None:  # noqa: N802
        self.settings_section_exists = True
        if self.is_resource:
            self.missing_doc_resource_file.check(node)
        else:
            self.missing_doc_test_suite.check(node)

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.missing_doc_keyword.check(node)
        self.keyword_section_out_of_order.check(node)
        if not node.name.lstrip().startswith("#"):
            self.too_many_arguments.check(node)
            # a keyword that is already reported as too long is not additionally reported for the number of calls
            if not self.too_long_keyword.check(node):
                keyword_count = count_keyword_calls(node)
                if not self.too_few_calls_in_keyword.check(node, keyword_count):
                    self.too_many_calls_in_keyword.check(node, keyword_count)
        self.generic_visit(node)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.missing_doc_test_case.check(node, self.templated_suite)
        self.test_case_section_out_of_order.check(node)
        if node.name:
            self.not_capitalized_test_case_title.check(node)
        else:
            self.test_case_name_is_empty.check(node)
        self.check_test_case_length(node)
        self.generic_visit(node)

    def check_test_case_length(self, node: TestCase) -> None:
        templated = is_templated_test(node, self.templated_suite)
        if templated and self.too_long_test_case.ignore_templated:
            return
        self.too_long_test_case.check(node)
        skip_too_many = templated and self.too_many_calls_in_test_case.ignore_templated
        skip_too_few = templated and self.too_few_calls_in_test_case.ignore_templated
        if skip_too_many and skip_too_few:
            return
        keyword_count = count_keyword_calls(node)
        reported = not skip_too_many and self.too_many_calls_in_test_case.check(node, keyword_count)
        if not reported and not skip_too_few:
            self.too_few_calls_in_test_case.check(node, keyword_count)

    def visit_TestCaseName(self, node: TestCaseName) -> None:  # noqa: N802
        self.not_allowed_char_in_name.check(node, "test case")

    def visit_KeywordName(self, node: KeywordName) -> None:  # noqa: N802
        self.not_allowed_char_in_name.check(node, "keyword", is_keyword=True)
