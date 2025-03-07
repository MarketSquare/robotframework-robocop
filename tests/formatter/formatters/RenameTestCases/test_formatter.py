from tests.formatter import FormatterAcceptanceTest


class TestRenameTestCases(FormatterAcceptanceTest):
    FORMATTER_NAME = "RenameTestCases"

    def test_formatter(self):
        self.compare(source="test.robot", expected="test.robot")

    def test_test_without_name(self):
        self.compare(source="empty_test_name.robot", not_modified=True)

    def test_replace_pattern_to_empty(self):
        self.compare(
            source="test.robot",
            expected="replace_pattern_empty.robot",
            configure=[rf"{self.FORMATTER_NAME}.replace_pattern=[A-Z]+-\d{{1,}}"],
        )

    def test_replace_pattern_to_placeholder(self):
        configure = [
            rf"{self.FORMATTER_NAME}.replace_pattern=[A-Z]+-\d{{1,}}",
            f"{self.FORMATTER_NAME}.replace_to=PLACEHOLDER",
        ]
        self.compare(
            source="test.robot",
            expected="replace_pattern_placeholder.robot",
            configure=configure,
        )

    def test_replace_pattern_special_chars(self):
        self.compare(
            source="test.robot",
            expected="replace_pattern_special_chars.robot",
            configure=[rf"{self.FORMATTER_NAME}.replace_pattern=[\:?$@]"],
        )

    def test_selected_lines(self):
        self.compare(source="test.robot", expected="selected.robot", start_line=5, end_line=5)

    # def test_invalid_pattern(self):  TODO check error output
    #     result = self.run_tidy(
    #         select=[self.FORMATTER_NAME],
    #         configure=[f"{self.FORMATTER_NAME}.replace_pattern=[\911]"],
    #         source="test.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         rf"Error: {self.FORMATTER_NAME}: Invalid 'replace_pattern' parameter value: '[\911]'. "
    #         "It should be a valid regex expression. Regex error: 'bad escape \\9'\n"
    #     )
    #     assert expected_output == result.output

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    def test_upper_case_words(self):
        self.compare(
            source="test.robot", expected="test.robot", configure=[f"{self.FORMATTER_NAME}.capitalize_each_word=False"]
        )
        self.compare(
            source="test.robot",
            expected="upper_case.robot",
            configure=[f"{self.FORMATTER_NAME}.capitalize_each_word=True"],
        )
