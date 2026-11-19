from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
import typer

from robocop.config.manager import ConfigManager
from robocop.embedded import extract_robot_blocks, is_embedded_extension, reconstruct_source
from robocop.linter.fix import Fix, FixApplicability, FixApplier, TextEdit
from robocop.run import check_files, format_files
from robocop.source_file import EmbeddedSourceFile
from tests import working_directory
from tests.linter.utils import get_result, isolated_output

TEST_DATA = Path(__file__).parent / "test_data"


def read(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


class TestExtraction:
    def test_markdown_two_blocks(self):
        lines = read(TEST_DATA / "two_blocks.md").splitlines(keepends=True)
        blocks = extract_robot_blocks(lines)
        assert len(blocks) == 2
        first, second = blocks
        assert (first.start_line, first.end_line, first.indent) == (6, 8, "")
        assert (second.start_line, second.end_line, second.indent) == (14, 16, "")

    def test_python_indented_block(self):
        lines = read(TEST_DATA / "docstring.py").splitlines(keepends=True)
        blocks = extract_robot_blocks(lines)
        assert len(blocks) == 1
        block = blocks[0]
        assert block.indent == "    "
        assert block.start_line == 6
        assert block.end_line == 8

    def test_no_blocks(self):
        lines = read(TEST_DATA / "no_blocks.md").splitlines(keepends=True)
        assert extract_robot_blocks(lines) == []

    def test_empty_block(self):
        lines = ["```robotframework\n", "```\n"]
        blocks = extract_robot_blocks(lines)
        assert len(blocks) == 1
        assert blocks[0].is_empty

    def test_markdown_dedents_by_fence_and_preserves_blank_whitespace(self):
        lines = ["  ```robot\n", "    Log    one\n", " \n", " Log    two\n", "  ```\n"]
        blocks = extract_robot_blocks(lines, markdown=True)
        assert reconstruct_source(lines, blocks, markdown=True) == "\n  Log    one\n \nLog    two\n\n"

    @pytest.mark.parametrize(
        ("suffix", "expected"),
        [
            (".md", True),
            (".markdown", True),
            (".py", True),
            (".MD", True),
            (".robot", False),
            (".resource", False),
            (".txt", False),
        ],
    )
    def test_is_embedded_extension(self, suffix, expected):
        assert is_embedded_extension(suffix) is expected


def run_check(source: str, select: list[str] | None = None, issue_format: str = "default") -> list[str]:
    default_format = "{source}:{line}:{col} [{severity}] {rule_id} {desc}"
    end_col_format = "{source}:{line}:{col}:{end_line}:{end_col} [{severity}] {rule_id} {desc}"
    fmt = end_col_format if issue_format == "end_col" else default_format
    with isolated_output() as output, working_directory(TEST_DATA):
        with pytest.raises(typer.Exit):
            check_files(
                sources=[TEST_DATA / source],
                select=select,
                issue_format=fmt,
                configure=["print_issues.output_format=simple"],
                ignore_file_config=True,
                cache=False,
            )
        sys.stdout.flush()
        result = get_result(output)
    return [line for line in result.splitlines() if line.startswith(source)]


class TestLinter:
    def test_markdown_physical_line_numbers(self):
        issues = run_check("two_blocks.md")
        assert "two_blocks.md:7:1 [W] DOC02 Missing documentation in 'Example Test' test case" in issues
        assert "two_blocks.md:15:1 [W] DOC01 Missing documentation in 'Example Keyword' keyword" in issues

    def test_python_docstring_column_offset(self):
        # The block is indented by 4 spaces, so the reported column is shifted by 4.
        issues = run_check("docstring.py", select=["DOC02"], issue_format="end_col")
        assert issues == ["docstring.py:7:5:7:17 [W] DOC02 Missing documentation in 'Example Test' test case"]

    def test_no_blocks_no_issues(self):
        assert run_check("no_blocks.md") == []

    def test_markdown_blocks_share_suite(self, tmp_path):
        source = tmp_path / "suite.markdown"
        source.write_text(
            "# Examples\n\n```robot\n*** Test Cases ***\nExample\n    Log    one\n```\n"
            "\nProse\n\n```robot\n    Log    two\n```\n",
            encoding="utf-8",
        )
        issues = check_files(
            sources=[source], select=["DOC03", "MISC06"], return_result=True, cache=False, ignore_file_config=True
        )
        assert [issue.rule.rule_id for issue in issues] == ["DOC03"]

    def test_spacing_ignores_markdown_prose_between_blocks(self, tmp_path):
        source = tmp_path / "spacing.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nOne\n    Log    one\n```\n"
            "Prose\n```robot\n    Log    two\n```\n"
            "Prose\n```robot\nTwo\n    Log    three\n```\n"
            "Prose\n```robot\n*** Keywords ***\nKeyword\n    Log    value\n```\n",
            encoding="utf-8",
        )
        issues = check_files(
            sources=[source],
            select=["SPC03", "SPC04", "SPC05", "SPC09", "SPC12"],
            return_result=True,
            cache=False,
            ignore_file_config=True,
        )
        assert not issues

    def test_spacing_still_reports_empty_code_lines(self, tmp_path):
        source = tmp_path / "spacing.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nOne\n    Log    one\n\n\n    Log    two\n```\n"
            "Prose\n```robot\n    Log    three\n```\n",
            encoding="utf-8",
        )
        issues = check_files(
            sources=[source], select=["SPC12"], return_result=True, cache=False, ignore_file_config=True
        )
        assert [(issue.range.start.line, issue.range.end.line) for issue in issues] == [(5, 6)]

    def test_spacing_checks_ignore_masked_lines_inside_syntax(self, tmp_path):
        source = tmp_path / "spacing.md"
        source.write_text(
            "```robot\n*** Test Cases ***\n```\nProse\n```robot\n"
            "Example\n    [Template]    Example Keyword\n    first\n```\nProse\n```robot\n"
            "    second\n\nControl\n    IF    ${True}\n```\nProse\n```robot\n"
            "        Log    value\n    END\n```\n",
            encoding="utf-8",
        )
        issues = check_files(
            sources=[source],
            select=["SPC09", "SPC13", "SPC23", "SPC24"],
            return_result=True,
            cache=False,
            ignore_file_config=True,
        )
        assert not issues

    def test_spacing_between_tests_in_one_block_is_checked(self, tmp_path):
        source = tmp_path / "spacing.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nOne\n    Log    one\nTwo\n    Log    two\n```\n",
            encoding="utf-8",
        )
        issues = check_files(
            sources=[source], select=["SPC04"], return_result=True, cache=False, ignore_file_config=True
        )
        assert [issue.rule.rule_id for issue in issues] == ["SPC04"]

    @pytest.mark.parametrize(("blank_lines", "expected"), [("", 0), ("\n", 1)])
    def test_statement_spacing_ignores_only_masked_lines(self, tmp_path, blank_lines, expected):
        source = tmp_path / "spacing.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nExample\n"
            f"    Log    value\n{blank_lines}```\nProse\n```robot\n    ...    more\n```\n",
            encoding="utf-8",
        )
        issues = check_files(
            sources=[source], select=["SPC13"], return_result=True, cache=False, ignore_file_config=True
        )
        assert len(issues) == expected

    @pytest.mark.parametrize(
        ("rule", "code", "line"),
        [
            ("SPC23", "*** Test Cases ***\nExample\n    [Template]    Keyword\n    first\n\n    second\n", 6),
            ("SPC24", "*** Test Cases ***\nExample\n    IF    ${True}\n\n        Log    value\n    END\n", 5),
        ],
    )
    def test_spacing_checks_real_blank_lines_in_embedded_code(self, tmp_path, rule, code, line):
        source = tmp_path / "spacing.md"
        source.write_text(f"```robot\n{code}```\n", encoding="utf-8")
        issues = check_files(sources=[source], select=[rule], return_result=True, cache=False, ignore_file_config=True)
        assert [(issue.rule.rule_id, issue.range.start.line) for issue in issues] == [(rule, line)]

    def test_markdown_continuation_keeps_keyword_indentation(self, tmp_path):
        source = tmp_path / "suite.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nExample\n    Log    one\n```\nProse\n```robot\n    Log    two\n```\n",
            encoding="utf-8",
        )
        config = ConfigManager(sources=[], root=tmp_path, ignore_file_config=True).default_config
        embedded = EmbeddedSourceFile(path=source, config=config)
        test = embedded.model.sections[1].body[0]
        assert [statement.keyword for statement in test.body if hasattr(statement, "keyword")] == ["Log", "Log"]
        assert [statement.lineno for statement in test.body if hasattr(statement, "keyword")] == [4, 8]

    def test_markdown_uses_fence_indent_for_columns(self, tmp_path):
        source = tmp_path / "suite.md"
        source.write_text("  ```robot\n  *** Test Cases ***\n Example\n    Log    hi\n  ```\n", encoding="utf-8")
        issues = check_files(
            sources=[source], select=["DOC02"], return_result=True, cache=False, ignore_file_config=True
        )
        assert len(issues) == 1
        assert issues[0].range.start.line == 3
        assert issues[0].range.start.character == 2

    def test_fix_cannot_delete_prose_between_blocks(self, tmp_path):
        source = tmp_path / "suite.md"
        source.write_text("```robot\n*** Test Cases ***\n```\nProse\n```robot\nExample\n```\n", encoding="utf-8")
        config = ConfigManager(sources=[], root=tmp_path, ignore_file_config=True).default_config
        embedded = EmbeddedSourceFile(path=source, config=config)
        edit = TextEdit.replace_lines("test", "test", 2, 6, "")
        fix = Fix(edits=[edit], message="Remove section", applicability=FixApplicability.SAFE)
        assert not FixApplier().apply_fixes(embedded, [fix])
        assert "Prose" in read(source)

    @pytest.mark.parametrize("suffix", [".md", ".py"])
    @pytest.mark.parametrize("end_line", [5, 6])
    def test_multiline_replacement_preserves_following_lines(self, tmp_path, suffix, end_line):
        source = tmp_path / f"suite{suffix}"
        original = (
            "  ```robot\n  *** Test Cases ***\n  Example\n"
            "      Log    one\n      Log    two\n      Log    three\n  ```\n  Prose\n"
        )
        source.write_text(original, encoding="utf-8")
        config = ConfigManager(sources=[], root=tmp_path, ignore_file_config=True).default_config
        embedded = EmbeddedSourceFile(path=source, config=config)
        edit = TextEdit("test", "test", 4, 1, end_line, 1, "    Log    replacement\n")
        fix = Fix(edits=[edit], message="Replace lines", applicability=FixApplicability.SAFE)
        assert FixApplier().apply_fixes(embedded, [fix])
        expected = original.splitlines(keepends=True)
        expected[3:end_line] = ["      Log    replacement\n"]
        assert "".join(embedded.source_lines).replace("\r\n", "\n") == "".join(expected)

    def test_python_blocks_remain_independent(self, tmp_path):
        source = tmp_path / "examples.py"
        source.write_text(
            '"""\n```robot\n*** Test Cases ***\nOne\n    Log    one\n```\n'
            '\n```robot\n*** Test Cases ***\nTwo\n    Log    two\n```\n"""\n',
            encoding="utf-8",
        )
        issues = check_files(
            sources=[source], select=["DOC03"], return_result=True, cache=False, ignore_file_config=True
        )
        assert len(issues) == 2


class TestFormatter:
    def _format(self, tmp_path: Path, source: str) -> str:
        work = tmp_path / source
        shutil.copy2(TEST_DATA / source, work)
        with pytest.raises(typer.Exit):
            format_files(sources=[work], overwrite=True, cache=False)
        return read(work)

    def test_markdown_block_formatted_prose_preserved(self, tmp_path):
        result = self._format(tmp_path, "unformatted.md")
        assert result == read(TEST_DATA / "expected" / "unformatted.md")

    def test_python_docstring_reindented(self, tmp_path):
        result = self._format(tmp_path, "unformatted.py")
        assert result == read(TEST_DATA / "expected" / "unformatted.py")

    def test_already_formatted_is_noop(self, tmp_path):
        result = self._format(tmp_path, "two_blocks.md")
        assert result == read(TEST_DATA / "two_blocks.md")

    def test_no_blocks_is_noop(self, tmp_path):
        result = self._format(tmp_path, "no_blocks.md")
        assert result == read(TEST_DATA / "no_blocks.md")

    def test_idempotent(self, tmp_path):
        once = self._format(tmp_path, "unformatted.md")
        work = tmp_path / "unformatted.md"
        with pytest.raises(typer.Exit):
            format_files(sources=[work], overwrite=True, cache=False)
        assert read(work) == once

    def test_continuation_across_blocks(self, tmp_path):
        source = tmp_path / "suite.md"
        source.write_text(
            "# Suite\n\n```robot\n*** Test Cases ***\nExample\n  Log  one\n```\n"
            "\nSome prose.\n\n```robot\n  Log  two\n\n*** Keywords ***\nKeyword\n  Log  value\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(typer.Exit):
            format_files(sources=[source], overwrite=True, cache=False, ignore_file_config=True)
        result = read(source)
        assert "    Log    one" in result
        assert "    Log    two" in result
        assert "*** Comments ***" not in result
        assert "```\n\nSome prose.\n\n```robot\n" in result.replace("\r\n", "\n")

    def test_continuation_only_block_is_formatted(self, tmp_path):
        source = tmp_path / "suite.md"
        original = (
            "```robot\r\n*** Test Cases ***\r\nExample\r\n    Log  one\r\n```\r\n"
            "Prose\r\n```robot\r\n    Log  two\r\n```\r\n"
        )
        with open(source, "w", encoding="utf-8", newline="") as stream:
            stream.write(original)
        with pytest.raises(typer.Exit):
            format_files(sources=[source], overwrite=True, cache=False, ignore_file_config=True, reruns=1)
        result = read(source)
        assert result == original.replace("Log  one", "Log    one").replace("Log  two", "Log    two")
        with pytest.raises(typer.Exit):
            format_files(sources=[source], overwrite=True, cache=False, ignore_file_config=True, reruns=1)
        assert read(source) == result

    @pytest.mark.parametrize(("line", "first", "second"), [(6, True, False), (14, False, True), (3, False, False)])
    def test_markdown_line_range_uses_physical_lines(self, tmp_path, line, first, second):
        source = tmp_path / "range.md"
        source.write_text(
            "# Suite\n\n```robot\n*** Test Cases ***\nFirst\n    Log      first   badly\n```\n"
            "\nSome prose.\n\n```robot\n*** Keywords ***\nSecond\n    Log      second   badly\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(typer.Exit):
            format_files(
                sources=[source],
                overwrite=True,
                cache=False,
                ignore_file_config=True,
                start_line=line,
                end_line=line,
            )
        result = read(source)
        assert ("    Log    first    badly" in result) is first
        assert ("    Log    second    badly" in result) is second

    def test_merge_sections_across_blocks(self, tmp_path):
        source = tmp_path / "merge.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nFirst\n    Log    one\n```\n"
            "Prose\n```robot\n*** Test Cases ***\nSecond\n    Log    two\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(typer.Exit):
            format_files(
                sources=[source], select=["MergeAndOrderSections"], overwrite=True, cache=False, ignore_file_config=True
            )
        result = read(source)
        assert result.count("*** Test Cases ***") == 1
        assert "Second" in result
        assert "Prose" in result

    def test_formatter_disabler_spans_markdown_blocks(self, tmp_path):
        source = tmp_path / "disabled.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nExample\n    # robocop: fmt: off\n  Log  one\n```\n"
            "Prose\n```robot\n  Log  two\n    # robocop: fmt: on\n  Log  three\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(typer.Exit):
            format_files(sources=[source], overwrite=True, cache=False, ignore_file_config=True)
        result = read(source)
        assert "  Log  one" in result
        assert "  Log  two" in result
        assert "    Log    three" in result

    @pytest.mark.parametrize("formatted", [True, False])
    def test_prose_heavy_markdown(self, tmp_path, formatted):
        source = tmp_path / "large.md"
        spacing = "    " if formatted else "  "
        prose = "A line of prose.\n" * 4000
        original = (
            f"{prose}```robot\n*** Test Cases ***\nExample\n    Log{spacing}first\n```\n"
            f"{prose}```robot\n    Log{spacing}second\n```\n{prose}"
        )
        source.write_text(original, encoding="utf-8", newline="")
        with pytest.raises(typer.Exit):
            format_files(
                sources=[source],
                select=["NormalizeSeparators"],
                overwrite=True,
                cache=False,
                ignore_file_config=True,
            )
        result = read(source)
        assert result == original.replace(f"Log{spacing}", "Log    ")

    def test_prose_heavy_markdown_with_newline_normalization(self, tmp_path):
        source = tmp_path / "large.md"
        prose = "Prose.\n" * 4000
        original = (
            f"{prose}```robot\n*** Test Cases ***\nExample\n  Log  first\n```\n"
            f"{prose}```robot\n  Log  second\n```\n{prose}"
        )
        source.write_text(original, encoding="utf-8", newline="")
        with pytest.raises(typer.Exit):
            format_files(sources=[source], overwrite=True, cache=False, ignore_file_config=True)
        result = read(source)
        assert result == original.replace("  Log  ", "    Log    ")

    @pytest.mark.parametrize("line_ending", ["\n", "\r\n"])
    def test_format_removes_trailing_blank_code_lines_before_fence(self, tmp_path, line_ending):
        source = tmp_path / "whitespace.md"
        original = "Before\n```robot\n*** Test Cases ***\nExample\n    Log    value\n\n\n\n```\nAfter\n"
        with open(source, "w", encoding="utf-8", newline="") as stream:
            stream.write(original.replace("\n", line_ending))
        with pytest.raises(typer.Exit):
            format_files(
                sources=[source],
                select=["NormalizeNewLines"],
                overwrite=True,
                cache=False,
                ignore_file_config=True,
            )
        assert read(source) == original.replace("\n\n\n\n```\n", "\n```\n").replace("\n", line_ending)

    def test_format_applies_whitespace_with_other_changes(self, tmp_path):
        source = tmp_path / "whitespace.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nExample\n  Log  value\n\n\n\n```\nProse\n",
            encoding="utf-8",
            newline="",
        )
        with pytest.raises(typer.Exit):
            format_files(sources=[source], overwrite=True, cache=False, ignore_file_config=True, reruns=1)
        assert read(source) == "```robot\n*** Test Cases ***\nExample\n    Log    value\n```\nProse\n"

    def test_format_blank_lines_around_prose_is_idempotent(self, tmp_path):
        source = tmp_path / "whitespace.md"
        source.write_text(
            "```robot\n*** Test Cases ***\nExample\n    Log    one\n\n\n\n```\nProse\n"
            "```robot\n\n\n    Log    two\n\n\n\n```\nAfter\n",
            encoding="utf-8",
            newline="",
        )
        with pytest.raises(typer.Exit):
            format_files(sources=[source], overwrite=True, cache=False, ignore_file_config=True, reruns=1)
        result = read(source)
        assert "```\nProse\n```robot\n" in result
        assert "    Log    two\n```\nAfter\n" in result
        with pytest.raises(typer.Exit):
            format_files(sources=[source], overwrite=True, cache=False, ignore_file_config=True, reruns=1)
        assert read(source) == result
