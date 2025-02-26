from tests.formatter import FormatterAcceptanceTest


class TestOrderTags(FormatterAcceptanceTest):
    FORMATTER_NAME = "OrderTags"

    def test_order_tags_default(self):
        self.compare(source="tests.robot", expected="default.robot")

    def test_case_insensitive(self):
        configure = [f"{self.FORMATTER_NAME}.case_sensitive=False", f"{self.FORMATTER_NAME}.reverse=False"]
        self.compare(
            source="tests.robot",
            expected="case_insensitive.robot",
            configure=configure,
        )

    def test_case_sensitive(self):
        configure = [f"{self.FORMATTER_NAME}.case_sensitive=True", f"{self.FORMATTER_NAME}.reverse=False"]
        self.compare(
            source="tests.robot",
            expected="case_sensitive.robot",
            configure=configure,
        )

    def test_insensitive_reverse(self):
        configure = [f"{self.FORMATTER_NAME}.case_sensitive=False", f"{self.FORMATTER_NAME}.reverse=True"]
        self.compare(
            source="tests.robot",
            expected="case_insensitive_reverse.robot",
            configure=configure,
        )

    def test_case_sensitive_reverse(self):
        configure = [f"{self.FORMATTER_NAME}.case_sensitive=True", f"{self.FORMATTER_NAME}.reverse=True"]
        self.compare(
            source="tests.robot",
            expected="case_sensitive_reverse.robot",
            configure=configure,
        )

    def test_default_tags_false(self):
        configure = [
            f"{self.FORMATTER_NAME}.case_sensitive=False",
            f"{self.FORMATTER_NAME}.reverse=False",
            f"{self.FORMATTER_NAME}.default_tags=False",
        ]
        self.compare(
            source="tests.robot",
            expected="default_tags_false.robot",
            configure=configure,
        )

    def test_force_tags_false(self):
        configure = [
            f"{self.FORMATTER_NAME}.case_sensitive=False",
            f"{self.FORMATTER_NAME}.reverse=False",
            f"{self.FORMATTER_NAME}.force_tags=False",
        ]
        self.compare(
            source="tests.robot",
            expected="force_tags_false.robot",
            configure=configure,
        )

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    def test_test_tags(self):
        self.compare(source="test_tags.robot", test_on_version=">=6")
