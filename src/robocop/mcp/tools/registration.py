"""MCP tool registration - FastMCP server tool registration."""

from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.server.context import Context
from pydantic import Field

from robocop.mcp.tools.batch_operations import _format_files_impl, _lint_files_impl
from robocop.mcp.tools.diagnostics import (
    _explain_issue_impl,
    _get_statistics_impl,
    _suggest_fixes_impl,
    _worst_files_impl,
)
from robocop.mcp.tools.documentation import (
    _get_formatter_info_impl,
    _get_rule_info_impl,
    _list_formatters_impl,
    _list_prompts_impl,
    _list_rules_impl,
    _search_rules_impl,
)
from robocop.mcp.tools.fixing import _apply_fix_impl, _get_fix_context_impl
from robocop.mcp.tools.formatting import (
    _format_content_impl,
    _format_file_impl,
    _lint_and_format_impl,
)
from robocop.mcp.tools.linting import _lint_content_impl, _lint_file_impl
from robocop.mcp.tools.models import (
    ApplyConfigurationResult,
    ApplyFixResult,
    DiagnosticResult,
    ExplainIssueResult,
    FixReplacement,
    FormatContentResult,
    FormatFileResult,
    FormatFilesResult,
    FormatterDetail,
    FormatterSummary,
    GetFixContextResult,
    GetStatisticsResult,
    LintAndFormatResult,
    LintFilesResult,
    NLConfigResult,
    PromptSummary,
    RuleDetail,
    RuleSearchResult,
    RuleSummary,
    SuggestFixesResult,
    WorstFilesResult,
)
from robocop.mcp.tools.natural_language_config import (
    _apply_config_impl,
    get_config_system_message,
    parse_config_from_llm_response,
)


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the server."""

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Lint Robot Framework Content"},
    )
    async def lint_content(
        content: Annotated[str, Field(description="Robot Framework source code to lint")],
        filename: Annotated[
            str, Field(description="Virtual filename (affects file type detection, use .robot or .resource)")
        ] = "stdin.robot",
        select: Annotated[
            list[str] | None,
            Field(description="List of rule IDs/names to enable (e.g., ['LEN01', 'too-long-keyword'])"),
        ] = None,
        ignore: Annotated[list[str] | None, Field(description="List of rule IDs/names to ignore")] = None,
        threshold: Annotated[
            Literal["I", "W", "E"], Field(description="Minimum severity to report: I=Info, W=Warning, E=Error")
        ] = "I",
        limit: Annotated[int | None, Field(description="Maximum number of issues to return (None = no limit)")] = None,
        configure: Annotated[
            list[str] | None, Field(description="Rule configurations (e.g., ['line-too-long.line_length=140'])")
        ] = None,
        ctx: Context | None = None,
    ) -> list[DiagnosticResult]:
        """
        Lint Robot Framework code provided as text content.

        Returns a list of diagnostic issues found, each containing rule_id, name, message,
        severity (I/W/E), line, column, end_line, and end_column.

        Example::

            lint_content("*** Test Cases ***...")
            # Returns: [DiagnosticResult(rule_id="NAME02", name="wrong-case-in-test-case-name", ...)]

        """
        if ctx:
            await ctx.info(f"Linting content ({len(content)} bytes)...")

        result = _lint_content_impl(content, filename, select, ignore, threshold, limit, configure)

        if ctx:
            await ctx.info(f"Found {len(result)} issue(s)")

        return result

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Lint Robot Framework File"},
    )
    async def lint_file(
        file_path: Annotated[str, Field(description="Absolute path to the .robot or .resource file")],
        select: Annotated[list[str] | None, Field(description="List of rule IDs/names to enable")] = None,
        ignore: Annotated[list[str] | None, Field(description="List of rule IDs/names to ignore")] = None,
        threshold: Annotated[
            Literal["I", "W", "E"], Field(description="Minimum severity to report: I=Info, W=Warning, E=Error")
        ] = "I",
        limit: Annotated[int | None, Field(description="Maximum number of issues to return (None = no limit)")] = None,
        configure: Annotated[
            list[str] | None, Field(description="Rule configurations (e.g., ['line-too-long.line_length=140'])")
        ] = None,
        ctx: Context | None = None,
    ) -> list[DiagnosticResult]:
        """
        Lint a Robot Framework file from disk.

        Returns a list of diagnostic issues found (same format as lint_content).

        Example::

            lint_file("/path/to/test.robot")
            lint_file("/path/to/test.robot", select=["LEN*"], threshold="W")

        """
        if ctx:
            await ctx.info(f"Linting file: {file_path}")

        result = _lint_file_impl(file_path, select, ignore, threshold, limit=limit, configure=configure)

        if ctx:
            await ctx.info(f"Found {len(result)} issue(s)")

        return result

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Lint Multiple Robot Files"},
    )
    async def lint_files(
        file_patterns: Annotated[
            list[str],
            Field(description="File paths or glob patterns (e.g., ['tests/**/*.robot', '*.resource'])"),
        ],
        base_path: Annotated[
            str | None, Field(description="Base directory for relative paths (defaults to current directory)")
        ] = None,
        select: Annotated[
            list[str] | None, Field(description="Rule IDs/names to enable (e.g., ['LEN01', 'too-long-keyword'])")
        ] = None,
        ignore: Annotated[list[str] | None, Field(description="Rule IDs/names to ignore")] = None,
        threshold: Annotated[
            Literal["I", "W", "E"], Field(description="Minimum severity: I=Info, W=Warning, E=Error")
        ] = "I",
        limit: Annotated[
            int | None, Field(description="Max issues to return (per group if group_by set, None = no limit)")
        ] = None,
        offset: Annotated[int, Field(description="Issues to skip for pagination (per group if group_by set)")] = 0,
        configure: Annotated[
            list[str] | None, Field(description="Rule configurations (e.g., ['line-too-long.line_length=140'])")
        ] = None,
        group_by: Annotated[
            Literal["severity", "rule", "file"] | None,
            Field(description="Group results by severity, rule, or file"),
        ] = None,
        summarize_only: Annotated[
            bool, Field(description="Return only summary stats without individual issues (for large codebases)")
        ] = False,
        ctx: Context | None = None,
    ) -> LintFilesResult:
        """
        Lint multiple Robot Framework files specified by paths or glob patterns.

        Returns total_files, total_issues, files_with_issues, issues (list or grouped dict),
        summary by severity, pagination info, and optionally top_rules when summarize_only=True.

        Example::

            lint_files(["tests/login.robot", "tests/checkout.robot"])
            lint_files(["tests/**/*.robot"], threshold="W")
            lint_files(["*.robot"], group_by="severity", limit=10)
            lint_files(["**/*.robot"], summarize_only=True)  # Just stats

        """
        if ctx:
            await ctx.info(f"Processing {len(file_patterns)} file pattern(s)...")

        return _lint_files_impl(
            file_patterns, base_path, select, ignore, threshold, limit, offset, configure, group_by, summarize_only
        )

    @mcp.tool(
        tags={"formatting"},
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "title": "Format Robot Framework Code",
        },
    )
    async def format_content(
        content: Annotated[str, Field(description="Robot Framework source code to format")],
        filename: Annotated[str, Field(description="Virtual filename (affects parsing)")] = "stdin.robot",
        select: Annotated[
            list[str] | None, Field(description="Formatter names to apply (empty = use defaults)")
        ] = None,
        space_count: Annotated[int, Field(description="Spaces for indentation")] = 4,
        line_length: Annotated[int, Field(description="Maximum line length")] = 120,
        ctx: Context | None = None,
    ) -> FormatContentResult:
        """
        Format Robot Framework code and return the formatted result.

        Returns formatted source code, whether it changed, and a unified diff.

        Example::

            format_content(robot_code)
            # Returns: FormatContentResult(formatted="...", changed=True, diff="...")

        """
        if ctx:
            await ctx.info(f"Formatting content ({len(content)} bytes)...")

        result = _format_content_impl(content, filename, select, space_count, line_length)

        if ctx:
            status = "Content modified" if result.changed else "No changes needed"
            await ctx.info(status)

        return result

    @mcp.tool(
        tags={"formatting"},
        annotations={
            "idempotentHint": True,
            "title": "Format Robot Framework File",
        },
    )
    async def format_file(
        file_path: Annotated[str, Field(description="Absolute path to .robot or .resource file")],
        select: Annotated[
            list[str] | None, Field(description="Formatter names to apply (empty = use defaults)")
        ] = None,
        space_count: Annotated[int, Field(description="Spaces for indentation")] = 4,
        line_length: Annotated[int, Field(description="Maximum line length")] = 120,
        overwrite: Annotated[bool, Field(description="Write formatted content back to file")] = False,
        ctx: Context | None = None,
    ) -> FormatFileResult:
        """
        Format a Robot Framework file from disk.

        WARNING: When overwrite=True, this tool PERMANENTLY MODIFIES the file on disk.
        The original content will be replaced. Use overwrite=False (default) to preview.

        Returns file path, formatted content, whether it changed, diff, and whether written.

        Example::

            format_file("/path/to/test.robot")  # Preview changes
            format_file("/path/to/test.robot", overwrite=True)  # Apply changes

        """
        if ctx:
            mode = "formatting and overwriting" if overwrite else "formatting (preview)"
            await ctx.info(f"{mode.capitalize()}: {file_path}")

        result = _format_file_impl(file_path, select, space_count, line_length, overwrite=overwrite)

        if ctx:
            if result.changed:
                status = "File modified and saved" if result.written else "Changes detected (not saved)"
            else:
                status = "No changes needed"
            await ctx.info(status)

        return result

    @mcp.tool(
        tags={"formatting"},
        annotations={
            "idempotentHint": True,
            "title": "Format Multiple Robot Files",
        },
    )
    async def format_files(
        file_patterns: Annotated[
            list[str],
            Field(description="File paths or glob patterns (e.g., ['tests/**/*.robot', '*.resource'])"),
        ],
        base_path: Annotated[
            str | None, Field(description="Base directory for relative paths (defaults to current directory)")
        ] = None,
        select: Annotated[
            list[str] | None, Field(description="Formatter names to apply (empty = use defaults)")
        ] = None,
        space_count: Annotated[int, Field(description="Spaces for indentation")] = 4,
        line_length: Annotated[int, Field(description="Maximum line length")] = 120,
        overwrite: Annotated[bool, Field(description="Write formatted content back to files")] = False,
        summarize_only: Annotated[
            bool, Field(description="Return only summary stats without per-file results")
        ] = False,
        ctx: Context | None = None,
    ) -> FormatFilesResult:
        """
        Format multiple Robot Framework files specified by paths or glob patterns.

        WARNING: When overwrite=True, this tool PERMANENTLY MODIFIES files on disk.
        Use overwrite=False (default) to preview changes before applying.

        Returns total_files, files_changed, files_unchanged, files_written, errors, and results.

        Example::

            format_files(["tests/**/*.robot"])  # Preview changes
            format_files(["tests/**/*.robot"], overwrite=True)  # Apply changes
            format_files(["**/*.robot"], summarize_only=True)  # Just stats

        """
        if ctx:
            mode = "formatting and overwriting" if overwrite else "formatting (preview)"
            await ctx.info(f"{mode.capitalize()} {len(file_patterns)} pattern(s)...")

        result = _format_files_impl(
            file_patterns,
            base_path,
            select,
            space_count,
            line_length,
            overwrite=overwrite,
            summarize_only=summarize_only,
        )

        if ctx:
            files_changed = result.files_changed
            files_written = result.files_written
            msg = f"Completed: {files_changed} file(s) changed"
            if overwrite:
                msg += f", {files_written} written"
            await ctx.info(msg)

        return result

    @mcp.tool(
        tags={"linting", "formatting"},
        annotations={
            "idempotentHint": True,
            "title": "Format and Lint Code",
        },
    )
    async def lint_and_format(
        content: Annotated[str | None, Field(description="Robot Framework source code (use this OR file_path)")] = None,
        file_path: Annotated[
            str | None, Field(description="Path to .robot/.resource file (use this OR content)")
        ] = None,
        filename: Annotated[str, Field(description="Virtual filename when using content")] = "stdin.robot",
        lint_select: Annotated[list[str] | None, Field(description="Linter rule IDs/names to enable")] = None,
        lint_ignore: Annotated[list[str] | None, Field(description="Linter rule IDs/names to ignore")] = None,
        threshold: Annotated[
            Literal["I", "W", "E"], Field(description="Minimum severity: I=Info, W=Warning, E=Error")
        ] = "I",
        format_select: Annotated[
            list[str] | None, Field(description="Formatter names to apply (empty = use defaults)")
        ] = None,
        space_count: Annotated[int, Field(description="Spaces for indentation")] = 4,
        line_length: Annotated[int, Field(description="Maximum line length")] = 120,
        limit: Annotated[int | None, Field(description="Max issues to return (None = no limit)")] = None,
        configure: Annotated[
            list[str] | None, Field(description="Rule configurations (e.g., ['line-too-long.line_length=140'])")
        ] = None,
        overwrite: Annotated[bool, Field(description="Write formatted content back to file (file_path only)")] = False,
        ctx: Context | None = None,
    ) -> LintAndFormatResult:
        """
        Format Robot Framework code and lint the result in one operation.

        WARNING: When file_path is used with overwrite=True, this tool PERMANENTLY
        MODIFIES the file on disk. Use overwrite=False (default) to preview.

        Returns formatted code, whether changed, diff, remaining issues, and fix counts.

        Example::

            lint_and_format(content=robot_code)
            lint_and_format(file_path="/path/to/test.robot")  # Preview
            lint_and_format(file_path="/path/to/test.robot", overwrite=True)  # Apply

        """
        if ctx:
            if file_path:
                mode = "formatting and overwriting" if overwrite else "processing"
                await ctx.info(f"{mode.capitalize()}: {file_path}")
            else:
                await ctx.info(f"Processing content ({len(content) if content else 0} bytes)...")

        result = _lint_and_format_impl(
            content=content,
            file_path=file_path,
            filename=filename,
            lint_select=lint_select,
            lint_ignore=lint_ignore,
            threshold=threshold,
            format_select=format_select,
            space_count=space_count,
            line_length=line_length,
            limit=limit,
            configure=configure,
            overwrite=overwrite,
        )

        if ctx:
            fixed = result.issues_fixed
            remaining = result.issues_after
            await ctx.info(f"Remaining issues: {remaining} ({fixed} fixed by formatting)")
            if file_path and result.written:
                await ctx.info("File overwritten with formatted content")

        return result

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "List Linting Rules"},
    )
    async def list_rules(
        category: Annotated[
            str | None, Field(description="Filter by category (e.g., 'LEN', 'NAME', 'DOC', 'SPACE')")
        ] = None,
        severity: Annotated[
            Literal["I", "W", "E"] | None, Field(description="Filter by severity: I=Info, W=Warning, E=Error")
        ] = None,
        enabled_only: Annotated[bool, Field(description="Only return rules enabled by default")] = False,
        ctx: Context | None = None,
    ) -> list[RuleSummary]:
        """
        List all available linting rules with optional filtering.

        Returns rule summaries with rule_id, name, severity, enabled status, and message.

        Example::

            list_rules(category="LEN")  # All length-related rules
            list_rules(severity="E")  # All error-level rules
            list_rules(enabled_only=True)  # Only enabled rules

        """
        if ctx:
            filters = []
            if category:
                filters.append(f"category={category}")
            if severity:
                filters.append(f"severity={severity}")
            if enabled_only:
                filters.append("enabled_only=True")
            filter_str = ", ".join(filters) if filters else "none"
            await ctx.debug(f"Listing rules with filters: {filter_str}")

        return _list_rules_impl(category, severity, enabled_only)

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "List Formatters"},
    )
    async def list_formatters(
        enabled_only: Annotated[bool, Field(description="Only return formatters enabled by default")] = True,
        ctx: Context | None = None,
    ) -> list[FormatterSummary]:
        """
        List all available formatters.

        Returns formatter summaries with name, enabled status, and description.

        Example::

            list_formatters()  # All enabled formatters
            list_formatters(enabled_only=False)  # All formatters including disabled

        """
        if ctx:
            await ctx.debug(f"Listing formatters (enabled_only={enabled_only})")

        return _list_formatters_impl(enabled_only)

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "Get Rule Details"},
    )
    async def get_rule_info(
        rule_name_or_id: Annotated[
            str, Field(description="Rule name (e.g., 'too-long-keyword') or ID (e.g., 'LEN01')")
        ],
        ctx: Context | None = None,
    ) -> RuleDetail:
        """
        Get detailed documentation for a linting rule.

        Returns rule_id, name, message, severity, enabled, deprecated, docs, parameters,
        added_in_version, and version_requirement.

        Example::

            get_rule_info("LEN01")
            get_rule_info("too-long-keyword")

        """
        if ctx:
            await ctx.debug(f"Looking up rule: {rule_name_or_id}")

        return _get_rule_info_impl(rule_name_or_id)

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "Get Formatter Details"},
    )
    async def get_formatter_info(
        formatter_name: Annotated[
            str, Field(description="Formatter name (e.g., 'NormalizeSeparators', 'AlignKeywordsSection')")
        ],
        ctx: Context | None = None,
    ) -> FormatterDetail:
        """
        Get detailed documentation for a formatter.

        Returns name, enabled status, docs, min_version, parameters, and skip_options.

        Example::

            get_formatter_info("NormalizeSeparators")

        """
        if ctx:
            await ctx.debug(f"Looking up formatter: {formatter_name}")

        return _get_formatter_info_impl(formatter_name)

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Suggest Code Fixes"},
    )
    async def suggest_fixes(
        content: Annotated[str, Field(description="Robot Framework source code to analyze")],
        filename: Annotated[str, Field(description="Virtual filename (affects file type detection)")] = "stdin.robot",
        rule_ids: Annotated[
            list[str] | None, Field(description="Specific rule IDs to get suggestions for (None = all)")
        ] = None,
        ctx: Context | None = None,
    ) -> SuggestFixesResult:
        """
        Analyze Robot Framework code and suggest fixes for linting issues.

        Returns fixes with suggestions, total_issues, auto_fixable count, manual_required
        count, and overall recommendation.

        Example::

            suggest_fixes(robot_code)

        """
        if ctx:
            await ctx.info(f"Analyzing content for fix suggestions ({len(content)} bytes)...")

        result = _suggest_fixes_impl(content, filename, rule_ids)

        if ctx:
            await ctx.info(
                f"Found {result.total_issues} issues: "
                f"{result.auto_fixable} auto-fixable, {result.manual_required} manual"
            )

        return result

    @mcp.tool(
        tags={"linting", "statistics"},
        annotations={"readOnlyHint": True, "title": "Get Codebase Statistics"},
    )
    async def get_statistics(
        directory_path: Annotated[str, Field(description="Absolute path to the directory to analyze")],
        recursive: Annotated[bool, Field(description="Search subdirectories")] = True,
        select: Annotated[list[str] | None, Field(description="Rule IDs/names to enable")] = None,
        ignore: Annotated[list[str] | None, Field(description="Rule IDs/names to ignore")] = None,
        threshold: Annotated[
            Literal["I", "W", "E"], Field(description="Minimum severity: I=Info, W=Warning, E=Error")
        ] = "I",
        configure: Annotated[
            list[str] | None, Field(description="Rule configurations (e.g., ['line-too-long.line_length=140'])")
        ] = None,
        ctx: Context | None = None,
    ) -> GetStatisticsResult:
        """
        Get code quality statistics for a Robot Framework codebase.

        Returns directory, summary stats, severity_breakdown, top_issues, quality_score
        (with grade A-F), and recommendations.

        Example::

            get_statistics("/path/to/tests")

        """
        if ctx:
            await ctx.info(f"Analyzing codebase: {directory_path}")

        result = _get_statistics_impl(directory_path, recursive, select, ignore, threshold, configure=configure)

        if ctx:
            score = result.quality_score
            await ctx.info(f"Quality score: {score.score}/100 (Grade: {score.grade})")

        return result

    @mcp.tool(
        tags={"linting", "documentation"},
        annotations={"readOnlyHint": True, "title": "Explain Issue at Line"},
    )
    async def explain_issue(
        content: Annotated[str, Field(description="Robot Framework source code to analyze")],
        line: Annotated[int, Field(description="Line number to explain (1-indexed)")],
        filename: Annotated[str, Field(description="Virtual filename (affects file type detection)")] = "stdin.robot",
        context_lines: Annotated[int, Field(description="Lines to show before/after the target line")] = 3,
        ctx: Context | None = None,
    ) -> ExplainIssueResult:
        """
        Explain issues at a specific line with surrounding context.

        Returns line, issues_found, detailed issue explanations with fix suggestions,
        related_issues on nearby lines, and code context.

        Example::

            explain_issue(robot_code, line=42)

        """
        if ctx:
            await ctx.info(f"Explaining issues at line {line}...")

        result = _explain_issue_impl(content, line, filename, context_lines)

        if ctx:
            if result.issues_found:
                count = len(result.issues) if result.issues else 0
                await ctx.info(f"Found {count} issue(s) at line {line}")
            else:
                await ctx.info(f"No issues found at or near line {line}")

        return result

    @mcp.tool(
        tags={"linting", "statistics"},
        annotations={"readOnlyHint": True, "title": "Find Worst Files"},
    )
    async def worst_files(
        directory_path: Annotated[str, Field(description="Absolute path to the directory to analyze")],
        n: Annotated[int, Field(description="Number of worst files to return")] = 10,
        recursive: Annotated[bool, Field(description="Search subdirectories")] = True,
        select: Annotated[list[str] | None, Field(description="Rule IDs/names to enable")] = None,
        ignore: Annotated[list[str] | None, Field(description="Rule IDs/names to ignore")] = None,
        threshold: Annotated[
            Literal["I", "W", "E"], Field(description="Minimum severity: I=Info, W=Warning, E=Error")
        ] = "I",
        configure: Annotated[
            list[str] | None, Field(description="Rule configurations (e.g., ['line-too-long.line_length=140'])")
        ] = None,
        ctx: Context | None = None,
    ) -> WorstFilesResult:
        """
        Get the N files with the most linting issues.

        Returns files (sorted by issue count), total_files_analyzed, and files_with_issues.

        Example::

            worst_files("/path/to/tests")  # Top 10 worst files
            worst_files("/path/to/tests", n=5, threshold="E")  # Top 5 by errors

        """
        if ctx:
            await ctx.info(f"Finding {n} worst files in: {directory_path}")

        result = _worst_files_impl(
            directory_path,
            n,
            recursive,
            select=select,
            ignore=ignore,
            threshold=threshold,
            configure=configure,
        )

        if ctx:
            await ctx.info(
                f"Found {result.files_with_issues} files with issues out of {result.total_files_analyzed} analyzed"
            )

        return result

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "Search Rules"},
    )
    async def search_rules(
        query: Annotated[str, Field(description="Search query (case-insensitive substring match)")],
        fields: Annotated[
            list[str] | None,
            Field(description="Fields to search: 'name', 'message', 'docs', 'rule_id' (default: name, message, docs)"),
        ] = None,
        category: Annotated[str | None, Field(description="Filter by category (e.g., 'LEN', 'NAME')")] = None,
        severity: Annotated[
            Literal["I", "W", "E"] | None, Field(description="Filter by severity: I=Info, W=Warning, E=Error")
        ] = None,
        limit: Annotated[int, Field(description="Maximum results to return")] = 20,
        ctx: Context | None = None,
    ) -> list[RuleSearchResult]:
        """
        Search for linting rules by keyword.

        Returns matching rules with rule_id, name, message, severity, enabled,
        match_field, and match_snippet.

        Example::

            search_rules("long")  # Find rules about length
            search_rules("keyword", category="NAME")  # Keyword naming rules

        """
        if ctx:
            await ctx.debug(f"Searching rules for: {query}")

        return _search_rules_impl(query, fields, category, severity, limit)

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "List Prompts"},
    )
    async def list_prompts(ctx: Context | None = None) -> list[PromptSummary]:
        """
        List all available MCP prompt templates.

        Returns prompt summaries with name, description, and arguments.

        Example::

            list_prompts()

        """
        if ctx:
            await ctx.debug("Listing available prompts")

        return _list_prompts_impl()

    @mcp.tool(
        tags={"linting", "fixing"},
        annotations={"readOnlyHint": True, "title": "Get Fix Context for LLM"},
    )
    async def get_fix_context(
        content: Annotated[str | None, Field(description="Robot Framework source code (use this OR file_path)")] = None,
        file_path: Annotated[str | None, Field(description="Absolute path to .robot/.resource file")] = None,
        filename: Annotated[str, Field(description="Virtual filename when using content")] = "stdin.robot",
        line: Annotated[int | None, Field(description="Specific line to get context for (None = all issues)")] = None,
        rule_ids: Annotated[
            list[str] | None, Field(description="Filter to specific rule IDs (e.g., ['LEN01', 'NAME02'])")
        ] = None,
        context_lines: Annotated[int, Field(description="Lines of context before and after target")] = 5,
        ctx: Context | None = None,
    ) -> GetFixContextResult:
        """
        Get rich context for LLM-assisted fixing of Robot Framework code issues.

        Returns the problematic code snippet, issue details with fix suggestions,
        rule documentation, and structured guidance for generating fixes.

        Use this tool to understand issues before generating a fix, then apply
        the fix with apply_fix.

        Example workflow::

            # 1. Get context for an issue at line 42
            context = get_fix_context(file_path="/path/to/test.robot", line=42)

            # 2. Use context.llm_guidance and context.issues to generate fix

            # 3. Apply fix with apply_fix tool

        """
        if ctx:
            target = f"line {line}" if line else "all issues"
            source = file_path or f"content ({len(content) if content else 0} bytes)"
            await ctx.info(f"Getting fix context for {target} in {source}...")

        result = _get_fix_context_impl(
            content=content,
            file_path=file_path,
            filename=filename,
            line=line,
            rule_ids=rule_ids,
            context_lines=context_lines,
        )

        if ctx:
            await ctx.info(f"Found {len(result.issues)} issue(s) in target area")

        return result

    @mcp.tool(
        tags={"linting", "fixing"},
        annotations={"idempotentHint": True, "title": "Apply LLM-Generated Fix"},
    )
    async def apply_fix(
        content: Annotated[
            str | None, Field(description="Original Robot Framework source (use this OR file_path)")
        ] = None,
        file_path: Annotated[str | None, Field(description="Path to the file to fix")] = None,
        filename: Annotated[str, Field(description="Virtual filename when using content")] = "stdin.robot",
        replacement: Annotated[FixReplacement, Field(description="The line-based replacement to apply")] = None,
        overwrite: Annotated[bool, Field(description="Write the fix to disk (only with file_path)")] = False,
        validate: Annotated[bool, Field(description="Re-lint to validate the fix resolved issues")] = True,
        select: Annotated[list[str] | None, Field(description="Rule IDs to check in validation")] = None,
        ignore: Annotated[list[str] | None, Field(description="Rule IDs to ignore in validation")] = None,
        ctx: Context | None = None,
    ) -> ApplyFixResult:
        """
        Apply an LLM-generated fix to Robot Framework code.

        Takes a line-based replacement (start_line, end_line, new_content) and
        applies it to the code. Validates the fix by re-linting to ensure issues
        were actually resolved.

        WARNING: When file_path is used with overwrite=True, this PERMANENTLY
        MODIFIES the file on disk. Use overwrite=False (default) to preview.

        Example::

            # Apply a fix to lines 42-43
            apply_fix(
                file_path="/path/to/test.robot",
                replacement={"start_line": 42, "end_line": 43, "new_content": "Fixed Code"},
                overwrite=True
            )

        """
        if ctx:
            source = file_path or f"content ({len(content) if content else 0} bytes)"
            mode = "applying and writing" if overwrite else "previewing fix"
            await ctx.info(f"{mode.capitalize()} for {source}...")

        result = _apply_fix_impl(
            content=content,
            file_path=file_path,
            filename=filename,
            replacement=replacement,
            overwrite=overwrite,
            validate=validate,
            select=select,
            ignore=ignore,
        )

        if ctx:
            if result.success:
                msg = f"Fix applied: {result.issues_fixed} issue(s) resolved"
                if result.written:
                    msg += " (file updated)"
            else:
                msg = f"Fix failed: {result.validation_error}"
            await ctx.info(msg)

        return result

    @mcp.tool(
        tags={"configuration", "natural-language"},
        annotations={"readOnlyHint": True, "title": "Get Configuration Context for Natural Language"},
    )
    async def get_config_context(
        ctx: Context | None = None,
    ) -> dict[str, str]:
        """
        Get the system message and instructions for natural language configuration.

        This tool provides the context needed to parse natural language descriptions
        into Robocop configuration. Use this to understand available rules and
        configuration options before calling parse_config_response.

        Workflow:
        1. Call get_config_context() to get the system message
        2. Use the system message to process the user's natural language request
        3. Call parse_config_response() with the LLM's JSON response
        4. Review suggestions with the user
        5. Call apply_configuration() to write to pyproject.toml

        Returns:
            A dict with 'system_message' containing all rules and instructions.

        """
        if ctx:
            await ctx.info("Building rule catalog for configuration context...")

        system_message = get_config_system_message()

        if ctx:
            await ctx.info("Configuration context ready")

        return {"system_message": system_message}

    @mcp.tool(
        tags={"configuration", "natural-language"},
        annotations={"readOnlyHint": True, "title": "Parse Configuration Response"},
    )
    async def parse_config_response(
        llm_response: Annotated[
            str,
            Field(
                description="The JSON response from the LLM after processing a natural language configuration request"
            ),
        ],
        ctx: Context | None = None,
    ) -> NLConfigResult:
        """
        Parse an LLM's JSON response into validated configuration suggestions.

        After getting context from get_config_context() and having the LLM process
        a user's natural language request, call this tool with the LLM's JSON response
        to get validated configuration suggestions.

        The LLM response should be JSON with this structure:
        {
            "interpretation": "What the user wanted",
            "suggestions": [
                {
                    "rule_id": "LEN02",
                    "rule_name": "line-too-long",
                    "action": "configure",  // or "enable" or "disable"
                    "parameter": "line_length",  // for "configure" action
                    "value": "140",  // for "configure" action
                    "interpretation": "Allow 140 char lines",
                    "explanation": "Default is 120"
                }
            ],
            "warnings": []
        }

        Returns:
            Validated suggestions and ready-to-use TOML configuration.

        Example::

            # After LLM processes "allow longer lines up to 140 characters"
            result = parse_config_response('{"interpretation": "...", "suggestions": [...]}')
            # result.toml_config contains the TOML to apply

        """
        if ctx:
            await ctx.info("Parsing and validating configuration response...")

        result = parse_config_from_llm_response(llm_response)

        if ctx:
            if result.success:
                await ctx.info(f"Generated {len(result.suggestions)} configuration suggestion(s)")
            else:
                await ctx.info("Failed to parse configuration response")
            if result.warnings:
                for warning in result.warnings[:3]:  # Show first 3 warnings
                    await ctx.debug(f"Warning: {warning}")

        return result

    @mcp.tool(
        tags={"configuration"},
        annotations={"title": "Apply Configuration to File"},
    )
    async def apply_configuration(
        toml_config: Annotated[
            str,
            Field(description="TOML configuration string (e.g., from parse_config_response().toml_config)"),
        ],
        file_path: Annotated[
            str,
            Field(description="Path to configuration file (default: pyproject.toml)"),
        ] = "pyproject.toml",
        ctx: Context | None = None,
    ) -> ApplyConfigurationResult:
        """
        Apply Robocop configuration to a TOML file.

        WARNING: This tool MODIFIES files on disk. The configuration will be merged
        with any existing [tool.robocop.lint] section in the target file.

        Use this after reviewing suggestions from parse_config_response().

        Example::

            # After getting config from parse_config_response()
            result = apply_configuration(
                toml_config='[tool.robocop.lint]\\nconfigure = ["line-too-long.line_length=140"]',
                file_path="pyproject.toml"
            )
            # Check result.diff to see what changed

        Returns:
            Result with success status, file path, whether created,
            validation status, and any errors.

        """  # noqa: D301
        if ctx:
            await ctx.info(f"Applying configuration to {file_path}...")

        result = _apply_config_impl(toml_config, file_path)

        if ctx:
            if result.success:
                if result.file_created:
                    await ctx.info(f"Created new file: {result.file_path}")
                else:
                    await ctx.info(f"Updated: {result.file_path}")
                if result.validation_passed:
                    await ctx.info("Configuration validated successfully")
                else:
                    await ctx.info(f"Validation warning: {result.validation_error}")
            else:
                await ctx.info(f"Failed to apply configuration: {result.validation_error}")

        return result
