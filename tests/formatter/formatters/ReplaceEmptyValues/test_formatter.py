from tests.formatter import FormatterAcceptanceTest


class TestReplaceEmptyValues(FormatterAcceptanceTest):
    FORMATTER_NAME = "ReplaceEmptyValues"

    def test_formatter(self):
        self.compare(source="test.robot", expected="test.robot")

    def test_skip_section(self):
        self.compare(source="test.robot", skip_sections=["variables"], not_modified=True)

    def test_keywords_section(self):
        """Test formatting empty values in Keywords section only."""
        configure = [f"{self.FORMATTER_NAME}.sections=keywords"]
        self.compare(
            source="keywords.robot",
            expected="keywords.robot",
            configure=configure,
        )

    def test_testcases_section(self):
        """Test formatting empty values in Test Cases section only."""
        configure = [f"{self.FORMATTER_NAME}.sections=testcases"]
        self.compare(
            source="testcases.robot",
            expected="testcases.robot",
            configure=configure,
        )

    def test_all_sections(self):
        """Test formatting empty values in all sections (variables, keywords, testcases)."""
        configure = [f"{self.FORMATTER_NAME}.sections=all"]
        self.compare(
            source="all_sections.robot",
            expected="all_sections.robot",
            configure=configure,
        )

    def test_mixed_sections_list(self):
        """Test formatting with a list of specific sections (variables and keywords)."""
        configure = [f"{self.FORMATTER_NAME}.sections=variables,keywords"]
        self.compare(
            source="mixed_sections.robot",
            expected="mixed_sections.robot",
            configure=configure,
        )

    def test_keywords_section_only_does_not_modify_variables(self):
        """Test that when configured for keywords only, variables section is not modified."""
        configure = [f"{self.FORMATTER_NAME}.sections=keywords"]
        self.compare(
            source="variables_only.robot",
            not_modified=True,
            configure=configure,
        )

    def test_testcases_section_only_does_not_modify_variables(self):
        """Test that when configured for testcases only, variables section is not modified."""
        configure = [f"{self.FORMATTER_NAME}.sections=testcases"]
        self.compare(
            source="variables_only.robot",
            not_modified=True,
            configure=configure,
        )
