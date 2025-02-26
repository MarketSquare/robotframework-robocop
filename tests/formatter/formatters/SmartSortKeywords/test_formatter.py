from tests.formatter import FormatterAcceptanceTest


class TestSmartSortKeywords(FormatterAcceptanceTest):
    FORMATTER_NAME = "SmartSortKeywords"

    def test_ci_sort(self):
        self.compare(
            source="sort_input.robot",
            expected="sort_ci.robot",
            configure=[f"{self.FORMATTER_NAME}.ignore_other_underscore=False"],
        )

    def test_ci_ilu(self):
        configure = [
            f"{self.FORMATTER_NAME}.ignore_leading_underscore=True",
            f"{self.FORMATTER_NAME}.ignore_other_underscore=False",
        ]
        self.compare(
            source="sort_input.robot",
            expected="sort_ci_ilu.robot",
            configure=configure,
        )

    def test_ci_iou(self):
        self.compare(source="sort_input.robot", expected="sort_ci_iou.robot")

    def test_ci_ilu_iou(self):
        self.compare(
            source="sort_input.robot",
            expected="sort_ci_ilu_iou.robot",
            configure=[f"{self.FORMATTER_NAME}.ignore_leading_underscore=True"],
        )

    def test_ilu_iou(self):
        configure = [
            f"{self.FORMATTER_NAME}.case_insensitive=False",
            f"{self.FORMATTER_NAME}.ignore_leading_underscore=True",
        ]
        self.compare(
            source="sort_input.robot",
            expected="sort_ilu_iou.robot",
            configure=configure,
        )

    def test_iou(self):
        self.compare(
            source="sort_input.robot",
            expected="sort_iou.robot",
            configure=[f"{self.FORMATTER_NAME}.case_insensitive=False"],
        )

    def test_ilu(self):
        configure = [
            f"{self.FORMATTER_NAME}.case_insensitive=False",
            f"{self.FORMATTER_NAME}.ignore_leading_underscore=True",
            f"{self.FORMATTER_NAME}.ignore_other_underscore=False",
        ]
        self.compare(
            source="sort_input.robot",
            expected="sort_ilu.robot",
            configure=configure,
        )

    def test_(self):
        configure = [
            f"{self.FORMATTER_NAME}.case_insensitive=False",
            f"{self.FORMATTER_NAME}.ignore_other_underscore=False",
        ]
        self.compare(
            source="sort_input.robot",
            expected="sort_.robot",
            configure=configure,
        )

    def test_empty_section(self):
        self.compare(source="empty_before_fist_keyword.robot", not_modified=True)

    def test_multiple_sections(self):
        self.compare(source="multiple_sections.robot")

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)
