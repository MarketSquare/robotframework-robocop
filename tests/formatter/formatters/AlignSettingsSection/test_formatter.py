import pytest

from tests.formatter import FormatterAcceptanceTest


class TestAlignSettingsSection(FormatterAcceptanceTest):
    FORMATTER_NAME = "AlignSettingsSection"

    def test_align(self):
        self.compare(source="test.robot")

    def test_align_all_columns(self):
        self.compare(
            source="test.robot", expected="all_columns.robot", configure=[f"{self.FORMATTER_NAME}.up_to_column=0"]
        )

    def test_align_three_columns(self):
        self.compare(
            source="test.robot", expected="three_columns.robot", configure=[f"{self.FORMATTER_NAME}.up_to_column=3"]
        )

    def test_align_selected_whole(self):
        self.compare(source="test.robot", expected="selected_whole.robot", start_line=1, end_line=25)

    def test_align_selected_part(self):
        self.compare(source="test.robot", expected="selected_part.robot", start_line=9, end_line=14)

    def test_empty_lines_inside_statement(self):
        # bug from #75
        self.compare(source="empty_lines.robot")

    def test_continued_statement_style(self):
        self.compare(source="multiline_keywords.robot")

    def test_continued_statement_style_all_columns(self):
        self.compare(
            source="multiline_keywords.robot",
            expected="multiline_keywords_all_col.robot",
            configure=[f"{self.FORMATTER_NAME}.up_to_column=3"],
        )

    @pytest.mark.parametrize("indent", [0, 2, 20])
    def test_continued_statement_style_all_columns_configure_indent(self, indent):
        configure = [f"{self.FORMATTER_NAME}.up_to_column=3", f"{self.FORMATTER_NAME}.argument_indent={indent}"]
        self.compare(
            source="multiline_keywords.robot",
            expected=f"multiline_keywords_{indent}indent.robot",
            configure=configure,
        )

    def test_multiline_with_blank_line(self):
        self.compare(source="blank_line_doc.robot")

    def test_doc_multiline_and_whitespace(self):
        self.compare(source="blank_line_and_whitespace.robot")

    def test_fixed_test(self):
        self.compare(
            source="test.robot", expected="test_fixed.robot", configure=[f"{self.FORMATTER_NAME}.fixed_width=35"]
        )

    def test_fixed_all_columns(self):
        self.compare(
            source="test.robot",
            expected="all_columns_fixed.robot",
            configure=[f"{self.FORMATTER_NAME}.fixed_width=20", f"{self.FORMATTER_NAME}.up_to_column=0"],
        )

    def test_disablers(self):
        self.compare(source="test_disablers.robot")

    def test_argument_indents(self):
        self.compare(source="argument_indents.robot")

    @pytest.mark.parametrize("min_width", [0, 1, 20])
    def test_min_width_shorter(self, min_width):
        self.compare(
            source="test.robot",
            expected="test_min_width.robot",
            configure=[f"{self.FORMATTER_NAME}.min_width={min_width}"],
        )

    @pytest.mark.parametrize("min_width", [49, 50, 51, 52])
    def test_min_width_longer(self, min_width):
        self.compare(
            source="test.robot",
            expected="test_min_width_50_width.robot",
            configure=[f"{self.FORMATTER_NAME}.min_width={min_width}"],
        )

    # TODO: global skip
    # @pytest.mark.parametrize("skip_config", [" --skip-documentation", ":skip_documentation=True"])
    # def test_skip_documentation(self, skip_config):
    #     self.compare(source="test.robot", expected="test_skip_documentation.robot", config=skip_config)
