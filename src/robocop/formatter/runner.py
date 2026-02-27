from __future__ import annotations

import os
import sys
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
from robocop.runtime.resolver import ConfigResolver
from robocop.source_file import SourceFile, StatementLinesCollector

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing import File

    from robocop.config.manager import ConfigManager
    from robocop.config.schema import Config
    from robocop.runtime.resolved_config import ResolvedConfig


console = Console()


class RobocopFormatter:
    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.config_resolver = ConfigResolver(load_formatters=True)
        self.config: Config = self.config_manager.default_config

    def run(self) -> int:
        changed_files = 0
        skipped_files = 0
        all_files = 0
        cached_files = 0
        previous_changed_files = 0  # TODO: hold in one container
        stdin = False

        for source_file in self.config_manager.paths:
            try:
                # stdin = False
                # if str(source) == "-":
                #     stdin = True
                #     if self.config.verbose:
                #         click.echo("Loading file from stdin")
                #     source = self.load_from_stdin()
                if self.config.verbose:
                    print(f"Formatting {source_file.path} file")
                self.config = source_file.config

                all_files += 1

                if source_file.config.cache.enabled:
                    # Check cache - if file hasn't changed and didn't need formatting before, skip it
                    cached_entry = self.config_manager.cache.get_formatter_entry(
                        source_file.path, source_file.config.hash
                    )
                    if cached_entry is not None and not cached_entry.needs_formatting:
                        # File hasn't changed and didn't need formatting - skip it
                        cached_files += 1
                        continue
                previous_changed_files = changed_files
                diff, old_model, new_model, model = self.format_until_stable(source_file)
                # if stdin:
                #     self.print_to_stdout(new_model)
                if diff and old_model and new_model:
                    model_path = model.source or source_file.path
                    self.save_model(model_path, model)
                    self.log_formatted_source(source_file.path, stdin)
                    self.output_diff(model_path, old_model, new_model)
                    changed_files += 1
                # Cache result - after formatting (or if no changes needed), file is now clean
                self.config_manager.cache.set_formatter_entry(
                    source_file.path, source_file.config.hash, needs_formatting=False
                )
            except DataError as err:
                if not source_file.config.silent:
                    print(f"Failed to decode {source_file.path} with an error: {err}\nSkipping file")  # TODO stderr
                changed_files = previous_changed_files
                skipped_files += 1

        # Save cache at the end
        self.config_manager.cache.save()

        if self.config_manager.default_config.verbose and cached_files > 0:
            print(f"Skipped {cached_files} unchanged files from cache.")

        return self.formatting_result(all_files, changed_files, skipped_files, stdin)

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

    def format_until_stable(
        self, source_file: SourceFile
    ) -> tuple[bool, StatementLinesCollector | None, StatementLinesCollector | None, File]:
        model = source_file.model
        resolved_config = self.config_resolver.resolve_config(source_file.config)
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

    def save_model(self, source: Path, model: File) -> None:
        if self.config.formatter.overwrite:
            output = self.config.formatter.output or source
            misc.ModelWriter(output=str(output), newline=self.get_line_ending(str(source))).write(model)

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

    def output_diff(
        self,
        path: Path,
        old_model: StatementLinesCollector,
        new_model: StatementLinesCollector,
    ) -> None:
        if not self.config.formatter.diff:
            return
        # TODO: handle printing with rich console, with markup disabled
        old = [line + "\n" for line in old_model.text.splitlines()]
        new = [line + "\n" for line in new_model.text.splitlines()]
        lines = list(unified_diff(old, new, fromfile=f"{path}\tbefore", tofile=f"{path}\tafter"))
        if not lines:
            return
        if self.config.formatter.color:
            output = misc.decorate_diff_with_color(lines)
        else:
            output = misc.escape_rich_markup(lines)
        for line in output:
            console.print(line, end="", highlight=False, soft_wrap=True)
