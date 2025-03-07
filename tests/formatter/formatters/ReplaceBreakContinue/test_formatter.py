from tests.formatter import FormatterAcceptanceTest


class TestReplaceBreakContinue(FormatterAcceptanceTest):
    FORMATTER_NAME = "ReplaceBreakContinue"

    def test_formatter(self):
        self.compare(source="test.robot")

    def test_with_errors(self):
        self.compare(source="errors.robot", not_modified=True)

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)
