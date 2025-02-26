import pytest

from tests.formatter import FormatterAcceptanceTest


class TestNormalizeNewLines(FormatterAcceptanceTest):
    FORMATTER_NAME = "NormalizeNewLines"

    def test_normalize_new_lines(self):
        self.compare(source="tests.robot")

    def test_normalize_new_lines_three_lines_after_section(self):
        self.compare(
            source="tests.robot",
            expected="tests_three_lines_section.robot",
            configure=[f"{self.FORMATTER_NAME}.section_lines=3"],
        )

    def test_normalize_new_lines_two_lines_keywords(self):
        self.compare(
            source="tests.robot",
            expected="tests_two_lines_keywords.robot",
            configure=[f"{self.FORMATTER_NAME}.keyword_lines=2"],
        )

    def test_templated_tests(self):
        self.compare(source="templated_tests.robot")

    def test_templated_tests_separated(self):
        self.compare(
            source="templated_tests.robot",
            expected="templated_tests_with_1_line.robot",
            configure=[f"{self.FORMATTER_NAME}.separate_templated_tests=True"],
        )

    def test_test_case_last_0(self):
        self.compare(source="test_case_last_0_lines.robot", expected="test_case_last.robot")

    def test_test_case_last_1(self):
        self.compare(source="test_case_last_1_lines.robot", not_modified=True)

    @pytest.mark.parametrize("empty_lines", [0, 1, 2])
    def test_consecutive_empty_lines(self, empty_lines):
        self.compare(
            source="consecutive_empty_lines.robot",
            expected=f"consecutive_empty_lines_{empty_lines}line.robot",
            configure=[f"{self.FORMATTER_NAME}.consecutive_lines={empty_lines}"],
        )

    @pytest.mark.parametrize("trailing_lines", [0, 1, 2])
    def test_inline_if(self, trailing_lines):
        self.compare(
            source=f"inline_if_{trailing_lines}_lines.robot", expected="inline_if.robot", test_on_version=">=5"
        )

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    def test_disablers_selected(self):
        self.compare(source="disablers_selected.robot")

    def test_blocks(self):
        self.compare(source="blocks.robot", test_on_version=">=5")

    def test_remove_empty_multiline(self):
        self.compare(source="multiline.robot")

    def test_language_header(self):
        self.compare(source="language_header_0empty.robot", test_on_version=">=6")
        self.compare(source="language_header_2empty.robot", test_on_version=">=6")
        self.compare(
            source="language_header_5empty.robot", expected="language_header_2empty.robot", test_on_version=">=6"
        )
        self.compare(source="language_header_and_comments.robot", test_on_version=">=6")
