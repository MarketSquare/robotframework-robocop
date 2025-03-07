from tests.formatter import FormatterAcceptanceTest


class TestRenameKeywords(FormatterAcceptanceTest):
    FORMATTER_NAME = "RenameKeywords"

    def test_formatter(self):
        self.compare(source="test.robot", expected="test.robot")

    def test_transform_library(self):
        self.compare(
            source="test.robot",
            expected="test_transform_library.robot",
            configure=[f"{self.FORMATTER_NAME}.ignore_library=False"],
        )

    def test_renaming_pattern(self):
        configure = [
            rf"{self.FORMATTER_NAME}.replace_pattern=(?i)rename\s?me",
            f"{self.FORMATTER_NAME}.replace_to=New_Shining_Name",
        ]
        self.compare(source="test.robot", expected="rename_pattern_partial.robot", configure=configure)

    def test_renaming_whole_name_pattern(self):
        configure = [
            rf"{self.FORMATTER_NAME}.replace_pattern=(?i)^rename\s?me$",
            f"{self.FORMATTER_NAME}.replace_to=New_Shining_Name",
        ]
        self.compare(source="test.robot", expected="rename_pattern_whole.robot", configure=configure)

    def test_keep_underscores(self):
        self.compare(
            source="test.robot",
            expected="with_underscores.robot",
            configure=[f"{self.FORMATTER_NAME}.remove_underscores=False"],
        )

    # def test_invalid_pattern(self): TODO check error output
    #     result = self.run_tidy(
    #         select=[self.FORMATTER_NAME],
    #         configure=[f"{self.FORMATTER_NAME}.replace_pattern=[\911]"]
    #         source="test.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         rf"Error: {self.FORMATTER_NAME}: Invalid 'replace_pattern' parameter value: '[\911]'. "
    #         "It should be a valid regex expression. Regex error: 'bad escape \\9'\n"
    #     )
    #     assert expected_output == result.output

    def test_with_library_name_ignore(self):
        self.compare(source="with_library_name.robot")

    def test_with_library_name_transform(self):
        self.compare(
            source="with_library_name.robot",
            expected="with_library_name_transform.robot",
            configure=[f"{self.FORMATTER_NAME}.ignore_library=False"],
        )

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    def test_run_keywords(self):
        self.compare(source="run_keywords.robot")

    def test_embedded_variables(self):
        self.compare(source="embedded_variables.robot")

    def test_embedded_with_pattern(self):
        configure = [
            rf"{self.FORMATTER_NAME}.replace_pattern=(?i)rename\s?with\s.+variable$",
            f"{self.FORMATTER_NAME}.replace_to=New_Name_${{keyword}}_And_${{var}}",
        ]
        self.compare(
            configure=configure,
            source="library_embedded_var_pattern.robot",
        )

    def test_underscore_handling_bugs(self):
        self.compare(source="bug537_538.robot")

    def test_no_title_case(self):
        self.compare(
            source="no_title_case.robot",
            configure=[f"{self.FORMATTER_NAME}.keyword_case=ignore"],
        )

    def test_first_word_case(self):
        self.compare(
            source="no_title_case.robot",
            expected="capitalize_first.robot",
            configure=[f"{self.FORMATTER_NAME}.keyword_case=capitalize_first"],
        )
