import pytest

from tests.formatter import FormatterAcceptanceTest


class TestAlignTemplatedTestCases(FormatterAcceptanceTest):
    FORMATTER_NAME = "AlignTemplatedTestCases"
    KEEP = f"{FORMATTER_NAME}.args_with_test=keep"

    @pytest.mark.parametrize(
        "source",
        [
            "test.robot",
            "no_header_col.robot",
            "with_settings.robot",
            "templated_for_loops.robot",
            "templated_for_loops_and_without.robot",
            "templated_for_loops_header_cols.robot",
            "empty_line.robot",
        ],
    )
    def test_formatter(self, source):
        self.compare(
            source=source,
            expected=source,
            configure=[self.KEEP],
            not_modified=source == "templated_for_loops.robot",
        )

    @pytest.mark.parametrize("source", ["for_loops.robot"])
    def test_should_not_modify(self, source):
        self.compare(source=source, not_modified=True, configure=[self.KEEP])

    def test_only_with_headers(self):
        self.compare(
            source="no_header_col.robot",
            not_modified=True,
            configure=[f"{self.FORMATTER_NAME}.only_with_headers=True", self.KEEP],
        )

    def test_fixed(self):
        self.compare(
            source="test.robot",
            expected="test_fixed.robot",
            configure=[f"{self.FORMATTER_NAME}.min_width=30", self.KEEP],
        )

    def test_for_fixed(self):
        self.compare(
            source="templated_for_loops_and_without.robot",
            expected="templated_for_loops_and_without_fixed.robot",
            configure=[f"{self.FORMATTER_NAME}.min_width=25", self.KEEP],
        )

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True, configure=[self.KEEP])

    def test_tags(self):
        self.compare(
            source="tags_settings.robot",
            configure=[f"{self.FORMATTER_NAME}.enabled=True", self.KEEP],
            run_all=True,
        )

    def test_partly_templated(self):
        self.compare(source="partly_templated.robot", configure=[self.KEEP])

    @pytest.mark.parametrize("headers", ["header", "no_header"])
    @pytest.mark.parametrize("mode", ["split", "split_on_settings", "keep"])
    def test_args_with_test(self, mode, headers):
        source = f"args_with_test_{headers}.robot"
        self.compare(
            source=source,
            expected=f"args_with_test_{headers}_{mode}.robot",
            configure=[f"{self.FORMATTER_NAME}.args_with_test={mode}"],
        )

    def test_invalid_args_with_test(self):
        result = self.run_tidy(
            select=[self.FORMATTER_NAME],
            configure=[f"{self.FORMATTER_NAME}.args_with_test=invalid"],
            source="args_with_test_header.robot",
            exit_code=2,
        )
        expected_output = "Supported values: split, split_on_settings, keep."
        assert "args_with_test" in str(result.value)
        assert expected_output in str(result.value)
