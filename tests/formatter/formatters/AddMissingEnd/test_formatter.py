from tests.formatter import FormatterAcceptanceTest


class TestAddMissingEnd(FormatterAcceptanceTest):
    FORMATTER_NAME = "AddMissingEnd"

    def test_transformer(self):
        self.compare(source="test.robot", expected="test.robot")

    def test_selected(self):
        self.compare(source="test.robot", expected="test_selected.robot", start_line=166, end_line=188)

    def test_rf5_syntax(self):
        self.compare(source="test_5.robot", target_version=">=5")

    def test_disablers(self):
        self.compare(source="test_5_disablers.robot", target_version=">=5", not_modified=True)
