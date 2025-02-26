from __future__ import annotations

import pytest

from tests.formatter import FormatterAcceptanceTest


class TestAlignTestCasesSection(FormatterAcceptanceTest):
    FORMATTER_NAME = "AlignTestCasesSection"

    def test_blocks(self):
        self.compare(source="blocks.robot")

    def test_blocks_auto(self):
        self.compare(
            source="blocks.robot",
            expected="blocks_auto.robot",
            configure=[f"{self.FORMATTER_NAME}.alignment_type=auto"],
        )

    def test_blocks_auto_with_0(self):
        configure = [f"{self.FORMATTER_NAME}.alignment_type=auto", f"{self.FORMATTER_NAME}.widths=0"]
        self.compare(source="blocks.robot", expected="blocks_auto_0.robot", configure=configure)

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
        self.compare(source="settings.robot")

    def test_settings_align_separately(self):
        configure = [
            f"{self.FORMATTER_NAME}.alignment_type=auto",
            f"{self.FORMATTER_NAME}.align_settings_separately=True",
        ]
        self.compare(
            source="settings.robot",
            expected="settings_auto_separate_settings.robot",
            configure=configure,
        )

    def test_compact_overflow_first_line(self):
        configure = [
            f"{self.FORMATTER_NAME}.widths=24,28,20,20",
            f"{self.FORMATTER_NAME}.handle_too_long=compact_overflow",
        ]
        self.compare(source="overflow_first_line.robot", configure=configure)

    @pytest.mark.parametrize("alignment_type", ["auto"])  # "fixed",  # TODO why it's commented?
    @pytest.mark.parametrize("skip_doc", [False])  # True,
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
            f"{self.FORMATTER_NAME}.widths=24,24,24,28",
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

    def test_templated(self):
        self.compare(source="templated.robot", not_modified=True)

    def test_compact_overflow_bug(self):
        configure = [
            f"{self.FORMATTER_NAME}.widths=24,28,20",
            f"{self.FORMATTER_NAME}.handle_too_long=compact_overflow",
        ]
        self.compare(source="compact_overflow_bug.robot", configure=configure)

    def test_dynamic_compact_overflow(self):
        configure = [
            f"{self.FORMATTER_NAME}.widths=24,28,20",
            f"{self.FORMATTER_NAME}.handle_too_long=compact_overflow",
            f"{self.FORMATTER_NAME}.skip_keyword_call=Log",
        ]
        self.compare(
            source="dynamic_compact_overflow.robot",
            configure=configure,
        )

    def test_dynamic_compact_overflow_limit_1(self):
        configure = [
            f"{self.FORMATTER_NAME}.widths=24,28,20",
            f"{self.FORMATTER_NAME}.handle_too_long=compact_overflow",
            f"{self.FORMATTER_NAME}.skip_keyword_call=Log",
            f"{self.FORMATTER_NAME}.compact_overflow_limit=1",
        ]
        self.compare(
            source="dynamic_compact_overflow_limit_1.robot",
            configure=configure,
        )

    def test_skip_return_values_overflow(self):
        """From https://github.com/MarketSquare/robotframework-tidy/issues/386"""
        configure = [
            f"{self.FORMATTER_NAME}.widths=24,28,20",
            f"{self.FORMATTER_NAME}.handle_too_long=compact_overflow",
            f"{self.FORMATTER_NAME}.compact_overflow_limit=1",
            f"{self.FORMATTER_NAME}.skip_return_values=True",
        ]
        self.compare(
            source="skip_return_values_overflow.robot",
            configure=configure,
        )

    def test_templated_test_with_setting(self):
        """Tests with [Template]"""
        self.compare(
            source="templated_with_setting.robot",
            configure=[f"{self.FORMATTER_NAME}.align_comments=True"],
            select=["NormalizeSeparators"],
        )

    def test_templated_test_with_setting_separate(self):
        """Tests with [Template]"""
        configure = [
            f"{self.FORMATTER_NAME}.alignment_type=auto",
            f"{self.FORMATTER_NAME}.align_settings_separately=True",
            f"{self.FORMATTER_NAME}.align_comments=True",
        ]
        self.compare(
            source="templated_with_setting.robot",
            expected="templated_with_settings_auto.robot",
            configure=configure,
            select=["NormalizeSeparators", "NormalizeComments"],
        )
