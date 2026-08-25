"""
Checker for rules that analyze the raw file content.

Rules that inspect the source lines instead of the parsed Robot Framework model are all handled by a single
checker, so the file content is only iterated once. Rule definitions stay in their own category modules
(``comments``, ``lengths``, ``spacing``) - only the ``check`` methods are called from here.
"""

from __future__ import annotations

from codecs import BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE
from typing import TYPE_CHECKING

from robocop.linter.rules import RawFileChecker, comments, lengths, spacing

if TYPE_CHECKING:
    from pathlib import Path

BOM_MARKERS = (BOM_UTF32_BE, BOM_UTF32_LE, BOM_UTF8, BOM_UTF16_LE, BOM_UTF16_BE)


class RawFileRulesChecker(RawFileChecker):
    """Checker for rules reported based on the raw file content."""

    trailing_whitespace: spacing.TrailingWhitespaceRule
    missing_trailing_blank_line: spacing.MissingTrailingBlankLineRule
    too_many_trailing_blank_lines: spacing.TooManyTrailingBlankLinesRule
    line_too_long: lengths.LineTooLongRule
    ignored_data: comments.IgnoredDataRule
    bom_encoding_in_file: comments.BomEncodingRule

    def parse_file(self) -> None:
        self.lines = self.source_file.source_lines
        if self.ignored_data.enabled or self.bom_encoding_in_file.enabled:
            is_bom = detect_bom(self.source_file.path)
            self.bom_encoding_in_file.check(is_bom)
            self.ignored_data.check(self.lines, is_bom)
        if self.trailing_whitespace.enabled or self.line_too_long.enabled:
            doc_lines: frozenset[int] = frozenset()
            if self.line_too_long.enabled and self.line_too_long.ignore_docs:
                doc_lines = self.line_too_long.get_documentation_lines(self.source_file.model)
            for lineno, line in enumerate(self.lines, start=1):
                self.trailing_whitespace.check(line, lineno)
                self.line_too_long.check(line, lineno, doc_lines)
        self.too_many_trailing_blank_lines.check(self.lines)
        self.missing_trailing_blank_line.check(self.lines)


def detect_bom(source: Path) -> bool:
    """Return whether the file starts with a Byte Order Mark."""
    try:
        with open(source, "rb") as raw_file:
            first_four = raw_file.read(4)
    except OSError:
        return False
    return any(first_four.startswith(bom_marker) for bom_marker in BOM_MARKERS)
