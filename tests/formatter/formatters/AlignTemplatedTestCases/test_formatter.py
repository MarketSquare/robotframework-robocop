import pytest

from tests.formatter import FormatterAcceptanceTest


class TestAlignTemplatedTestCases(FormatterAcceptanceTest):
    FORMATTER_NAME = "AlignTemplatedTestCases"

    @pytest.mark.parametrize(
        "source",
        [
            "test.robot",
            "no_header_col.robot",
            "with_settings.robot",
            "templated_for_loops.robot",
            "templated_for_loops_and_without.robot",
            "templated_for_loops_header_cols.robot",
        ],
    )
    def test_formatter(self, source):
        self.compare(source=source, expected=source)

    @pytest.mark.parametrize("source", ["for_loops.robot", "empty_line.robot"])
    def test_should_not_modify(self, source):
        self.compare(source=source, not_modified=True)

    def test_only_with_headers(self):
        self.compare(
            source="no_header_col.robot",
            not_modified=True,
            configure=[f"{self.FORMATTER_NAME}.only_with_headers=True"],
        )

    def test_fixed(self):
        self.compare(
            source="test.robot", expected="test_fixed.robot", configure=[f"{self.FORMATTER_NAME}.min_width=30"]
        )

    def test_for_fixed(self):
        self.compare(
            source="templated_for_loops_and_without.robot",
            expected="templated_for_loops_and_without_fixed.robot",
            configure=[f"{self.FORMATTER_NAME}.min_width=25"],
        )

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    def test_tags(self):
        self.compare(source="tags_settings.robot", configure=[f"{self.FORMATTER_NAME}.enabled=True"], run_all=True)

    def test_partly_templated(self):
        self.compare(source="partly_templated.robot")
