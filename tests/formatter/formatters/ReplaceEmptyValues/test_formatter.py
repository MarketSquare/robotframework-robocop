from tests.formatter import FormatterAcceptanceTest


class TestReplaceEmptyValues(FormatterAcceptanceTest):
    FORMATTER_NAME = "ReplaceEmptyValues"

    def test_formatter(self):
        self.compare(source="test.robot", expected="test.robot")

    def test_skip_section(self):
        self.compare(source="test.robot", skip_sections=["variables"], not_modified=True)
