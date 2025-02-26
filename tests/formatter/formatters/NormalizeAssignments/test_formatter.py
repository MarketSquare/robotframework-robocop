import pytest

from tests.formatter import FormatterAcceptanceTest


class TestNormalizeAssignments(FormatterAcceptanceTest):
    FORMATTER_NAME = "NormalizeAssignments"

    @pytest.mark.parametrize(
        "filename", ["common_remove.robot", "common_equal_sign.robot", "common_space_and_equal_sign.robot"]
    )
    def test_autodetect(self, filename):
        self.compare(source=filename)

    @pytest.mark.parametrize("filename", ["common_remove", "common_equal_sign", "common_space_and_equal_sign"])
    def test_autodetect_variables(self, filename):
        self.compare(
            source=filename + ".robot",
            expected=filename + "_variables.robot",
            configure=[f"{self.FORMATTER_NAME}.equal_sign_type_variables=autodetect"],
        )

    def test_remove(self):
        self.compare(
            source="tests.robot", expected="remove.robot", configure=[f"{self.FORMATTER_NAME}.equal_sign_type=remove"]
        )

    def test_add_equal_sign(self):
        self.compare(
            source="tests.robot",
            expected="equal_sign.robot",
            configure=[f"{self.FORMATTER_NAME}.equal_sign_type=equal_sign"],
        )

    def test_add_space_and_equal_sign(self):
        self.compare(
            source="tests.robot",
            expected="space_and_equal_sign.robot",
            configure=[f"{self.FORMATTER_NAME}.equal_sign_type=space_and_equal_sign"],
        )

    # TODO check test error output
    # @pytest.mark.parametrize("param_name", ["equal_sign_type", "equal_sign_type_variables"])
    # def test_invalid_equal_sign_type(self, param_name):
    #     result = self.run_tidy(
    #         select=[self.FORMATTER_NAME],
    #         configure=[f"{self.FORMATTER_NAME}.{param_name}=="],
    #         source="tests.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         f"Error: {self.FORMATTER_NAME}: Invalid '=' parameter value: '{param_name}'. "
    #         "Possible values:\n    remove\n    equal_sign\n    space_and_equal_sign\n"
    #     )
    #     assert expected_output == result.output

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)
