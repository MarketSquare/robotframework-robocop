from tests.formatter import FormatterAcceptanceTest


class TestNormalizeComments(FormatterAcceptanceTest):
    FORMATTER_NAME = "NormalizeComments"

    def test_transformer(self):
        self.compare(source="test.robot", expected="test.robot")
