import pytest

from tests.formatter import FormatterAcceptanceTest


class TestNormalizeTags(FormatterAcceptanceTest):
    FORMATTER_NAME = "NormalizeTags"

    def test_default(self):
        self.compare(source="tests.robot", expected="lowercase.robot")

    def test_lowercase(self):
        configure = [f"{self.FORMATTER_NAME}.case=lowercase", f"{self.FORMATTER_NAME}.normalize_case=True"]
        self.compare(source="tests.robot", expected="lowercase.robot", configure=configure)

    def test_uppercase(self):
        self.compare(
            source="tests.robot", expected="uppercase.robot", configure=[f"{self.FORMATTER_NAME}.case=uppercase"]
        )

    def test_titlecase(self):
        self.compare(
            source="tests.robot", expected="titlecase.robot", configure=[f"{self.FORMATTER_NAME}.case=titlecase"]
        )

    # def test_wrong_case(self):  TODO check error output in test
    #     result = self.run_tidy(
    #         select=[self.FORMATTER_NAME],
    #         configure=[f"{self.FORMATTER_NAME}.case=invalid"],
    #         source="tests.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         f"Error: {self.FORMATTER_NAME}: Invalid 'case' parameter value: 'invalid'. "
    #         f"Supported cases: lowercase, uppercase, titlecase.\n"
    #     )
    #     assert expected_output == result.output

    def test_only_remove_duplicates(self):
        self.compare(source="duplicates.robot", configure=[f"{self.FORMATTER_NAME}.normalize_case=False"])

    @pytest.mark.parametrize(
        "disablers", ["disablers.robot", "disablers2.robot", "disablers3.robot", "disablers4.robot"]
    )
    def test_disablers(self, disablers):
        self.compare(source=disablers, not_modified=True)

    @pytest.mark.parametrize("indent", [2, 4])
    @pytest.mark.parametrize("spaces", [2, 4])
    def test_spacing(self, spaces, indent):
        self.compare(
            source="spacing.robot",
            expected=f"spacing_{indent}indent_{spaces}spaces.robot",
            space_count=spaces,
            indent=indent,
        )

    def test_rf6(self):
        self.compare(source="rf6.robot", test_on_version=">=6", not_modified=True)

    def test_preserve_format(self):
        self.compare(
            source="preserve_format.robot",
            expected="preserve_format_enabled.robot",
            configure=[f"{self.FORMATTER_NAME}.preserve_format=True"],
        )

    def test_preserve_format_do_not_normalize_case(self):
        configure = [f"{self.FORMATTER_NAME}.preserve_format=True", f"{self.FORMATTER_NAME}.normalize_case=False"]
        self.compare(source="preserve_format.robot", configure=configure, not_modified=True)

    def test_ignore_format(self):
        self.compare(source="preserve_format.robot", expected="preserve_format_default.robot")

    @pytest.mark.parametrize("case_function", ["lowercase", "uppercase", "titlecase"])
    def test_variable_in_tag(self, case_function: str):
        self.compare(
            source="variables_in_tags.robot",
            expected=f"variables_in_tags_{case_function}.robot",
            configure=[f"{self.FORMATTER_NAME}.case={case_function}"],
            test_on_version=">=6",
        )
