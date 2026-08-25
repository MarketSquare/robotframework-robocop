from tests.formatter import FormatterAcceptanceTest


class TestAlignBDDStatements(FormatterAcceptanceTest):
    FORMATTER_NAME = "AlignBDDStatements"

    def test_formatter(self):
        self.compare(source="test.robot", expected="test.robot")

    def test_indent(self):
        self.compare(source="test.robot", expected="indent.robot", indent=2)

    def test_nested_blocks(self):
        self.compare(source="nested.robot", expected="nested.robot")

    def test_keywords_are_not_formatted(self):
        self.compare(source="keywords.robot", not_modified=True)

    def test_translated_bdd_prefixes(self):
        self.compare(
            source="translated.robot",
            expected="translated.robot",
            language=["pl"],
            test_on_version=">=6",
        )

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    def test_selected_lines(self):
        self.compare(source="test.robot", expected="selected.robot", start_line=3, end_line=4)
