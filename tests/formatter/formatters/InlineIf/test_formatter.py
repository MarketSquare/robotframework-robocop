import pytest

from tests.formatter import FormatterAcceptanceTest


class TestInlineIf(FormatterAcceptanceTest):
    FORMATTER_NAME = "InlineIf"

    def test_formatter(self):
        self.compare(source="test.robot")

    def test_formatter_skip_else(self):
        configure = [f"{self.FORMATTER_NAME}.skip_else=True", f"{self.FORMATTER_NAME}.line_length=120"]
        self.compare(source="test.robot", expected="test_skip_else.robot", configure=configure)

    def test_invalid_if(self):
        self.compare(source="invalid_if.robot", not_modified=True)

    def test_invalid_inline_if(self):
        self.compare(
            source="invalid_inline_if.robot", not_modified=True, configure=[f"{self.FORMATTER_NAME}.line_length=120"]
        )

    def test_disablers(self):
        self.compare(source="test_disablers.robot")

    @pytest.mark.parametrize("indent", [2, 4])
    @pytest.mark.parametrize("spaces", [2, 4])
    def test_one_if_spacing(self, spaces, indent):
        self.compare(source="one_if.robot", expected=f"one_if_{spaces}spaces.robot", space_count=spaces, indent=indent)
