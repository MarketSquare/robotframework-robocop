from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
import typer

from robocop.embedded import extract_robot_blocks, is_embedded_extension
from robocop.run import check_files, format_files
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
