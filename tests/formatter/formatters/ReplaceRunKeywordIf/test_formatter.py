from tests.formatter import FormatterAcceptanceTest


class TestReplaceRunKeywordIf(FormatterAcceptanceTest):
    FORMATTER_NAME = "ReplaceRunKeywordIf"

    def test_run_keyword_if_replaced_selected(self):
        self.compare(source="tests.robot", expected="tests_selected.robot", start_line=18, end_line=20)

    def test_run_keyword_if_replaced(self):
        self.compare(source="tests.robot")

    def test_invalid_data(self):
        self.compare(source="invalid_data.robot")

    def test_golden_file(self):
        self.compare(source="golden.robot", not_modified=True)

    def test_remove_useless_set_variable(self):
        self.compare(source="set_variable_workaround.robot")

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    def test_configure_whitespace(self):
        self.compare(source="configure_whitespace.robot", space_count=2, indent=4)

    def test_keyword_name_in_variable(self):
        self.compare(source="keyword_name_in_var.robot")
