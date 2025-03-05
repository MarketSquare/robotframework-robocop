from __future__ import annotations

import os
import sys
from difflib import unified_diff
from typing import TYPE_CHECKING

from rich import console
from robot.api import get_model
from robot.errors import DataError

from robocop.formatter import disablers  # TODO compare robocop vs robotidy disablers, if we can merge something
from robocop.formatter.utils import misc

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing import File

    from robocop.config import Config, ConfigManager


console = console.Console()


class RobocopFormatter:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config: Config = self.config_manager.default_config

    def get_model(self, source: Path) -> File:
        if misc.rf_supports_lang():
            return get_model(source, lang=self.config.formatter.languages)
        return get_model(source)

    def run(self):
        changed_files = 0
        skipped_files = 0
        all_files = 0
        previous_changed_files = 0  # TODO: hold in one container
        stdin = False
        for source, config in self.config_manager.paths:
            try:
                # stdin = False
                # if str(source) == "-":
                #     stdin = True
                #     if self.config.verbose:
                #         click.echo("Loading file from stdin")
                #     source = self.load_from_stdin()
                if self.config.verbose:
                    print(f"Formatting {source} file")
                self.config = config
                all_files += 1
                disabler_finder = disablers.RegisterDisablers(
                    self.config.formatter.start_line, self.config.formatter.end_line
                )
                previous_changed_files = changed_files
                model = self.get_model(source)
                model_path = model.source or source
                disabler_finder.visit(model)
                if disabler_finder.is_disabled_in_file(disablers.ALL_FORMATTERS):
                    continue
                diff, old_model, new_model, model = self.format_until_stable(model, disabler_finder)
                # if stdin:
                #     self.print_to_stdout(new_model)
                if diff:
                    self.save_model(model_path, model)
                    self.log_formatted_source(source, stdin)
                    self.output_diff(model_path, old_model, new_model)
                    changed_files += 1
            except DataError as err:
                print(f"Failed to decode {source} with an error: {err}\nSkipping file")  # TODO stderr
                changed_files = previous_changed_files
                skipped_files += 1
        return self.formatting_result(all_files, changed_files, skipped_files, stdin)

    def formatting_result(self, all_files: int, changed_files: int, skipped_files: int, stdin: bool) -> int:
        """Print formatting summary and return status code."""
        if not stdin:
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
        if not self.config_manager.default_config.formatter.check or not changed_files:
            return 0
        return 1  # FIXME: ensure proper exit status is returned

    def format_until_stable(self, model: File, disabler_finder: disablers.RegisterDisablers):
        diff, old_model, new_model = self.format(model, disabler_finder.disablers)
        reruns = self.config.formatter.reruns
        while diff and reruns:
            model = get_model(new_model.text)
            disabler_finder.visit(model)
            new_diff, _, new_model = self.format(model, disabler_finder.disablers)
            if not new_diff:
                break
            reruns -= 1
        return diff, old_model, new_model, model

    def format(
        self, model: File, disablers: disablers.DisablersInFile
    ) -> tuple[bool, misc.StatementLinesCollector, misc.StatementLinesCollector]:
        old_model = misc.StatementLinesCollector(model)
        for name, formatter in self.config.formatter.formatters.items():
            formatter.disablers = disablers  # set dynamically to allow using external formatters
            if disablers.is_disabled_in_file(name):
                continue
            formatter.visit(model)
        new_model = misc.StatementLinesCollector(model)
        return new_model != old_model, old_model, new_model

    def log_formatted_source(self, source: Path, stdin: bool):
        if stdin:
            return
        if not self.config.formatter.overwrite:
            print(f"Would reformat {source}")  # TODO: replace prints with typer equivalent (if needed)
        else:
            print(f"Reformatted {source}")

    @staticmethod
    def load_from_stdin() -> str:
        return sys.stdin.read()

    def print_to_stdout(self, collected_lines):
        if not self.config.formatter.diff:
            print(collected_lines.text)

    def save_model(self, source, model):
        if self.config.formatter.overwrite:
            output = self.config.formatter.output or source
            misc.ModelWriter(output=output, newline=self.get_line_ending(source)).write(model)

    def get_line_ending(self, path: str):
        if self.config.formatter.whitespace_config.line_ending == "auto":
            with open(path) as f:
                f.readline()
                if f.newlines is None:
                    return os.linesep
                if isinstance(f.newlines, str):
                    return f.newlines
                return f.newlines[0]
        return self.config.formatter.whitespace_config.line_ending

    def output_diff(self, path: Path, old_model: misc.StatementLinesCollector, new_model: misc.StatementLinesCollector):
        if not self.config.formatter.diff:
            return
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
