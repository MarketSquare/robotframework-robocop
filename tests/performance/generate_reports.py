"""
Generate performance reports.

Reports from previous runs are stored in the reports folder and can be used for comparison.

Each report is run multiple times and calculates a trimmed mean by excluding the bottom and top 10% of values.
"""

import json
import tempfile
import time
from functools import wraps
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from robocop import __version__, config
from robocop.formatter.formatters import FORMATTERS
from robocop.run import check_files, format_files
from tests import working_directory

LINTER_TESTS_DIR = Path(__file__).parent.parent / "linter"
TEST_DATA = Path(__file__).parent / "test_data"
REPORTS = {}


def performance_report(runs: int = 100):
    """Use as decorator to measure performance of a function and store results."""

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
                end = time.perf_counter()
                time_taken = end - start
                run_times.append(time_taken)
                print(f"  Execution time: {time_taken:.6f} seconds")
            run_times.sort()
            cut_off = int(runs * 0.1)
            if cut_off + 2 > runs:
                cut_off = 0
            if len(run_times) > 2:
                avg_time = sum(run_times[cut_off:-cut_off]) / (len(run_times) - 2 * cut_off)
            else:
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


@performance_report(runs=50)
def project_traversing_report() -> int:
    """
    Measure how long it takes to traverse Robocop repository files.

    We are using the `` tests / linter `` directory as a reference.

    Returns the number of files found (to take into account the growing number of files with each release).
    """
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


@performance_report(runs=50)
def formatter_report(formatter: str, report_name: str, cache: bool = True) -> int:  # noqa: ARG001
    main_dir = Path(__file__).parent.parent.parent
    formatter_dir = main_dir / "tests" / "formatter" / "formatters" / formatter
    with working_directory(formatter_dir):
        format_files(["source"], select=[formatter], overwrite=False, return_result=True, silent=True, cache=cache)
    source_dir = formatter_dir / "source"
    return len(list(source_dir.iterdir()))


@performance_report(runs=10)
def linter_report(report_name: str, **kwargs) -> int:  # noqa: ARG001
    main_dir = Path(__file__).parent.parent.parent
    linter_dir = main_dir / "tests" / "linter"
    with working_directory(linter_dir):
        check_files(return_result=True, select=["ALL"], **kwargs)
    return len(list(linter_dir.glob("**/*.robot")))


@performance_report(runs=2)
def lint_large_file(report_name: str, lint_dir: Path, **kwargs) -> int:  # noqa: ARG001
    with working_directory(lint_dir):
        check_files(return_result=True, select=["ALL"], cache=False, **kwargs)
    return 1


def merge_dictionaries(d1: dict, d2: dict) -> dict:
    for key, value in d2.items():
        if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
            merge_dictionaries(d1[key], value)
        else:
            d1[key] = value
    return d1


def generate_large_file(template_path: Path, output_dir: Path) -> None:
    env = Environment(loader=FileSystemLoader(template_path.parent), autoescape=True)
    template = env.get_template(template_path.name)

    rendered_content = template.render()

    with open(f"{output_dir}/{template_path.name}", "w", encoding="utf-8") as f:
        f.write(rendered_content)


if __name__ == "__main__":
    # TODO: prepare i.e. nox script to install external robocops and run this script
    # So we can generate reports for multiple past versions. It is important since the actual seconds change depending
    # on where we run the script from, but the % change between version should be comparable. Also we can use new tests
    # on old versions
    linter_report(report_name="with_print_cache", cache=True)
    linter_report(report_name="with_print_no_cache", cache=False)
    linter_report(report_name="without_print_cache", silent=True, cache=True)
    linter_report(report_name="without_print_no_cache", silent=True, cache=False)
    for formatter in FORMATTERS:
        formatter_report(formatter=formatter, report_name=formatter)
        formatter_report(formatter=formatter, report_name=f"{formatter}_no_cache", cache=False)
    project_traversing_report()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        generate_large_file(TEST_DATA / "large_file.robot", temp_dir)
        lint_large_file(report_name="large_file_with_print", lint_dir=temp_dir)
        lint_large_file(report_name="large_file_without_print", lint_dir=temp_dir, silent=True)

    report_path = Path(__file__).parent / "reports" / f"robocop_{__version__.replace('.', '_')}.json"
    if report_path.exists():
        with open(report_path) as fp:
            prev_report = json.load(fp)
            REPORTS = merge_dictionaries(prev_report, REPORTS)

    with open(report_path, "w") as fp:
        json.dump(REPORTS, fp, indent=4)
