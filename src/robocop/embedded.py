"""
Extraction of embedded Robot Framework code blocks from Markdown and Python files.

Robot Framework 7.5 added support for executing Robot code embedded in Markdown files. The code lives in fenced
code blocks tagged with ``robotframework`` (or ``robot``)::

    ```robotframework
    *** Test Cases ***
    Example
        Log    message
    ```

The same convention is used to embed runnable examples in Python docstrings (see Robot Framework's own
``Collections`` library). Robocop supports both sources.

Unlike Robot Framework -- which concatenates every block and throws away line positions -- Robocop needs to keep
the exact physical position (line and column) of each block so that reported issues and applied fixes point at the
right place in the original file. This module extracts blocks while preserving that information.

The extraction is intentionally line based (it does not parse Python syntax). A fenced ``robotframework`` block is
recognized wherever it appears, which covers both Markdown prose and Python docstrings. Blocks nested inside
indented docstrings keep their common indentation, which is stripped when the block is turned into a Robot model
and re-applied when the file is written back.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from robot.api.parsing import ModelVisitor

if TYPE_CHECKING:
    from robot.parsing.model import File
    from robot.parsing.model.statements import Statement

# Supported code block languages (case-insensitive), mirroring Robot Framework's Markdown parser.
ROBOT_BLOCK_LANGUAGES = frozenset({"robotframework", "robot"})

# File extensions that may contain embedded Robot Framework code blocks.
MARKDOWN_EXTENSIONS = frozenset({".md", ".markdown"})
PYTHON_EXTENSIONS = frozenset({".py"})
EMBEDDED_EXTENSIONS = MARKDOWN_EXTENSIONS | PYTHON_EXTENSIONS

# Opening fence: optional indentation, at least three backticks or tildes, then the language token.
_FENCE_OPEN = re.compile(r"(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})[ \t]*(?P<lang>\S+)")


@dataclass
class RobotCodeBlock:
    """
    A single embedded Robot Framework code block located inside a Markdown or Python file.

    Attributes:
        start_line: 1-indexed physical line number of the first code line (line just after the opening fence).
        end_line: 1-indexed physical line number of the last code line (inclusive). For an empty block this is
            ``start_line - 1`` so that ``range(start_line, end_line + 1)`` is empty.
        indent: Common leading whitespace shared by every non-blank code line. It is stripped when building the
            Robot model and re-applied when writing changes back to the file.
        fence_open_line: 1-indexed physical line number of the opening fence.
        fence_close_line: 1-indexed physical line number of the closing fence, or ``None`` if the block is closed
            implicitly by the end of the file.

    """

    start_line: int
    end_line: int
    indent: str
    fence_open_line: int
    fence_close_line: int | None

    @property
    def is_empty(self) -> bool:
        return self.end_line < self.start_line

    def contains(self, lineno: int) -> bool:
        """Return whether the given 1-indexed physical line is a code line of this block."""
        return self.start_line <= lineno <= self.end_line


def is_embedded_extension(suffix: str) -> bool:
    """Return whether files with the given suffix may contain embedded Robot Framework code blocks."""
    return suffix.lower() in EMBEDDED_EXTENSIONS


def _common_indent(lines: list[str]) -> str:
    """
    Return the longest leading whitespace shared by every non-blank line.

    Blank lines (only whitespace or empty) are ignored, mirroring :func:`textwrap.dedent`.
    """
    common: str | None = None
    for line in lines:
        stripped = line.lstrip(" \t")
        if not stripped or stripped in ("\n", "\r\n", "\r"):
            continue
        indent = line[: len(line) - len(stripped)]
        if common is None:
            common = indent
            continue
        # Shrink the common prefix to the shared portion.
        shared_len = 0
        for a, b in zip(common, indent, strict=False):
            if a != b:
                break
            shared_len += 1
        common = common[:shared_len]
        if not common:
            break
    return common or ""


def extract_robot_blocks(lines: list[str]) -> list[RobotCodeBlock]:
    """
    Find all embedded Robot Framework code blocks in the given file lines.

    Args:
        lines: The physical file lines, including line endings (as returned by ``file.readlines()``).

    Returns:
        List of :class:`RobotCodeBlock`, in file order. Empty if the file has no Robot code blocks.

    """
    blocks: list[RobotCodeBlock] = []
    total = len(lines)
    index = 0
    while index < total:
        match = _FENCE_OPEN.match(lines[index])
        if not match or match.group("lang").lower() not in ROBOT_BLOCK_LANGUAGES:
            index += 1
            continue
        fence = match.group("fence")
        fence_char = re.escape(fence[0])
        # Closing fence: at least as many of the same fence character, optionally surrounded by whitespace.
        close_re = re.compile(rf"[ \t]*{fence_char}{{{len(fence)},}}[ \t]*$")
        fence_open_line = index + 1
        code_lines: list[str] = []
        cursor = index + 1
        while cursor < total and not close_re.match(lines[cursor].rstrip("\r\n")):
            code_lines.append(lines[cursor])
            cursor += 1
        start_line = index + 2
        end_line = cursor  # cursor is the closing fence (or EOF); last code line is cursor - 1 (0-indexed) -> cursor
        fence_close_line = cursor + 1 if cursor < total else None
        blocks.append(
            RobotCodeBlock(
                start_line=start_line,
                end_line=end_line,
                indent=_common_indent(code_lines),
                fence_open_line=fence_open_line,
                fence_close_line=fence_close_line,
            )
        )
        index = cursor + 1
    return blocks


def strip_indent(line: str, indent: str) -> str:
    """Remove up to ``indent`` leading characters from ``line`` (only if the line starts with that indentation)."""
    if indent and line.startswith(indent):
        return line[len(indent) :]
    # Blank or shorter-indented lines: drop whatever leading whitespace overlaps the common indent.
    stripped = line.lstrip(" \t")
    leading = line[: len(line) - len(stripped)]
    keep = leading[len(indent) :] if len(leading) > len(indent) else ""
    return keep + stripped


def reconstruct_source(lines: list[str], blocks: list[RobotCodeBlock]) -> str:
    """
    Build a Robot Framework source string that preserves physical line numbers.

    Non-code lines (prose, fences, Python code) are replaced with blank lines and code lines are dedented by their
    block indentation. The resulting model therefore has line numbers matching the original file, while section
    headers and statements start at column 0 as Robot Framework requires.

    Args:
        lines: The physical file lines, including line endings.
        blocks: Blocks extracted from ``lines`` via :func:`extract_robot_blocks`.

    Returns:
        Robot Framework source text with one entry per physical line.

    """
    reconstructed = ["\n"] * len(lines)
    for block in blocks:
        for lineno in range(block.start_line, block.end_line + 1):
            original = lines[lineno - 1]
            newline = _line_ending(original)
            reconstructed[lineno - 1] = strip_indent(original.rstrip("\r\n"), block.indent) + newline
    return "".join(reconstructed)


def _line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


class _LineShifter(ModelVisitor):  # type: ignore[misc]
    """Shift every token line number by a fixed offset, turning block-local lines into physical file lines."""

    def __init__(self, offset: int) -> None:
        self.offset = offset

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        for token in node.tokens:
            token.lineno += self.offset


def shift_model_lines(model: File, offset: int) -> File:
    """Add ``offset`` to every token line number in the model (in place) and return it."""
    if offset:
        _LineShifter(offset).visit(model)
    return model
