from tests.formatter import FormatterAcceptanceTest


class TestIndentNestedKeywords(FormatterAcceptanceTest):
    FORMATTER_NAME = "IndentNestedKeywords"

    def test_run_keyword(self):
        self.compare(source="run_keyword.robot")

    def test_split_and_indent(self):
        self.compare(
            source="run_keyword.robot",
            expected="split_and_indent.robot",
            configure=[f"{self.FORMATTER_NAME}.indent_and=split_and_indent"],
        )

    def test_and_keep_in_line(self):
        self.compare(
            source="run_keyword.robot",
            expected="keep_in_line.robot",
            configure=[f"{self.FORMATTER_NAME}.indent_and=keep_in_line"],
        )

    def test_indent_and_continuation_indent(self):
        self.compare(
            source="run_keyword.robot",
            expected="indent_and_2spaces_4cont_indent.robot",
            configure=[f"{self.FORMATTER_NAME}.indent_and=split_and_indent"],
            space_count=2,
            continuation_indent=4,
        )

    def test_comments(self):
        self.compare(source="comments.robot")

    def test_run_keyword_in_settings(self):
        self.compare(source="settings.robot")

    def test_skip_settings(self):
        self.compare(
            source="settings.robot", not_modified=True, configure=[f"{self.FORMATTER_NAME}.skip_settings=True"]
        )

    def test_too_long_line(self):
        self.compare(source="too_long_line.robot", select=[self.FORMATTER_NAME, "SplitTooLongLine"])
