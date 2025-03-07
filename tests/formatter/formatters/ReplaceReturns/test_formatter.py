import pytest

from tests.formatter import FormatterAcceptanceTest


class TestReplaceReturns(FormatterAcceptanceTest):
    FORMATTER_NAME = "ReplaceReturns"

    @pytest.mark.parametrize(
        "source",
        [
            "return_from_keyword.robot",
            "return_from_keyword_if.robot",
            "test.robot",
        ],
    )
    def test_formatter(self, source):
        self.compare(source=source)

    @pytest.mark.parametrize(
        "source",
        [
            "errors.robot",
            "run_keyword_and_return.robot",
            "run_keyword_and_return_if.robot",
        ],
    )
    def test_should_not_modify(self, source):
        self.compare(source=source, not_modified=True)

    def test_return_selected(self):
        self.compare(
            source="test.robot",
            expected="test_selected.robot",
            start_line=10,
            end_line=17,
        )

    def test_return_from_keyword_if_selected(self):
        self.compare(
            source="return_from_keyword_if.robot",
            expected="return_from_keyword_if_selected.robot",
            start_line=11,
            end_line=15,
        )

    def test_disablers(self):
        self.compare(source="replace_returns_disablers.robot", not_modified=True)
