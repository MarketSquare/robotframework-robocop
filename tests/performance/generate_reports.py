"""
Generate performance reports.

Reports from previous runs are stored in the reports folder and can be used for comparison.

Each report is run multiple times and calculates a trimmed mean by excluding the bottom and top values (according to
cut_off parameter).
"""

import json
import sys
import tempfile
import time
from functools import wraps
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from robocop import __version__
from robocop.formatter.formatters import FORMATTERS
from robocop.run import check_files, format_files
from tests import working_directory

try:
    from robocop.config.manager import ConfigManager
    from robocop.version_handling import Version
except ImportError:  # < 7.3.0
    from robocop.config import ConfigManager
    from robocop.linter.utils.misc import Version


LINTER_TESTS_DIR = Path(__file__).parent.parent / "linter"
TEST_DATA = Path(__file__).parent / "test_data"
ROBOCOP_VERSION = Version(__version__)
REPORTS = {}


def performance_report(runs: int = 100, cut_off: int = 0):
    """
    Use as decorator to measure performance of a function and store results.

    Args:
        runs: Number of runs to take into account when calculating the average.
        cut_off: Number of slowest and fastest runs to exclude from the average.

    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            report_name = kwargs.get("report_name", "")
            print(report_name)
            run_times = []
            counter = 0
            for run in range(runs):
                print(f"Run {run + 1} / {runs} of {func.__name__}")
                start = time.perf_counter()
                counter = func(*args, **kwargs)
                time_taken = time.perf_counter() - start
                run_times.append(time_taken)
                print(f"  Execution time: {time_taken:.6f} seconds")
            run_times.sort()
            if cut_off:
                run_times = run_times[cut_off:-cut_off]
            avg_time = sum(run_times) / len(run_times)
            print(f"Mean average execution time over {runs} runs: {avg_time:.6f} seconds")
            if report_name:
                if func.__name__ not in REPORTS:
                    REPORTS[func.__name__] = {}
                REPORTS[func.__name__][report_name] = {"avg_time": avg_time, "counter": counter}
            else:
                REPORTS[func.__name__] = {"avg_time": avg_time, "counter": counter}

        return wrapper

    return decorator


@performance_report(runs=10, cut_off=2)
def project_traversing_report() -> int:
    """
    Measure how long it takes to traverse Robocop repository files.

    We are using the `` tests / linter `` directory as a reference.

    Returns the number of files found (to take into account the growing number of files with each release).
    """
    main_dir = Path(__file__).parent.parent.parent
    with working_directory(main_dir):
        config_manager = ConfigManager(
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
        for _source_file in config_manager.paths:
            files_count += 1
    return files_count


@performance_report(runs=10, cut_off=2)
def formatter_report(formatter: str, report_name: str, **kwargs) -> int:  # noqa: ARG001
    """Measure how long it takes to format test files using a specific formatter."""
    main_dir = Path(__file__).parent.parent.parent
    formatter_dir = main_dir / "tests" / "formatter" / "formatters" / formatter
    if not formatter_dir.exists():
        return 0
    source_dir = formatter_dir / "source"
    with working_directory(formatter_dir):
        format_files([source_dir], select=[formatter], overwrite=False, return_result=True, silent=True, **kwargs)
    return len(list(source_dir.iterdir()))


@performance_report(runs=5)
def linter_report(report_name: str, **kwargs) -> int:  # noqa: ARG001
    """Measure how long it takes to lint all linter test files."""
    main_dir = Path(__file__).parent.parent.parent
    linter_dir = main_dir / "tests" / "linter"
    with working_directory(linter_dir):
        check_files(return_result=True, select=["ALL"], **kwargs)
    return len(list(linter_dir.glob("**/*.robot")))


@performance_report(runs=1)
def lint_large_file(report_name: str, lint_dir: Path, **kwargs) -> int:  # noqa: ARG001
    """Measure how long it takes to lint a large file."""
    with working_directory(lint_dir):
        check_files(return_result=True, select=["ALL"], **kwargs)
    return 1


def merge_dictionaries(d1: dict, d2: dict) -> dict:
    """
    Merge two dictionaries recursively.

    This function is used to merge two partial reports generated by different runs.
    """
    for key, value in d2.items():
        if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
            merge_dictionaries(d1[key], value)
        else:
            d1[key] = value
    return d1


def generate_large_file(template_path: Path, output_dir: Path) -> None:
    """
    Generate a large file based on a template.

    This function is used to generate a large file for performance testing. Because of the potential size and
     complexity, it is easier to use a templated file than hardcoded one.
    """
    env = Environment(loader=FileSystemLoader(template_path.parent), autoescape=True)
    template = env.get_template(template_path.name)

    rendered_content = template.render()

    with open(f"{output_dir}/{template_path.name}", "w", encoding="utf-8") as f:
        f.write(rendered_content)


def generate_reports() -> None:
    """Entry point for generating performance reports and saving it to global REPORTS variable."""
    if Version("7.1.0") > ROBOCOP_VERSION:
        disable_cache_option = {}
    elif Version("7.1.0") == ROBOCOP_VERSION:
        disable_cache_option = {"no_cache": True}
    else:
        disable_cache_option = {"cache": False}

    if disable_cache_option:
        linter_report(report_name="with_print_cache")
    linter_report(report_name="with_print_no_cache", **disable_cache_option)
    if disable_cache_option:
        linter_report(report_name="without_print_cache", silent=True)
    linter_report(report_name="without_print_no_cache", silent=True, **disable_cache_option)
    for formatter in FORMATTERS:
        formatter_report(formatter=formatter, report_name=f"{formatter}_no_cache", **disable_cache_option)
    project_traversing_report()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        generate_large_file(TEST_DATA / "large_file.robot", temp_dir)
        lint_large_file(report_name="large_file_with_print", lint_dir=temp_dir, **disable_cache_option)
        lint_large_file(report_name="large_file_without_print", lint_dir=temp_dir, silent=True, **disable_cache_option)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        report_name = sys.argv[1].replace(".", "_")
    else:
        report_name = __version__.replace(".", "_")
    whole_run_start = time.perf_counter()
    report_path = Path(__file__).parent / "reports" / f"robocop_{report_name}.json"
    if not report_path.exists():  # additional safe guard in case we run on the same version (there was no version bump)
        generate_reports()
        print(f"Generating report in {report_path}")
        with open(report_path, "w") as fp:
            json.dump(REPORTS, fp, indent=4)
    print(f"Took {time.perf_counter() - whole_run_start:.2f} seconds to generate report.")
