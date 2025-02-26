from __future__ import annotations

import pytest

from tests.formatter import FormatterAcceptanceTest


class TestAlignKeywordsSection(FormatterAcceptanceTest):
    FORMATTER_NAME = "AlignKeywordsSection"

    def test_blocks(self):
        self.compare(source="blocks.robot")

    def test_blocks_auto(self):
        self.compare(
            source="blocks.robot",
            expected="blocks_auto.robot",
            configure=[f"{self.FORMATTER_NAME}.alignment_type=auto"],
        )

    def test_blocks_auto_with_0(self):
        self.compare(
            source="blocks.robot",
            expected="blocks_auto_0.robot",
            configure=[f"{self.FORMATTER_NAME}.alignment_type=auto", f"{self.FORMATTER_NAME}.widths=0"],
        )

    def test_blocks_rf5(self):
        self.compare(source="blocks_rf5.robot", test_on_version=">=5")

    def test_one_column(self):
        self.compare(source="one_column.robot")

    def test_invalid(self):
        self.compare(source="non_ascii_spaces.robot", test_on_version=">=5")

    @pytest.mark.parametrize(
        "widths",
        [
            (0,),
            (0, 0, 0),
            (24, 24, 24),
            (24, 40, 24),
            (24, 0, 24),
            (4, 4, 4),
        ],
    )
    @pytest.mark.parametrize("handle_too_long", ["overflow", "ignore_line", "ignore_rest"])
    @pytest.mark.parametrize("alignment_type", ["auto", "fixed"])
    def test_simple(self, alignment_type, handle_too_long, widths: tuple[int, ...]):
        width_name = "_".join(str(width) for width in widths)
        if width_name == "0_0_0":
            width_name = "0"  # it should be the same result so we can reuse expected file
        width_csv = ",".join(str(width) for width in widths)
        expected = f"simple_{alignment_type}_{handle_too_long}_{width_name}.robot"
        configure = [
            f"{self.FORMATTER_NAME}.alignment_type={alignment_type}",
            f"{self.FORMATTER_NAME}.handle_too_long={handle_too_long}",
            f"{self.FORMATTER_NAME}.widths={width_csv}",
        ]
        self.compare(source="simple.robot", expected=expected, configure=configure)

    def test_settings(self):
        self.compare(source="settings.robot", configure=[f"{self.FORMATTER_NAME}.skip_timeout=True"])

    def test_skip_settings(self):
        self.compare(
            source="settings.robot",
            expected="skip_settings.robot",
            configure=[f"{self.FORMATTER_NAME}.skip_settings=True"],
        )
        #  TODO implement global skip options
        # self.compare(source="settings.robot", expected="skip_settings.robot", config=" --skip-settings")

    def test_compact_overflow_first_line(self):
        configure = [
            f"{self.FORMATTER_NAME}.widths=24,28,20,20",
            f"{self.FORMATTER_NAME}.handle_too_long=compact_overflow",
        ]
        self.compare(source="overflow_first_line.robot", configure=configure)

    @pytest.mark.parametrize("alignment_type", ["fixed", "auto"])
    @pytest.mark.parametrize("skip_doc", [True, False])
    def test_documentation(self, skip_doc, alignment_type):
        doc_formatting = "skip" if skip_doc else "align_first_col"
        configure = [
            f"{self.FORMATTER_NAME}.alignment_type={alignment_type}",
            f"{self.FORMATTER_NAME}.skip_documentation={skip_doc}",
        ]
        self.compare(
            source="documentation.robot",
            expected=f"documentation_{alignment_type}_{doc_formatting}.robot",
            configure=configure,
        )

    def test_skip_keyword_name(self):
        configure = [
            f"{self.FORMATTER_NAME}.skip_keyword_call=should_not_be_none",
            f"{self.FORMATTER_NAME}.skip_keyword_call_pattern=Contain,(?i)^prefix",
            f"{self.FORMATTER_NAME}.skip_return_values=True",
        ]
        self.compare(
            "skip_keywords.robot",
            configure=configure,
        )

    @pytest.mark.parametrize("handle_too_long", ["overflow", "compact_overflow", "ignore_line", "ignore_rest"])
    def test_auto_overflow_token_should_not_be_counted(self, handle_too_long):
        expected = f"too_long_token_counter_{handle_too_long}.robot"
        configure = [
            f"{self.FORMATTER_NAME}.alignment_type=auto",
            f"{self.FORMATTER_NAME}.handle_too_long={handle_too_long}",
        ]
        self.compare(
            "too_long_token_counter.robot",
            expected=expected,
            configure=configure,
        )

    def test_compact_overflow_last_0(self):
        self.compare(source="compact_overflow_last_0.robot", configure=[f"{self.FORMATTER_NAME}.widths=4,0"])

    def test_too_long_line(self):
        self.compare(source="too_long_line.robot", select=["SplitTooLongLine"])

    def test_too_long_line_disablers(self):
        self.compare(source="too_long_line_disablers.robot", select=["SplitTooLongLine"])

    def test_error_node(self):
        self.compare(source="error_node.robot", not_modified=True, test_on_version=">=5")

    def test_skip_return_values(self):
        configure = [
            f"{self.FORMATTER_NAME}.widths=24,28,20",
            f"{self.FORMATTER_NAME}.handle_too_long=compact_overflow",
            f"{self.FORMATTER_NAME}.skip_return_values=True",
        ]
        self.compare(
            source="skip_return_values.robot",
            configure=configure,
        )

    def test_align_settings_separately(self):
        configure = [
            f"{self.FORMATTER_NAME}.alignment_type=auto",
            f"{self.FORMATTER_NAME}.align_settings_separately=True",
        ]
        self.compare(source="align_settings_separately.robot", configure=configure)
