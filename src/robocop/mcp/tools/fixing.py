"""LLM-assisted fixing tools for MCP."""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path

from fastmcp.exceptions import ToolError

from robocop.mcp.tools.linting import _lint_content_impl
from robocop.mcp.tools.models import (
    ApplyFixResult,
    CodeSnippet,
    DiagnosticResult,
    FixReplacement,
    GetFixContextResult,
    IssueForFix,
)
from robocop.mcp.tools.utils.constants import VALID_EXTENSIONS


def _build_llm_guidance(issues: list[IssueForFix], start_line: int, end_line: int) -> str:
    """
    Build structured guidance for the LLM to generate a fix.

    Args:
        issues: List of issues to fix.
        start_line: First line of the target snippet.
        end_line: Last line of the target snippet.

    Returns:
        A formatted string with guidance for the LLM.

    """
    if not issues:
        return "No issues found in the target area."

    lines = [
        "Fix the following Robot Framework code issue(s):",
        "",
    ]

    for i, issue in enumerate(issues, 1):
        lines.extend(
            (
                f"## Issue {i}: {issue.name} ({issue.rule_id})",
                f"## Issue {i}: {issue.name} ({issue.rule_id})",
                f"- **Line:** {issue.line}",
                f"- **Severity:** {issue.severity}",
                f"- **Message:** {issue.message}",
            )
        )
        if issue.fix_suggestion:
            lines.append(f"- **Suggestion:** {issue.fix_suggestion}")
        lines.append("")

    lines.extend(
        [
            "## Instructions",
            f"The target code is shown between lines {start_line} and {end_line}.",
            "Generate the corrected code that fixes all issues listed above.",
            "",
            "**Requirements:**",
            "- Preserve correct Robot Framework syntax and indentation",
            "- Only fix the issues mentioned - do not make other changes",
            "- Return ONLY the corrected code for the target lines",
            "- Do not include line numbers or markdown code fences",
        ]
    )

    return "\n".join(lines)


def _get_line_range(content: str, line: int | None, context_lines: int) -> tuple[int, int]:
    """
    Calculate the line range for the target snippet.

    Args:
        content: The full source code content.
        line: The target line (1-indexed), or None for full content.
        context_lines: Number of context lines before and after.

    Returns:
        A tuple of (start_line, end_line), both 1-indexed.

    """
    lines = content.splitlines()
    total_lines = len(lines)

    if line is None:
        return 1, total_lines

    # Convert to 0-indexed for calculation
    line_idx = line - 1
    start_idx = max(0, line_idx - context_lines)
    end_idx = min(total_lines - 1, line_idx + context_lines)

    # Convert back to 1-indexed
    return start_idx + 1, end_idx + 1


def _extract_snippet(content: str, start_line: int, end_line: int) -> str:
    """
    Extract a code snippet from content.

    Args:
        content: The full source code content.
        start_line: First line to include (1-indexed).
        end_line: Last line to include (1-indexed).

    Returns:
        The extracted snippet as a string.

    """
    lines = content.splitlines()
    # Convert to 0-indexed
    start_idx = start_line - 1
    end_idx = end_line  # end_line is inclusive, so we use it directly for slicing

    return "\n".join(lines[start_idx:end_idx])


def _get_fix_context_impl(
    content: str | None = None,
    file_path: str | None = None,
    filename: str = "stdin.robot",
    line: int | None = None,
    rule_ids: list[str] | None = None,
    context_lines: int = 5,
) -> GetFixContextResult:
    """
    Get context for LLM-assisted fixing of Robot Framework code issues.

    Args:
        content: Robot Framework source code (use this OR file_path).
        file_path: Path to the file (use this OR content).
        filename: Virtual filename when using content.
        line: Specific line to get context for (None = all issues).
        rule_ids: Filter to specific rule IDs.
        context_lines: Lines of context before and after target.

    Returns:
        A GetFixContextResult with all context needed for LLM to generate a fix.

    Raises:
        ToolError: If neither content nor file_path provided, or both provided.

    """
    from robocop.mcp.cache import get_linter_config

    # Validate inputs
    if content is None and file_path is None:
        raise ToolError("Either 'content' or 'file_path' must be provided.")
    if content is not None and file_path is not None:
        raise ToolError("Provide either 'content' or 'file_path', not both.")

    # Read file if needed
    resolved_file_path: str | None = None
    if file_path is not None:
        path = Path(file_path)
        if not path.exists():
            raise ToolError(f"File not found: {file_path}")
        if path.suffix not in VALID_EXTENSIONS:
            raise ToolError(f"Invalid file type: {path.suffix}. Expected one of: {', '.join(VALID_EXTENSIONS)}")
        content = path.read_text(encoding="utf-8")
        resolved_file_path = str(path)
        filename = path.name

    # Lint to find issues
    issues = _lint_content_impl(content, filename, select=rule_ids)

    # Filter issues by line if specified
    if line is not None:
        # Get issues at or near the target line (within context range)
        issues = [i for i in issues if abs(i.line - line) <= context_lines]

    # Calculate target snippet range
    if line is not None:
        start_line, end_line = _get_line_range(content, line, context_lines)
    elif issues:
        # If no specific line, use the range covering all issues
        min_line = min(i.line for i in issues)
        max_line = max(i.end_line for i in issues)
        start_line = max(1, min_line - context_lines)
        end_line = min(len(content.splitlines()), max_line + context_lines)
    else:
        # No issues found, return full content
        start_line, end_line = 1, len(content.splitlines())

    # Extract snippet
    snippet_content = _extract_snippet(content, start_line, end_line)

    # Get rule details for each issue
    linter_config = get_linter_config()
    rules = linter_config.rules

    issues_for_fix: list[IssueForFix] = []
    for issue in issues:
        rule = rules.get(issue.rule_id)
        fix_suggestion = rule.fix_suggestion if rule else None
        rule_docs = rule.docs if rule else None

        issues_for_fix.append(
            IssueForFix(
                rule_id=issue.rule_id,
                name=issue.name,
                message=issue.message,
                severity=issue.severity,
                line=issue.line,
                column=issue.column,
                end_line=issue.end_line,
                end_column=issue.end_column,
                fix_suggestion=fix_suggestion,
                rule_docs=rule_docs,
            )
        )

    # Build LLM guidance
    llm_guidance = _build_llm_guidance(issues_for_fix, start_line, end_line)

    return GetFixContextResult(
        file_path=resolved_file_path,
        full_content=content,
        target_snippet=CodeSnippet(
            content=snippet_content,
            start_line=start_line,
            end_line=end_line,
        ),
        issues=issues_for_fix,
        llm_guidance=llm_guidance,
    )


def _apply_replacement(content: str, replacement: FixReplacement) -> str:
    """
    Apply a line-based replacement to content.

    Args:
        content: The original source code content.
        replacement: The replacement to apply.

    Returns:
        The content with the replacement applied.

    Raises:
        ToolError: If the replacement indices are invalid.

    """
    lines = content.splitlines(keepends=True)

    # Handle case where content doesn't end with newline
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    # Convert to 0-indexed
    start_idx = replacement.start_line - 1
    end_idx = replacement.end_line  # end_line is inclusive

    # Validate indices
    if start_idx < 0 or start_idx >= len(lines):
        raise ToolError(f"Invalid start_line: {replacement.start_line}. File has {len(lines)} lines.")
    if end_idx < start_idx or end_idx > len(lines):
        raise ToolError(f"Invalid end_line: {replacement.end_line}. File has {len(lines)} lines.")

    # Prepare new content lines
    new_lines = replacement.new_content.splitlines(keepends=True)
    if new_lines and not new_lines[-1].endswith("\n"):
        new_lines[-1] += "\n"

    # Apply replacement
    result_lines = lines[:start_idx] + new_lines + lines[end_idx:]

    result = "".join(result_lines)
    # Remove trailing newline if original didn't have one
    if not content.endswith("\n") and result.endswith("\n"):
        result = result[:-1]

    return result


def _generate_diff(original: str, modified: str, filename: str) -> str | None:
    """
    Generate a unified diff between original and modified content.

    Args:
        original: The original content.
        modified: The modified content.
        filename: The filename to use in the diff header.

    Returns:
        A unified diff string, or None if no changes.

    """
    if original == modified:
        return None

    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )

    return "".join(diff)


def _apply_fix_impl(
    content: str | None = None,
    file_path: str | None = None,
    filename: str = "stdin.robot",
    replacement: FixReplacement | None = None,
    overwrite: bool = False,
    validate: bool = True,
    select: list[str] | None = None,
    ignore: list[str] | None = None,
) -> ApplyFixResult:
    """
    Apply an LLM-generated fix to Robot Framework code.

    Args:
        content: Original Robot Framework source code (use this OR file_path).
        file_path: Path to the file to fix (use this OR content).
        filename: Virtual filename when using content.
        replacement: The line-based replacement to apply.
        overwrite: Whether to write the fix to disk (only with file_path).
        validate: Whether to re-lint and validate the fix.
        select: Rule IDs to check in validation.
        ignore: Rule IDs to ignore in validation.

    Returns:
        An ApplyFixResult with success status, diff, and issue counts.

    Raises:
        ToolError: If inputs are invalid or replacement fails.

    """
    # Validate inputs
    if content is None and file_path is None:
        raise ToolError("Either 'content' or 'file_path' must be provided.")
    if content is not None and file_path is not None:
        raise ToolError("Provide either 'content' or 'file_path', not both.")
    if replacement is None:
        raise ToolError("'replacement' is required.")

    # Read file if needed
    resolved_file_path: str | None = None
    if file_path is not None:
        path = Path(file_path)
        if not path.exists():
            raise ToolError(f"File not found: {file_path}")
        if path.suffix not in VALID_EXTENSIONS:
            raise ToolError(f"Invalid file type: {path.suffix}. Expected one of: {', '.join(VALID_EXTENSIONS)}")
        content = path.read_text(encoding="utf-8")
        resolved_file_path = str(path)
        filename = path.name

    # Count issues before fix
    issues_before_list = _lint_content_impl(content, filename, select=select, ignore=ignore)
    issues_before = len(issues_before_list)

    # Apply the replacement
    try:
        new_content = _apply_replacement(content, replacement)
    except ToolError:
        raise
    except Exception as e:
        raise ToolError(f"Failed to apply replacement: {e}") from e

    # Generate diff
    diff = _generate_diff(content, new_content, filename)

    # Validate by re-linting
    issues_after = 0
    remaining_issues: list[DiagnosticResult] | None = None
    validation_error: str | None = None
    success = True

    if validate:
        try:
            issues_after_list = _lint_content_impl(new_content, filename, select=select, ignore=ignore)
            issues_after = len(issues_after_list)
            remaining_issues = issues_after_list[:10] if issues_after_list else None

            # Check if fix made things worse
            if issues_after > issues_before:
                validation_error = f"Fix introduced new issues: {issues_before} before, {issues_after} after."
                success = False
        except ToolError as e:
            validation_error = f"Validation failed: {e}"
            success = False

    # Write to file if requested
    written = False
    if overwrite and resolved_file_path and success:
        path = Path(resolved_file_path)
        path.write_text(new_content, encoding="utf-8")
        written = True

    issues_fixed = max(0, issues_before - issues_after)

    return ApplyFixResult(
        success=success,
        file_path=resolved_file_path,
        written=written,
        new_content=new_content,
        diff=diff,
        issues_before=issues_before,
        issues_after=issues_after,
        issues_fixed=issues_fixed,
        remaining_issues=remaining_issues,
        validation_error=validation_error,
    )
