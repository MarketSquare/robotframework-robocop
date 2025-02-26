import pytest

from tests.formatter import FormatterAcceptanceTest


class TestNormalizeSectionHeaderName(FormatterAcceptanceTest):
    FORMATTER_NAME = "NormalizeSectionHeaderName"

    def test_normalize_names(self):
        self.compare(source="tests.robot")

    def test_uppercase_names(self):
        self.compare(
            source="tests.robot", expected="uppercase.robot", configure=[f"{self.FORMATTER_NAME}.uppercase=True"]
        )

    def test_normalize_names_selected(self):
        self.compare(source="tests.robot", expected="selected.robot", start_line=5, end_line=6)

    @pytest.mark.parametrize("source", ["task.robot", "task2.robot"])
    def test_tasks(self, source):
        self.compare(source=source)

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)

    def test_translated(self):
        self.compare(source="translated.robot", test_on_version=">=6")
