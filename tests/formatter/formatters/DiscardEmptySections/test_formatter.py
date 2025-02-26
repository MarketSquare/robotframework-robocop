from tests.formatter import FormatterAcceptanceTest


class TestDiscardEmptySections(FormatterAcceptanceTest):
    FORMATTER_NAME = "DiscardEmptySections"

    def test_removes_empty_sections(self):
        self.compare(
            source="removes_empty_sections.robot", configure=[f"{self.FORMATTER_NAME}.allow_only_comments=False"]
        )

    def test_removes_empty_sections_except_comments(self):
        self.compare(
            source="removes_empty_sections.robot",
            expected="removes_empty_sections_except_comments.robot",
        )

    def test_remove_selected_empty_node(self):
        self.compare(
            source="removes_empty_sections.robot",
            expected="removes_selected_empty_section.robot",
            start_line=17,
            end_line=18,
        )

    def test_disablers(self):
        self.compare(source="removes_empty_sections_disablers.robot", not_modified=True)

    def test_skip_section(self):
        self.compare(
            source="removes_empty_sections.robot",
            expected="removes_empty_sections_skip_variables.robot",
            configure=[f"{self.FORMATTER_NAME}.skip_sections=variables"],
        )
        self.compare(
            source="removes_empty_sections.robot",
            expected="removes_empty_sections_skip_variables.robot",
            skip_sections=["variables"],
        )
