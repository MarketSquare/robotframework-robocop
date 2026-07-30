import pytest
import typer

from robocop.run import format_files
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

    def test_match_assignment(self):
        self.compare(source="assignment_char.robot")

    def test_item_access(self):
        self.compare(source="item_access.robot", not_modified=True)

    @pytest.mark.parametrize(
        ("keyword_call", "expected_comment"),
        [
            (
                "&{task_dict}    Create Dictionary    #    Task State=Task Name    Subtask Status=Subtask Name",
                "    #    Task State=Task Name    Subtask Status=Subtask Name",
            ),
            ("@{list}    Create List    value    # comment    with cells", "    # comment    with cells"),
        ],
    )
    def test_inline_comment_is_not_split_into_keyword_calls(self, keyword_call, expected_comment, tmp_path):
        """Cells of a single inline comment must stay in one comment line (#1715)."""
        source = tmp_path / "inline_comment.robot"
        source.write_text(f"*** Test Cases ***\nTest\n    {keyword_call}\n", encoding="utf-8")

        with pytest.raises(typer.Exit):
            format_files(sources=[source], select=[self.FORMATTER_NAME], overwrite=True, cache=False)

        assert source.read_text(encoding="utf-8").splitlines()[2] == expected_comment
