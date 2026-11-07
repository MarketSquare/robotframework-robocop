from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from difflib import unified_diff
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from robot.api import get_model
from robot.errors import DataError

from robocop.formatter import (
    disablers,  # TODO compare robocop vs robotidy disablers, if we can merge something
)
from robocop.formatter.utils import misc
from robocop.parallel import get_workers_count
from robocop.runtime.resolver import ConfigResolver
from robocop.source_file import SourceFile, StatementLinesCollector

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
        disabler_finder.visit(model)
        if disabler_finder.is_disabled_in_file(disablers.ALL_FORMATTERS):
            return False, None, None, model
        diff, old_model, new_model = self.format(model, disabler_finder.disablers, resolved_config)
        reruns = self.config.formatter.reruns
        while diff and reruns:
            model = get_model(new_model.text)
            disabler_finder.visit(model)
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
        Format every Robot code block embedded in a Markdown or Python file independently.

        Each block is formatted on its own, re-indented to its original position and spliced back into the physical
        file, leaving prose, fences and indentation of the surrounding document untouched.

        Returns:
            Tuple of (changed, original_text, new_text) with the full physical file contents.

        """
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

    def format_block(self, model: File, resolved_config: ResolvedConfig) -> str | None:
        """
        Run the configured formatters on a single block model.

        Returns:
            The formatted block text, or ``None`` if the block is unchanged or fully disabled.

        """
        disabler_finder = disablers.RegisterDisablers(self.config.formatter.start_line, self.config.formatter.end_line)
        disabler_finder.visit(model)
        if disabler_finder.is_disabled_in_file(disablers.ALL_FORMATTERS):
            return None
        original_text = StatementLinesCollector(model).text
        formatted = self._apply_formatters(model, disabler_finder.disablers, resolved_config)
        reruns = self.config.formatter.reruns
        while formatted != original_text and reruns:
            rerun_model = get_model(formatted)
            rerun_disablers = disablers.RegisterDisablers(
                self.config.formatter.start_line, self.config.formatter.end_line
            )
            rerun_disablers.visit(rerun_model)
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

            if source_file.config.cache.enabled:
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
        if not result.changed or self.config.formatter.overwrite:
            self.config_manager.cache.set_formatter_entry(
                source_file.path, source_file.config.hash, needs_formatting=False
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
