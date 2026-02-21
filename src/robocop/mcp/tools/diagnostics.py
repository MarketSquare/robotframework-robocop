"""Higher-level analysis tools - statistics, suggestions, and explanations."""

from __future__ import annotations

import operator
from pathlib import Path
from typing import Literal

from fastmcp.exceptions import ToolError

from robocop.mcp.tools.batch_operations import _collect_robot_files
from robocop.mcp.tools.linting import _lint_content_impl, _lint_file_impl
from robocop.mcp.tools.models import (
    CodeContext,
    ContextLine,
    ExplainIssueResult,
    FixSuggestion,
    GetStatisticsResult,
    IssueExplanation,
    QualityScore,
    RelatedIssue,
    SeveritySummary,
    StatisticsSummary,
    SuggestFixesResult,
    TopRule,
    WorstFile,
    WorstFilesResult,
)


def _suggest_fixes_impl(
    content: str, filename: str = "stdin.robot", rule_ids: list[str] | None = None, config_path: Path | None = None
) -> SuggestFixesResult:
    """
    Suggest fixes for linting issues in Robot Framework code.

    Args:
        content: The Robot Framework source code to analyze.
        filename: The virtual filename (affects parsing).
        rule_ids: Optional list of rule IDs to get suggestions for.
        config_path: Path to the Robocop toml configuration file

    Returns:
        A SuggestFixesResult model containing fix suggestions.

    """
    from robocop.mcp.cache import get_linter_config

    # Get lint issues first
    issues = _lint_content_impl(content, filename, select=rule_ids)

    # Get rule objects to look up fix_suggestion attribute
    linter_config = get_linter_config(config_path)
    rules = linter_config.rules

    fixes: list[FixSuggestion] = []
    auto_fixable = 0
    manual_required = 0

    for issue in issues:
        rule_id = issue.rule_id
        category = rule_id[:3] if len(rule_id) >= 3 else rule_id

        # Get suggestion from rule's fix_suggestion attribute, or provide a generic one
        suggestion: str
        if rule_id in rules and rules[rule_id].fix_suggestion:
            suggestion = str(rules[rule_id].fix_suggestion)
        else:
            suggestion = f"Review the rule documentation for {rule_id} ({issue.name})."

        # Determine if auto-fixable (formatting issues generally are)
        is_auto_fixable = category in {"SPACE", "MISC"} or rule_id == "LEN08"

        if is_auto_fixable:
            auto_fixable += 1
        else:
            manual_required += 1

        fixes.append(
            FixSuggestion(
                rule_id=rule_id,
                name=issue.name,
                line=issue.line,
                message=issue.message,
                suggestion=suggestion,
                auto_fixable=is_auto_fixable,
            )
        )

    return SuggestFixesResult(
        fixes=fixes,
        total_issues=len(fixes),
        auto_fixable=auto_fixable,
        manual_required=manual_required,
        recommendation=(
            "Run format_content to apply automatic fixes, then address manual fixes."
            if auto_fixable > 0
            else "All issues require manual fixes."
        ),
    )


def _get_statistics_impl(
    directory_path: str,
    recursive: bool = True,
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
    *,
    configure: list[str] | None = None,
) -> GetStatisticsResult:
    """
    Get statistics about code quality in a directory.

    Args:
        directory_path: Path to the directory to analyze.
        recursive: Whether to search subdirectories.
        select: List of rule IDs to enable.
        ignore: List of rule IDs to ignore.
        threshold: Minimum severity threshold.
        configure: List of rule configurations.

    Returns:
        A GetStatisticsResult model containing statistics about the codebase.

    Raises:
        ToolError: If the directory does not exist or contains no files.

    """
    path = Path(directory_path)

    if not path.exists():
        raise ToolError(f"Directory not found: {directory_path}")

    if not path.is_dir():
        raise ToolError(f"Not a directory: {directory_path}")

    files = _collect_robot_files(path, recursive)

    if not files:
        raise ToolError(f"No .robot or .resource files found in {directory_path}")

    # Collect all issues
    files_with_issues = 0
    files_clean = 0
    severity_counts = {"E": 0, "W": 0, "I": 0}
    rule_counts: dict[str, int] = {}
    issues_per_file: list[int] = []
    total_issues = 0

    for file in files:
        try:
            issues = _lint_file_impl(
                str(file),
                select,
                ignore,
                threshold,
                include_file_in_result=True,
                configure=configure,
            )
            issues_per_file.append(len(issues))

            if issues:
                files_with_issues += 1
                total_issues += len(issues)
                for issue in issues:
                    severity = issue.severity
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                    rule_id = issue.rule_id
                    rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
            else:
                files_clean += 1
        except ToolError:
            # Skip files that fail to parse
            pass

    total_files = len(files)

    # Calculate statistics
    avg_issues_per_file = total_issues / total_files if total_files > 0 else 0
    max_issues_in_file = max(issues_per_file) if issues_per_file else 0

    # Find top 10 most common rules
    top_rules = sorted(rule_counts.items(), key=operator.itemgetter(1), reverse=True)[:10]

    # Calculate a simple quality score (0-100)
    # Score decreases based on issues per file, weighted by severity
    weighted_issues = severity_counts["E"] * 3 + severity_counts["W"] * 1.5 + severity_counts["I"] * 0.5
    issues_ratio = weighted_issues / total_files if total_files > 0 else 0
    quality_score = max(0, min(100, int(100 - issues_ratio * 10)))

    # Determine quality grade
    grade: Literal["A", "B", "C", "D", "F"]
    if quality_score >= 90:
        grade = "A"
        quality_label = "Excellent"
    elif quality_score >= 80:
        grade = "B"
        quality_label = "Good"
    elif quality_score >= 70:
        grade = "C"
        quality_label = "Fair"
    elif quality_score >= 60:
        grade = "D"
        quality_label = "Poor"
    else:
        grade = "F"
        quality_label = "Critical"

    return GetStatisticsResult(
        directory=str(path),
        summary=StatisticsSummary(
            total_files=total_files,
            files_with_issues=files_with_issues,
            files_clean=files_clean,
            total_issues=total_issues,
            avg_issues_per_file=round(avg_issues_per_file, 2),
            max_issues_in_file=max_issues_in_file,
        ),
        severity_breakdown=SeveritySummary(E=severity_counts["E"], W=severity_counts["W"], INFO=severity_counts["I"]),
        top_issues=[TopRule(rule_id=rule_id, count=count) for rule_id, count in top_rules],
        quality_score=QualityScore(
            score=quality_score,
            grade=grade,
            label=quality_label,
        ),
        recommendations=_generate_recommendations(severity_counts, top_rules, quality_score),
    )


def _generate_recommendations(
    severity_counts: dict[str, int],
    top_rules: list[tuple[str, int]],
    quality_score: int,
) -> list[str]:
    """
    Generate recommendations based on statistics.

    Args:
        severity_counts: Count of issues by severity level.
        top_rules: List of (rule_id, count) tuples sorted by count.
        quality_score: The calculated quality score (0-100).

    Returns:
        A list of recommendation strings.

    """
    recommendations = []

    if severity_counts["E"] > 0:
        recommendations.append(f"Fix {severity_counts['E']} error(s) first - these may cause test failures.")

    if top_rules:
        top_rule_id, top_count = top_rules[0]
        if top_count > 5:
            recommendations.append(
                f"Address '{top_rule_id}' which appears {top_count} times - "
                f"fixing this pattern will significantly reduce issues."
            )

    if quality_score < 70:
        recommendations.append("Consider running the formatter to auto-fix style issues.")

    if not recommendations:
        recommendations.append("Code quality is good. Keep up the good work!")

    return recommendations


def _explain_issue_impl(
    content: str,
    line: int,
    filename: str = "stdin.robot",
    context_lines: int = 3,
    config_path: Path | None = None,
) -> ExplainIssueResult:
    """
    Explain a specific issue at a given line with context.

    Args:
        content: The Robot Framework source code.
        line: The line number to explain (1-indexed).
        filename: The virtual filename.
        context_lines: Number of context lines to include before and after.
        config_path: Path to the Robocop toml configuration file

    Returns:
        An ExplainIssueResult model containing the issue explanation with context.

    """
    from robocop.mcp.cache import get_linter_config

    # Lint the content to find issues
    issues = _lint_content_impl(content, filename)

    # Find issues at or near the specified line
    issues_at_line = [i for i in issues if i.line == line]
    issues_near_line = [i for i in issues if abs(i.line - line) <= 2 and i.line != line]

    if not issues_at_line and not issues_near_line:
        return ExplainIssueResult(
            line=line,
            issues_found=False,
            message=f"No issues found at or near line {line}.",
            context=_get_line_context(content, line, context_lines),
        )

    # Get rule documentation for issues
    linter_config = get_linter_config(config_path)
    rules = linter_config.rules

    explanations: list[IssueExplanation] = []
    for issue in issues_at_line:
        rule_id = issue.rule_id
        rule = rules.get(rule_id)

        configurable_parameters = None
        why_it_matters = None
        fix_suggestion = None
        full_documentation = None

        if rule:
            why_it_matters = rule.docs.split("\n")[0] if rule.docs else None
            fix_suggestion = rule.fix_suggestion
            full_documentation = rule.docs
            if rule.parameters:
                configurable_parameters = [
                    {"name": p.name, "description": p.desc, "default": str(p.raw_value)} for p in rule.parameters
                ]

        explanations.append(
            IssueExplanation(
                rule_id=rule_id,
                name=issue.name,
                message=issue.message,
                severity=issue.severity,
                line=issue.line,
                column=issue.column,
                why_it_matters=why_it_matters,
                fix_suggestion=fix_suggestion,
                full_documentation=full_documentation,
                configurable_parameters=configurable_parameters,
            )
        )

    # Include nearby issues as related
    related_issues = [
        RelatedIssue(rule_id=i.rule_id, name=i.name, line=i.line, message=i.message) for i in issues_near_line
    ]

    return ExplainIssueResult(
        line=line,
        issues_found=True,
        issues=explanations,
        related_issues=related_issues,
        context=_get_line_context(content, line, context_lines),
    )


def _worst_files_impl(
    directory_path: str,
    n: int = 10,
    recursive: bool = True,
    *,
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
    configure: list[str] | None = None,
    config_path: Path | None = None,
) -> WorstFilesResult:
    """
    Get the N files with the most linting issues.

    This tool helps identify problem areas in large codebases by showing which
    files need the most attention.

    Args:
        directory_path: Path to the directory to analyze.
        n: Number of files to return (default: 10).
        recursive: Whether to search subdirectories (default: True).
        select: List of rule IDs to enable.
        ignore: List of rule IDs to ignore.
        threshold: Minimum severity threshold (I/W/E).
        configure: List of rule configurations.
        config_path: Path to the Robocop toml configuration file

    Returns:
        A WorstFilesResult model containing:
        - files: List of worst files, each with file path, issue_count, and severity_breakdown
        - total_files_analyzed: Total number of files scanned
        - files_with_issues: Number of files that have at least one issue

    Raises:
        ToolError: If the directory does not exist or contains no files.

    """
    path = Path(directory_path)

    if not path.exists():
        raise ToolError(f"Directory not found: {directory_path}")

    if not path.is_dir():
        raise ToolError(f"Not a directory: {directory_path}")

    files = _collect_robot_files(path, recursive)

    if not files:
        raise ToolError(f"No .robot or .resource files found in {directory_path}")

    # Collect issue counts per file
    file_stats: list[WorstFile] = []
    files_with_issues = 0

    for file in files:
        try:
            issues = _lint_file_impl(
                str(file),
                select,
                ignore,
                threshold,
                include_file_in_result=False,
                configure=configure,
                config_path=config_path,
            )

            if issues:
                files_with_issues += 1
                severity_counts = {"E": 0, "W": 0, "I": 0}
                for issue in issues:
                    severity = issue.severity
                    if severity in severity_counts:
                        severity_counts[severity] += 1

                file_stats.append(
                    WorstFile(
                        file=str(file),
                        issue_count=len(issues),
                        severity_breakdown=SeveritySummary(
                            E=severity_counts["E"], W=severity_counts["W"], INFO=severity_counts["I"]
                        ),
                    )
                )
        except ToolError:
            # Skip files that fail to parse
            pass

    # Sort by issue count (descending) and take top N
    file_stats.sort(key=lambda x: x.issue_count, reverse=True)
    worst_files = file_stats[:n]

    return WorstFilesResult(
        files=worst_files,
        total_files_analyzed=len(files),
        files_with_issues=files_with_issues,
    )


def _get_line_context(content: str, line: int, context_lines: int) -> CodeContext:
    """
    Get surrounding lines for context.

    Args:
        content: The full source code content.
        line: The target line number (1-indexed).
        context_lines: Number of lines to include before and after.

    Returns:
        A CodeContext model with context lines and target line information.

    """
    lines = content.splitlines()
    total_lines = len(lines)

    # Adjust for 0-indexed list
    line_idx = line - 1

    start = max(0, line_idx - context_lines)
    end = min(total_lines, line_idx + context_lines + 1)

    context_content: list[ContextLine] = []
    for i in range(start, end):
        context_content.append(
            ContextLine(
                line_number=i + 1,
                content=lines[i] if i < len(lines) else "",
                is_target=i == line_idx,
            )
        )

    return CodeContext(
        lines=context_content,
        target_line=line,
        target_content=lines[line_idx] if 0 <= line_idx < len(lines) else None,
    )
