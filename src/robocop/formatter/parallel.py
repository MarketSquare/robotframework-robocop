"""Format files in worker processes (``--jobs`` option)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.formatter.runner import FileFormatter, FormatResult
from robocop.parallel import FileTask, create_file_tasks, run_in_workers

if TYPE_CHECKING:
    from collections.abc import Iterator

    from robocop.config.schema import Config
    from robocop.source_file import SourceFile


class _WorkerState:
    configs: list[Config]
    formatter: FileFormatter


def _init_worker(configs: list[Config]) -> None:
    _WorkerState.configs = configs
    _WorkerState.formatter = FileFormatter(configs[0])


def _format_file(task: FileTask) -> FormatResult:
    return _WorkerState.formatter.format_file(task.build_source_file(_WorkerState.configs))


def format_in_workers(source_files: list[SourceFile], workers: int) -> Iterator[FormatResult]:
    """
    Format the source files in worker processes. Formatted files are saved by the workers (if overwrite is enabled).

    Yields:
        Results of the formatting, in the order of the source files.

    """
    tasks, configs = create_file_tasks(source_files)
    yield from run_in_workers(_format_file, tasks, workers, _init_worker, (configs,))
