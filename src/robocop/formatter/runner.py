from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from difflib import SequenceMatcher, unified_diff
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from robot.api import get_model
from robot.errors import DataError

from robocop.embedded import MARKDOWN_EXTENSIONS, ModelContentCollector, extract_robot_blocks, reconstruct_source
from robocop.formatter import (
    disablers,  # TODO compare robocop vs robotidy disablers, if we can merge something
)
from robocop.formatter.utils import misc
from robocop.parallel import get_workers_count
from robocop.runtime.resolver import ConfigResolver
from robocop.source_file import EmbeddedSourceFile, SourceFile, StatementLinesCollector

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from robot.parsing import File

    from robocop.config.manager import ConfigManager
    from robocop.config.schema import Config
    from robocop.runtime.resolved_config import ResolvedConfig


console = Console()


@dataclass
class FormatResult:
    """
    Result of formatting a single file.

    Attributes:
        changed: Whether the file was (or would be) reformatted.
        diff_lines: Unified diff of the changes, only collected if the diff output is enabled.
        error: Error message if the file could not be parsed.

    """

    changed: bool = False
    diff_lines: list[str] = field(default_factory=list)
    error: str | None = None


class FileFormatter:
    """Format and save the single files. It does not print anything, so it can be used in worker processes."""

    def __init__(self, config: Config) -> None:
        self.config_resolver = ConfigResolver(load_formatters=True)
        self.config: Config = config

    def format_file(self, source_file: SourceFile) -> FormatResult:
        """
        Format the file and save it (if overwrite is enabled).

        Returns:
            Result of the formatting.

        """
        self.config = source_file.config
        try:
            if source_file.is_embedded:
                changed, old_text, new_text = self.format_embedded(source_file)
                diff_path = source_file.path
                if changed:
                    self.save_text(source_file.path, new_text)
            else:
                diff, old_model, new_model, model = self.format_until_stable(source_file)
                if not (diff and old_model is not None and new_model is not None):
                    return FormatResult()
                changed = True
                diff_path = model.source or source_file.path
                self.save_model(diff_path, model)
                old_text, new_text = old_model.text, new_model.text
        except DataError as err:
            return FormatResult(error=str(err))
        if changed and self.config.formatter.diff:
            return FormatResult(changed=True, diff_lines=self.get_diff_lines(diff_path, old_text, new_text))
        return FormatResult(changed=changed)

    def format_until_stable(
        self, source_file: SourceFile
    ) -> tuple[bool, StatementLinesCollector | None, StatementLinesCollector | None, File]:
        model = source_file.model
        resolved_config = self.config_resolver.resolve_config(source_file.config)
        self.set_file_languages(source_file, resolved_config)
        disabler_finder = disablers.RegisterDisablers(self.config.formatter.start_line, self.config.formatter.end_line)
        disabler_finder.find_disablers(model, "".join(source_file.source_lines))
        if disabler_finder.is_disabled_in_file(disablers.ALL_FORMATTERS):
            return False, None, None, model
        diff, old_model, new_model = self.format(model, disabler_finder.disablers, resolved_config)
        reruns = self.config.formatter.reruns
        while diff and reruns:
            model = get_model(new_model.text)
            disabler_finder.find_disablers(model, new_model.text)
            new_diff, _, new_model = self.format(model, disabler_finder.disablers, resolved_config)
            if not new_diff:
                break
            reruns -= 1
        return diff, old_model, new_model, model

    def format(
        self, model: File, disablers: disablers.DisablersInFile, resolved_config: ResolvedConfig
    ) -> tuple[bool, StatementLinesCollector, StatementLinesCollector]:
        old_model = StatementLinesCollector(model)
        for name, formatter in resolved_config.formatters.items():
            formatter.disablers = disablers  # set dynamically to allow using external formatters
            if disablers.is_disabled_in_file(name):
                continue
            formatter.visit(model)
        new_model = StatementLinesCollector(model)
        return new_model != old_model, old_model, new_model

    def format_embedded(self, source_file: SourceFile) -> tuple[bool, str, str]:
        """
        Format embedded Robot code and preserve the surrounding document.

        Markdown blocks share a model; Python blocks are formatted independently.

        Returns:
            Tuple of (changed, original_text, new_text) with the full physical file contents.

        """
        if isinstance(source_file, EmbeddedSourceFile) and source_file.path.suffix.lower() in MARKDOWN_EXTENSIONS:
            return self.format_markdown(source_file)
        resolved_config = self.config_resolver.resolve_config(source_file.config)
        original = list(source_file.source_lines)
        physical = list(original)
        newline = self._detect_newline(original)
        format_blocks = source_file.format_blocks()  # type: ignore[attr-defined]
        self.set_file_languages(source_file, resolved_config)
        # Blocks are spliced bottom-to-top so that changing the length of one block does not shift the others.
        for block, model in reversed(format_blocks):
            formatted = self.format_block(model, resolved_config)
            if formatted is None:
                continue
            physical[block.start_line - 1 : block.end_line] = self._reindent_block(formatted, block.indent, newline)
        new_text = "".join(physical)
        old_text = "".join(original)
        return new_text != old_text, old_text, new_text

    def format_markdown(self, source_file: EmbeddedSourceFile) -> tuple[bool, str, str]:
        """Format the combined model, retaining the physical boundaries between code blocks."""
        original = "".join(source_file.source_lines)
        if not source_file.blocks:
            return False, original, original
        physical = self._format_markdown_once(source_file)
        for _ in range(self.config.formatter.reruns):
            if physical == original:
                break
            updated = EmbeddedSourceFile(
                path=source_file.path, config=source_file.config, _source_lines=physical.splitlines(keepends=True)
            )
            new_physical = self._format_markdown_once(updated)
            if new_physical == physical:
                break
            physical = new_physical
        return physical != original, original, physical

    def _format_markdown_once(self, source_file: EmbeddedSourceFile) -> str:
        resolved_config = self.config_resolver.resolve_config(source_file.config)
        model = source_file.model
        self.set_file_languages(source_file, resolved_config)
        finder = disablers.RegisterDisablers(self.config.formatter.start_line, self.config.formatter.end_line)
        finder.find_disablers(model, "".join(source_file.model_lines))
        physical = "".join(source_file.source_lines)
        previous_text = StatementLinesCollector(model).text
        for name, formatter in resolved_config.formatters.items():
            if finder.is_disabled_in_file(name):
                continue
            previous = physical
            formatter.disablers = finder.disablers
            leading = None
            if name == "MergeAndOrderSections" and model.sections:
                first = model.sections[0]
                if first.header is None and not any(
                    token.value.strip() for statement in first.body for token in statement.tokens
                ):
                    leading = model.sections.pop(0)
            formatter.visit(model)
            if leading is not None:
                model.sections.insert(0, leading)
            formatted = StatementLinesCollector(model).text
            if formatted == previous_text:
                continue
            projected = self._project_markdown(source_file, formatted)
            if projected is not None:
                physical_lines = projected.splitlines(keepends=True)
                reconstructed = reconstruct_source(
                    physical_lines, extract_robot_blocks(physical_lines, markdown=True), markdown=True
                )
                if (
                    ModelContentCollector(source_file.build_embedded_model(formatted)).tokens
                    != ModelContentCollector(source_file.build_embedded_model(reconstructed)).tokens
                ):
                    projected = None
            if projected is None:
                previous_lines = previous.splitlines(keepends=True)
                restored = reconstruct_source(
                    previous_lines, extract_robot_blocks(previous_lines, markdown=True), markdown=True
                )
                model = source_file.build_embedded_model(restored)
                finder = disablers.RegisterDisablers(self.config.formatter.start_line, self.config.formatter.end_line)
                finder.find_disablers(model, restored)
                previous_text = StatementLinesCollector(model).text
            else:
                physical = projected
                previous_text = formatted
        return physical

    def _project_markdown(self, source_file: EmbeddedSourceFile, formatted: str) -> str | None:
        """Project changes onto blocks; reject transformations that cannot preserve their boundaries."""
        original = source_file.model_lines
        blocks = source_file.blocks
        lines = formatted.splitlines(keepends=True)
        physical = list(source_file.source_lines)
        newline = self._detect_newline(physical)
        changes: list[tuple[int, int, list[str]]] = []
        matcher = SequenceMatcher(
            isjunk=lambda line: not line.strip(),
            a=[line.rstrip("\r\n") for line in original],
            b=[line.rstrip("\r\n") for line in lines],
            autojunk=False,
        )
        for tag, start, end, new_start, new_end in matcher.get_opcodes():
            if tag == "equal":
                continue
            replacement = lines[new_start:new_end]
            matching = [block for block in blocks if block.start_line - 1 <= start <= end <= block.end_line]
            if not matching:
                if any(line.strip() for line in original[start:end] + replacement):
                    return self._project_markdown_code_lines(source_file, formatted)
                continue
            block = matching[0]
            changes.append((start, end, self._reindent_block("".join(replacement), block.indent, newline)))
        for start, end, replacement in reversed(changes):
            physical[start:end] = replacement
        projected = reconstruct_source(physical, extract_robot_blocks(physical, markdown=True), markdown=True)
        # Blank masked lines are immaterial, but all formatted code must survive the projection in order.
        if [line for line in projected.splitlines() if line.strip()] != [
            line for line in formatted.splitlines() if line.strip()
        ]:
            return self._project_markdown_code_lines(source_file, formatted)
        return "".join(physical)

    def _project_markdown_code_lines(self, source_file: EmbeddedSourceFile, formatted: str) -> str | None:
        """Map code changes across masked gaps when a whitespace diff cannot locate the boundaries."""
        original = source_file.model_lines
        blocks = source_file.blocks
        old_lines = [(index, line) for index, line in enumerate(original) if line.strip()]
        new_lines = [line for line in formatted.splitlines(keepends=True) if line.strip()]
        matcher = SequenceMatcher(
            a=[line.rstrip("\r\n") for _, line in old_lines],
            b=[line.rstrip("\r\n") for line in new_lines],
            autojunk=False,
        )
        physical = list(source_file.source_lines)
        newline = self._detect_newline(physical)
        changes: list[tuple[int, int, list[str]]] = []
        for tag, start, end, new_start, new_end in matcher.get_opcodes():
            if tag == "equal":
                continue
            if not old_lines:
                return None
            replacements = new_lines[new_start:new_end]
            if start == 0 and any(line.strip().lower() == "*** comments ***" for line in replacements):
                return None
            for offset, (index, _) in enumerate(old_lines[start:end]):
                block = next((block for block in blocks if block.contains(index + 1)), None)
                if block is None:
                    return None
                line = replacements[offset] if offset < len(replacements) else ""
                changes.append((index, index + 1, self._reindent_block(line, block.indent, newline)))
            remaining = replacements[end - start :]
            if remaining:
                if end > start:
                    index = old_lines[end - 1][0] + 1
                    block_line = index
                elif start < len(old_lines):
                    index = old_lines[start][0]
                    block_line = index + 1
                else:
                    index = old_lines[-1][0] + 1
                    block_line = index
                block = next((block for block in blocks if block.contains(block_line)), None)
                if block is None:
                    return None
                changes.append((index, index, self._reindent_block("".join(remaining), block.indent, newline)))
        for start, end, replacement in sorted(changes, key=lambda change: change[0], reverse=True):
            physical[start:end] = replacement
        projected = reconstruct_source(physical, extract_robot_blocks(physical, markdown=True), markdown=True)
        if [line for line in projected.splitlines() if line.strip()] != [line.rstrip("\r\n") for line in new_lines]:
            return None
        return "".join(physical)

    def format_block(self, model: File, resolved_config: ResolvedConfig) -> str | None:
        """
        Run the configured formatters on a single block model.

        Returns:
            The formatted block text, or ``None`` if the block is unchanged or fully disabled.

        """
        original_text = StatementLinesCollector(model).text
        disabler_finder = disablers.RegisterDisablers(self.config.formatter.start_line, self.config.formatter.end_line)
        disabler_finder.find_disablers(model, original_text)
        if disabler_finder.is_disabled_in_file(disablers.ALL_FORMATTERS):
            return None
        formatted = self._apply_formatters(model, disabler_finder.disablers, resolved_config)
        reruns = self.config.formatter.reruns
        while formatted != original_text and reruns:
            rerun_model = get_model(formatted)
            rerun_disablers = disablers.RegisterDisablers(
                self.config.formatter.start_line, self.config.formatter.end_line
            )
            rerun_disablers.find_disablers(rerun_model, formatted)
            new_formatted = self._apply_formatters(rerun_model, rerun_disablers.disablers, resolved_config)
            if new_formatted == formatted:
                break
            formatted = new_formatted
            reruns -= 1
        return formatted if formatted != original_text else None

    @staticmethod
    def set_file_languages(source_file: SourceFile, resolved_config: ResolvedConfig) -> None:
        """Use languages of the formatted file, including languages from its ``language:`` header."""
        languages = source_file.languages
        if languages is None:
            return
        for formatter in resolved_config.formatters.values():
            formatter.languages = languages

    @staticmethod
    def _apply_formatters(
        model: File, disablers_in_file: disablers.DisablersInFile, resolved_config: ResolvedConfig
    ) -> str:
        for name, formatter in resolved_config.formatters.items():
            formatter.disablers = disablers_in_file
            if disablers_in_file.is_disabled_in_file(name):
                continue
            formatter.visit(model)
        return StatementLinesCollector(model).text

    @staticmethod
    def _detect_newline(lines: list[str]) -> str:
        """Return the line ending used by the physical file so formatted blocks keep the surrounding style."""
        for line in lines:
            if line.endswith("\r\n"):
                return "\r\n"
            if line.endswith("\n"):
                return "\n"
            if line.endswith("\r"):
                return "\r"
        return os.linesep

    @staticmethod
    def _reindent_block(text: str, indent: str, newline: str) -> list[str]:
        """Re-apply the block indentation and the file's line ending to formatted lines, leaving blanks unindented."""
        return [f"{indent}{line}{newline}" if line.strip() else f"{line}{newline}" for line in text.splitlines()]

    def save_model(self, source: Path, model: File) -> None:
        if self.config.formatter.overwrite:
            output = self.config.formatter.output or source
            misc.ModelWriter(output=str(output), newline=self.get_line_ending(str(source))).write(model)

    def save_text(self, source: Path, text: str) -> None:
        """Write the full physical file content of an embedded file, preserving its original line endings."""
        if self.config.formatter.overwrite:
            output = self.config.formatter.output or source
            with open(output, "w", encoding="utf-8", newline="") as f:
                f.write(text)

    def get_line_ending(self, path: str) -> str:
        if self.config.formatter.whitespace_config.line_ending == "auto":
            with open(path) as f:
                f.readline()
                if f.newlines is None:
                    return os.linesep
                if isinstance(f.newlines, str):
                    return f.newlines
                return f.newlines[0]
        return self.config.formatter.whitespace_config.line_ending

    @staticmethod
    def get_diff_lines(path: Path, old_text: str, new_text: str) -> list[str]:
        old = [line + "\n" for line in old_text.splitlines()]
        new = [line + "\n" for line in new_text.splitlines()]
        return list(unified_diff(old, new, fromfile=f"{path}\tbefore", tofile=f"{path}\tafter"))


class RobocopFormatter(FileFormatter):
    def __init__(self, config_manager: ConfigManager) -> None:
        super().__init__(config_manager.default_config)
        self.config_manager = config_manager

    def run(self) -> int:
        changed_files = 0
        skipped_files = 0
        all_files = 0
        cached_files = 0
        stdin = False
        default_config = self.config_manager.default_config
        # with the output option every file is saved to the same path, so the files are processed one by one
        parallel = default_config.jobs != 1 and not default_config.formatter.output
        pending: list[SourceFile] = []

        for source_file in self.config_manager.paths:
            # stdin = False
            # if str(source) == "-":
            #     stdin = True
            #     if self.config.verbose:
            #         typer.echo("Loading file from stdin")
            #     source = self.load_from_stdin()
            if self.config.verbose:
                print(f"Formatting {source_file.path} file")
            self.config = source_file.config

            all_files += 1

            if self._can_use_cache(source_file):
                # Check cache - if file hasn't changed and didn't need formatting before, skip it
                cached_entry = self.config_manager.cache.get_formatter_entry(source_file.path, source_file.config.hash)
                if cached_entry is not None and not cached_entry.needs_formatting:
                    # File hasn't changed and didn't need formatting - skip it
                    cached_files += 1
                    continue
            if parallel:
                pending.append(source_file)
                continue
            result = self.format_file(source_file)
            self.handle_result(source_file, result, stdin)
            changed_files += result.changed
            skipped_files += result.error is not None

        last_config = self.config
        for source_file, result in self.format_files_in_parallel(pending):
            self.handle_result(source_file, result, stdin)
            changed_files += result.changed
            skipped_files += result.error is not None
        self.config = last_config

        # Save cache at the end
        self.config_manager.cache.save()

        if self.config_manager.default_config.verbose and cached_files > 0:
            print(f"Skipped {cached_files} unchanged files from cache.")

        return self.formatting_result(all_files, changed_files, skipped_files, stdin)

    def format_files_in_parallel(self, source_files: list[SourceFile]) -> Iterator[tuple[SourceFile, FormatResult]]:
        """
        Format the files in worker processes and yield the results in the order of the files.

        The number of workers is limited by the number of files, and if only one worker would be used,
        the files are formatted in the current process.

        Yields:
            Source file with the result of its formatting.

        """
        if not source_files:
            return
        workers = get_workers_count(self.config_manager.default_config.jobs, len(source_files))
        if workers == 1:
            for source_file in source_files:
                yield source_file, self.format_file(source_file)
            return
        from robocop.formatter.parallel import format_in_workers  # noqa: PLC0415

        yield from zip(source_files, format_in_workers(source_files, workers), strict=True)

    def handle_result(self, source_file: SourceFile, result: FormatResult, stdin: bool) -> None:
        """Report the result of formatting the file and store it in the cache."""
        self.config = source_file.config
        if result.error is not None:
            if not source_file.config.silent:  # TODO stderr
                print(f"Failed to decode {source_file.path} with an error: {result.error}\nSkipping file")
            return
        if result.changed:
            self.log_formatted_source(source_file.path, stdin)
            self.print_diff(result.diff_lines)
        # Cache result only if a file does not need formatting or was formatted (no --check and --no-overwrite)
        if self._can_use_cache(source_file) and (not result.changed or self.config.formatter.overwrite):
            self.config_manager.cache.set_formatter_entry(
                source_file.path, source_file.config.hash, needs_formatting=False
            )

    @staticmethod
    def _can_use_cache(source_file: SourceFile) -> bool:
        """Return whether the file's formatter configuration allows cache use."""
        formatter_config = source_file.config.formatter
        return (
            source_file.config.cache.enabled
            and formatter_config.start_line is None
            and formatter_config.end_line is None
        )

    def formatting_result(self, all_files: int, changed_files: int, skipped_files: int, stdin: bool) -> int:
        """Print formatting summary and return status code."""
        if not stdin and not self.config_manager.default_config.silent:
            all_files = all_files - changed_files - skipped_files
            all_files_plurar = "" if all_files == 1 else "s"
            changed_files_plurar = "" if changed_files == 1 else "s"
            skipped_files_plurar = "" if skipped_files == 1 else "s"

            future_tense = "" if self.config.formatter.overwrite else " would be"
            print(
                f"\n{changed_files} file{changed_files_plurar}{future_tense} reformatted, "
                f"{all_files} file{all_files_plurar}{future_tense} left unchanged."
                + (f" {skipped_files} file{skipped_files_plurar}{future_tense} skipped." if skipped_files else "")
            )
        if changed_files and self.config_manager.default_config.formatter.check:
            exit_code = 1
        else:
            exit_code = 0
        if self.config_manager.default_config.formatter.return_result:
            return exit_code
        raise typer.Exit(code=exit_code)

    def log_formatted_source(self, source: Path, stdin: bool) -> None:
        if stdin or self.config.silent:
            return
        if not self.config.formatter.overwrite:
            print(f"Would reformat {source}")  # TODO: replace prints with typer equivalent (if needed)
        else:
            print(f"Reformatted {source}")

    @staticmethod
    def load_from_stdin() -> str:
        return sys.stdin.read()

    def print_to_stdout(self, collected_lines: StatementLinesCollector) -> None:
        if not self.config.formatter.diff:
            print(collected_lines.text)

    def print_diff(self, lines: list[str]) -> None:
        if not self.config.formatter.diff or not lines:
            return
        # TODO: handle printing with rich console, with markup disabled
        if self.config.formatter.color:
            output = misc.decorate_diff_with_color(lines)
        else:
            output = misc.escape_rich_markup(lines)
        for line in output:
            console.print(line, end="", highlight=False, soft_wrap=True)
