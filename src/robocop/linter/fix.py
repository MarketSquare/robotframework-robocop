from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from robot.api import Token

from robocop.files import path_relative_to_cwd

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing.model.statements import Statement

    from robocop.linter.diagnostics import Diagnostic, Range
    from robocop.linter.rules import Rule
    from robocop.source_file import SourceFile


class TextEditKind(Enum):
    """
    Enumeration of edit operation types.

    Attributes:
        REPLACEMENT (str): Replace an existing line or part of it with the new content.
        INSERTION (str): Insert a new line or lines without changing existing lines.
        DELETION (str): Delete line or lines.

    """

    REPLACEMENT = "replace"
    REPLACEMENT_LINES = "replace_lines"
    INSERTION = "insert"
    DELETION = "delete"


@dataclass
class TextEdit:
    """
    Represents a text edit operation to be applied to a document.

    For single-line replacement you can use column position to update existing lines.
    For multi-line replacement column position is ignored, and replacement replaces lines
    between start_line and end_line.
    If you want to update multiple lines without replacing them fully, use multiple TextEdit instances.

    Attributes:
        rule_id (str): The rule id that generated the fix.
        rule_name (str): The rule name that generated the fix.
        start_line (int): The 1-indexed line number where the edit begins.
        start_col (int): The 1-indexed column number where the edit begins.
        end_line (int): The 1-indexed line number where the edit ends.
        end_col (int): The 1-indexed column number where the edit ends.
        replacement (str): The text content to insert at the specified position,
            replacing the text between the start and end coordinates.

    """

    rule_id: str
    rule_name: str
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    replacement: str
    kind: TextEditKind = TextEditKind.REPLACEMENT

    @classmethod
    def replace_at_range(cls, rule_id: str, rule_name: str, diag_range: Range, replacement: str) -> TextEdit:
        return cls(
            rule_id=rule_id,
            rule_name=rule_name,
            start_line=diag_range.start.line,
            start_col=diag_range.start.character,
            end_line=diag_range.end.line,
            end_col=diag_range.end.character,
            replacement=replacement,
            kind=TextEditKind.REPLACEMENT,
        )

    @classmethod
    def replace_lines(cls, rule_id: str, rule_name: str, start_line: int, end_line: int, replacement: str) -> TextEdit:
        """Replace multiple lines between start_line and end_line."""
        return cls(
            rule_id=rule_id,
            rule_name=rule_name,
            start_line=start_line,
            start_col=1,
            end_line=end_line,
            end_col=1,
            replacement=replacement,
            kind=TextEditKind.REPLACEMENT_LINES,
        )

    @classmethod
    def remove_at_range(cls, rule_id: str, rule_name: str, diag_range: Range) -> TextEdit:
        """Remove lines between start_line and end_line from the edit range."""
        return cls(
            rule_id=rule_id,
            rule_name=rule_name,
            start_line=diag_range.start.line,
            start_col=1,
            end_line=diag_range.end.line,
            end_col=1,
            replacement="",
            kind=TextEditKind.DELETION,
        )

    @classmethod
    def insert_at_range(cls, rule_id: str, rule_name: str, diag_range: Range, replacement: str) -> TextEdit:
        """Insert new content at start_line."""
        return cls(
            rule_id=rule_id,
            rule_name=rule_name,
            start_line=diag_range.start.line,
            start_col=1,
            end_line=1,
            end_col=1,
            replacement=replacement,
            kind=TextEditKind.INSERTION,
        )


class FixApplicability(Enum):
    """
    Enumeration for categorizing the applicability level of a fix.

    Attributes:
        SAFE: Indicates that the fix can be automatically applied without manual
            intervention and is guaranteed to be correct and safe.
        UNSAFE: Indicates that the fix can be automatically applied but may
            introduce unintended side effects or require verification. Requires --fix-unsafe flag.
        MANUAL: Indicates that the fix requires manual implementation and cannot
            be automatically applied. Never applied automatically and only show suggestion.

    """

    SAFE = "safe"
    UNSAFE = "unsafe"
    MANUAL = "manual"


class FixAvailability(Enum):
    """
    Enumeration for indicating whether a rule can provide fixes.

    Attributes:
        NONE: Rule never provides fixes.
        SOMETIMES: Rule provides fixes for some violations but not all cases.
        ALWAYS: Rule always provides fixes for all violations it detects.

    """

    NONE = "none"
    SOMETIMES = "sometimes"
    ALWAYS = "always"


@dataclass
class Fix:
    edits: list[TextEdit]
    message: str
    applicability: FixApplicability


def _comment_lines(node: Statement, source_lines: list[str]) -> list[str]:
    """
    Return lines with the comments from the statement, without the statement data itself.

    Only the first comment in the line is used, since the rest of the line is taken as it is.
    The original indentation of the line is preserved.
    """
    comment_lines = []
    seen_lines = set()
    for token in node.get_tokens(Token.COMMENT):
        if token.lineno in seen_lines:
            continue
        seen_lines.add(token.lineno)
        line = source_lines[token.lineno - 1]
        indent = line[: len(line) - len(line.lstrip())]
        comment_lines.append(f"{indent}{line[token.col_offset :]}")
    return comment_lines


def remove_lines_fix(rule: Rule, start_line: int, end_line: int, message: str, replacement: str = "") -> Fix:
    """Create a fix that removes lines between ``start_line`` and ``end_line`` or replaces them with new content."""
    if replacement:
        edit = TextEdit.replace_lines(rule.rule_id, rule.name, start_line, end_line, replacement)
    else:
        edit = TextEdit(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            start_line=start_line,
            start_col=1,
            end_line=end_line,
            end_col=1,
            replacement="",
            kind=TextEditKind.DELETION,
        )
    return Fix(edits=[edit], message=message, applicability=FixApplicability.SAFE)


def remove_statement_fix(rule: Rule, node: Statement, source_lines: list[str], message: str) -> Fix:
    """
    Create a fix that removes the whole statement.

    Comments are not removed together with the statement - they are left in place instead.
    """
    comment_lines = _comment_lines(node, source_lines)
    return remove_lines_fix(rule, node.lineno, node.end_lineno, message, "".join(comment_lines))


def add_setting_value_fix(rule: Rule, node: Statement, value: str, message: str, separator: str = "    ") -> Fix:
    """Create a fix that adds the value to the setting without any value."""
    setting_token = node.data_tokens[0]
    column = setting_token.end_col_offset + 1
    edit = TextEdit(
        rule_id=rule.rule_id,
        rule_name=rule.name,
        start_line=setting_token.lineno,
        start_col=column,
        end_line=setting_token.lineno,
        end_col=column,
        replacement=f"{separator}{value}",
    )
    return Fix(edits=[edit], message=message, applicability=FixApplicability.SAFE)


def remove_empty_setting_fix(rule: Rule, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
    """
    Create a fix for the setting without any value.

    Empty settings are removed, unless they overwrite the suite setting. In such case the ``NONE`` value is used
    to make the intention explicit.
    """
    node = diag.node
    if node is None or not node.data_tokens:
        return None
    setting_name = node.data_tokens[0].value
    if diag.reported_arguments.get("overwrites_suite_setting"):
        return add_setting_value_fix(
            rule, node, "NONE", f"Replace empty '{setting_name}' setting with an explicit NONE value"
        )
    return remove_statement_fix(rule, node, source_lines, f"Remove empty '{setting_name}' setting")


@dataclass
class FixStats:
    """
    Statistics about applied fixes.

    Attributes:
        total_fixes: Total number of fixes applied.
        by_file: Dictionary mapping file paths to rule statistics.
                 Each entry contains (rule_id, rule_name) -> count.

    """

    total_fixes: int = 0
    by_file: dict[Path, dict[tuple[str, str], int]] = field(default_factory=dict)

    def format_summary(self) -> str:
        """
        Format the fix statistics as a human-readable summary.

        Returns:
            Formatted string with fix statistics grouped by file and rule.

        """
        if self.total_fixes == 0:
            return "No fixes applied."

        lines = [f"[green]Fixed {self.total_fixes} issue{'s' if self.total_fixes != 1 else ''}:[/green]"]
        for file_path in sorted(self.by_file.keys()):
            rules = self.by_file[file_path]
            lines.append(f"[bold]- {path_relative_to_cwd(file_path)}:[/bold]")
            # Sort by rule_id (first element of the tuple)
            for (rule_id, rule_name), count in sorted(rules.items(), key=lambda x: x[0][0]):
                lines.append(f"    {count} x [red]{rule_id}[/red] ({rule_name})")

        return "\n".join(lines) + "\n"


class FixApplier:
    def __init__(self) -> None:
        self.fix_stats = FixStats()
        self.modified_files: list[SourceFile] = []

    def apply_fixes(self, source_file: SourceFile, fixes: list[Fix]) -> bool:
        """
        Apply fixes to the source file.

        Args:
            source_file: The source file to apply fixes to.
            fixes: List of fixes to apply.

        Returns:
            Boolean object with the information whether fixes were applied.

        """
        if not fixes:
            return False
        # Filter by applicability - SAFE always, UNSAFE only if allowed, MANUAL never
        allow_unsafe = source_file.config.linter.unsafe_fixes
        applicable_fixes = [
            fix
            for fix in fixes
            if fix
            and (
                fix.applicability == FixApplicability.SAFE
                or (fix.applicability == FixApplicability.UNSAFE and allow_unsafe)
            )
        ]

        # Collect all edits from safe fixes
        all_edits = [edit for fix in applicable_fixes for edit in fix.edits]

        if not all_edits:
            return False

        sorted_edits = sorted(all_edits, key=lambda e: (e.start_line, e.start_col))
        non_overlapping_edits = self._remove_overlapping_edits(sorted_edits)

        if source_file.path not in self.fix_stats.by_file:
            self.fix_stats.by_file[source_file.path] = {}
        for edit in reversed(non_overlapping_edits):
            self._apply_edit(source_file.source_lines, edit)
            key = (edit.rule_id, edit.rule_name)
            self.fix_stats.by_file[source_file.path][key] = self.fix_stats.by_file[source_file.path].get(key, 0) + 1

        source_file.modified = True
        if source_file not in self.modified_files:
            self.modified_files.append(source_file)

        source_file.reload_model()
        return True

    @staticmethod
    def _remove_overlapping_edits(sorted_edits: list[TextEdit]) -> list[TextEdit]:
        """
        Remove overlapping edits, keeping only the first edit for each line.

        Args:
            sorted_edits: List of edits sorted by start line.

        Returns:
            List of non-overlapping edits.

        """
        non_overlapping = [sorted_edits[0]]

        for edit in sorted_edits[1:]:
            # Check if this edit starts after the previous edit ends
            previous = non_overlapping[-1]
            end_line = previous.end_line if previous.end_line is not None else previous.start_line
            if edit.start_line > end_line or FixApplier._is_after_on_the_same_line(previous, edit):
                non_overlapping.append(edit)

        return non_overlapping

    @staticmethod
    def _is_after_on_the_same_line(previous: TextEdit, edit: TextEdit) -> bool:
        """
        Check if both edits replace a part of the same line and do not overlap.

        Only single line replacements can be applied together, other kinds of edits replace, insert or delete
        whole lines.

        Returns:
            True if the edit can be applied together with the previous one.

        """
        single_line_kinds = (
            previous.kind == TextEditKind.REPLACEMENT
            and edit.kind == TextEditKind.REPLACEMENT
            and previous.start_line == previous.end_line
            and edit.start_line == edit.end_line
        )
        return single_line_kinds and previous.start_line == edit.start_line and edit.start_col >= previous.end_col

    @staticmethod
    def _apply_edit(lines: list[str], edit: TextEdit) -> None:
        """
        Apply a single edit to the list of lines (modifies in place).

        Args:
            lines: List of source file lines (0-indexed list).
            edit: The edit to apply (uses 1-indexed line/col numbers).

        """
        # TODO: different kind of edits should have different apply_edit
        if edit.end_line > len(lines) or edit.start_line < 1:
            return

        start_line_idx = edit.start_line - 1
        end_line_idx = edit.end_line - 1

        if edit.kind == TextEditKind.REPLACEMENT_LINES:
            lines[start_line_idx : end_line_idx + 1] = edit.replacement.splitlines(keepends=True)
        elif edit.kind == TextEditKind.REPLACEMENT:
            start_col_idx = edit.start_col - 1
            end_col_idx = edit.end_col - 1
            if start_line_idx == end_line_idx:  # single line
                line = lines[edit.start_line - 1]
                new_line = line[:start_col_idx] + edit.replacement + line[end_col_idx:]
                lines[start_line_idx : start_line_idx + 1] = new_line.splitlines(keepends=True)
            else:  # Multi-line edit
                # When edit is multiline, we replace the lines fully
                lines[start_line_idx : end_line_idx + 2] = edit.replacement.splitlines(keepends=True)
        elif edit.kind == TextEditKind.INSERTION:
            lines[start_line_idx:start_line_idx] = edit.replacement.splitlines(keepends=True)
        elif edit.kind == TextEditKind.DELETION:
            del lines[start_line_idx : edit.end_line]
