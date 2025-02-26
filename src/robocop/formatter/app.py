import os
import sys
from difflib import unified_diff

try:
    import rich_click as click
except ImportError:  # Fails on vendored-in LSP plugin
    import click

from robot.api import get_model
from robot.errors import DataError
from robotidy import disablers
from robotidy.config import MainConfig
from robotidy.rich_console import console
from robotidy.utils import misc


class Robotidy:
    def __init__(self, main_config: "MainConfig"):
        self.main_config = main_config
        self.config = main_config.default_loaded

    def get_model(self, source):
        if misc.rf_supports_lang():
            return get_model(source, lang=self.config.language)
        return get_model(source)

    def transform_files(self):
        changed_files = 0
        skipped_files = 0
        all_files = 0
        stdin = False
        for source, config in self.main_config.get_sources_with_configs():
            self.config = config
            all_files += 1
            disabler_finder = disablers.RegisterDisablers(
                self.config.formatting.start_line, self.config.formatting.end_line
            )
            previous_changed_files = changed_files
            try:
                stdin = False
                if str(source) == "-":
                    stdin = True
                    if self.config.verbose:
                        click.echo("Loading file from stdin")
                    source = self.load_from_stdin()
                elif self.config.verbose:
                    click.echo(f"Found {source} file")
                model = self.get_model(source)
                model_path = model.source or source
                disabler_finder.visit(model)
                if disabler_finder.is_disabled_in_file(disablers.ALL_TRANSFORMERS):
                    continue
                diff, old_model, new_model, model = self.transform_until_stable(model, disabler_finder)
                if stdin:
                    self.print_to_stdout(new_model)
                elif diff:
                    self.save_model(model_path, model)
                    self.log_formatted_source(source, stdin)
                    self.output_diff(model_path, old_model, new_model)
                    changed_files += 1
            except DataError as err:
                click.echo(f"Failed to decode {source} with an error: {err}\nSkipping file", err=True)
                changed_files = previous_changed_files
                skipped_files += 1
        return self.formatting_result(all_files, changed_files, skipped_files, stdin)

    def formatting_result(self, all_files: int, changed_files: int, skipped_files: int, stdin: bool):
        """
        Print formatting summary and return status code.
        """
        if not stdin:
            all_files = all_files - changed_files - skipped_files
            all_files_plurar = "" if all_files == 1 else "s"
            changed_files_plurar = "" if changed_files == 1 else "s"
            skipped_files_plurar = "" if skipped_files == 1 else "s"

            future_tense = "" if self.config.overwrite else " would be"
            click.echo(
                f"\n{changed_files} file{changed_files_plurar}{future_tense} reformatted, "
                f"{all_files} file{all_files_plurar}{future_tense} left unchanged."
                + (f" {skipped_files} file{skipped_files_plurar}{future_tense} skipped." if skipped_files else "")
            )
        if not self.config.check or not changed_files:
            return 0
        return 1

    def log_formatted_source(self, source: str, stdin: bool):
        if stdin:
            return
        if not self.config.overwrite:
            click.echo(f"Would reformat {source}")
        else:
            click.echo(f"Reformatted {source}")

    def transform_until_stable(self, model, disabler_finder):
        diff, old_model, new_model = self.transform(model, disabler_finder.disablers)
        reruns = self.config.reruns
        while diff and reruns:
            model = get_model(new_model.text)
            disabler_finder.visit(model)
            new_diff, _, new_model = self.transform(model, disabler_finder.disablers)
            if not new_diff:
                break
            reruns -= 1
        return diff, old_model, new_model, model

    def transform(self, model, disablers):
        old_model = misc.StatementLinesCollector(model)
        for transformer in self.config.transformers:
            transformer.disablers = disablers  # set dynamically to allow using external transformers
            if disablers.is_disabled_in_file(transformer.__class__.__name__):
                continue
            transformer.visit(model)
        new_model = misc.StatementLinesCollector(model)
        return new_model != old_model, old_model, new_model

    @staticmethod
    def load_from_stdin() -> str:
        return sys.stdin.read()

    def print_to_stdout(self, collected_lines):
        if not self.config.show_diff:
            click.echo(collected_lines.text)

    def save_model(self, source, model):
        if self.config.overwrite:
            output = self.config.output or source
            misc.ModelWriter(output=output, newline=self.get_line_ending(source)).write(model)

    def get_line_ending(self, path: str):
        if self.config.formatting.line_sep == "auto":
            with open(path) as f:
                f.readline()
                if f.newlines is None:
                    return os.linesep
                if isinstance(f.newlines, str):
                    return f.newlines
                return f.newlines[0]
        return self.config.formatting.line_sep

    def output_diff(self, path: str, old_model: misc.StatementLinesCollector, new_model: misc.StatementLinesCollector):
        if not self.config.show_diff:
            return
        old = [l + "\n" for l in old_model.text.splitlines()]
        new = [l + "\n" for l in new_model.text.splitlines()]
        lines = list(unified_diff(old, new, fromfile=f"{path}\tbefore", tofile=f"{path}\tafter"))
        if not lines:
            return
        if self.config.color:
            output = misc.decorate_diff_with_color(lines)
        else:
            output = misc.escape_rich_markup(lines)
        for line in output:
            console.print(line, end="", highlight=False, soft_wrap=True)
