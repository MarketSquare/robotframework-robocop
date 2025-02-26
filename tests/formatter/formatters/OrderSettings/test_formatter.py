import pytest

from tests.formatter import ROBOT_VERSION, FormatterAcceptanceTest


class TestOrderSettings(FormatterAcceptanceTest):
    FORMATTER_NAME = "OrderSettings"

    def test_order(self):
        if ROBOT_VERSION.major < 7:
            expected = "test_pre_rf7.robot"
        else:
            expected = "test.robot"
        self.compare(source="test.robot", expected=expected)

    @pytest.mark.parametrize(
        ("keyword_before", "keyword_after", "test_before", "test_after", "expected"),
        [
            (
                "documentation,tags,arguments,timeout,setup",
                "teardown,return",
                "documentation,tags,template,timeout,setup",
                "teardown",
                "custom_order_default",
            ),
            (
                "",
                "documentation,tags,timeout,arguments,teardown,setup,return",
                "",
                "documentation,tags,template,timeout,setup,teardown",
                "custom_order_all_end",
            ),
            (None, None, None, "", "custom_order_without_test_teardown"),
        ],
    )
    def test_custom_order(self, keyword_before, keyword_after, test_before, test_after, expected):
        configure = []
        if keyword_before is not None:
            configure.append(f"{self.FORMATTER_NAME}.keyword_before={keyword_before}")
        if keyword_after is not None:
            configure.append(f"{self.FORMATTER_NAME}.keyword_after={keyword_after}")
        if test_before is not None:
            configure.append(f"{self.FORMATTER_NAME}.test_before={test_before}")
        if test_after is not None:
            configure.append(f"{self.FORMATTER_NAME}.test_after={test_after}")
        if ROBOT_VERSION.major < 7:
            expected += "_pre_rf7.robot"
        else:
            expected += ".robot"
        self.compare(source="test.robot", expected=expected, configure=configure)

    # def test_custom_order_invalid_param(self):  TODO: check error output in test
    #     result = self.run_tidy(
    #         select=[self.FORMATTER_NAME],
    #         configure=[f"{self.FORMATTER_NAME}.keyword_before=documentation:keyword_after=tags,invalid"],
    #         source="test.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         f"Error: {self.FORMATTER_NAME}: Invalid 'keyword_after' parameter value: 'tags,invalid'."
    #         f" Custom order should be provided in comma separated list with valid setting names: "
    #         f"arguments,documentation,return,setup,tags,teardown,timeout\n"
    #     )
    #     assert result.output == expected_output

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    # def test_custom_order_setting_twice_in_one(self):  # TODO check error output test
    #     result = self.run_tidy(
    #         select=[self.FORMATTER_NAME],
    #         configure=[f"{self.FORMATTER_NAME}.test_after=teardown,teardown"]
    #         source="test.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         f"Error: {self.FORMATTER_NAME}: Invalid 'test_after' parameter value: 'teardown,teardown'. "
    #         "Custom order cannot contain duplicated setting names.\n"
    #     )
    #     assert result.output == expected_output

    # def test_custom_order_setting_twice_in_after_before(self):
    #     configure = [
    #         f"{self.FORMATTER_NAME}.keyword_before=documentation,arguments",
    #         f"{self.FORMATTER_NAME}.keyword_after=teardown,documentation",
    #     ]
    #     result = self.run_tidy(
    #         select=[self.FORMATTER_NAME],
    #         configure=configure,
    #         source="test.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         f"Error: {self.FORMATTER_NAME}: Invalid 'keyword_before' and 'keyword_after' order values. "
    #         f"Following setting names exists in both orders: documentation\n"
    #     )
    #     assert result.output == expected_output

    def test_translated(self):
        self.compare(source="translated.robot", test_on_version=">=6")

    def test_stick_comments_with_settings(self):
        self.compare(source="stick_comments.robot")
