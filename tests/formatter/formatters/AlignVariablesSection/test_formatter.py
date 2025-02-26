import pytest

from tests.formatter import FormatterAcceptanceTest


class TestAlignVariablesSection(FormatterAcceptanceTest):
    FORMATTER_NAME = "AlignVariablesSection"

    def test_align_variables(self):
        self.compare(source="tests.robot")

    def test_align_variables_2space_sep(self):
        self.compare(source="tests.robot", expected="tests_2space_sep.robot", space_count=2)

    def test_align_three_columns(self):
        self.compare(
            source="tests.robot", expected="three_columns.robot", configure=[f"{self.FORMATTER_NAME}.up_to_column=3"]
        )

    def test_align_all_columns(self):
        self.compare(
            source="tests.robot", expected="all_columns.robot", configure=[f"{self.FORMATTER_NAME}.up_to_column=0"]
        )

    def test_align_with_optional_equal_signs(self):
        self.compare(source="optional_equal_sign.robot")

    def test_align_with_long_comment(self):
        self.compare(source="long_comment.robot")

    def test_align_selected_whole(self):
        self.compare(source="align_selected.robot", expected="align_selected_whole.robot", start_line=5, end_line=17)

    def test_align_selected_part(self):
        self.compare(source="align_selected.robot", expected="align_selected_part.robot", start_line=10, end_line=12)

    def test_multiline_with_blank(self):
        self.compare(source="multiline_with_blank.robot")

    def test_align_variables_skip(self):
        self.compare(
            source="tests.robot", expected="tests_skip.robot", configure=[f"{self.FORMATTER_NAME}.skip_types=dict,list"]
        )

    def test_align_variables_skip_scalar(self):
        self.compare(
            source="align_selected.robot",
            expected="align_selected_skip.robot",
            configure=[f"{self.FORMATTER_NAME}.skip_types=scalar"],
        )

    def test_multiline_skip(self):
        self.compare(source="multiline_skip.robot", configure=[f"{self.FORMATTER_NAME}.skip_types=list,dict"])

    def test_fixed_tests(self):
        self.compare(
            source="tests.robot", expected="tests_fixed.robot", configure=[f"{self.FORMATTER_NAME}.fixed_width=30"]
        )

    def test_fixed_tests_zero(self):
        self.compare(
            source="tests.robot", expected="tests_fixed_one.robot", configure=[f"{self.FORMATTER_NAME}.fixed_width=1"]
        )

    def test_fixed_all_columns(self):
        configure = [
            f"{self.FORMATTER_NAME}.fixed_width=20",
            f"{self.FORMATTER_NAME}.up_to_column=0",
        ]
        self.compare(
            source="tests.robot",
            expected="all_columns_fixed.robot",
            configure=configure,
        )

    def test_disablers(self):
        self.compare(source="tests_disablers.robot")

    @pytest.mark.parametrize("min_width", [0, 1, 20])
    def test_min_width_shorter(self, min_width):
        self.compare(
            source="tests.robot",
            expected="tests_min_width.robot",
            configure=[f"{self.FORMATTER_NAME}.min_width={min_width}"],
        )

    @pytest.mark.parametrize("min_width", [49, 50, 51, 52])
    def test_min_width_longer(self, min_width):
        self.compare(
            source="tests.robot",
            expected="tests_min_width_50_width.robot",
            configure=[f"{self.FORMATTER_NAME}.min_width={min_width}"],
        )

    @pytest.mark.parametrize("space_count", [2, 4])
    def test_single_var(self, space_count):
        not_modified = space_count == 4
        self.compare(source="single_var.robot", not_modified=not_modified, space_count=space_count)
