from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from robot.parsing.model import Block, File
    from robot.parsing.model.statements import Statement

    from robocop.linter.rules import Rule


@dataclass
class Position:
    line: int
    character: int


@dataclass
class Range:
    start: Position
    end: Position


class Diagnostics:
    def __init__(self, diagnostics: list[Diagnostic]) -> None:
        self.diagnostics = diagnostics
        self.diag_by_source = self.group_diag_by_source()

    def group_diag_by_source(self) -> dict[str, list[Diagnostic]]:
        diag_by_source: dict[str, list[Diagnostic]] = {}
        for diagnostic in self.diagnostics:
            source_str = str(diagnostic.source)
            if source_str not in diag_by_source:
                diag_by_source[source_str] = []
            diag_by_source[source_str].append(diagnostic)
        for source, diags in diag_by_source.items():
            diag_by_source[source] = sorted(diags)
        return diag_by_source

    def __iter__(self) -> Iterator[Diagnostic]:
        yield from self.diagnostics


class Diagnostic:
    def __init__(
        self,
        rule: Rule,
        source: str | Path,
        model: File | None,
        lineno: int | None,
        col: int | None,
        end_lineno: int | None,
        end_col: int | None,
        node: Statement | Block | None = None,
        extended_disablers: tuple[int, int] | None = None,
        sev_threshold_value: int | None = None,
        **kwargs: object,
    ) -> None:
        self.rule = rule
        self.source = source
        self.node = node
        self.range = self.get_range(lineno, col, end_lineno, end_col, node)
        self.extended_disablers = extended_disablers if extended_disablers else []
        self.reported_arguments = kwargs
        self.severity = rule.get_severity_with_threshold(sev_threshold_value)
        self.model = model
        self._message = None

    @property
    def message(self) -> str:
        return self.rule.message.format(**self.reported_arguments)

    @staticmethod
    def get_range(
        lineno: int | None, col: int | None, end_lineno: int | None, end_col: int | None, node: Statement | Block | None
    ) -> Range:
        """
        Return Range describing the position of the issue.

        Args:
            lineno: start line of the issue
            col: start column of the issue
            end_lineno: optional end line of the issue - if not provided, start line is used
            end_col: optional end column of the issue - if not provided, end column is used
            node: optional source node. Its position is used if lineno or col are not provided

        """
        if not lineno:
            lineno = node.lineno if node and node.lineno > -1 else 1
        if not col:
            col = node.col_offset + 1 if node else 1
        start = Position(line=lineno, character=col)
        end_lineno = lineno if end_lineno is None else end_lineno
        end_col = col if end_col is None else end_col
        end = Position(line=end_lineno, character=end_col)
        return Range(start=start, end=end)

    def __lt__(self, other: Diagnostic) -> bool:
        """Sort diagnostics for displaying purposes."""
        return (self.range.start.line, self.range.start.character, self.rule.rule_id) < (
            other.range.start.line,
            other.range.start.character,
            other.rule.rule_id,
        )
