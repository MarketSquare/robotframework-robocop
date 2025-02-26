from tests.formatter import FormatterAcceptanceTest


class TestReplaceEmptyValues(FormatterAcceptanceTest):
    FORMATTER_NAME = "ReplaceEmptyValues"

    def test_transformer(self):
        self.compare(source="test.robot", expected="test.robot")

    # def test_skip_section(self):  TODO global skip
    #     self.compare(source="test.robot", config=" --skip-sections=variables", not_modified=True)
