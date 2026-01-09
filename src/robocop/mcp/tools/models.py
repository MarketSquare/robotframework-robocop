"""
Pydantic models for MCP tool return types.

These models provide structured, validated return types that generate JSON schemas
for better LLM tool integration.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# --- Core Diagnostic Models ---


class DiagnosticResult(BaseModel):
    """A single linting diagnostic issue."""

    rule_id: str = Field(description="The rule identifier (e.g., 'LEN01')")
    name: str = Field(description="The rule name (e.g., 'too-long-keyword')")
    message: str = Field(description="Description of the issue")
    severity: Literal["I", "W", "E"] = Field(description="Severity level: I=Info, W=Warning, E=Error")
    line: int = Field(description="Line number (1-indexed)")
    column: int = Field(description="Column number (1-indexed)")
    end_line: int = Field(description="End line number")
    end_column: int = Field(description="End column number")
    file: str | None = Field(default=None, description="File path (included when linting files)")


# --- Formatting Models ---


class FormatContentResult(BaseModel):
    """Result of formatting Robot Framework content."""

    formatted: str = Field(description="The formatted source code")
    changed: bool = Field(description="Whether the content was modified by formatting")
    diff: str | None = Field(description="Unified diff if content changed, None otherwise")


class FormatFileResult(FormatContentResult):
    """Result of formatting a single Robot Framework file."""

    file: str = Field(description="The file path that was formatted")
    written: bool = Field(description="Whether the file was written (only True when overwrite=True and changed)")


class FormatFileInfo(BaseModel):
    """Summary info for a formatted file (used in batch operations)."""

    file: str = Field(description="The file path")
    changed: bool = Field(description="Whether the file content changed")
    written: bool = Field(description="Whether the file was written to disk")


class FormatFilesResult(BaseModel):
    """Result of formatting multiple Robot Framework files."""

    total_files: int = Field(description="Number of files processed")
    files_changed: int = Field(description="Number of files with formatting changes")
    files_unchanged: int = Field(description="Number of files already properly formatted")
    files_written: int = Field(description="Number of files actually written (when overwrite=True)")
    errors: list[dict[str, str]] = Field(description="List of files that failed to process with error messages")
    unmatched_patterns: list[str] = Field(description="Patterns that didn't match any files")
    results: list[FormatFileInfo] | None = Field(
        default=None, description="Per-file results (omitted when summarize_only=True)"
    )


# --- Lint and Format Combined ---


class LintAndFormatResult(BaseModel):
    """Result of formatting and linting Robot Framework code in one operation."""

    formatted: str = Field(description="The formatted source code")
    changed: bool = Field(description="Whether formatting modified the code")
    diff: str | None = Field(description="Unified diff if formatting changed, None otherwise")
    issues: list[DiagnosticResult] = Field(description="Remaining lint issues in the formatted code")
    issues_before: int = Field(description="Number of issues before formatting")
    issues_after: int = Field(description="Number of issues after formatting")
    issues_fixed: int = Field(description="Number of issues fixed by formatting")
    file: str | None = Field(default=None, description="File path (only when file_path was used)")
    written: bool | None = Field(default=None, description="Whether file was overwritten (only when file_path used)")


# --- Batch Linting Models ---


class SeveritySummary(BaseModel):
    """Summary of issues by severity level."""

    model_config = {"populate_by_name": True}

    E: int = Field(description="Count of Error-level issues")
    W: int = Field(description="Count of Warning-level issues")
    INFO: int = Field(description="Count of Info-level issues", alias="I")


class TopRule(BaseModel):
    """A rule that appears frequently in linting results."""

    rule_id: str = Field(description="The rule identifier")
    count: int = Field(description="Number of times this rule was triggered")


class LintFilesResult(BaseModel):
    """Result of linting multiple Robot Framework files."""

    total_files: int = Field(description="Number of files linted")
    total_issues: int = Field(description="Total number of issues found (before limit/offset)")
    files_with_issues: int = Field(description="Number of files that have at least one issue")
    issues: list[DiagnosticResult] | dict[str, list[DiagnosticResult]] | None = Field(
        default=None, description="List of issues (or dict if group_by set, omitted when summarize_only=True)"
    )
    summary: SeveritySummary = Field(description="Issues by severity {E: count, W: count, I: count}")
    limited: bool | None = Field(default=None, description="Whether results were truncated by limit")
    offset: int | None = Field(default=None, description="The offset applied (for pagination tracking)")
    has_more: bool | None = Field(default=None, description="Whether more results exist beyond offset+limit")
    unmatched_patterns: list[str] = Field(description="Patterns that didn't match any files")
    group_counts: dict[str, int] | None = Field(
        default=None, description="Total count per group before limit (only when group_by set)"
    )
    top_rules: list[TopRule] | None = Field(
        default=None, description="Top 10 most common rules (only when summarize_only=True)"
    )


# --- Rule/Formatter Documentation Models ---


class RuleParam(BaseModel):
    """A configurable parameter for a linting rule."""

    name: str = Field(description="Parameter name")
    default: str | None = Field(description="Default value")
    description: str = Field(description="Parameter description")
    type: str = Field(description="Parameter type")


class RuleSummary(BaseModel):
    """Summary information for a linting rule (used in list_rules)."""

    rule_id: str = Field(description="The rule ID (e.g., 'LEN01')")
    name: str = Field(description="The rule name (e.g., 'too-long-keyword')")
    severity: Literal["I", "W", "E"] = Field(description="Default severity level")
    enabled: bool = Field(description="Whether the rule is enabled by default")
    message: str = Field(description="The rule message template")


class RuleDetail(BaseModel):
    """Detailed information for a linting rule (used in get_rule_info)."""

    rule_id: str = Field(description="The rule ID")
    name: str = Field(description="The rule name")
    message: str = Field(description="The rule message template")
    severity: Literal["I", "W", "E"] = Field(description="Default severity level")
    enabled: bool = Field(description="Whether the rule is enabled by default")
    deprecated: bool = Field(description="Whether the rule is deprecated")
    docs: str | None = Field(description="Full documentation")
    parameters: list[RuleParam] = Field(description="Configurable parameters")
    added_in_version: str | None = Field(description="Robocop version when rule was added")
    version_requirement: str | None = Field(description="Robot Framework version requirement (if any)")


class RuleSearchResult(BaseModel):
    """A rule matching a search query."""

    rule_id: str = Field(description="The rule ID")
    name: str = Field(description="The rule name")
    message: str = Field(description="The rule message template")
    severity: Literal["I", "W", "E"] = Field(description="Default severity level")
    enabled: bool = Field(description="Whether the rule is enabled by default")
    match_field: str = Field(description="Which field matched the query (name, message, docs, rule_id)")
    match_snippet: str = Field(description="Context around the match")


class FormatterSummary(BaseModel):
    """Summary information for a formatter."""

    name: str = Field(description="Formatter name")
    enabled: bool = Field(description="Whether the formatter is enabled by default")
    description: str = Field(description="Brief description of what the formatter does")


class FormatterParam(BaseModel):
    """A configurable parameter for a formatter."""

    name: str = Field(description="Parameter name")
    default: bool | int | str | None = Field(description="Default value")
    type: str = Field(description="Parameter type")


class FormatterDetail(BaseModel):
    """Detailed information for a formatter."""

    name: str = Field(description="Formatter name")
    enabled: bool = Field(description="Whether enabled by default")
    docs: str = Field(description="Full documentation")
    min_version: str | None = Field(description="Minimum Robot Framework version (if any)")
    parameters: list[FormatterParam] = Field(description="Configurable parameters")
    skip_options: list[str] = Field(description="Skip options this formatter handles")


# --- Fix Suggestion Models ---


class FixSuggestion(BaseModel):
    """A suggested fix for a linting issue."""

    rule_id: str = Field(description="The rule ID")
    name: str = Field(description="The rule name")
    line: int = Field(description="Line number")
    message: str = Field(description="The issue description")
    suggestion: str = Field(description="How to fix this issue")
    auto_fixable: bool = Field(description="Whether format_content can fix this automatically")


class SuggestFixesResult(BaseModel):
    """Result of analyzing code for fix suggestions."""

    fixes: list[FixSuggestion] = Field(description="List of fix suggestions")
    total_issues: int = Field(description="Total number of issues found")
    auto_fixable: int = Field(description="Count of issues that can be auto-fixed by formatting")
    manual_required: int = Field(description="Count of issues requiring manual fixes")
    recommendation: str = Field(description="Overall recommendation for fixing")


# --- Statistics Models ---


class StatisticsSummary(BaseModel):
    """Summary statistics for a codebase."""

    total_files: int = Field(description="Total number of Robot Framework files")
    files_with_issues: int = Field(description="Number of files with at least one issue")
    files_clean: int = Field(description="Number of files with no issues")
    total_issues: int = Field(description="Total number of issues found")
    avg_issues_per_file: float = Field(description="Average issues per file")
    max_issues_in_file: int = Field(description="Maximum issues in a single file")


class QualityScore(BaseModel):
    """Code quality score for a codebase."""

    score: int = Field(description="Score from 0-100")
    grade: Literal["A", "B", "C", "D", "F"] = Field(description="Letter grade")
    label: str = Field(description="Quality label (Excellent, Good, Fair, Poor, Critical)")


class GetStatisticsResult(BaseModel):
    """Result of analyzing codebase quality statistics."""

    directory: str = Field(description="The analyzed directory path")
    summary: StatisticsSummary = Field(description="Overview statistics")
    severity_breakdown: SeveritySummary = Field(description="Issues by severity level")
    top_issues: list[TopRule] = Field(description="Most common rules with counts")
    quality_score: QualityScore = Field(description="Quality score, grade, and label")
    recommendations: list[str] = Field(description="Actionable suggestions for improvement")


# --- Explain Issue Models ---


class IssueExplanation(BaseModel):
    """Detailed explanation of a linting issue."""

    rule_id: str = Field(description="The rule ID")
    name: str = Field(description="The rule name")
    message: str = Field(description="The issue description")
    severity: Literal["I", "W", "E"] = Field(description="Severity level")
    line: int = Field(description="Line number")
    column: int = Field(description="Column number")
    why_it_matters: str | None = Field(default=None, description="First line of rule documentation")
    fix_suggestion: str | None = Field(default=None, description="How to fix this issue")
    full_documentation: str | None = Field(default=None, description="Complete rule documentation")
    configurable_parameters: list[dict[str, str]] | None = Field(
        default=None, description="Parameters that can be adjusted"
    )


class RelatedIssue(BaseModel):
    """A related issue on a nearby line."""

    rule_id: str = Field(description="The rule ID")
    name: str = Field(description="The rule name")
    line: int = Field(description="Line number")
    message: str = Field(description="The issue description")


class ContextLine(BaseModel):
    """A line of code in the context."""

    line_number: int = Field(description="The line number (1-indexed)")
    content: str = Field(description="The line content")
    is_target: bool = Field(description="Whether this is the target line")


class CodeContext(BaseModel):
    """Context around a specific line of code."""

    lines: list[ContextLine] = Field(description="Context lines with line numbers")
    target_line: int = Field(description="The target line number")
    target_content: str | None = Field(description="The content of the target line")


class ExplainIssueResult(BaseModel):
    """Result of explaining issues at a specific line."""

    line: int = Field(description="The requested line number")
    issues_found: bool = Field(description="Whether issues were found at or near this line")
    message: str | None = Field(default=None, description="Message when no issues found")
    issues: list[IssueExplanation] | None = Field(default=None, description="Detailed issue explanations")
    related_issues: list[RelatedIssue] | None = Field(default=None, description="Issues on nearby lines")
    context: CodeContext = Field(description="Surrounding code with line numbers")


# --- Worst Files Models ---


class WorstFile(BaseModel):
    """A file with many linting issues."""

    file: str = Field(description="File path")
    issue_count: int = Field(description="Total number of issues")
    severity_breakdown: SeveritySummary = Field(description="Issues by severity level")


class WorstFilesResult(BaseModel):
    """Result of finding files with the most issues."""

    files: list[WorstFile] = Field(description="List of files sorted by issue count (descending)")
    total_files_analyzed: int = Field(description="Total number of files scanned")
    files_with_issues: int = Field(description="Number of files with at least one issue")


# --- Prompt Models ---


class PromptArgument(BaseModel):
    """An argument for a prompt template."""

    name: str = Field(description="Argument name")
    required: bool = Field(description="Whether the argument is required")


class PromptSummary(BaseModel):
    """Summary of an MCP prompt template."""

    name: str = Field(description="Prompt name")
    description: str = Field(description="Brief description of what the prompt does")
    arguments: list[PromptArgument] = Field(description="Arguments the prompt accepts")


# --- LLM-Assisted Fixing Models ---


class CodeSnippet(BaseModel):
    """A snippet of code with line information."""

    content: str = Field(description="The code content")
    start_line: int = Field(description="First line number (1-indexed)")
    end_line: int = Field(description="Last line number (1-indexed)")


class IssueForFix(BaseModel):
    """Details of an issue to be fixed by an LLM."""

    rule_id: str = Field(description="The rule ID (e.g., 'NAME01')")
    name: str = Field(description="The rule name (e.g., 'not-allowed-char-in-name')")
    message: str = Field(description="The specific issue message")
    severity: Literal["I", "W", "E"] = Field(description="Severity level")
    line: int = Field(description="Line number where the issue occurs")
    column: int = Field(description="Column number")
    end_line: int = Field(description="End line number")
    end_column: int = Field(description="End column number")
    fix_suggestion: str | None = Field(default=None, description="Built-in fix suggestion if available")
    rule_docs: str | None = Field(default=None, description="Full rule documentation")


class GetFixContextResult(BaseModel):
    """Complete context for LLM-assisted fixing."""

    file_path: str | None = Field(default=None, description="File path if from file")
    full_content: str = Field(description="The complete file/content being analyzed")
    target_snippet: CodeSnippet = Field(description="The problematic code section with surrounding context")
    issues: list[IssueForFix] = Field(description="Issues found in the target area")
    llm_guidance: str = Field(description="Structured guidance for the LLM on how to generate the fix")


class FixReplacement(BaseModel):
    """A line-based replacement for applying a fix."""

    start_line: int = Field(description="First line to replace (1-indexed)")
    end_line: int = Field(description="Last line to replace (1-indexed, inclusive)")
    new_content: str = Field(description="The replacement content (lines joined with newlines)")


class ApplyFixResult(BaseModel):
    """Result of applying a fix."""

    success: bool = Field(description="Whether the fix was successfully applied")
    file_path: str | None = Field(default=None, description="File path if written to disk")
    written: bool = Field(description="Whether the fix was written to disk")
    new_content: str = Field(description="The content after applying the fix")
    diff: str | None = Field(default=None, description="Unified diff showing the changes")
    issues_before: int = Field(description="Number of issues before the fix")
    issues_after: int = Field(description="Number of issues after the fix")
    issues_fixed: int = Field(description="Number of issues resolved by the fix")
    remaining_issues: list[DiagnosticResult] | None = Field(
        default=None, description="Issues that remain after the fix (limited to first 10)"
    )
    validation_error: str | None = Field(default=None, description="Error message if fix validation failed")


# --- Natural Language Configuration Models ---


class ConfigSuggestion(BaseModel):
    """A single suggested configuration option from natural language input."""

    rule_id: str | None = Field(default=None, description="Rule identifier (e.g., 'LEN02') - for rule-related actions")
    rule_name: str | None = Field(
        default=None, description="Rule name (e.g., 'line-too-long') - for rule-related actions"
    )
    action: Literal["configure", "enable", "disable", "set"] = Field(
        description="Action: configure (rule param), enable/disable (rule), set (scalar config option)"
    )
    parameter: str | None = Field(default=None, description="Parameter name for 'configure' or option name for 'set'")
    value: str | None = Field(default=None, description="Value for 'configure' or 'set' actions")
    section: Literal["common", "lint", "format"] = Field(
        default="lint",
        description="Config section: common ([tool.robocop]), lint, or format",
    )
    interpretation: str = Field(description="What we understood the user meant")
    explanation: str = Field(description="Why this configuration is appropriate")


class NLConfigResult(BaseModel):
    """Result of parsing natural language into Robocop configuration."""

    success: bool = Field(description="Whether the parsing was successful")
    suggestions: list[ConfigSuggestion] = Field(description="List of suggested configuration changes")
    toml_config: str = Field(
        description="Ready-to-use TOML configuration (may include multiple sections: common, lint, format)"
    )
    warnings: list[str] = Field(default_factory=list, description="Ambiguities, conflicts, or unsupported features")
    explanation: str = Field(description="Summary of what the configuration achieves")


class ApplyConfigurationResult(BaseModel):
    """Result of applying configuration to a file."""

    success: bool = Field(description="Whether the configuration was successfully applied")
    file_path: str = Field(description="Path to the configuration file")
    file_created: bool = Field(description="True if a new file was created")
    diff: str | None = Field(default=None, description="Unified diff showing changes")
    merged_config: str = Field(description="The full [tool.robocop.lint] section after merging")
    validation_passed: bool = Field(description="True if Robocop accepts the configuration")
    validation_error: str | None = Field(default=None, description="Error message if validation failed")
