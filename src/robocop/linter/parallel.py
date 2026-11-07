"""Check files in worker processes (``--jobs`` option)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from robot.errors import DataError

from robocop.cache import CachedDiagnostic
from robocop.linter.fix import FixApplier
from robocop.linter.runner import check_source_file
from robocop.parallel import FileTask, create_file_tasks, run_in_workers
from robocop.runtime.resolver import ConfigResolver

if TYPE_CHECKING:
    from collections.abc import Iterator

    from robocop.config.schema import Config
    from robocop.source_file import SourceFile


@dataclass
class CheckResult:
    """
    Picklable result of checking a single file in a worker process.

    Attributes:
        diagnostics: Found issues.
        error: Error message if the file could not be parsed.
        total_fixes: Number of fixed issues.
        applied_fixes: Number of applied fixes per rule, if any fix was applied.
        modified: Whether the file was modified (and saved) by fixes.

    """

    diagnostics: list[CachedDiagnostic] = field(default_factory=list)
    error: str | None = None
    total_fixes: int = 0
    applied_fixes: dict[tuple[str, str], int] | None = None
    modified: bool = False


class _WorkerState:
    configs: list[Config]
    config_resolver: ConfigResolver


def _init_worker(configs: list[Config]) -> None:
    _WorkerState.configs = configs
    _WorkerState.config_resolver = ConfigResolver(load_rules=True)


def _check_file(task: FileTask) -> CheckResult:
    source_file = task.build_source_file(_WorkerState.configs)
    fix_applier = FixApplier()
    try:
        diagnostics = check_source_file(source_file, _WorkerState.config_resolver, fix_applier)
    except DataError as error:
        return CheckResult(error=str(error))
    return CheckResult(
        diagnostics=[CachedDiagnostic.from_diagnostic(diagnostic) for diagnostic in diagnostics],
        total_fixes=fix_applier.fix_stats.total_fixes,
        applied_fixes=fix_applier.fix_stats.by_file.get(source_file.path),
        modified=bool(fix_applier.modified_files),
    )


def check_in_workers(source_files: list[SourceFile], workers: int) -> Iterator[CheckResult]:
    """
    Check the source files in worker processes. Fixes (if enabled) are applied and saved by the workers.

    Yields:
        Results of the checks, in the order of the source files.

    """
    tasks, configs = create_file_tasks(source_files)
    yield from run_in_workers(_check_file, tasks, workers, _init_worker, (configs,))
