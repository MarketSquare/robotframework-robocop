from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from robot.parsing.model import Block
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


class Diagnostic:
    def __init__(
        self,
        rule: Rule,
        source: str,
        lineno: int,
        col: int,
        end_lineno: int | None,
        end_col: int | None,
        node = None,
        extended_disablers: tuple[int, int] | None = None,
        sev_threshold_value: int | None = None,
        overwrite_severity=None,
        **kwargs,
    ) -> None:
        self.rule = rule
        self.source = source
        self.node = node
        self.range = self.get_range(lineno, col, end_lineno, end_col, node)
        self.extended_disablers = extended_disablers if extended_disablers else []
        self.reported_arguments = kwargs
        self.severity = self.get_severity(overwrite_severity, rule, sev_threshold_value)
        self._message = None

    @property
    def message(self) -> str:
        if self._message is None:
            self._message = self.rule.get_message(**self.reported_arguments)
        return self._message

    @staticmethod
    def get_range(lineno: int, col: int, end_lineno: int | None, end_col: int | None, node: type[Statement] | type[Block] | None) -> Range:
        """
        Return Range describing position of the issue.

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

    @staticmethod
    def get_severity(overwrite_severity, rule, sev_threshold_value):
        if overwrite_severity is not None:
            return overwrite_severity
        return rule.get_severity_with_threshold(sev_threshold_value)

    def __lt__(self, other: Diagnostic) -> bool:
        """Used to sort diagnostics for displaying purposes."""
        return (self.range.start.line, self.range.start.character, self.rule.rule_id) < (
            other.range.start.line,
            other.range.start.character,
            other.rule.rule_id,
        )

    def get_fullname(self) -> str:  # can be moved where it is used
        return f"{self.severity.value}{self.rule.rule_id} ({self.rule.name})"
