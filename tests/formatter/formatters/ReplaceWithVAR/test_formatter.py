from tests.formatter import FormatterAcceptanceTest


class TestReplaceWithVAR(FormatterAcceptanceTest):
    FORMATTER_NAME = "ReplaceWithVAR"

    def test_formatter(self):
        self.compare(source="test.robot", expected="test.robot")

    def test_explicit_local(self):
        self.compare(
            source="test.robot",
            expected="explicit_local.robot",
            configure=[f"{self.FORMATTER_NAME}.explicit_local=True"],
        )

    def test_replace_catenate_disabled(self):
        self.compare(
            source="test.robot",
            expected="replace_catenate_false.robot",
            configure=[f"{self.FORMATTER_NAME}.replace_catenate=False"],
        )

    def test_replace_create_dictionary_disabled(self):
        self.compare(
            source="test.robot",
            expected="replace_create_dictionary_false.robot",
            configure=[f"{self.FORMATTER_NAME}.replace_create_dictionary=False"],
        )

    def test_replace_create_list_disabled(self):
        self.compare(
            source="test.robot",
            expected="replace_create_list_false.robot",
            configure=[f"{self.FORMATTER_NAME}.replace_create_list=False"],
        )

    def test_replace_set_variable_if_disabled(self):
        self.compare(
            source="test.robot",
            expected="replace_set_variable_if_false.robot",
            configure=[f"{self.FORMATTER_NAME}.replace_set_variable_if=False"],
        )

    def test_invalid_inline_if(self):
        self.compare(source="invalid_inline_if.robot", not_modified=True)

    def test_too_long(self):
        self.compare(source="too_long.robot", configure=[f"{self.FORMATTER_NAME}.enabled=True"], run_all=True)
