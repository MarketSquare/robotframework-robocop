"""
Script for merging performance reports and calculating % difference.

Generate reports script generates a report for each tested version under the ``reports`` subdirectory.
We are iterating over the files and aggregating the results. We are comparing the current result with the previous
version to calculate the percentage difference.

Results are saved in the perf_report.md file in Markdown format (for GitHub).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
REPORTS_DIR = Path(__file__).parent / "reports"
REPORT_TEST = {
    "project_traversing_report": "Project traversal",
    "linter_report.with_print_cache": "Linting (print+cache)",
    "linter_report.with_print_no_cache": "Linting (print+no cache)",
    "linter_report.without_print_cache": "Linting (no print+cache)",
    "linter_report.without_print_no_cache": "Linting (no print+no cache)",
    "lint_large_file.large_file_with_print": "Linting (large file with print)",
    "lint_large_file.large_file_without_print": "Linting (large file without print)",
    "formatter_report": "Formatting",
}


def load_reports(directory: Path) -> dict[str, dict]:
    reports: dict[str, dict] = {}
    for report_path in sorted(directory.glob("*.json")):
        version_str = report_path.stem.replace("robocop_", "").replace("_", ".")
        reports[version_str] = json.loads(report_path.read_text())

    # Sort reports by version
    return dict(sorted(reports.items(), key=lambda item: item[0]))


def calculate_total_time(data: dict, report_key: str) -> float | None:
    """
    Calculate total time for a given report key.

    If a report key is a subreport, we need to sum all values (for example sum total time for all formatters).

    Args:
        data (dict): A dictionary that contains report categories and their associated metrics.
        report_key (str): A string representing the key for the report. It can be in
            the format 'category.name' to specify a nested report.

    Returns:
        float | None: The average time for the report. None if no average time is found.

    """
    if "." in report_key:
        category, name = report_key.split(".")
        values = data.get(category, {}).get(name, {"avg_time": None})
    else:
        values = data.get(report_key, {"avg_time": None})

    if "avg_time" not in values:
        # Handle cases where we need to sum sub-reports
        return sum(v["avg_time"] for v in data[report_key].values())
    return values["avg_time"]


def generate_rows(reports: dict[str, dict]) -> list[dict]:
    """Iterate over the report files and return aggregated report metrics."""
    rows = []
    for version, data in reports.items():
        current_metrics = {}
        for report_key, report_title in REPORT_TEST.items():
            total_time = calculate_total_time(data, report_key)
            current_metrics[report_title] = {"total_time": total_time, "repr": "-"}

            if total_time is None:
                continue

            if not rows:
                current_metrics[report_title]["repr"] = f"{total_time:.3f}s"
            else:
                prev_val = rows[-1].get(report_title, {}).get("total_time")
                if prev_val:
                    diff = round((total_time - prev_val) / prev_val * 100, 2)
                    current_metrics[report_title]["repr"] = f"{total_time:.3f}s (**{diff}%**)"
                else:
                    current_metrics[report_title]["repr"] = f"{total_time:.3f}s"

        rows.append({"Version": {"repr": version}, **current_metrics})
    return rows


def save_markdown_table(rows: list[dict]) -> None:
    if not rows:
        return
    headers = rows[0].keys()
    lines = [
        "## Performance Report\n",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    lines.extend(["| " + " | ".join(str(row[h]["repr"]) for h in headers) + " |" for row in reversed(rows)])
    output_file = ROOT / "perf_report.md"
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    all_reports = load_reports(REPORTS_DIR)
    report_rows = generate_rows(all_reports)
    save_markdown_table(report_rows)
