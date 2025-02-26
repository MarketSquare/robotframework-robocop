import pytest

from robocop.formatter.utils.misc import ROBOT_VERSION
from tests.formatter import FormatterAcceptanceTest


class TestNormalizeSeparators(FormatterAcceptanceTest):
    FORMATTER_NAME = "NormalizeSeparators"

    def test_normalize_separators(self):
        self.compare(source="test.robot")

    def test_normalize_with_8_spaces(self):
        self.compare(source="test.robot", expected="test_8spaces.robot", space_count=8)

    def test_pipes(self):
        self.compare(source="pipes.robot")

    @pytest.mark.parametrize(
        "skip_sections",
        ["all", "testcases,keywords", "settings,variables,testcases", ""],
    )
    def test_disable_section(self, skip_sections):
        if skip_sections == "all":
            self.compare(
                source="test.robot",
                not_modified=True,
                configure=[f"{self.FORMATTER_NAME}.skip_sections=settings,variables,testcases,keywords,comments"],
            )
        elif not skip_sections:
            self.compare(source="test.robot", expected="skip_none.robot")
        else:
            self.compare(
                source="test.robot",
                expected=skip_sections.replace(",", "_") + ".robot",
                configure=[f"{self.FORMATTER_NAME}.skip_sections={skip_sections}"],
            )

    def test_rf5_syntax(self):
        self.compare(source="rf5_syntax.robot", test_on_version=">=5")

    @pytest.mark.parametrize(
        "disablers", ["disablers.robot", "disablers2.robot", "disablers3.robot", "disablers4.robot"]
    )
    def test_disablers(self, disablers):
        self.compare(source=disablers, not_modified=True)

    def test_skip_documentation_default(self):
        self.compare(source="test.robot", configure=[f"{self.FORMATTER_NAME}.skip_documentation=False"])

    def test_skip_documentation(self):
        self.compare(
            source="test.robot",
            expected="skip_documentation.robot",
            configure=[f"{self.FORMATTER_NAME}.skip_documentation=True"],
        )

    def test_continuation_indent(self):
        self.compare(source="continuation_indent.robot", space_count=2, indent=4, continuation_indent=4)

    @pytest.mark.parametrize("indent", [2, 4])
    @pytest.mark.parametrize("spaces", [2, 4])
    def test_inline_if(self, spaces, indent):
        self.compare(
            source="inline_if.robot",
            expected=f"inline_if_{indent}indent_{spaces}spaces.robot",
            space_count=spaces,
            indent=indent,
            test_on_version=">=5",
        )

    def test_inline_if_flatten(self):
        self.compare(
            source="inline_if.robot",
            expected="inline_if_flatten.robot",
            space_count=4,
            indent=4,
            configure=[f"{self.FORMATTER_NAME}.flatten_lines=True"],
            test_on_version=">=5",
        )

    def test_skip_keyword_call(self):
        self.compare(
            source="test.robot",
            expected="test_skip_keyword.robot",
            configure=[rf"{self.FORMATTER_NAME}.skip_keyword_call_pattern=(?i)should\sbe\sequal"],
        )

    def test_file_with_pipes_bug390(self):
        self.compare(source="bug390.robot")

    def test_skip_comments(self):
        configure = [f"{self.FORMATTER_NAME}.skip_comments=True"]
        expected = "comments_skip_comments.robot"
        self.compare(source="comments.robot", expected=expected, configure=configure, test_on_version=">=5")

    def test_skip_block_comments(self):
        configure = [f"{self.FORMATTER_NAME}.skip_block_comments=True"]
        expected = "comments_skip_block_comments.robot"
        self.compare(source="comments.robot", expected=expected, configure=configure, test_on_version=">=5")

    def test_skip_all_comments(self):
        configure = [f"{self.FORMATTER_NAME}.skip_comments=True", f"{self.FORMATTER_NAME}.skip_block_comments=True"]
        expected = "comments_skip_comments.robot"
        self.compare(source="comments.robot", expected=expected, configure=configure, test_on_version=">=5")

    def test_flatten_lines(self):
        if ROBOT_VERSION.major > 4:
            self.compare(source="flatten.robot", configure=[f"{self.FORMATTER_NAME}.flatten_lines=True"])
        else:
            self.compare(
                source="flatten.robot",
                expected="flatten_rf4.robot",
                configure=[f"{self.FORMATTER_NAME}.flatten_lines=True"],
            )

    def test_align_new_line(self):
        self.compare(
            source="continuation_indent.robot",
            expected="cont_indent_align_new_line.robot",
            configure=[f"{self.FORMATTER_NAME}.align_new_line=True"],
        )
