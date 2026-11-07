"""Helpers for processing files in parallel, in separate worker processes."""

from __future__ import annotations

import contextlib
import io
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any, TypeVar

from robocop import files
from robocop.source_file import build_source_file

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from pathlib import Path

    from robocop.config.schema import Config
    from robocop.source_file import SourceFile

_T = TypeVar("_T")
_R = TypeVar("_R")

# Starting a worker process and loading the configuration in it has a fixed cost, so every worker should get enough
# files to make it worth it.
MIN_FILES_PER_WORKER = 20
# Files are sent to the workers in chunks to limit the communication overhead. Every worker gets several chunks,
# so that the work is balanced when the files have different sizes.
CHUNKS_PER_WORKER = 8


def get_cpu_count() -> int:
    process_cpu_count = getattr(os, "process_cpu_count", None)  # Python 3.13+
    count = process_cpu_count() if process_cpu_count is not None else os.cpu_count()
    return count or 1


def get_workers_count(jobs: int, tasks_count: int) -> int:
    """
    Return the number of worker processes used to process the given number of tasks.

    Args:
        jobs: Requested number of processes. 0 means the number of available CPUs.
        tasks_count: Number of tasks (files) to process.

    Returns:
        Number of worker processes. 1 means that the tasks should be processed in the current process.

    """
    if jobs == 0:
        jobs = get_cpu_count()
    return max(1, min(jobs, math.ceil(tasks_count / MIN_FILES_PER_WORKER)))


def split_into_chunks(items: Sequence[_T], workers: int) -> list[list[_T]]:
    chunk_size = max(1, math.ceil(len(items) / (workers * CHUNKS_PER_WORKER)))
    return [list(items[start : start + chunk_size]) for start in range(0, len(items), chunk_size)]


@dataclass(frozen=True)
class FileTask:
    """Picklable reference to the source file processed in a worker process."""

    path: Path
    resolved_path: Path
    config_index: int

    def build_source_file(self, configs: list[Config]) -> SourceFile:
        files.mark_resolved(self.path, self.resolved_path)
        return build_source_file(self.path, configs[self.config_index])


def create_file_tasks(source_files: list[SourceFile]) -> tuple[list[FileTask], list[Config]]:
    """
    Create tasks for the source files.

    Source files share a limited number of configurations, so the configurations are sent to every worker only
    once (with the initializer) and the tasks refer to them by the index.

    Returns:
        Tasks in the order of the source files, and the list of the distinct configurations.

    """
    configs: list[Config] = []
    config_indexes: dict[int, int] = {}
    tasks = []
    for source_file in source_files:
        index = config_indexes.get(id(source_file.config))
        if index is None:
            index = config_indexes[id(source_file.config)] = len(configs)
            configs.append(source_file.config)
        tasks.append(FileTask(source_file.path, source_file.resolved_path, index))
    return tasks, configs


def _process_chunk(func: Callable[[_T], _R], items: list[_T]) -> list[tuple[_R, str]]:
    """
    Process the chunk of items in the worker process.

    Output printed while processing the item (for example warnings) is captured, so that it can be printed by the
    main process in the order of the items, instead of being mixed with the output of other workers.

    Returns:
        Result of every item, together with its captured output.

    """
    results = []
    for item in items:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = func(item)
        results.append((result, buffer.getvalue()))
    return results


def run_in_workers(
    func: Callable[[_T], _R],
    items: Sequence[_T],
    workers: int,
    initializer: Callable[..., None],
    initargs: tuple[Any, ...],
) -> Iterator[_R]:
    """
    Process items in worker processes and yield the results in the same order as the items.

    Args:
        func: Function processing a single item. It must be picklable (defined at the module level).
        items: Items to process.
        workers: Number of worker processes.
        initializer: Function called once in every worker process, before processing any item.
        initargs: Arguments passed to the initializer.

    Yields:
        Results for the items, in the order of the items. Output printed by the worker while processing the item is
        printed just before its result is yielded.

    """
    chunks = split_into_chunks(items, workers)
    with ProcessPoolExecutor(max_workers=workers, initializer=initializer, initargs=initargs) as executor:
        for chunk_results in executor.map(partial(_process_chunk, func), chunks):
            for result, output in chunk_results:
                if output:
                    sys.stdout.write(output)
                yield result
