"""
Generate performance reports.

Reports from previous runs are stored in the reports folder and can be used for comparison.

Each report is run multiple times and calculates a trimmed mean by excluding the bottom and top 10% of values.
"""

import json
import time
from functools import wraps
from pathlib import Path

from robocop import __version__, config
from tests import working_directory

LINTER_TESTS_DIR = Path(__file__).parent.parent / "linter"
REPORTS = {}


def performance_report(runs=100):
    """Use as decorator to measure performance of a function and store results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            run_times = []
            counter = 0
            for run in range(runs):
                print(f"Run {run + 1} / {runs} of {func.__name__}")
                start = time.perf_counter()
                counter = func(*args, **kwargs)
                end = time.perf_counter()
                time_taken = end - start
                run_times.append(time_taken)
                print(f"  Execution time: {time_taken:.6f} seconds")
            run_times.sort()
            cut_off = int(runs * 0.1)
            if cut_off + 2 > runs:
                cut_off = 0
            avg_time = sum(run_times[cut_off:-cut_off]) / (len(run_times) - 2 * cut_off)
            print(f"Mean average execution time over {runs} runs: {avg_time:.6f} seconds")
            REPORTS[func.__name__] = {"avg_time": avg_time, "counter": counter}

        return wrapper

    return decorator


@performance_report(runs=100)
def project_traversing_report() -> int:
    """
    Measure how long it takes to traverse Robocop repository files.

    We are using the `` tests / linter `` directory as a reference.

    Returns number of files found (to take into account growing number of files with each release).
    """
    # LINTER_TESTS_DIR
    main_dir = Path(__file__).parent.parent.parent
    with working_directory(main_dir):
        config_manager = config.ConfigManager(
            sources=["tests/linter"],
            config=None,
            root=None,
            ignore_git_dir=False,
            ignore_file_config=False,
            skip_gitignore=False,
            force_exclude=False,
            overwrite_config=None,
        )
        files_count = 0
        for _source, _config in config_manager.paths:
            files_count += 1
    return files_count


if __name__ == "__main__":
    project_traversing_report()

    report_path = Path(__file__).parent / "reports" / f"robocop_{__version__.replace('.', '_')}.json"
    with open(report_path, "w") as fp:
        json.dump(REPORTS, fp, indent=4)
