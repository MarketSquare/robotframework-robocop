from timeit import default_timer as timer

import robocop.linter.reports
from robocop.config import Config


class TimeTakenReport(robocop.linter.reports.ComparableReport):
    """
    **Report name**: ``scan_timer``

    Report that returns Robocop execution time

    Example::

        Scan finished in 0.054s.
    """

    def __init__(self, config: Config):
        self.name = "scan_timer"
        self.description = "Returns Robocop execution time"
        self.start_time = timer()
        self.time_taken = "0.000"
        super().__init__(config)

    def persist_result(self):
        return {"time_taken": self.time_taken}

    def generate_report(self, prev_results: dict, **kwargs) -> None:  # noqa: ARG002
        time_taken = timer() - self.start_time
        if self.compare_runs and prev_results:
            rerun_diff = time_taken - float(prev_results["time_taken"])
            prefix = "+" if rerun_diff >= 0 else ""
            diff = f" ({prefix}{rerun_diff:.3f})"
        else:
            diff = ""
        self.time_taken = f"{time_taken:.3f}"
        print(f"\nScan finished in {self.time_taken}s{diff}.")
